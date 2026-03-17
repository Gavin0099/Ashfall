#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.state_models import PlayerState
from src.combat_engine import CombatEngine, EnemyState

def test_equipment_effects():
    # Test hardened_blade (+1 damage)
    player_w = PlayerState(hp=10, food=10, ammo=5, medkits=1, weapon_slot="hardened_blade")
    enemy_w = EnemyState(id="thug", name="Thug", hp=10, damage_min=1, damage_max=1)
    engine = CombatEngine(seed=101) # Seed 101: first randint(1,3) is 3
    
    # Base 3 + 1 = 4 damage
    damage = engine.player_attack(player_w, enemy_w)
    assert damage == 4
    assert enemy_w.hp == 6
    print("hardened_blade (+1 damage) verification passed.")

    # Test plate_armor (-1 damage taken)
    player_a = PlayerState(hp=10, food=10, ammo=5, medkits=1, armor_slot="plate_armor")
    enemy_a = EnemyState(id="thug", name="Thug", hp=5, damage_min=2, damage_max=2)
    
    # 2 damage - 1 = 1 damage taken
    damage_taken = engine.enemy_attack(player_a, enemy_a)
    assert damage_taken == 1
    assert player_a.hp == 9
    print("plate_armor (-1 dmg taken) verification passed.")

    # Test combined effect (Soldier + Plate Armor)
    player_c = PlayerState(hp=10, food=10, ammo=5, medkits=1, background="soldier", armor_slot="plate_armor")
    # 3 damage - 1 (Soldier) - 1 (Plate) = 1 damage taken
    enemy_c = EnemyState(id="thug", name="Thug", hp=5, damage_min=3, damage_max=3)
    damage_taken_c = engine.enemy_attack(player_c, enemy_c)
    assert damage_taken_c == 1
    assert player_c.hp == 9
    print("Soldier + Plate Armor combined (-2 dmg) verification passed.")

if __name__ == "__main__":
    try:
        test_equipment_effects()
        print("\nv0.2 Equipment Effects verification SUCCESS.")
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
