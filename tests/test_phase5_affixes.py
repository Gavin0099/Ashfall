import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from src.state_models import PlayerState, EquipmentState, CharacterProfile, EnemyState
from src.item_factory import ItemFactory
from src.combat_engine import CombatEngine

class TestPhase5Affixes(unittest.TestCase):
    def setUp(self):
        self.factory = ItemFactory("data/item_catalog.json", "data/affix_catalog.json")

    def create_test_player(self):
        # Providing necessary arguments for PlayerState
        return PlayerState(hp=10, food=10, ammo=10, medkits=2)

    def test_item_generation_rarity(self):
        item = self.factory.create_random_equipment("rust_rifle", rarity_override="legendary", seed=42)
        self.assertEqual(item.rarity, "legendary")
        self.assertGreaterEqual(len(item.affixes) + len(item.tags), 2)

    def test_combat_atk_bonus(self):
        player = self.create_test_player()
        weapon = EquipmentState(id="rust_rifle", slot="weapon", rarity="rare", affixes={"atk": 2})
        player.equip(weapon)
        
        engine = CombatEngine(seed=42)
        enemy = EnemyState(id="target", name="Target", hp=100, damage_min=1, damage_max=1)
        
        dealt = engine.player_attack(player, enemy)
        self.assertGreaterEqual(dealt, 3) # base 1-3 + 2

    def test_combat_def_bonus(self):
        player = self.create_test_player()
        armor = EquipmentState(id="plate_armor", slot="armor", rarity="rare", affixes={"def": 2})
        player.equip(armor)
        player.hp = 10
        
        enemy = EnemyState(id="target", name="Target", hp=10, damage_min=3, damage_max=3)
        
        engine = CombatEngine(seed=42)
        taken = engine.enemy_attack(player, enemy)
        # Expected: 3 (enemy) - 1 (plate_armor legacy) - 2 (def affix) = 0
        self.assertEqual(taken, 0) 
        self.assertEqual(player.hp, 10)

if __name__ == "__main__":
    unittest.main()
