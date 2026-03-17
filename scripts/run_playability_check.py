#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.event_templates import instantiate_event_catalog, load_template_catalog
from src.difficulty import build_starting_player
from src.enemy_catalog import load_enemy_catalog
from src.run_engine import RunEngine, build_map
from src.event_engine import pick_event_id, get_available_options
from src.run_summary import build_run_summary
from src.state_models import PlayerState, RunState, CharacterProfile


OUTPUT_DIR = ROOT / "output" / "playability"
ANALYTICS_DIR = ROOT / "output" / "analytics"


@dataclass
class RoutePlan:
    name: str
    seed: int
    route: List[str]
    options: Dict[str, int]
    difficulty: str = "normal"
    archetype: Optional[str] = None
    character_id: Optional[str] = None
    travel_mode_strategy: str = "normal"  # normal, rush, careful, dynamic"


def build_node_payloads() -> Dict[str, dict]:
    return {
        "node_start": {"id": "node_start", "node_type": "story", "connections": ["node_north_1", "node_south_1"], "event_pool": ["evt_departure"], "is_start": True},
        "node_north_1": {"id": "node_north_1", "node_type": "resource", "connections": ["node_north_2"], "event_pool": ["evt_scrapyard", "evt_factory_ruins"]},
        "node_north_2": {"id": "node_north_2", "node_type": "combat", "connections": ["node_mid"], "event_pool": ["evt_tunnel", "evt_mutant_burrow", "evt_collapsed_overpass", "evt_quest_medical_discovery"]},
        "node_south_1": {"id": "node_south_1", "node_type": "trade", "connections": ["node_south_2"], "event_pool": ["evt_village", "evt_raider_toll_bridge", "evt_quest_village_medical_request"]},
        "node_south_2": {"id": "node_south_2", "node_type": "resource", "connections": ["node_mid"], "event_pool": ["evt_floodplain", "evt_radioactive_orchard", "evt_abandoned_cache", "evt_quest_medical_discovery"]},
        "node_mid": {"id": "node_mid", "node_type": "combat", "connections": ["node_approach"], "event_pool": ["evt_checkpoint", "evt_sniper_nest", "evt_quest_medical_completion"]},
        "node_approach": {"id": "node_approach", "node_type": "story", "connections": ["node_final"], "event_pool": ["evt_waystation", "evt_emergency_beacon", "evt_quest_medical_completion"]},
        "node_final": {"id": "node_final", "node_type": "story", "connections": [], "event_pool": ["evt_final"], "is_final": True},
    }


def build_event_catalog(seed: int) -> Dict[str, dict]:
    catalog_path = ROOT / "schemas" / "event_template_catalog.json"
    quest_path = ROOT / "schemas" / "quest_events_v09.json"
    
    template_catalog = load_template_catalog(catalog_path)
    if quest_path.exists():
        quest_catalog = load_template_catalog(quest_path)
        # Merge events
        template_catalog["events"].extend(quest_catalog.get("events", []))
        
    return instantiate_event_catalog(seed, template_catalog)


def build_enemy_catalog() -> Dict[str, dict]:
    return load_enemy_catalog()


def route_plans() -> List[RoutePlan]:
    return [
        RoutePlan("north_aggressive", 101, ["node_north_1", "node_north_2", "node_mid", "node_approach", "node_final"], {"node_north_1": 0, "node_north_2": 0, "node_mid": 0, "node_approach": 1, "node_final": 1}),
        RoutePlan("north_cautious", 102, ["node_north_1", "node_north_2", "node_mid", "node_approach", "node_final"], {"node_north_1": 1, "node_north_2": 1, "node_mid": 1, "node_approach": 0, "node_final": 0}),
        RoutePlan("south_aggressive", 103, ["node_south_1", "node_south_2", "node_mid", "node_approach", "node_final"], {"node_south_1": 1, "node_south_2": 0, "node_mid": 0, "node_approach": 1, "node_final": 1}),
        RoutePlan("south_cautious", 104, ["node_south_1", "node_south_2", "node_mid", "node_approach", "node_final"], {"node_south_1": 0, "node_south_2": 1, "node_mid": 1, "node_approach": 0, "node_final": 0}),
        RoutePlan("mixed_pressure", 105, ["node_north_1", "node_north_2", "node_mid", "node_approach", "node_final"], {"node_north_1": 0, "node_north_2": 1, "node_mid": 0, "node_approach": 1, "node_final": 1}),
    ]


