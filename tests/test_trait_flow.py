import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, CharacterProfile
from src.event_engine import get_available_options, resolve_event_choice

def test_trait_flow():
    print("Testing Trait-based Event Options (End-to-End)...")
    
    # Mock event payload for evt_floodplain
    event_payload = {
        "event_id": "evt_floodplain",
        "description": "氾濫地",
        "options": [
            {"text": "Option 1 (Normal)", "effects": {"hp": -1}},
            {
                "text": "Option 2 (Trait Required)",
                "character_filters": {
                    "require_any_tag": ["rad_resistant"]
                },
                "effects": {"medkits": 1}
            }
        ]
    }
    
    # 1. Test Player WITH trait
    print("--- Testing Player WITH rad_resistant ---")
    char_with = CharacterProfile(
        background_id="test", display_name="Hero", 
        special={}, traits=["radiation_adapted"], tags=["rad_resistant"]
    )
    player_with = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char_with)
    
    opts_with = get_available_options(player_with, event_payload)
    assert opts_with[1]["is_met"] is True
    print("Option 2 is Met for Trait-user: OK")
    
    # 2. Test Player WITHOUT trait
    print("--- Testing Player WITHOUT rad_resistant ---")
    char_without = CharacterProfile(
        background_id="test", display_name="Noob", 
        special={}, traits=[], tags=[]
    )
    player_without = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char_without)
    
    opts_without = get_available_options(player_without, event_payload)
    assert opts_without[1]["is_met"] is False
    print("Option 2 is NOT Met for non-Trait-user: OK")
    
    # 3. Test SPECIAL requirement
    print("--- Testing Strength Requirement ---")
    event_payload["options"].append({
        "text": "Option 3 (STR Req)",
        "character_filters": {
            "require_special": {"strength": {"min": 8}}
        }
    })
    
    char_weak = CharacterProfile(background_id="test", display_name="Weakling", special={"strength": 3})
    player_weak = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char_weak)
    opts_weak = get_available_options(player_weak, event_payload)
    assert opts_weak[2]["is_met"] is False
    print("Option 3 is NOT Met for low-STR player: OK")
    
    char_strong = CharacterProfile(background_id="test", display_name="Strongman", special={"strength": 8})
    player_strong = PlayerState(hp=10, food=10, ammo=10, medkits=0, character=char_strong)
    opts_strong = get_available_options(player_strong, event_payload)
    assert opts_strong[2]["is_met"] is True
    print("Option 3 is Met for high-STR player: OK")

    print("\nAll Trait/Tag flow tests passed!")

if __name__ == "__main__":
    test_trait_flow()
