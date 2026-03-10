#!/usr/bin/env python3
"""EXP-4: Minimal equipment slots with real acquisition flow.

Design question:
  Do event-earned equipment rewards change route evaluation when acquired
  through the normal run flow, including replacement?

Method:
  Compare the same route/policy with equipment rewards enabled vs disabled.
  This isolates the impact of acquisition/replacement from baseline event effects.

Policy:
  All runs use option_index=0 at every node so both north and south routes
  intentionally take the reward-bearing branch when available.

Equipment path in current catalog:
  north: evt_scrapyard -> makeshift_blade, evt_checkpoint -> rust_rifle
  south: evt_village -> scavenger_kit, evt_floodplain -> field_pack

Output:
  output/analytics/exp/exp4_equipment_slots.json
"""
from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
)
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState

OUTPUT_DIR = ROOT / "output" / "analytics" / "exp"

CONDITIONS = ("disabled", "enabled")
ROUTES = {
    "north": ["node_north_1", "node_north_2", "node_mid", "node_final"],
    "south": ["node_south_1", "node_south_2", "node_mid", "node_final"],
}


@dataclass
class RunRecord:
    seed: int
    condition: str
    route: str
    victory: bool = False
    end_reason: str = ""
    steps: int = 0
    final_hp: int = 0
    final_food: int = 0
    final_ammo: int = 0
    final_radiation: int = 0
    final_weapon: str | None = None
    final_tool: str | None = None
    acquisitions: list[str] = field(default_factory=list)
    replacements: int = 0


def _initial_player() -> PlayerState:
    return PlayerState(hp=10, food=6, ammo=4, medkits=2, scrap=0, radiation=0)


def _build_conditioned_catalog(seed: int, condition: str) -> dict[str, dict]:
    catalog = build_event_catalog(seed)
    if condition == "enabled":
        return catalog

    patched = copy.deepcopy(catalog)
    for payload in patched.values():
        for option in payload.get("options", []):
            option.pop("equipment_reward", None)
    return patched


def simulate_run(
    seed: int,
    condition: str,
    route_name: str,
    node_payloads: dict,
    enemy_catalog: dict,
) -> RunRecord:
    event_catalog = _build_conditioned_catalog(seed, condition)
    map_state = build_map(node_payloads, "node_start")
    engine = RunEngine(map_state, seed, event_catalog=event_catalog, enemy_catalog=enemy_catalog)
    run = engine.create_run(_initial_player(), seed)
    record = RunRecord(seed=seed, condition=condition, route=route_name)

    start_node = map_state.get_node("node_start")
    start_outcome = engine.resolve_node_event(start_node, run, option_index=0)
    start_equipment_change = start_outcome.get("equipment_change")
    if start_equipment_change and start_equipment_change.get("changed"):
        record.acquisitions.append(start_equipment_change["item"])
        if start_equipment_change.get("replaced") is not None:
            record.replacements += 1

    step = 0
    for next_node_id in ROUTES[route_name]:
        if run.ended:
            break
        step += 1
        node = engine.move_to(run, next_node_id)
        if run.ended:
            break
        outcome = engine.resolve_node_event(node, run, option_index=0)
        equipment_change = outcome.get("equipment_change")
        if equipment_change and equipment_change.get("changed"):
            record.acquisitions.append(equipment_change["item"])
            if equipment_change.get("replaced") is not None:
                record.replacements += 1

    record.steps = step
    record.victory = run.victory
    record.end_reason = run.end_reason or ""
    record.final_hp = run.player.hp
    record.final_food = run.player.food
    record.final_ammo = run.player.ammo
    record.final_radiation = run.player.radiation
    record.final_weapon = run.player.weapon_slot
    record.final_tool = run.player.tool_slot
    return record


def run_group(
    condition: str,
    route_name: str,
    seeds: list[int],
    node_payloads: dict,
    enemy_catalog: dict,
) -> list[RunRecord]:
    return [
        simulate_run(seed, condition, route_name, node_payloads, enemy_catalog)
        for seed in seeds
    ]