def snapshot_player(player: PlayerState) -> dict:
    return {
        "hp": player.hp,
        "food": player.food,
        "ammo": player.ammo,
        "medkits": player.medkits,
        "scrap": player.scrap,
        "radiation": player.radiation,
        "archetype": player.archetype,
        "character": player.character.to_dict() if player.character else None,
        "weapon_slot": player.weapon_slot.to_dict() if player.weapon_slot else None,
        "armor_slot": player.armor_slot.to_dict() if player.armor_slot else None,
        "tool_slot": player.tool_slot.to_dict() if player.tool_slot else None,
    }


def summarize_equipment_change(equipment_change: dict | None) -> str | None:
    if not equipment_change or not equipment_change.get("changed"):
        return None
    replaced = equipment_change.get("replaced") or "empty"
    item_id = equipment_change.get("item")
    return f"{equipment_change['slot']} -> {item_id} (replaced {replaced})"


def is_pressure_moment(run: RunState, event_payload: dict, option_index: int, outcome: dict) -> bool:
    option = event_payload["options"][option_index]
    effects = option.get("effects", {})
    has_negative_effect = any(value < 0 for value in effects.values())
    has_irreversible_effect = int(effects.get("radiation", 0)) > 0
    high_risk_choice = float(option.get("combat_chance", 0.0)) >= 0.5
    fragile_state = (
        run.player.hp <= 4
        or run.player.food <= 2
        or run.player.ammo <= 1
        or run.player.medkits <= 0
        or run.player.radiation >= 2
    )
    return bool(outcome.get("combat_triggered") or high_risk_choice or has_negative_effect or has_irreversible_effect or fragile_state)


def build_warning_signals(player: PlayerState, event_payload: dict, option_index: int, remaining_steps_after_choice: int) -> List[str]:
    option = event_payload["options"][option_index]
    effects = option.get("effects", {})
    warnings: List[str] = []
    projected_radiation = player.radiation + int(effects.get("radiation", 0))

    if projected_radiation > 0:
        warnings.append("WARNING: radiation will continue to threaten future travel.")
    if int(effects.get("radiation", 0)) > 0:
        warnings.append("WARNING: this option adds radiation and increases long-term risk.")
    if projected_radiation > 0 and player.hp <= projected_radiation + 1:
        warnings.append("CRITICAL: another irradiated move may kill you.")
    if player.food <= 2:
        warnings.append("WARNING: food is low and route slack is nearly gone.")
    if float(option.get("combat_chance", 0.0)) >= 0.5:
        warnings.append("DANGER: this choice carries a high combat risk.")
    if projected_radiation > 0 and player.medkits <= 0 and remaining_steps_after_choice >= 2:
        warnings.append("CRITICAL: no medkits remain to buffer future radiation attrition.")
    return warnings


