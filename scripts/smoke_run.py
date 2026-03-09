#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    node_paths = sorted((ROOT / "schemas" / "samples" / "nodes").glob("*.json"))
    event_paths = sorted((ROOT / "schemas" / "samples" / "events").glob("*.json"))
    if not node_paths or not event_paths:
        print("Missing sample data")
        return 1

    nodes = {}
    for path in node_paths:
        payload = load_json(path)
        nodes[payload["id"]] = payload

    events = {}
    for path in event_paths:
        payload = load_json(path)
        events[payload["id"]] = payload
    enemies = {}
    for path in sorted((ROOT / "schemas" / "samples" / "enemies").glob("*.json")):
        payload = load_json(path)
        enemies[payload["id"]] = payload

    # Ensure final node exists for reachability in smoke run.
    nodes["node_final"] = {
        "id": "node_final",
        "node_type": "story",
        "connections": [],
        "event_pool": ["abandoned_store"],
        "is_start": False,
        "is_final": True,
        "resource_cost": {"food": 1},
    }

    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(map_state=map_state, seed=42, event_catalog=events, enemy_catalog=enemies)
    run = engine.create_run(PlayerState(hp=10, food=5, ammo=3, medkits=1), seed=42)

    node = engine.move_to(run, "node_crossroads")
    event_outcome = engine.resolve_node_event(node, run, option_index=0)
    if not run.ended:
        engine.move_to(run, "node_final")

    print("Smoke run OK")
    print(
        {
            "current_node": run.current_node,
            "visited_nodes": run.visited_nodes,
            "ended": run.ended,
            "victory": run.victory,
            "player": {
                "hp": run.player.hp,
                "food": run.player.food,
                "ammo": run.player.ammo,
                "medkits": run.player.medkits,
                "scrap": run.player.scrap,
                "radiation": run.player.radiation,
            },
            "event_outcome": event_outcome,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
