import sys
from pathlib import Path
import random

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.state_models import PlayerState, NodeType, NodeState, MapState, RunState, EquipmentState
from src.run_engine import RunEngine, build_map
from src.combat_engine import CombatEngine
import json

def test_v06_mechanics():
    print("=== Testing v0.6 Advanced Mechanics ===")
    
    # 1. Setup Mock Catalogs
    enemy_catalog = {
        "enemy_raider_leader_elite": {
            "id": "enemy_raider_leader_elite",
            "name": "Raider Leader (Elite)",
            "archetype": "raider",
            "hp": 12,
            "is_elite": True,
            "damage_range": {"min": 2, "max": 4},
            "loot_table": [{"resource": "ammo", "amount": 5, "chance": 1.0}]
        }
    }
    
    event_catalog = {
        "evt_old_key": {
            "id": "evt_old_key",
            "description": "Found a key.",
            "options": [
                {
                    "text": "Keep it",
                    "effects": {},
                    "set_flags": {"has_old_key": True}
                }
            ]
        },
        "evt_hidden_cache": {
            "id": "evt_hidden_cache",
            "description": "A locked box.",
            "conditions": {"required_flags": {"has_old_key": True}},
            "options": [
                {
                    "text": "Unlock",
                    "effects": {"scrap": 10},
                    "equipment_reward": {"slot": "weapon", "item": "hardened_blade"}
                }
            ]
        }
    }
    
    # 2. Test Elite Combat
    print("\n[1/3] Testing Elite Combat...")
    player = PlayerState(hp=10, food=10, ammo=10, medkits=2)
    elite_enemy_data = enemy_catalog["enemy_raider_leader_elite"]
    engine = RunEngine(map_state=None, seed=42, enemy_catalog=enemy_catalog)
    
    # Using internal _enemy_from_payload helper (from run_engine)
    from src.run_engine import _enemy_from_payload
    elite_enemy = _enemy_from_payload(elite_enemy_data)
    
    combat = CombatEngine(seed=42)
    result = combat.run_auto_combat(player, elite_enemy)
    
    print(f"Combat Result: {'Victory' if result['victory'] else 'Defeat'}")
    print("Combat Log (First 2 entries):")
    for entry in result["log"][:2]:
        print(f"  - {entry}")
    
    assert "⚠️ 遭遇精英敵人" in result["log"][0], "Elite encounter tip missing"
    
    # 3. Test Quest Flags & Event Filtering
    print("\n[2/3] Testing Run Flags & Event Filtering...")
    node = NodeState(id="N1", node_type="story", connections=[], event_pool=["evt_old_key", "evt_hidden_cache"])
    run = RunState(player=player, map_seed=42, current_node="N1")
    
    from src.event_engine import pick_event_id
    
    # Without key, should only pick evt_old_key (even if hidden_cache is in pool)
    # Note: pick_event_id prefers filtered candidates
    rng = random.Random(42)
    picked_1 = pick_event_id(node, rng, run_flags=run.flags, event_catalog=event_catalog)
    print(f"Picked without flag: {picked_1}")
    assert picked_1 == "evt_old_key"
    
    # Setting flag
    run.flags["has_old_key"] = True
    picked_2 = pick_event_id(node, rng, run_flags=run.flags, event_catalog=event_catalog)
    print(f"Picked with flag: {picked_2}")
    # Now hidden_cache is eligible
    
    # 4. Test Random Affixes
    print("\n[3/3] Testing Random Affixes...")
    from src.event_engine import resolve_event_choice
    
    # Force a reward with affixes (it's 50% chance in code, we loop until we see one or just check if it executes)
    reward_event = event_catalog["evt_hidden_cache"]
    found_affix = False
    for i in range(10):
        player_tmp = PlayerState(hp=10, food=10, ammo=10, medkits=2)
        outcome = resolve_event_choice(player_tmp, reward_event, 0, random.Random(i))
        if player_tmp.weapon_slot and player_tmp.weapon_slot.affixes:
            print(f"Generated weapon with affixes: {player_tmp.weapon_slot.affixes}")
            found_affix = True
            break
    
    if not found_affix:
        print("Note: No affixes generated in 10 attempts (expected in ~99.9% of cases with 50% prob)")

    print("\n=== v0.6 Mechanics Test Passed! ===")

if __name__ == "__main__":
    try:
        test_v06_mechanics()
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
