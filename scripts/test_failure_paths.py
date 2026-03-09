#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.combat_engine import CombatEngine
from src.event_engine import resolve_event_choice
from src.run_engine import RunEngine, build_map
from src.state_models import EnemyState, PlayerState


def expect_raises(fn, exc_type: type[BaseException], label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"{label}: expected {exc_type.__name__}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_combat_failures() -> None:
    engine = CombatEngine(seed=7)
    player = PlayerState(hp=10, food=5, ammo=0, medkits=0)
    enemy = EnemyState(id="e1", name="raider", hp=5, damage_min=1, damage_max=2)

    expect_raises(lambda: engine.player_attack(player, enemy), ValueError, "attack_without_ammo")
    expect_raises(lambda: engine.player_use_medkit(player), ValueError, "medkit_without_stock")


def test_event_failures() -> None:
    player = PlayerState(hp=10, food=5, ammo=1, medkits=0)
    bad_event = {"id": "bad", "description": "broken", "options": []}
    expect_raises(lambda: resolve_event_choice(player, bad_event, 0, __import__("random").Random(1)), ValueError, "event_empty_options")

    good_event = {
        "id": "ok",
        "description": "test",
        "options": [{"text": "one", "effects": {"food": -1}, "combat_chance": 0.2}],
    }
    expect_raises(lambda: resolve_event_choice(player, good_event, 1, __import__("random").Random(1)), IndexError, "event_option_oob")
    high_chance_event = {
        "id": "high",
        "description": "boundary",
        "options": [{"text": "max", "effects": {"food": 0}, "combat_chance": 1.0}],
    }
    low_chance_event = {
        "id": "low",
        "description": "boundary",
        "options": [{"text": "min", "effects": {"food": 0}, "combat_chance": 0.0}],
    }
    out_high = resolve_event_choice(player, high_chance_event, 0, __import__("random").Random(1))
    out_low = resolve_event_choice(player, low_chance_event, 0, __import__("random").Random(1))
    if not out_high["combat_triggered"]:
        raise AssertionError("combat_chance=1.0 should always trigger")
    if out_low["combat_triggered"]:
        raise AssertionError("combat_chance=0.0 should never trigger")
    invalid_chance_event = {
        "id": "invalid",
        "description": "bad boundary",
        "options": [{"text": "bad", "effects": {"food": 0}, "combat_chance": 1.1}],
    }
    expect_raises(
        lambda: resolve_event_choice(player, invalid_chance_event, 0, __import__("random").Random(1)),
        ValueError,
        "combat_chance_out_of_range",
    )


def test_run_failures() -> None:
    node_payloads = {
        "node_start": {
            "id": "node_start",
            "node_type": "story",
            "connections": ["node_a"],
            "event_pool": ["abandoned_store"],
            "is_start": True,
        },
        "node_a": {
            "id": "node_a",
            "node_type": "resource",
            "connections": ["node_final"],
            "event_pool": ["abandoned_store"],
        },
        "node_final": {
            "id": "node_final",
            "node_type": "story",
            "connections": [],
            "event_pool": ["abandoned_store"],
            "is_final": True,
        },
    }
    map_state = build_map(node_payloads, start_node_id="node_start", final_node_id="node_final")
    events = {
        "abandoned_store": load_json(ROOT / "schemas" / "samples" / "events" / "abandoned_store.json"),
    }
    engine = RunEngine(map_state=map_state, seed=4, event_catalog=events)
    run = engine.create_run(PlayerState(hp=10, food=2, ammo=1, medkits=0), seed=4)
    expect_raises(lambda: engine.move_to(run, "node_final"), ValueError, "invalid_connection_move")
    expect_raises(lambda: engine.resolve_node_event(map_state.get_node("node_a"), run, option_index=99), IndexError, "invalid_event_option")


def test_combat_boundaries() -> None:
    engine = CombatEngine(seed=7)
    player = PlayerState(hp=10, food=5, ammo=1, medkits=1)
    enemy = EnemyState(id="e2", name="hound", hp=1, damage_min=1, damage_max=1)
    dealt = engine.player_attack(player, enemy)
    if dealt < 1 or dealt > 3:
        raise AssertionError("player_attack damage out of spec range")
    if player.ammo != 0:
        raise AssertionError("player ammo boundary decrement failed")
    taken = engine.enemy_attack(player, enemy)
    if taken != 1:
        raise AssertionError("enemy damage boundary min=max failed")


def main() -> int:
    test_combat_failures()
    test_combat_boundaries()
    test_event_failures()
    test_run_failures()
    print("Failure-path tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
