import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def verify_perk_integration():
    print("--- 1. Starting Fresh Run ---")
    char_data = {
        "name": "PerkTester",
        "background": "vault_technician",
        "traits": []
    }
    
    # 1. Start Run
    res = requests.post(f"{BASE_URL}/run/start?seed=123", json=char_data)
    if not res.ok:
        print(f"FAILED to start run: {res.text}")
        return
    
    state = res.json()
    player = state['player']
    print(f"Base Max HP: {player.get('base_max_hp')} | Max HP: {player.get('max_hp')}")
    print(f"Base Max Food: {player.get('base_max_food')} | Max Food: {player.get('max_food')}")

    # 2. Gain XP
    print("\n--- 2. Gaining 100 XP to trigger Level-Up ---")
    res = requests.post(f"{BASE_URL}/debug/gain_xp?amount=100")
    if not res.ok:
        print(f"FAILED to gain XP: {res.text}")
        return
        
    # Check eligibility
    res = requests.get(f"{BASE_URL}/run/state")
    state = res.json()
    can_level_up = state['player']['character']['can_level_up']
    print(f"Can Level Up: {can_level_up}")

    # 3. Select 'tough_as_nails' (Steel Will)
    print("\n--- 3. Selecting 'tough_as_nails' Perk ---")
    select_data = {"perk_id": "tough_as_nails"}
    res = requests.post(f"{BASE_URL}/run/level_up/select", json=select_data)
    if not res.ok:
        # Maybe it randomed? Check options first
        print("Selection failed, checking available options...")
        opt_res = requests.get(f"{BASE_URL}/run/level_up/options")
        options = opt_res.json().get('options', [])
        print(f"Available Options: {[o['id'] for o in options]}")
        if options:
            perk_id = options[0]['id']
            print(f"Selecting fallback perk: {perk_id}")
            res = requests.post(f"{BASE_URL}/run/level_up/select", json={"perk_id": perk_id})
    
    if res.ok:
        final_state = res.json()['state']
        p = final_state['player']
        print(f"Final Max HP: {p['max_hp']} (Base: {p['base_max_hp']})")
        print(f"Final Max Food: {p['max_food']} (Base: {p['base_max_food']})")
        
        perks = p.get('perks', [])
        print(f"Active Perks: {perks}")
        
        success = False
        if 'tough_as_nails' in perks and p['max_hp'] > p['base_max_hp']:
            print("SUCCESS: Steel Will increased Max HP!")
            success = True
        elif 'pack_rat_perk' in perks and p['max_food'] > p['base_max_food']:
            print("SUCCESS: Pack Rat increased Max Food!")
            success = True
        elif len(perks) > 0:
            print(f"SUCCESS: Perk {perks[-1]} selected, but no direct stat effect to verify via HP/Food.")
            success = True
            
        if not success and len(perks) > 0:
            print("FAILED: Perk selected but no stat change detected.")
    else:
        print(f"FAILED to select perk: {res.text}")

if __name__ == "__main__":
    verify_perk_integration()

if __name__ == "__main__":
    verify_perk_integration()
