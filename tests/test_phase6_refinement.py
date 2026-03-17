import unittest
from src.state_models import EquipmentState
from src.item_factory import ItemFactory
import os

class TestPhase6Refinement(unittest.TestCase):
    def setUp(self):
        # Ensure we have access to the catalogs
        self.factory = ItemFactory("data/item_catalog.json", "data/affix_catalog.json")

    def test_basic_refinement_cost(self):
        item = EquipmentState(id="makeshift_blade", slot="weapon", rarity="common")
        # Base cost for common is 5
        self.assertEqual(item.get_refine_cost(), 5)
        item.refinement_count = 1
        # 5 + 1*2 = 7
        self.assertEqual(item.get_refine_cost(), 7)

    def test_rarity_promotion_common_to_rare(self):
        item = EquipmentState(id="makeshift_blade", slot="weapon", rarity="common")
        self.assertEqual(len(item.affixes), 0)
        
        # First refinement should promote common to rare
        res = self.factory.refine_equipment(item, seed=42)
        self.assertTrue(res["success"])
        self.assertTrue(res["promoted"])
        self.assertEqual(item.rarity, "rare")
        self.assertEqual(item.refinement_count, 1)
        self.assertGreater(len(item.affixes), 0)

    def test_rarity_promotion_rare_to_legendary(self):
        item = EquipmentState(id="makeshift_blade", slot="weapon", rarity="rare", refinement_count=2)
        initial_affix_count = len(item.affixes)
        
        # Third refinement (from 2nd to 3rd) should promote rare to legendary
        res = self.factory.refine_equipment(item, seed=100)
        self.assertTrue(res["success"])
        self.assertTrue(res["promoted"])
        self.assertEqual(item.rarity, "legendary")
        self.assertEqual(item.refinement_count, 3)
        # Should have added another affix
        self.assertGreater(len(item.affixes), initial_affix_count)

    def test_stat_growth(self):
        item = EquipmentState(id="makeshift_blade", slot="weapon", rarity="rare", refinement_count=1)
        initial_atk = item.affixes.get("atk", 0)
        
        # Second refinement should trigger stat growth (+1 atk)
        self.factory.refine_equipment(item)
        self.assertEqual(item.affixes.get("atk", 0), initial_atk + 1)

if __name__ == "__main__":
    unittest.main()
