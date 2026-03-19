import sys
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, EnemyState, RunState
from src.combat_engine import CombatEngine
from src.event_engine import get_available_options, resolve_event_choice

def test_quest_flags():
    print("--- Testing Quest Flags ---")
    player = PlayerState(hp=20, food=10, ammo=10, medkits=5)
    run = RunState(player=player, map_seed=123, current_node="start")
    
    event_payload = {
        "id": "test_event",
        "options": [
            {
                "text": "Requires Flag A",
                "required_flags": {"flag_a": True},
                "effects": {"xp": 10}
            },
            {
                "text": "Sets Flag A",
                "effects": {"xp": 5},
                "set_flags": {"flag_a": True}
            }
        ]
    }
    
    # 1. Check availability without flag
    all_options = get_available_options(player, event_payload, run_flags=run.flags)
    met_options = [o for o in all_options if o["is_met"]]
    assert len(met_options) == 1
    assert met_options[0]["text"] == "Sets Flag A"
    print("OK: Option filtering works (Required Flags)")

    # 2. Resolve option that sets flag
    outcome = resolve_event_choice(player, event_payload, 1, random.Random(42), run_flags=run.flags)
    run.flags.update(outcome.get("set_flags", {}))
    assert run.flags.get("flag_a") is True
    print("OK: Setting flags works")

    # 3. Check availability with flag
    all_options = get_available_options(player, event_payload, run_flags=run.flags)
    met_options = [o for o in all_options if o["is_met"]]
    assert len(met_options) == 2
    print("OK: Flag-dependent option now available")

def test_merchant_costs():
    print("\n--- Testing Merchant Costs ---")
    player = PlayerState(hp=20, food=10, ammo=10, medkits=5, scrap=10)
    
    event_payload = {
        "id": "merchant_event",
        "options": [
            {
                "text": "Buy Item (15 Scrap)",
                "resource_requirement": {"scrap": 15},
                "effects": {"scrap": -15, "food": 5}
            },
            {
                "text": "Buy Item (5 Scrap)",
                "resource_requirement": {"scrap": 5},
                "effects": {"scrap": -5, "food": 5}
            }
        ]
    }
    
    # Check availability
    all_options = get_available_options(player, event_payload)
    met_options = [o for o in all_options if o["is_met"]]
    assert len(met_options) == 1
    assert met_options[0]["text"] == "Buy Item (5 Scrap)"
    print("OK: Resource requirement filtering works")

    # Try resolving expensive option (should fail)
    try:
        resolve_event_choice(player, event_payload, 0, random.Random(42))
        assert False, "Should have failed due to insufficient resources"
    except ValueError as e:
        assert "Insufficient scrap" in str(e)
        print("OK: resolve_event_choice prevents overspending")

def test_elite_passives():
    print("\n--- Testing Elite Passives ---")
    player = PlayerState(hp=20, food=10, ammo=10, medkits=5)
    # Shielded enemy: damage reduced by 1
    enemy_shielded = EnemyState(id="e1", name="S", hp=10, damage_min=1, damage_max=2, passives=["shielded"])
    # Thorns enemy: reflects 1 damage
    enemy_thorns = EnemyState(id="e2", name="T", hp=10, damage_min=1, damage_max=2, passives=["thorns"])
    
    engine = CombatEngine(seed=42)
    
    # Test Shielded
    damage, thorns = engine.player_attack(player, enemy_shielded)
    print(f"DEBUG: Damage vs Shielded = {damage}")
    # Base for seed 42:
    # random.Random(42).randint(1, 3) is 3
    # 3 - 1 (shielded) = 2
    assert damage == 2
    print("OK: Shielded passive reduces damage")
    
    # Test Thorns
    # Next randint(1, 3) for seed 42 is 1
    old_hp = player.hp
    damage, thorns = engine.player_attack(player, enemy_thorns)
    print(f"DEBUG: Damage vs Thorns = {damage}, Reflection = {thorns}")
    assert damage > 0
    assert thorns == 1
    assert player.hp == old_hp - 1
    print("OK: Thorns passive reflects damage")

if __name__ == "__main__":
    test_quest_flags()
    test_merchant_costs()
    test_elite_passives()
    print("\nAll Phase 9.0 feature verifications PASSED!")
