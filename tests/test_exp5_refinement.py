import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, EquipmentState, RunState, MapState, NodeState
from src.run_engine import RunEngine

def test_equipment_refinement():
    print("Testing Equipment Refinement (EXP-5)...")
    
    # Setup
    weapon = EquipmentState(id="trusty_sword", slot="weapon", durability=5, max_durability=10)
    player = PlayerState(hp=10, food=10, ammo=10, medkits=5, scrap=20, weapon_slot=weapon)
    
    node = NodeState(id="node_start", node_type="story", connections=[], event_pool=[])
    map_state = MapState(nodes={"node_start": node}, start_node_id="node_start", final_node_id="node_start")
    
    engine = RunEngine(map_state=map_state, seed=123)
    run = engine.create_run(player, seed=123)
    
    # 1. Test Repair
    print(f"Initial: Durability={weapon.durability}, Scrap={player.scrap}")
    res = engine.refine_equipment(run, "weapon", "repair")
    print(f"Repair Result: {res}")
    assert res["success"] == True
    assert run.player.weapon_slot.durability == 10
    assert run.player.scrap == 10
    
    # 2. Test Reinforce ATK
    print(f"Initial Affixes: {run.player.weapon_slot.affixes}, Scrap={run.player.scrap}")
    res = engine.refine_equipment(run, "weapon", "reinforce_atk")
    print(f"Reinforce Result: {res}")
    assert res["success"] == True
    assert run.player.weapon_slot.affixes["atk"] == 1
    assert run.player.scrap == 0
    
    # 3. Test Insufficient Scrap
    res = engine.refine_equipment(run, "weapon", "reinforce_def")
    print(f"Insufficient Scrap Result: {res}")
    assert res["success"] == False
    assert res["reason"] == "insufficient_scrap"
    
    print("\nAll EXP-5 refinement tests passed!")

if __name__ == "__main__":
    test_equipment_refinement()
