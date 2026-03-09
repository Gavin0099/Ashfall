#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.event_templates import instantiate_event_catalog, load_template_catalog
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState, RunState


OUTPUT_DIR = ROOT / "output" / "playability"
ANALYTICS_DIR = ROOT / "output" / "analytics"


@dataclass
class RoutePlan:
    name: str
    seed: int
    route: List[str]
    options: Dict[str, int]


def build_node_payloads() -> Dict[str, dict]:
    return {
        "node_start": {"id": "node_start", "node_type": "story", "connections": ["node_north_1", "node_south_1"], "event_pool": ["evt_departure"], "is_start": True},
        "node_north_1": {"id": "node_north_1", "node_type": "resource", "connections": ["node_north_2"], "event_pool": ["evt_scrapyard"]},
        "node_north_2": {"id": "node_north_2", "node_type": "combat", "connections": ["node_mid"], "event_pool": ["evt_tunnel"]},
        "node_south_1": {"id": "node_south_1", "node_type": "trade", "connections": ["node_south_2"], "event_pool": ["evt_village"]},
        "node_south_2": {"id": "node_south_2", "node_type": "resource", "connections": ["node_mid"], "event_pool": ["evt_floodplain"]},
        "node_mid": {"id": "node_mid", "node_type": "combat", "connections": ["node_final"], "event_pool": ["evt_checkpoint"]},
        "node_final": {"id": "node_final", "node_type": "story", "connections": [], "event_pool": ["evt_final"], "is_final": True},
    }


def build_event_catalog(seed: int) -> Dict[str, dict]:
    catalog_path = ROOT / "schemas" / "event_template_catalog.json"
    template_catalog = load_template_catalog(catalog_path)
    return instantiate_event_catalog(seed, template_catalog)


def build_enemy_catalog() -> Dict[str, dict]:
    return {
        "enemy_raider_scout": {"id": "enemy_raider_scout", "name": "Raider Scout", "hp": 5, "damage_range": {"min": 1, "max": 2}},
        "enemy_mutant_brute": {"id": "enemy_mutant_brute", "name": "Mutant Brute", "hp": 7, "damage_range": {"min": 1, "max": 3}},
    }


def route_plans() -> List[RoutePlan]:
    return [
        RoutePlan("north_aggressive", 101, ["node_north_1", "node_north_2", "node_mid", "node_final"], {"node_north_1": 0, "node_north_2": 0, "node_mid": 0, "node_final": 1}),
        RoutePlan("north_cautious", 102, ["node_north_1", "node_north_2", "node_mid", "node_final"], {"node_north_1": 1, "node_north_2": 1, "node_mid": 1, "node_final": 0}),
        RoutePlan("south_aggressive", 103, ["node_south_1", "node_south_2", "node_mid", "node_final"], {"node_south_1": 1, "node_south_2": 0, "node_mid": 0, "node_final": 1}),
        RoutePlan("south_cautious", 104, ["node_south_1", "node_south_2", "node_mid", "node_final"], {"node_south_1": 0, "node_south_2": 1, "node_mid": 1, "node_final": 0}),
        RoutePlan("mixed_pressure", 105, ["node_north_1", "node_north_2", "node_mid", "node_final"], {"node_north_1": 0, "node_north_2": 1, "node_mid": 0, "node_final": 1}),
    ]


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


def run_plan(plan: RoutePlan, nodes: Dict[str, dict], events: Dict[str, dict], enemies: Dict[str, dict]) -> dict:
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(map_state=map_state, seed=plan.seed, event_catalog=events, enemy_catalog=enemies)
    run = engine.create_run(PlayerState(hp=10, food=7, ammo=3, medkits=1), seed=plan.seed)

    pressure_count = 0
    moments = []
    decision_log = []
    for next_node in plan.route:
        if run.ended:
            break
        node = engine.move_to(run, next_node)
        option_index = plan.options.get(next_node, 0)
        outcome = engine.resolve_node_event(node, run, option_index=option_index)
        pressure = is_pressure_moment(run, events[outcome["event_id"]], option_index, outcome)
        if pressure:
            pressure_count += 1
        moments.append(
            {
                "node": next_node,
                "option_index": option_index,
                "event_outcome": outcome,
                "player": {
                    "hp": run.player.hp,
                    "food": run.player.food,
                    "ammo": run.player.ammo,
                    "medkits": run.player.medkits,
                    "radiation": run.player.radiation,
                },
                "pressure": pressure,
            }
        )
        decision_log.append(
            {
                "step": len(decision_log) + 1,
                "node": next_node,
                "event_id": outcome["event_id"],
                "option_index": option_index,
                "pressure": pressure,
                "combat_triggered": bool(outcome.get("combat_triggered", False)),
                "player_after": {
                    "hp": run.player.hp,
                    "food": run.player.food,
                    "ammo": run.player.ammo,
                    "medkits": run.player.medkits,
                    "radiation": run.player.radiation,
                },
            }
        )

    if not run.ended and run.current_node == "node_final":
        run.end(victory=True, reason="reached_final_node")

    resource_signature = (
        f"hp:{run.player.hp}|food:{run.player.food}|ammo:{run.player.ammo}|"
        f"medkits:{run.player.medkits}|scrap:{run.player.scrap}|radiation:{run.player.radiation}"
    )
    analytics = {
        "run_id": plan.name,
        "seed": plan.seed,
        "route": plan.route,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "player_final": {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "scrap": run.player.scrap,
            "radiation": run.player.radiation,
        },
        "decision_log": decision_log,
        "summary": {
            "pressure_count": pressure_count,
            "death_cause_attribution": (not run.victory and run.end_reason is not None) or run.victory,
            "resource_signature": resource_signature,
        },
    }

    return {
        "plan": plan.name,
        "seed": plan.seed,
        "route": plan.route,
        "pressure_count": pressure_count,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "player_final": {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "radiation": run.player.radiation,
        },
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
