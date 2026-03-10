#!/usr/bin/env python3
"""run_exp2_travel_mode.py — EXP-2: Travel Mode controlled experiment.

Design question:
  Can one additional travel decision layer increase consequence length
  without drowning the route-choice hypothesis?

Travel modes (applied before each move):
  normal  — baseline, no modifier
  rush    — food cost -1 (min 0), next event combat_chance += 0.2 (capped 1.0)
  careful — food cost +1, next event combat_chance -= 0.2 (min 0.0)

Groups:
  A = always normal   (baseline control)
  B = always rush
  C = always careful
  D = alternating rush/careful per node

Seeds: 101..150 (50 per group, same seeds across groups)

Output: output/analytics/exp/exp2_travel_mode.json
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
from src.state_models import PlayerState, RunState

OUTPUT_DIR = ROOT / "output" / "analytics" / "exp"

TRAVEL_MODES = ("normal", "rush", "careful")

# modifiers applied to food cost before move.
# rush = lower travel friction (save 1 food this step, offset travel cost)
# careful = higher travel cost (spend 1 extra food, buy safety)
FOOD_DELTA = {"normal": 0, "rush": +1, "careful": -1}
# modifiers applied to next event combat_chance
# rush saves food now → more danger next node
# careful spends food now → less danger next node
COMBAT_DELTA = {"normal": 0.0, "rush": +0.2, "careful": -0.2}


@dataclass
class RunRecord:
    seed: int
    group: str
    travel_modes_used: list[str] = field(default_factory=list)
    victory: bool = False
    end_reason: str = ""
    steps: int = 0
    nodes_visited: list[str] = field(default_factory=list)
    food_warning_step: int = -1   # first step food <= 2
    death_step: int = -1
    steps_from_food_warning_to_death: int = -1
    final_hp: int = 0
    final_food: int = 0
    final_radiation: int = 0


def _initial_player() -> PlayerState:
    return PlayerState(hp=10, food=6, ammo=4, medkits=2, scrap=0, radiation=0)


def _pick_next_node(engine: RunEngine, run: RunState) -> str:
    """Always pick the first available connection (deterministic)."""
    current = engine.map_state.get_node(run.current_node)
    return current.connections[0]


def _apply_travel_mode_pre_move(run: RunState, mode: str) -> None:
    """Apply food cost delta for travel mode before move_to()."""
    delta = FOOD_DELTA[mode]
    if delta < 0:
        run.player.food = max(0, run.player.food + delta)
    elif delta > 0:
        run.player.food = run.player.food + delta  # careful costs more


def _apply_travel_mode_post_event(event_payload: dict, mode: str) -> dict:
    """Return a modified copy of event_payload with adjusted combat_chance."""
    if mode == "normal":
        return event_payload
    delta = COMBAT_DELTA[mode]
    patched = copy.deepcopy(event_payload)
    for opt in patched.get("options", []):
        if "combat_chance" in opt:
            opt["combat_chance"] = max(0.0, min(1.0, opt["combat_chance"] + delta))
    return patched


def simulate_run(seed: int, group: str, node_payloads: dict, enemy_catalog: dict) -> RunRecord:
    event_catalog = build_event_catalog(seed)
    map_state = build_map(node_payloads, "node_start")
    engine = RunEngine(map_state, seed, event_catalog=event_catalog, enemy_catalog=enemy_catalog)

    player = _initial_player()
    run = engine.create_run(player, seed)

    record = RunRecord(seed=seed, group=group)
    step = 0
    mode_cycle = 0  # for group D alternating

    # resolve start node event
    start_node = map_state.get_node("node_start")
    engine.resolve_node_event(start_node, run, option_index=0)
    record.nodes_visited = list(run.visited_nodes)

    while not run.ended:
        step += 1

        # pick travel mode for this group
        if group == "A":
            mode = "normal"
        elif group == "B":
            mode = "rush"
        elif group == "C":
            mode = "careful"
        else:  # group D alternating
            mode = "rush" if mode_cycle % 2 == 0 else "careful"
            mode_cycle += 1

        record.travel_modes_used.append(mode)

        # food warning tracking (before move)
        if record.food_warning_step == -1 and run.player.food <= 2:
            record.food_warning_step = step

        # apply pre-move travel modifier
        _apply_travel_mode_pre_move(run, mode)

        if run.player.food <= 0:
            run.end(victory=False, reason="starvation")
            record.death_step = step
            break

        # move
        try:
            next_node_id = _pick_next_node(engine, run)
        except IndexError:
            break

        node = engine.move_to(run, next_node_id)
        record.nodes_visited = list(run.visited_nodes)

        if run.ended:
            record.death_step = step
            break

        # resolve event with travel-mode combat modifier
        raw_payload = engine.event_catalog.get(
            next(iter(node.event_pool), ""), {}
        ) if node.event_pool else {}

        # Use engine's normal resolve but we need to patch combat_chance inline.
        # Patch: temporarily replace catalog entry, restore after.
        if node.event_pool:
            eid_key = node.event_pool[0]
            if eid_key in engine.event_catalog:
                original = engine.event_catalog[eid_key]
                patched = _apply_travel_mode_post_event(original, mode)
                engine.event_catalog[eid_key] = patched
                engine.resolve_node_event(node, run, option_index=0)
                engine.event_catalog[eid_key] = original
            else:
                engine.resolve_node_event(node, run, option_index=0)
        else:
            engine.resolve_node_event(node, run, option_index=0)

        if run.ended:
            record.death_step = step
            break

    record.steps = step
    record.victory = run.victory
    record.end_reason = run.end_reason or ""
    record.final_hp = run.player.hp
    record.final_food = run.player.food
    record.final_radiation = run.player.radiation

    if record.food_warning_step != -1 and record.death_step != -1:
        record.steps_from_food_warning_to_death = record.death_step - record.food_warning_step

    return record


def run_group(group: str, seeds: list[int], node_payloads: dict, enemy_catalog: dict) -> list[RunRecord]:
    records = []
    for seed in seeds:
        rec = simulate_run(seed, group, node_payloads, enemy_catalog)
        records.append(rec)
    return records


def summarize(records: list[RunRecord]) -> dict[str, Any]:
    n = len(records)
    wins = sum(1 for r in records if r.victory)
    deaths = [r for r in records if not r.victory]
    steps_list = [r.steps for r in records]
    consequence_lengths = [
        r.steps_from_food_warning_to_death
        for r in records
        if r.steps_from_food_warning_to_death >= 0
    ]
    radiation_deaths = sum(1 for r in deaths if "radiation" in r.end_reason)
    starvation_deaths = sum(1 for r in deaths if "starv" in r.end_reason)

    return {
        "n": n,
        "win_rate": round(wins / n, 3),
        "avg_steps": round(sum(steps_list) / n, 2) if steps_list else 0,
        "avg_consequence_length": (
            round(sum(consequence_lengths) / len(consequence_lengths), 2)
            if consequence_lengths else None
        ),
        "consequence_length_samples": len(consequence_lengths),
        "radiation_death_rate": round(radiation_deaths / n, 3),
        "starvation_death_rate": round(starvation_deaths / n, 3),
        "avg_final_hp": round(sum(r.final_hp for r in records) / n, 2),
        "avg_final_food": round(sum(r.final_food for r in records) / n, 2),
        "avg_final_radiation": round(sum(r.final_radiation for r in records) / n, 2),
    }


def main() -> int:
    seeds = list(range(101, 151))  # 50 seeds
    node_payloads = build_node_payloads()
    enemy_catalog = build_enemy_catalog()

    print("EXP-2: Travel Mode experiment")
    print(f"  Seeds: {seeds[0]}..{seeds[-1]} ({len(seeds)} per group)")

    results: dict[str, Any] = {}
    for group in ("A", "B", "C", "D"):
        mode_label = {"A": "normal", "B": "rush", "C": "careful", "D": "alternating"}[group]
        records = run_group(group, seeds, node_payloads, enemy_catalog)
        summary = summarize(records)
        results[f"group_{group}_{mode_label}"] = summary
        print(f"  Group {group} ({mode_label}): win={summary['win_rate']:.0%}  "
              f"avg_steps={summary['avg_steps']}  "
              f"consequence_len={summary['avg_consequence_length']}")

    # delta analysis vs baseline (group A)
    baseline = results["group_A_normal"]
    deltas: dict[str, Any] = {}
    for key in ("group_B_rush", "group_C_careful", "group_D_alternating"):
        g = results[key]
        d: dict[str, Any] = {}
        for metric in ("win_rate", "avg_steps", "radiation_death_rate", "starvation_death_rate"):
            base_val = baseline[metric]
            g_val = g[metric]
            d[f"delta_{metric}"] = round(g_val - base_val, 3)
        # consequence length delta (None-safe)
        if g["avg_consequence_length"] is not None and baseline["avg_consequence_length"] is not None:
            d["delta_consequence_length"] = round(
                g["avg_consequence_length"] - baseline["avg_consequence_length"], 2
            )
        deltas[key] = d

    output = {
        "experiment": "EXP-2",
        "description": "Travel Mode: normal / rush / careful / alternating",
        "seeds": f"{seeds[0]}..{seeds[-1]}",
        "n_per_group": len(seeds),
        "groups": results,
        "deltas_vs_normal": deltas,
        "hypothesis": "rush extends consequence length (delta_consequence_length > 0); careful reduces it",
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "exp2_travel_mode.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults written to {out_path}")

    # verdict
    rush_delta = deltas.get("group_B_rush", {}).get("delta_consequence_length")
    careful_delta = deltas.get("group_C_careful", {}).get("delta_consequence_length")
    print("\nVerdict:")
    if rush_delta is not None and rush_delta > 0:
        print(f"  SUPPORTED — rush extends consequence length by {rush_delta} steps vs normal")
    elif rush_delta is not None:
        print(f"  NOT SUPPORTED — rush did not extend consequence length (delta={rush_delta})")
    else:
        print("  INCONCLUSIVE — insufficient food-warning samples in rush group")
    if careful_delta is not None:
        direction = "shorter" if careful_delta < 0 else "longer"
        print(f"  careful consequence length: {direction} by {abs(careful_delta)} steps vs normal")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
