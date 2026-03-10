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
from src.state_models import EnemyState, PlayerState, apply_effects


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
    unsupported_effect_event = {
        "id": "unsupported",
        "description": "bad effect",
        "options": [{"text": "bad", "effects": {"morale": 1}, "combat_chance": 0.0}],
    }
    expect_raises(
        lambda: resolve_event_choice(player, unsupported_effect_event, 0, __import__("random").Random(1)),
        ValueError,
        "unsupported_effect_key",
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


def test_radiation_attrition() -> None:
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
    engine = RunEngine(map_state=map_state, seed=9, event_catalog={"abandoned_store": load_json(ROOT / "schemas" / "samples" / "events" / "abandoned_store.json")})
    run = engine.create_run(PlayerState(hp=2, food=5, ammo=1, medkits=0, radiation=1), seed=9)
    engine.move_to(run, "node_a")
    if run.player.hp != 1:
        raise AssertionError("radiation attrition should reduce hp on move")
    engine.move_to(run, "node_final")
    if not run.ended or run.end_reason != "radiation_death":
        raise AssertionError("radiation death should be attributable")


def test_apply_effects_clamp() -> None:
    player = PlayerState(hp=1, food=1, ammo=0, medkits=0, scrap=0, radiation=0)
    apply_effects(player, {"hp": -5, "food": -2, "ammo": -1, "medkits": -1, "scrap": -3, "radiation": -2})
    if any(value < 0 for value in (player.hp, player.food, player.ammo, player.medkits, player.scrap, player.radiation)):
        raise AssertionError("apply_effects should clamp state to lower bounds")


def test_create_run_copies_player_state() -> None:
    node_payloads = {
        "node_start": {"id": "node_start", "node_type": "story", "connections": [], "event_pool": [], "is_start": True, "is_final": True}
    }
    map_state = build_map(node_payloads, start_node_id="node_start", final_node_id="node_start")
    player = PlayerState(hp=10, food=5, ammo=1, medkits=0)
    run = RunEngine(map_state=map_state, seed=1, event_catalog={}).create_run(player, seed=1)
    run.player.hp = 1
    if player.hp != 10:
        raise AssertionError("create_run should isolate player state from caller mutations")


def test_node_resource_cost() -> None:
    node_payloads = {
        "node_start": {
            "id": "node_start",
            "node_type": "story",
            "connections": ["node_cost"],
            "event_pool": ["abandoned_store"],
            "is_start": True,
        },
        "node_cost": {
            "id": "node_cost",
            "node_type": "resource",
            "connections": ["node_final"],
            "event_pool": ["abandoned_store"],
            "resource_cost": {"food": 2, "ammo": 1},
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
    engine = RunEngine(map_state=map_state, seed=2, event_catalog={"abandoned_store": load_json(ROOT / "schemas" / "samples" / "events" / "abandoned_store.json")})
    run = engine.create_run(PlayerState(hp=10, food=5, ammo=2, medkits=0), seed=2)
    engine.move_to(run, "node_cost")
    if run.player.food != 3 or run.player.ammo != 1:
        raise AssertionError("node resource_cost should apply instead of hardcoded travel cost")


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


def test_equipment_rewards_and_replacement() -> None:
    player = PlayerState(hp=10, food=5, ammo=3, medkits=1)
    blade_event = {
        "id": "blade",
        "description": "gear",
        "options": [
            {
                "text": "equip blade",
                "effects": {"ammo": 1},
                "equipment_reward": {"slot": "weapon", "item": "makeshift_blade"},
                "combat_chance": 0.0,
            }
        ],
    }
    rifle_event = {
        "id": "rifle",
        "description": "gear",
        "options": [
            {
                "text": "equip rifle",
                "effects": {"ammo": 1},
                "equipment_reward": {"slot": "weapon", "item": "rust_rifle"},
                "combat_chance": 0.0,
            }
        ],
    }
    tool_event = {
        "id": "tool",
        "description": "gear",
        "options": [
            {
                "text": "equip tool",
                "effects": {"food": 0},
                "equipment_reward": {"slot": "tool", "item": "scavenger_kit"},
                "combat_chance": 0.0,
            }
        ],
    }
    pack_event = {
        "id": "pack",
        "description": "gear",
        "options": [
            {
                "text": "equip pack",
                "effects": {"food": -1},
                "equipment_reward": {"slot": "tool", "item": "field_pack"},
                "combat_chance": 0.0,
            }
        ],
    }

    out_blade = resolve_event_choice(player, blade_event, 0, __import__("random").Random(1))
    if player.weapon_slot != "makeshift_blade":
        raise AssertionError("weapon reward should equip initial weapon")
    if not out_blade["equipment_change"]["changed"]:
        raise AssertionError("first equipment reward should report change")

    out_rifle = resolve_event_choice(player, rifle_event, 0, __import__("random").Random(1))
    if player.weapon_slot != "rust_rifle":
        raise AssertionError("weapon reward should replace existing weapon")
    if out_rifle["equipment_change"]["replaced"] != "makeshift_blade":
        raise AssertionError("weapon replacement should report previous item")

    enemy = EnemyState(id="e3", name="raider", hp=10, damage_min=1, damage_max=1)
    damage = CombatEngine(seed=3).player_attack(player, enemy)
    if damage < 2 or damage > 4:
        raise AssertionError("rust_rifle should add +1 damage to attack roll")

    out_tool = resolve_event_choice(player, tool_event, 0, __import__("random").Random(1))
    if player.tool_slot != "scavenger_kit":
        raise AssertionError("tool reward should equip scavenger kit")
    if out_tool["equipment_change"]["replaced"] is not None:
        raise AssertionError("first tool equip should not report replacement")

    food_before_pack = player.food
    out_pack = resolve_event_choice(player, pack_event, 0, __import__("random").Random(1))
    if player.tool_slot != "field_pack":
        raise AssertionError("field_pack should replace current tool")
    if out_pack["equipment_change"]["replaced"] != "scavenger_kit":
        raise AssertionError("field_pack should report replaced tool")
    if player.food != food_before_pack + 1:
        raise AssertionError("field_pack should grant net +1 food after the event's -1 cost proxy")


def main() -> int:
    test_combat_failures()
    test_combat_boundaries()
    test_equipment_rewards_and_replacement()
    test_event_failures()
    test_run_failures()
    test_radiation_attrition()
    test_apply_effects_clamp()
    test_create_run_copies_player_state()
    test_node_resource_cost()
    print("Failure-path tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
