
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from src.state_models import PlayerState, EquipmentState, NodeState, MapState
from src.run_engine import RunEngine, build_map

class TestPhase3SpecialNodes(unittest.TestCase):
    def setUp(self):
        self.player = PlayerState(hp=5, food=10, ammo=10, medkits=1, scrap=10, radiation=2)
        self.node_payloads = {
            "node_start": {"id": "node_start", "node_type": "resource", "connections": ["node_camp", "node_ruins"]},
            "node_camp": {
                "id": "node_camp", 
                "node_type": "camp", 
                "connections": ["node_final"],
                "metadata": {"facilities": {"repair_bench": True}}
            },
            "node_ruins": {
                "id": "node_ruins", 
                "node_type": "ruins", 
                "connections": ["node_final"],
                "event_pool": ["evt_ruins_1"]
            },
            "node_final": {"id": "node_final", "node_type": "story", "connections": [], "is_final": True}
        }
        self.map_state = build_map(self.node_payloads, "node_start", "node_final")
        self.engine = RunEngine(self.map_state, seed=42)
        self.run = self.engine.create_run(self.player, seed=42)

    def test_camp_rest_options(self):
        # Move to camp
        self.engine.move_to(self.run, "node_camp")
        
        # Test Option 0: 1 Food -> 2 HP
        initial_hp = self.run.player.hp
        initial_food = self.run.player.food
        res = self.engine.rest_at_camp(self.run, 0)
        self.assertTrue(res["success"])
        self.assertEqual(self.run.player.hp, initial_hp + 2)
        self.assertEqual(self.run.player.food, initial_food - 1)

        # Test Option 1: 2 Food -> 3 HP, -1 Rad
        self.run.player.hp = 5
        self.run.player.radiation = 2
        initial_food = self.run.player.food
        res = self.engine.rest_at_camp(self.run, 1)
        self.assertTrue(res["success"])
        self.assertEqual(self.run.player.hp, 8)
        self.assertEqual(self.run.player.radiation, 1)
        self.assertEqual(self.run.player.food, initial_food - 2)

    def test_camp_repair_discount(self):
        # Move to camp
        self.engine.move_to(self.run, "node_camp")
        
        # Equip a damaged item
        weapon = EquipmentState(id="rust_rifle", slot="weapon", durability=5, max_durability=10)
        self.run.player.weapon_slot = weapon
        self.run.player.scrap = 10
        
        # Base cost is 2 scrap per durability. 
        # Camp with repair_bench should reduce cost to 1.
        res = self.engine.refine_equipment(self.run, "weapon", "repair")
        self.assertTrue(res["success"])
        # Repaired 5 points, cost should be 5 scrap (discounted from 10)
        self.assertEqual(res["cost"], 5)
        self.assertEqual(weapon.durability, 10)
        self.assertEqual(self.run.player.scrap, 5)

    def test_ruins_loot_accumulation_and_finalize(self):
        self.engine.move_to(self.run, "node_ruins")
        
        # Stage 1 loot
        self.engine.add_to_temporary_loot(self.run, {"scrap": 5, "xp": 10})
        self.assertEqual(self.run.temporary_loot["scrap"], 5)
        self.assertEqual(self.run.player.scrap, 10) # Using value from setUp player
        
        # Stage 2 loot
        self.engine.add_to_temporary_loot(self.run, {"scrap": 5, "ammo": 2})
        self.assertEqual(self.run.temporary_loot["scrap"], 10)
        
        # Finalize (Completion)
        final_loot = self.engine.finalize_ruins_loot(self.run, retreat_penalty=False)
        self.assertEqual(final_loot["scrap"], 10)
        self.assertEqual(self.run.player.scrap, 20)
        self.assertEqual(self.run.temporary_loot, {})

    def test_ruins_retreat_penalty(self):
        self.engine.move_to(self.run, "node_ruins")
        self.run.player.scrap = 0
        self.engine.add_to_temporary_loot(self.run, {"scrap": 10, "medkits": 2})
        
        # Finalize with retreat (30% penalty)
        final_loot = self.engine.finalize_ruins_loot(self.run, retreat_penalty=True)
        # 10 * 0.7 = 7
        # 2 * 0.7 = 1
        self.assertEqual(final_loot["scrap"], 7)
        self.assertEqual(final_loot["medkits"], 1)
        self.assertEqual(self.run.player.scrap, 7)
        self.assertEqual(self.run.player.medkits, 2) # 1 starting + 1 rewarded

if __name__ == "__main__":
    unittest.main()