def analyze_failure(decision_log: List[dict], ended: bool, victory: bool, end_reason: str | None) -> dict:
    if not ended or victory or not decision_log:
        return {
            "death_chain_length": 0,
            "primary_blame_factor": None,
            "regret_nodes": [],
            "steps_from_regret_to_death": 0,
            "is_trash_time_death": False,
        }

    weighted_nodes: List[dict] = []
    factor_totals = {"radiation": 0.0, "combat": 0.0, "resource_exhaustion": 0.0}
    total_score = 0.0
    total_steps = len(decision_log)

    for index, entry in enumerate(decision_log, start=1):
        effects = entry.get("effects", {})
        player_after = entry.get("player_after", {})
        score = 0.0
        factors: List[str] = []
        recency_weight = 1.0 + (index / max(1, total_steps)) * 0.2
        remaining_steps = total_steps - index

        radiation_delta = max(0, int(effects.get("radiation", 0)))
        if radiation_delta > 0:
            radiation_score = radiation_delta * (2.2 if end_reason == "radiation_death" else 1.0)
            score += radiation_score
            factor_totals["radiation"] += radiation_score
            factors.append("radiation")

        if entry.get("combat_triggered", False):
            combat_score = 1.8 if end_reason == "combat_death" else 0.7
            score += combat_score
            factor_totals["combat"] += combat_score
            factors.append("combat")

        hp_loss = max(0, -int(effects.get("hp", 0)))
        food_loss = max(0, -int(effects.get("food", 0)))
        if hp_loss > 0 or food_loss > 0:
            resource_score = hp_loss * 1.0 + food_loss * (1.4 if end_reason == "starvation" else 0.8)
            score += resource_score
            factor_totals["resource_exhaustion"] += resource_score
            factors.append("resource_exhaustion")

        # Carryover pressure matters even when the current event did not directly deduct resources.
        # This keeps the regret chain attached to the earlier decision that left the run with no slack.
        low_food_after = int(player_after.get("food", 0)) <= 2 and remaining_steps >= 1
        low_hp_after = int(player_after.get("hp", 0)) <= 3 and remaining_steps >= 1
        radiation_carryover = int(player_after.get("radiation", 0)) > 0 and remaining_steps >= 1
        if low_food_after:
            carryover_score = 1.2 if end_reason == "starvation" else 0.5
            score += carryover_score
            factor_totals["resource_exhaustion"] += carryover_score
            factors.append("resource_exhaustion")
        if low_hp_after:
            carryover_score = 0.7
            score += carryover_score
            factor_totals["resource_exhaustion"] += carryover_score
            factors.append("resource_exhaustion")
        if radiation_carryover:
            carryover_score = 1.4 if end_reason == "radiation_death" else 0.4
            score += carryover_score
            factor_totals["radiation"] += carryover_score
            factors.append("radiation")

        score = round(score * recency_weight, 3)
        if score <= 0:
            continue

        description_bits: List[str] = []
        if radiation_delta > 0:
            description_bits.append(f"took +{radiation_delta} radiation")
        if hp_loss > 0:
            description_bits.append(f"lost {hp_loss} hp")
        if food_loss > 0:
            description_bits.append(f"lost {food_loss} food")
        if entry.get("combat_triggered", False):
            description_bits.append("accepted combat risk")
        if low_food_after:
            description_bits.append("left food slack at 2 or less")
        if low_hp_after:
            description_bits.append("left hp at 3 or less")
        if radiation_carryover:
            description_bits.append("carried radiation into later travel")

        total_score += score
        weighted_nodes.append(
            {
                "node_id": entry["node"],
                "event_id": entry["event_id"],
                "step": index,
                "score": score,
                "description": ", ".join(description_bits) if description_bits else "risk accumulated here",
                "factors": factors,
            }
        )

    if total_score <= 0:
        return {
            "death_chain_length": 0,
            "primary_blame_factor": end_reason,
            "regret_nodes": [],
            "steps_from_regret_to_death": 0,
            "is_trash_time_death": False,
        }

    regret_nodes = []
    for item in sorted(weighted_nodes, key=lambda entry: entry["score"], reverse=True)[:3]:
        regret_nodes.append(
            {
                "node_id": item["node_id"],
                "event_id": item["event_id"],
                "blame_score": round(item["score"] / total_score, 2),
                "description": item["description"],
                "steps_to_death": total_steps - item["step"],
            }
        )

    primary_blame_factor = max(factor_totals, key=factor_totals.get) if any(value > 0 for value in factor_totals.values()) else end_reason
    is_trash_time_death = False
    for index, entry in enumerate(decision_log):
        remaining_steps = len(decision_log) - (index + 1)
        player_after = entry["player_after"]
        if (
            player_after["radiation"] > 0
            and player_after["medkits"] <= 0
            and remaining_steps >= 3
            and player_after["hp"] <= player_after["radiation"] * remaining_steps
        ):
            is_trash_time_death = True
            break

    return {
        "death_chain_length": len(regret_nodes),
        "primary_blame_factor": primary_blame_factor,
        "regret_nodes": regret_nodes,
        "steps_from_regret_to_death": regret_nodes[0]["steps_to_death"] if regret_nodes else 0,
        "is_trash_time_death": is_trash_time_death,
    }


