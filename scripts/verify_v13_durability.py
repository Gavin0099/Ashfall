import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState, EquipmentState, CharacterProfile
from src.repair import repair_equipment

def verify_durability():
    print("Verifying v1.3 Durability System...")
    
    # Initialize components
    nodes = {
        "node_start": {"id": "node_start", "node_type": "story", "connections": ["node_combat"], "is_start": True},
        "node_combat": {"id": "node_combat", "node_type": "combat", "connections": ["node_final"], "event_pool": ["evt_scrapyard"]},
        "node_final": {"id": "node_final", "node_type": "story", "connections": [], "is_final": True}
    }
    enemies = {"enemy_raider": {"id": "enemy_raider", "name": "Raider", "hp": 5, "damage_min": 1, "damage_max": 2, "is_elite": False, "loot_table": []}}
    events = {"evt_scrapyard": {"event_id": "evt_scrapyard", "options": [{"text": "Fight", "combat_chance": 1.0}]}}
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    
    engine = RunEngine(map_state=map_state, seed=42, event_catalog=events, enemy_catalog=enemies)
    
    # Initial Player State with fresh equipment
    char_profile = CharacterProfile(background_id="soldier", display_name="Test Soldier", special={"strength": 5})
    weapon = EquipmentState(id="rust_rifle", slot="weapon", durability=10, max_durability=10)
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1, scrap=10, weapon_slot=weapon, character=char_profile)
    run = engine.create_run(player, seed=42)
    
    print(f"Initial Weapon Durability: {player.weapon_slot.durability}")
    
    # Trigger Event and Combat
    node = engine.move_to(run, "node_combat")
    from src.event_engine import resolve_event_choice
    outcome = resolve_event_choice(run.player, events["evt_scrapyard"], 0, engine.rng)
    print(f"Event Outcome Combat Triggered: {outcome.get('combat_triggered')}")
    if outcome.get("combat_triggered"):
        engine.resolve_combat(run)
    
    print(f"After event resolution (including combat):")
    print(f"Weapon Durability (run): {run.player.weapon_slot.durability}")
    print(f"Weapon Durability (orig): {player.weapon_slot.durability}")
    
    if run.player.weapon_slot.durability < 10:
        print("PASS: Durability decreased after combat.")
    else:
        print("FAIL: Durability did not decrease.")
        sys.exit(1)
        
    # Test Repair
    print(f"Current Scrap: {player.scrap}")
    repair_success = repair_equipment(player, "weapon")
    print(f"Repair Success: {repair_success}")
    print(f"Weapon Durability after repair: {player.weapon_slot.durability}")
    print(f"Scrap after repair: {player.scrap}")
    
    if player.weapon_slot.durability == 10 and player.scrap < 10:
        print("PASS: Repair successful and scrap deducted.")
    else:
        print("FAIL: Repair failed or scrap not deducted.")
        sys.exit(1)

if __name__ == "__main__":
    verify_durability()
