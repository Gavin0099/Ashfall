import unittest
from src.state_models import PlayerState, CharacterProfile
from src.progression import gain_xp, get_eligible_perks, apply_perk, load_perk_catalog

class TestProgressionSystem(unittest.TestCase):
    def setUp(self):
        self.char = CharacterProfile(
            background_id="vault_technician",
            display_name="Test Subject",
            special={
                "strength": 7, "perception": 5, "endurance": 6,
                "charisma": 5, "intelligence": 7, "agility": 5, "luck": 5
            }
        )
        self.player = PlayerState(hp=10, food=10, ammo=10, medkits=1, character=self.char)
        self.catalog = load_perk_catalog()

    def test_xp_gain_and_level_up(self):
        # Level 1 -> 2 needs 1 * 10 = 10 XP
        leveled_up = gain_xp(self.player, 10)
        self.assertTrue(leveled_up)
        self.assertEqual(self.player.character.level, 2)
        self.assertEqual(self.player.character.xp, 0)

        # Level 2 -> 3 needs 2 * 10 = 20 XP
        leveled_up = gain_xp(self.player, 25)
        self.assertTrue(leveled_up)
        self.assertEqual(self.player.character.level, 3)
        self.assertEqual(self.player.character.xp, 5)

    def test_perk_eligibility(self):
        # At Level 1, no perks should be eligible (most need Level 2+)
        eligible = get_eligible_perks(self.player, self.catalog)
        self.assertEqual(len(eligible), 0)

        # Level up to 2
        gain_xp(self.player, 10)
        eligible = get_eligible_perks(self.player, self.catalog)
        
        # Should have Toughness (END 6), Medic (INT 6), Strong Back (STR 6)
        ids = [p["id"] for p in eligible]
        self.assertIn("toughness", ids)
        self.assertIn("medic_pro", ids)
        self.assertIn("strong_back", ids)
        self.assertNotIn("sniper", ids) # Needs high PER/AGI

    def test_perk_application(self):
        # Apply Toughness (+2 Max HP simulated as +2 HP for now)
        initial_hp = self.player.hp
        apply_perk(self.player, "toughness", self.catalog)
        
        self.assertIn("toughness", self.player.character.perks)
        self.assertEqual(self.player.hp, initial_hp + 2)

if __name__ == "__main__":
    unittest.main()