def run_plan(plan: RoutePlan, nodes: Dict[str, dict], events: Dict[str, dict], enemies: Dict[str, dict]) -> dict:
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(
        map_state=map_state,
        seed=plan.seed,
        event_catalog=events,
        enemy_catalog=enemies,
        difficulty=plan.difficulty,
    )
    profile = None
    if plan.character_id:
        char_path = ROOT / "data" / "characters" / f"{plan.character_id}.json"
        if char_path.exists():
            char_data = json.loads(char_path.read_text(encoding="utf-8"))
            profile = CharacterProfile.from_dict(char_data)
    elif plan.archetype:
        # Legacy archetype field in RoutePlan is now background_id
        profile = CharacterProfile(
            background_id=plan.archetype,
            display_name=plan.archetype,
            special={"strength": 5, "perception": 5, "endurance": 5, "charisma": 5, "intelligence": 5, "agility": 5, "luck": 5}
        )
    player = build_starting_player(plan.difficulty, character=profile)
    run = engine.create_run(player, seed=plan.seed)

    pressure_count = 0
    moments = []
    decision_log = []
    for next_node in plan.route:
        if run.ended:
            break
        # Strategy-based travel mode
        current_travel_mode = plan.travel_mode_strategy
        if plan.travel_mode_strategy == "dynamic":
            if run.player.food <= 2 and (len(plan.route) - len(decision_log) > 1):
                current_travel_mode = "rush"
            elif run.player.hp <= 3:
                current_travel_mode = "careful"
            else:
                current_travel_mode = "normal"
        
        node = engine.move_to(run, next_node, travel_mode=current_travel_mode)
        event_id = pick_event_id(node, engine.rng, run_flags=run.flags, event_catalog=events)
        event_payload = events[event_id]
        
        # v1.0 Filter available options
        avail = get_available_options(run.player, event_payload)
        met_indices = [i for i, o in enumerate(avail) if o["is_met"]]
        
        # Try to use plan's preferred option, fallback to first met or 0
        preferred_idx = plan.options.get(next_node, 0)
        if preferred_idx in met_indices:
            option_index = preferred_idx
        elif met_indices:
            option_index = met_indices[0]
        else:
            option_index = 0 # This will still likely cause ValueError but is the last resort
        
        warning_signals = build_warning_signals(run.player, event_payload, option_index, len(plan.route) - len(decision_log) - 1)
        pre_choice_state = snapshot_player(run.player)
        outcome = engine.resolve_node_event_with_id(node, run, event_id=event_id, option_index=option_index)
        pressure = is_pressure_moment(run, events[outcome["event_id"]], option_index, outcome)
        if pressure:
            pressure_count += 1
        equipment_summary = summarize_equipment_change(outcome.get("equipment_change"))
        moments.append(
            {
                "node": next_node,
                "option_index": option_index,
                "event_outcome": outcome,
                "warning_signals": warning_signals,
                "pre_choice_state": pre_choice_state,
                "equipment_summary": equipment_summary,
                "player": snapshot_player(run.player),
                "pressure": pressure,
            }
        )
        decision_log.append(
            {
                "step": len(decision_log) + 1,
                "node": next_node,
                "event_id": outcome["event_id"],
                "option_index": option_index,
                "warning_signals": warning_signals,
                "pre_choice_state": pre_choice_state,
                "pressure": pressure,
                "combat_triggered": bool(outcome.get("combat_triggered", False)),
                "combat_loot": list(outcome.get("combat", {}).get("loot", [])) if outcome.get("combat_triggered", False) else [],
                "effects": dict(events[outcome["event_id"]]["options"][option_index].get("effects", {})),
                "equipment_change": outcome.get("equipment_change"),
                "equipment_summary": equipment_summary,
                "player_after": snapshot_player(run.player),
            }
        )

    if not run.ended and run.current_node == "node_final":
        run.end(victory=True, reason="reached_final_node")

    resource_signature = (
        f"hp:{run.player.hp}|food:{run.player.food}|ammo:{run.player.ammo}|"
        f"medkits:{run.player.medkits}|scrap:{run.player.scrap}|radiation:{run.player.radiation}|"
        f"weapon:{run.player.weapon_slot}|armor:{run.player.armor_slot}|tool:{run.player.tool_slot}"
    )
    analytics = {
        "run_id": plan.name,
        "seed": plan.seed,
        "route": plan.route,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "player_final": snapshot_player(run.player),
        "decision_log": decision_log,
        "summary": {
            "pressure_count": pressure_count,
            "death_cause_attribution": (not run.victory and run.end_reason is not None) or run.victory,
            "resource_signature": resource_signature,
        },
        "failure_analysis": analyze_failure(decision_log, run.ended, run.victory, run.end_reason),
    }
    analytics["run_summary"] = build_run_summary(
        run_id=analytics["run_id"],
        route=analytics["route"],
        ended=analytics["ended"],
        victory=analytics["victory"],
        end_reason=analytics["end_reason"],
        player_final=analytics["player_final"],
        decision_log=analytics["decision_log"],
        summary=analytics["summary"],
        failure_analysis=analytics["failure_analysis"],
    )

    return {
        "plan": plan.name,
        "seed": plan.seed,
        "route": plan.route,
        "pressure_count": pressure_count,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "player_final": snapshot_player(run.player),
        "moments": moments,
        "analytics": analytics,
    }


