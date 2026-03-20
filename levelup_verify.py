import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_levelup_flow():
    # 1. Start Run
    print("--- 1. Starting Run ---")
    char_data = {
        "name": "TestHero",
        "background": "vault_technician",
        "traits": ["radiation_adaptation"]
    }
    try:
        res = requests.post(f"{BASE_URL}/run/start?seed=42", json=char_data)
        if res.status_code != 200:
            print(f"FAILED: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return

    state_dict = res.json()
    try:
        char = state_dict['player']['character']
    except KeyError:
        print(f"DEBUG: state_dict keys: {state_dict.keys()}")
        if 'player' in state_dict:
            print(f"DEBUG: player keys: {state_dict['player'].keys()}")
        print(f"FULL RESPONSE: {json.dumps(state_dict, indent=2)}")
        return
    
    if not char:
        print("ERROR: Character is None in start response.")
        return
    
    # 2. Get Perk Options
    print("\n--- 2. Checking Perk Options ---")
    res = requests.get(f"{BASE_URL}/run/level_up/options")
    if res.status_code != 200:
        print(f"FAILED: {res.text}")
        return
    options = res.json()["options"]
    print(f"Found {len(options)} perk options: {[o['display_name'] for o in options]}")
    
    if not options:
        print("ERROR: No options found despite XP threshold.")
        return

    # 3. Select Perk
    perk_id = options[0]["id"]
    print(f"\n--- 3. Selecting Perk: {perk_id} ---")
    res = requests.post(f"{BASE_URL}/run/level_up/select", json={"perk_id": perk_id})
    if res.status_code != 200:
        print(f"FAILED: {res.text}")
        return
    
    result = res.json()
    final_state = result["state"]
    new_perks = final_state["player"]["character"]["perks"]
    new_level = final_state["player"]["character"]["level"]
    print(f"SUCCESS: Level is now {new_level}, Perks: {new_perks}")
    
    if perk_id in new_perks and new_level == 2:
        print("\n=== VERIFICATION COMPLETE: Level-up logic works! ===")
    else:
        print("\n=== VERIFICATION FAILED: State mismatch. ===")

if __name__ == "__main__":
    test_levelup_flow()
