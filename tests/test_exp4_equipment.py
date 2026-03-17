import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState, EnemyState, CharacterProfile, EquipmentState
from src.combat_engine import CombatEngine
from src.run_engine import RunEngine, MapState, NodeState
from src.item_catalog import catalog

def test_equipment_requirements():
    print("Testing Equipment Requirements...")
    # Strength 3 player
    char = CharacterProfile(background_id="test", display_name="Weakling", special={"strength": 3})
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1, character=char)
    
    # Plate Armor (Requires STR 6)
    plate = catalog.create_instance("plate_armor")
    player.armor_slot = plate
    
    enemy = EnemyState(id="thug", name="Thug", hp=5, damage_min=3, damage_max=3)
    engine = CombatEngine(seed=42)
    
    # Armor should fail requirement, damage should be full (3)
    damage = engine.enemy_attack(player, enemy)
    print(f"Damage taken with STR 3 (Req 6): {damage}")
    assert damage == 3
    
    # Set STR to 10
    char.special["strength"] = 10
    # Armor should now work. 
    # Base 3 - 1 (plate_armor) - 1 (endurance 5 * 0.2) = 1
    player.hp = 10
    damage = engine.enemy_attack(player, enemy)
    print(f"Damage taken with STR 10 (Req 6): {damage}")
    assert damage == 1

def test_equipment_scaling():
    print("\nTesting Equipment Scaling...")
    # Player with STR 10
    char = CharacterProfile(background_id="test", display_name="Brute", special={"strength": 10})
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1, character=char)
    
    # Sledgehammer (Scaling: STR 1.2, Base: 4-7)
    # Damage = rng(4, 7) + int(10 * 1.2) = rng(4, 7) + 12
    hammer = catalog.create_instance("sledgehammer")
    player.weapon_slot = hammer
    
    enemy = EnemyState(id="dummy", name="Dummy", hp=100, damage_min=1, damage_max=1)
    engine = CombatEngine(seed=1) # Seed 1: rng(1,3) for base damage? No, player_attack uses 1-3 base
    
    # Re-calculate expected damage:
    # player_attack base = rng(1,3) + scaling.
    # hammer is NOT makeshift, so no +1.
    # Total = rng(1,3) + 12 = 13 to 15.
    
    damage = engine.player_attack(player, enemy)
    print(f"Damage dealt with Sledgehammer (STR 10): {damage}")
    assert 13 <= damage <= 15

def test_buff_ticking():
    print("\nTesting Buff Ticking...")
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1)
    player.buffs["adrenaline"] = 2
    
    # Mock map
    nodes = {
        "n1": NodeState(id="n1", node_type="resource", connections=["n2"], event_pool=[]),
        "n2": NodeState(id="n2", node_type="resource", connections=[], event_pool=[])
    }
    map_state = MapState(nodes=nodes, start_node_id="n1")
    engine = RunEngine(map_state=map_state, seed=42)
    run = engine.create_run(player, seed=42)
    
    print(f"Buffs before move: {run.player.buffs}")
    assert "adrenaline" in run.player.buffs
    
    engine.move_to(run, "n2")
    print(f"Buffs after 1 move: {run.player.buffs}")
    assert run.player.buffs["adrenaline"] == 1
    
    # Move is not possible to n3, but we can simulate tick
    engine.tick_buffs(run)
    print(f"Buffs after 2nd tick: {run.player.buffs}")
    assert "adrenaline" not in run.player.buffs

if __name__ == "__main__":
    try:
        test_equipment_requirements()
        test_equipment_scaling()
        test_buff_ticking()
        print("\nAll EXP-4 tests passed!")
    except AssertionError as e:
        print(f"\nTest failed!")
        sys.exit(1)
