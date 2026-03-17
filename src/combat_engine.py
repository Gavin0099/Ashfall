from __future__ import annotations

import random
from typing import Dict, List, Optional

from .state_models import EnemyState, PlayerState


class CombatEngine:
    """Simple turn-based combat loop from current combat spec."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def player_attack(self, player: PlayerState, enemy: EnemyState) -> int:
        if player.ammo <= 0:
            raise ValueError("Cannot attack without ammo")
        
        # Quick Hands Perk: 20% chance to save ammo
        if player.character and "quick_hands" in player.character.perks and self.rng.random() < 0.2:
            pass
        else:
            player.ammo -= 1
            
        damage = self.rng.randint(1, 3)
        
        weapon = player.weapon_slot
        if weapon and weapon.durability > 0:
            # Check Requirements
            met = True
            if player.character:
                for stat, val in weapon.requirements.items():
                    if player.character.special.get(stat, 0) < val:
                        met = False
                        break
            
            if met:
                # Base Logic
                if weapon.id in ("rust_rifle", "hardened_blade"):
                    damage += 1
                
                # Scaling Logic
                if player.character:
                    for stat, multiplier in weapon.scaling.items():
                        stat_val = player.character.special.get(stat, 5)
                        damage += int(stat_val * multiplier)

                # Phase 5.0: Random affixes (atk)
                damage += weapon.affixes.get("atk", 0)
            else:
                pass

        if enemy.special_ability == "thick_hide" and not enemy.special_used:
            damage = max(1, damage - 1)
            enemy.special_used = True
        enemy.hp -= damage
        return damage

    def player_use_medkit(self, player: PlayerState) -> int:
        if player.medkits <= 0:
            raise ValueError("Cannot use medkit without medkits")
        player.medkits -= 1
        heal = 8
        if player.archetype == "medic":
            heal += 1
        
        # Field Medic Perk: +2 heal
        if player.character and "field_medic_perk" in player.character.perks:
            heal += 2
        
        # Bloodlust penalty: healing halved
        if player.character and "bloodlust" in player.character.tags:
            heal = max(1, heal // 2)
            
        player.hp += heal
        return heal

    def enemy_attack(self, player: PlayerState, enemy: EnemyState) -> int:
        damage = self.rng.randint(enemy.damage_min, enemy.damage_max)
        
        # Elite bonus: +1 damage
        if enemy.is_elite:
            damage += 1

        if enemy.special_ability == "opening_shot" and not enemy.special_used:
            damage += 1
            enemy.special_used = True
        
        # Phase 4.0: Boss Special Abilities
        if enemy.special_ability == "shockwave" and not enemy.special_used:
            damage += 3
            enemy.special_used = True
        
        if enemy.special_ability == "frenzy" and enemy.hp < 15:
            damage += 2
        
        if player.archetype == "soldier":
            damage = max(1, damage - 1)
        
        # Legacy Specifics (Scaling/Fixed ID)
        armor = player.armor_slot
        if armor and armor.durability > 0:
            met = True
            if player.character:
                for stat, val in armor.requirements.items():
                    if player.character.special.get(stat, 0) < val:
                        met = False
                        break
            if met:
                if armor.id == "plate_armor":
                    damage = max(0, damage - 1)
                
                if player.character:
                    for stat, multiplier in armor.scaling.items():
                        stat_val = player.character.special.get(stat, 5)
                        damage = max(0, damage - int(stat_val * multiplier))

        # Phase 5.0: Equipment Affix Defense (global)
        def_bonus = 0
        if player.weapon_slot:
            def_bonus += player.weapon_slot.affixes.get("def", 0)
        if hasattr(player, "armor_slot") and player.armor_slot:
            def_bonus += player.armor_slot.affixes.get("def", 0)
        if hasattr(player, "tool_slot") and player.tool_slot:
            def_bonus += player.tool_slot.affixes.get("def", 0)
        
        damage = max(0, damage - def_bonus)
            
        damage = max(0, damage)
        player.hp -= damage
        return damage

    def run_auto_combat(self, player: PlayerState, enemy: EnemyState) -> Dict[str, object]:
        log: List[str] = []
        rounds = 0
        if enemy.is_elite:
            log.append(f"⚠️ 遭遇精英敵人：{enemy.name}！")

        while player.hp > 0 and enemy.hp > 0:
            rounds += 1
            # Survival first: use medkit if HP is critical
            if player.medkits > 0 and player.hp <= 6:
                healed = self.player_use_medkit(player)
                log.append(f"第 {rounds} 回合：你使用醫療包，回復 {healed} 點生命")
            elif player.ammo > 0:
                special_before = enemy.special_used
                dealt = self.player_attack(player, enemy)
                log.append(f"第 {rounds} 回合：你攻擊並造成 {dealt} 點傷害")
                if enemy.special_ability == "thick_hide" and not special_before and enemy.special_used:
                    log.append(f"第 {rounds} 回合：敵人的厚皮減少了 1 點傷害")
            else:
                log.append(f"第 {rounds} 回合：你無法有效反擊")

            if enemy.hp <= 0:
                return { "victory": True, "rounds": rounds, "player_hp": player.hp, "enemy_hp": enemy.hp, "log": log }

            special_before = enemy.special_used
            taken = self.enemy_attack(player, enemy)
            log.append(f"第 {rounds} 回合：敵人攻擊，造成 {taken} 點傷害")
            
            if enemy.special_ability == "opening_shot" and not special_before and enemy.special_used:
                log.append(f"第 {rounds} 回合：敵人的先發攻擊額外造成 1 點傷害")
            elif enemy.special_ability == "shockwave" and not special_before and enemy.special_used:
                log.append(f"第 {rounds} 回合：【首領技能】鋼鐵衝擊波造成額外 3 點傷害！")
            if enemy.special_ability == "frenzy" and enemy.hp < 15:
                log.append(f"第 {rounds} 回合：【首領技能】敵人陷入狂暴狀態，傷害提升！")

        return { "victory": enemy.hp <= 0 and player.hp > 0, "rounds": rounds, "player_hp": player.hp, "enemy_hp": enemy.hp, "log": log }
