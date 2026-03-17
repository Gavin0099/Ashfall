import sys
import random
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, CharacterProfile, EquipmentState, RunState, MapState, NodeState
from src.progression import gain_xp, apply_perk, load_perk_catalog
from src.run_engine import RunEngine
from src.combat_engine import CombatEngine

def test_progression_and_perks():
    print("Testing Phase 2.0: Progression & Perks...")
    
    # 1. Test XP Gain and Level Up
    char = CharacterProfile(background_id="test", display_name="Gavin", special={"intelligence": 8, "perception": 8}, level=1, xp=0)
    player = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char)
    
    leveled = gain_xp(player, 10)
    assert leveled is True
    assert char.level == 2
    assert char.xp == 0
    print("Level Up 1->2: OK")
    
    # 2. Test Perk Application (Scrappie)
    catalog = load_perk_catalog()
    apply_perk(player, "scrappie_perk", catalog)
    assert "scrappie_perk" in char.perks
    print("Perk Application (Scrappie): OK")
    
    # 3. Test Repair Discount
    # Mock MapState and NodeState
    mock_node = NodeState(id="node_start", node_type="story", connections=[], event_pool=[], is_start=True)
    mock_map = MapState(nodes={"node_start": mock_node}, start_node_id="node_start", final_node_id="node_start")
    
    engine = RunEngine(map_state=mock_map, seed=42)
    player.scrap = 10
    weapon = EquipmentState(id="rust_rifle", slot="weapon", durability=5, max_durability=10)
    player.weapon_slot = weapon
    
    run = RunState(player=player, map_seed=42, current_node="node_start")
    # Action 'repair': cost should be 1 scrap per durability because of scrappie_perk
    res = engine.refine_equipment(run, "weapon", "repair")
    assert res["success"] is True
    assert res["cost"] == 5 # 5 durability repaired * 1 scrap/each
    assert player.scrap == 5
    print("Repair Discount (Scrappie): OK")
    
    # 4. Test Eagle Eye (Encounter Chance)
    apply_perk(player, "eagle_eye_perk", catalog)
    event_payload = {
        "event_id": "test_evt",
        "options": [{"combat_chance": 0.5}]
    }
    # No difficulty delta for simplicity
    engine.difficulty_profile = type('obj', (object,), {'event_combat_delta': 0.0})
    patched = engine._event_payload_for_difficulty(event_payload, player)
    # 0.5 * 0.75 = 0.375
    assert abs(patched["options"][0]["combat_chance"] - 0.375) < 0.001
    print("Encounter Probability Reduction (Eagle Eye): OK")

    # 5. Test Quick Hands (Ammo Saving)
    apply_perk(player, "quick_hands", catalog)
    combat = CombatEngine(seed=1) 
    saved = False
    for i in range(100):
        test_player = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char)
        combat.player_attack(test_player, EnemyState(id="e1", name="Enemy", hp=10, damage_min=1, damage_max=2))
        if test_player.ammo == 10:
            saved = True
            break
    assert saved is True
    print("Ammo Saving (Quick Hands): OK")

    print("\nAll Progression & Perk tests passed!")

if __name__ == "__main__":
    from src.state_models import EnemyState # Ensure it's imported for the test
    test_progression_and_perks()