def evaluate_gates(results: List[dict]) -> dict:
    pressure_gate = all(r["pressure_count"] >= 3 for r in results)
    signatures = {
        (
            r["victory"],
            r["end_reason"],
            r["player_final"]["hp"],
            r["player_final"]["food"],
            r["player_final"]["ammo"],
            r["player_final"]["medkits"],
            r["player_final"]["radiation"],
        )
        for r in results
    }
    route_diversity_gate = len(signatures) >= 2
    death_runs = [r for r in results if not r["victory"]]
    death_trace_gate = all(r["end_reason"] is not None and len(r["moments"]) > 0 for r in death_runs) if death_runs else True
    rerun_signal_runs = sum(1 for r in results if r["pressure_count"] >= 3 and (not r["victory"] or r["player_final"]["food"] <= 2 or r["player_final"]["hp"] <= 3))
    rerun_signal_gate = rerun_signal_runs >= 3

    return {
        "playability_gate": {
            "pressure_choices_per_run": pressure_gate,
            "route_diversity": route_diversity_gate,
            "death_explainable_from_logs": death_trace_gate,
            "rerun_signal_3_of_5": rerun_signal_gate,
        },
        "metrics": {
            "distinct_outcome_signatures": len(signatures),
            "death_runs": len(death_runs),
            "rerun_signal_runs": rerun_signal_runs,
        },
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    plans = route_plans()

    results = [run_plan(plan, nodes, build_event_catalog(plan.seed), enemies) for plan in plans]
    for i, result in enumerate(results, start=1):
        (OUTPUT_DIR / f"run_{i}_{result['plan']}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (ANALYTICS_DIR / f"run_{i}_{result['plan']}.json").write_text(json.dumps(result["analytics"], indent=2), encoding="utf-8")

    summary = evaluate_gates(results)
    summary_payload = {"runs": results, "summary": summary}
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    analytics_summary = {
        "run_ids": [result["analytics"]["run_id"] for result in results],
        "metrics": summary["metrics"],
        "playability_gate": summary["playability_gate"],
    }
    (ANALYTICS_DIR / "summary.json").write_text(json.dumps(analytics_summary, indent=2), encoding="utf-8")

    print("Playability check completed")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
