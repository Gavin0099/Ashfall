import sys
from pathlib import Path
import random

# Add root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, CharacterProfile
from src.event_engine import get_available_options, resolve_event_choice
from src.difficulty import build_starting_player

def test_character_selection_and_resources():
    print("Testing Character Selection and Resources...")
    
    # Mock data from backgrounds.json
    bg_medic = {
        "background_id": "wasteland_medic",
        "special_preset": {"strength": 3, "perception": 6, "endurance": 5, "charisma": 6, "intelligence": 7, "agility": 4, "luck": 4},
        "granted_tags": ["medic_trained"],
        "starting_resource_bias": {"medkits": 3, "food": 1}
    }
    
    profile = CharacterProfile(
        background_id=bg_medic["background_id"],
        display_name="Medic",
        special=bg_medic["special_preset"],
        tags=bg_medic["granted_tags"]
    )
    
    player = build_starting_player(name="normal", character=profile, resource_bias=bg_medic["starting_resource_bias"])
    
    # Check resources (Normal: HP 10, Food 7, Ammo 3, Medkits 1)
    # Plus bias: Food +1, Medkits +3 -> Food 8, Medkits 4
    assert player.medkits == 4
    assert player.food == 8
    assert player.character.special["intelligence"] == 7
    print("✅ Resource bias and specialization passed.")

def test_special_filtering():
    print("Testing SPECIAL Filtering...")
    
    profile = CharacterProfile(
        background_id="test",
        display_name="Test",
        special={"strength": 8, "intelligence": 2, "perception": 5, "endurance": 5, "charisma": 5, "agility": 5, "luck": 5},
        tags=["strong"]
    )
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1, character=profile)
    
    event = {
        "id": "test_evt",
        "description": "Test",
        "options": [
            {
                "text": "Strong Man", 
                "character_filters": {"require_special": {"strength": {"min": 6}}},
                "effects": {}
            },
            {
                "text": "Smart Man", 
                "character_filters": {"require_special": {"intelligence": {"min": 5}}},
                "effects": {}
            },
            {
                "text": "Strong Tag", 
                "character_filters": {"require_any_tag": ["strong"]},
                "effects": {}
            }
        ]
    }
    
    avail = get_available_options(player, event)
    assert avail[0]["is_met"] is True # Strength 8 >= 6
    assert avail[1]["is_met"] is False # Intelligence 2 < 5
    assert avail[2]["is_met"] is True # Tag "strong" found
    print("✅ SPECIAL and Tag filtering passed.")

if __name__ == "__main__":
    try:
        test_character_selection_and_resources()
        test_special_filtering()
        print("\nAll v1.0 Character System tests PASSED.")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
