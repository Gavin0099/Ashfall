#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    analyze_failure,
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
    build_warning_signals,
)
from src.event_engine import pick_event_id, resolve_event_choice
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState


OUTPUT_DIR = ROOT / "output" / "cli"


def prompt_index(label: str, options: list[str]) -> int:
    while True:
        print(label)
        for index, option in enumerate(options):
            print(f"  [{index}] {option}")
        raw = input("> ").strip()
        if raw.isdigit() and 0 <= int(raw) < len(options):
            return int(raw)
        print("Invalid choice. Enter the option number.")


def estimate_remaining_steps(map_state, node_id: str) -> int:
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(node_id, 0)]
    while queue:
        current, depth = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = map_state.get_node(current)
        if node.is_final:
            return depth
        for nxt in node.connections:
            queue.append((nxt, depth + 1))
    return 0


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    nodes = build_node_payloads()
    events = build_event_catalog(seed)
    enemies = build_enemy_catalog()
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies)
    run = engine.create_run(PlayerState(hp=10, food=7, ammo=3, medkits=1), seed=seed)

    print(f"Ashfall CLI Run")
    print(f"Seed: {seed}")
    print("Goal: survive to the end.")

    decision_log: list[dict] = []

    while not run.ended:
        current = map_state.get_node(run.current_node)
        if current.connections:
            if run.player.radiation > 0:
                print(f"WARNING: radiation will burn you for 1 HP on travel. Current radiation: {run.player.radiation}")
                if run.player.hp <= run.player.radiation + 1:
                    print("CRITICAL: another irradiated move may kill you.")
            route_choice = prompt_index(
                f"\nCurrent node: {run.current_node}\nStatus: hp={run.player.hp} food={run.player.food} ammo={run.player.ammo} medkits={run.player.medkits} radiation={run.player.radiation}\nChoose next route:",
                current.connections,
            )
            next_node = current.connections[route_choice]
            hp_before_move = run.player.hp
            food_before_move = run.player.food
            node = engine.move_to(run, next_node)
            if run.player.radiation > 0 and run.player.hp < hp_before_move:
                print(f"Radiation burns you for {hp_before_move - run.player.hp} HP during travel.")
            if run.player.food < food_before_move:
                print("Travel consumes 1 food.")
            if run.ended:
                break
        else:
            node = current

        event_id = pick_event_id(node, engine.rng)
        event_payload = events[event_id]
        remaining_steps = estimate_remaining_steps(map_state, node.id)
        print(f"\nEvent: {event_payload['description']}")

        option_lines = []
        warning_cache: list[list[str]] = []
        for index, option in enumerate(event_payload["options"]):
            warnings = build_warning_signals(run.player, event_payload, index, remaining_steps)
            warning_cache.append(warnings)
            warning_label = f" [{'; '.join(warnings)}]" if warnings else ""
            option_lines.append(f"{option['text']}{warning_label}")

        option_index = prompt_index("Choose an option:", option_lines)
        pre_choice_state = {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "radiation": run.player.radiation,
        }
        outcome = resolve_event_choice(run.player, event_payload, option_index, engine.rng)
        if outcome["combat_triggered"]:
            combat = engine.resolve_combat(run)
            outcome["combat"] = combat
            print(f"Combat triggered: {combat['enemy_id']}")
            for line in combat["log"]:
                print(f"  {line}")
        if run.player.is_dead():
            run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))

        effects = dict(event_payload["options"][option_index].get("effects", {}))
        if effects:
            effect_text = ", ".join(f"{key} {value:+d}" for key, value in effects.items())
            print(f"Effects: {effect_text}")
        if run.player.radiation > pre_choice_state["radiation"]:
            print(f"WARNING: radiation increased to {run.player.radiation}. Future travel is more dangerous.")
        if run.player.hp <= 3 and run.player.radiation > 0:
            print("CRITICAL: you are low HP and still irradiated.")

        decision_log.append(
            {
                "step": len(decision_log) + 1,
                "node": node.id,
                "event_id": event_id,
                "option_index": option_index,
                "warning_signals": warning_cache[option_index],
                "pre_choice_state": pre_choice_state,
                "pressure": bool(warning_cache[option_index]),
                "combat_triggered": bool(outcome.get("combat_triggered", False)),
                "effects": effects,
                "player_after": {
                    "hp": run.player.hp,
                    "food": run.player.food,
                    "ammo": run.player.ammo,
                    "medkits": run.player.medkits,
                    "radiation": run.player.radiation,
                },
            }
        )

        if node.is_final and not run.ended:
            run.end(victory=True, reason="reached_final_node")

    failure_analysis = analyze_failure(decision_log, run.ended, run.victory, run.end_reason)
    result = {
        "seed": seed,
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
        "failure_analysis": failure_analysis,
    }
    output_path = OUTPUT_DIR / f"latest_seed_{seed}.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nRun complete")
    print(json.dumps({"victory": run.victory, "end_reason": run.end_reason, "failure_analysis": failure_analysis}, indent=2))
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
