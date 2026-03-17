import sys
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, EquipmentState, RunState, MapState, NodeState, EnemyState
from src.run_engine import RunEngine

def test_special_abilities():
    print("Testing Special Abilities (EXP-5.1)...")
    
    # Setup
    node = NodeState(id="node_start", node_type="story", connections=[], event_pool=[], resource_cost={"radiation": 1})
    map_state = MapState(nodes={"node_start": node}, start_node_id="node_start", final_node_id="node_start")
    
    # 1. Test Lead-lined
    print("--- Testing lead_lined ---")
    armor = EquipmentState(id="lead_armor", slot="armor", tags=["lead_lined"])
    player = PlayerState(hp=10, food=10, ammo=10, medkits=5, scrap=0, armor_slot=armor, radiation=0)
    engine = RunEngine(map_state=map_state, seed=123)
    run = engine.create_run(player, seed=123)
    
    # Move should normally cost 1 radiation, but Lead-lined reduces it by 1 -> 0
    engine.apply_node_cost(run, node)
    print(f"Radiation after move: {run.player.radiation}")
    assert run.player.radiation == 0
    
    # 2. Test Scavenger
    print("--- Testing scavenger ---")
    tool = EquipmentState(id="scav_tool", slot="tool", tags=["scavenger"])
    run.player.tool_slot = tool
    enemy_payload = {
        "id": "test_enemy",
        "name": "Test Enemy",
        "hp": 1, "damage_min": 1, "damage_max": 2,
        "loot_table": [{"resource": "scrap", "amount": 1, "chance": 1.0}]
    }
    engine.enemy_catalog = {"test_enemy": enemy_payload}
    
    # We need to mock rng to ensure victory and loot
    engine.rng = random.Random(123)
    res = engine.resolve_combat(run)
    print(f"Loot collected: {res['loot']}")
    # 1 base + 1 scavenger bonus = 2
    assert any(l["resource"] == "scrap" and l["amount"] == 2 for l in res["loot"])
    
    # 3. Test Vampiric
    print("--- Testing vampiric ---")
    weapon = EquipmentState(id="vamp_sword", slot="weapon", tags=["vampiric"])
    run.player.weapon_slot = weapon
    run.player.hp = 5
    res = engine.resolve_combat(run)
    print(f"HP after victory: {run.player.hp}")
    # Healed 1 from 5 -> 6 (Vampiric)
    assert run.player.hp == 6
    
    # 4. Test Sturdy
    print("--- Testing sturdy ---")
    weapon.tags = ["sturdy"]
    weapon.durability = 10
    # Run multiple combats to see if durability holds (50% chance)
    # Use a new random object for sturdy to be sure it's not seed-locked
    engine.rng = random.Random() 
    dur_hits = 0
    for _ in range(100):
        engine.resolve_combat(run)
        if run.player.weapon_slot.durability < 10:
            dur_hits += 1
            run.player.weapon_slot.durability = 10
            
    print(f"Durability drops in 100 runs: {dur_hits}")
    assert 0 < dur_hits < 100 
    
    print("\nAll EXP-5.1 special ability tests passed!")

if __name__ == "__main__":
    test_special_abilities()