def summarize(records: list[RunRecord]) -> dict[str, Any]:
    n = len(records)
    wins = sum(1 for r in records if r.victory)
    deaths = [r for r in records if not r.victory]
    rad_deaths = sum(1 for r in deaths if "radiation" in r.end_reason)
    starv_deaths = sum(1 for r in deaths if "starv" in r.end_reason)
    combat_deaths = sum(1 for r in deaths if "combat" in r.end_reason)
    weapon_counts: dict[str, int] = {}
    tool_counts: dict[str, int] = {}
    for record in records:
        if record.final_weapon:
            weapon_counts[record.final_weapon] = weapon_counts.get(record.final_weapon, 0) + 1
        if record.final_tool:
            tool_counts[record.final_tool] = tool_counts.get(record.final_tool, 0) + 1

    return {
        "n": n,
        "win_rate": round(wins / n, 3),
        "radiation_death_rate": round(rad_deaths / n, 3),
        "starvation_death_rate": round(starv_deaths / n, 3),
        "combat_death_rate": round(combat_deaths / n, 3),
        "avg_final_hp": round(sum(r.final_hp for r in records) / n, 2),
        "avg_final_food": round(sum(r.final_food for r in records) / n, 2),
        "avg_final_ammo": round(sum(r.final_ammo for r in records) / n, 2),
        "avg_acquisitions": round(sum(len(r.acquisitions) for r in records) / n, 2),
        "avg_replacements": round(sum(r.replacements for r in records) / n, 2),
        "final_weapon_distribution": weapon_counts,
        "final_tool_distribution": tool_counts,
    }


def main() -> int:
    seeds = list(range(101, 151))
    node_payloads = build_node_payloads()
    enemy_catalog = build_enemy_catalog()

    print("EXP-4: Equipment slots experiment (real acquisition flow)")
    print(f"  Seeds: {seeds[0]}..{seeds[-1]}  Conditions: {CONDITIONS}  Routes: north/south")

    results: dict[str, Any] = {}
    for condition in CONDITIONS:
        for route_name in ("north", "south"):
            key = f"{condition}_{route_name}"
            summary = summarize(run_group(condition, route_name, seeds, node_payloads, enemy_catalog))
            results[key] = summary
            print(
                f"  {key:22s}: win={summary['win_rate']:.0%}  "
                f"rad={summary['radiation_death_rate']:.0%}  "
                f"starv={summary['starvation_death_rate']:.0%}  "
                f"combat={summary['combat_death_rate']:.0%}  "
                f"acq={summary['avg_acquisitions']}  repl={summary['avg_replacements']}"
            )

    deltas: dict[str, Any] = {}
    print("\n  Win rate delta (enabled - disabled):")
    for route_name in ("north", "south"):
        delta_win = round(results[f"enabled_{route_name}"]["win_rate"] - results[f"disabled_{route_name}"]["win_rate"], 3)
        delta_rad = round(
            results[f"enabled_{route_name}"]["radiation_death_rate"] - results[f"disabled_{route_name}"]["radiation_death_rate"],
            3,
        )
        delta_starv = round(
            results[f"enabled_{route_name}"]["starvation_death_rate"] - results[f"disabled_{route_name}"]["starvation_death_rate"],
            3,
        )
        deltas[route_name] = {
            "delta_win_rate": delta_win,
            "delta_radiation_death_rate": delta_rad,
            "delta_starvation_death_rate": delta_starv,
        }
        print(f"  {route_name:5s}: win={delta_win:+.3f}  rad={delta_rad:+.3f}  starv={delta_starv:+.3f}")

    impactful_routes = [
        route_name
        for route_name, delta in deltas.items()
        if abs(delta["delta_win_rate"]) >= 0.1
    ]
    verdict = {
        "status": "SUPPORTED" if impactful_routes else "WEAK",
        "impactful_routes": impactful_routes,
        "summary": (
            "Event-earned equipment changes route outcomes in at least one route."
            if impactful_routes
            else "Event-earned equipment does not materially change route outcomes."
        ),
    }

    output = {
        "experiment": "EXP-4",
        "description": "Minimal equipment slots with real acquisition/replacement flow",
        "seeds": f"{seeds[0]}..{seeds[-1]}",
        "n_per_group": len(seeds),
        "policy": "option_index=0 on every node",
        "conditions": {
            "disabled": "equipment_reward stripped from event catalog",
            "enabled": "equipment_reward resolved normally through RunEngine",
        },
        "groups": {
            condition: {
                route_name: results[f"{condition}_{route_name}"]
                for route_name in ("north", "south")
            }
            for condition in CONDITIONS
        },
        "deltas_enabled_minus_disabled": deltas,
        "hypothesis": (
            "If equipment is route-shaping in the real flow, enabling acquisition/replacement should change "
            "at least one route win rate by >=10% versus the same route with rewards disabled."
        ),
        "verdict": verdict,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "exp4_equipment_slots.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nResults written to {out_path}")
    print("\nVerdict:")
    if impactful_routes:
        print(f"  SUPPORTED - routes with >=10% win-rate change from real equipment flow: {impactful_routes}")
    else:
        print("  WEAK - equipment acquisition/replacement changes no route by >=10%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
