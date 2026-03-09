from __future__ import annotations

import random
from typing import Dict, List

from .state_models import EnemyState, PlayerState


class CombatEngine:
    """Simple turn-based combat loop from current combat spec."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def player_attack(self, player: PlayerState, enemy: EnemyState) -> int:
        if player.ammo <= 0:
            raise ValueError("Cannot attack without ammo")
        player.ammo -= 1
        damage = self.rng.randint(1, 3)
        enemy.hp -= damage
        return damage

    def player_use_medkit(self, player: PlayerState) -> int:
        if player.medkits <= 0:
            raise ValueError("Cannot use medkit without medkits")
        player.medkits -= 1
        heal = 3
        player.hp += heal
        return heal

    def enemy_attack(self, player: PlayerState, enemy: EnemyState) -> int:
        damage = self.rng.randint(enemy.damage_min, enemy.damage_max)
        player.hp -= damage
        return damage

    def run_auto_combat(self, player: PlayerState, enemy: EnemyState) -> Dict[str, object]:
        """
        Automatic strategy:
        - Attack if ammo > 0
        - Else use medkit if available and hp <= 4
        - Else take direct hit (skip player action)
        """
        log: List[str] = []
        rounds = 0

        while player.hp > 0 and enemy.hp > 0:
            rounds += 1
            if player.ammo > 0:
                dealt = self.player_attack(player, enemy)
                log.append(f"R{rounds}: player attacks for {dealt}")
            elif player.medkits > 0 and player.hp <= 4:
                healed = self.player_use_medkit(player)
                log.append(f"R{rounds}: player uses medkit for +{healed} hp")
            else:
                log.append(f"R{rounds}: player cannot act effectively")

            if enemy.hp <= 0:
                return {
                    "victory": True,
                    "rounds": rounds,
                    "player_hp": player.hp,
                    "enemy_hp": enemy.hp,
                    "log": log,
                }

            taken = self.enemy_attack(player, enemy)
            log.append(f"R{rounds}: enemy attacks for {taken}")

        return {
            "victory": enemy.hp <= 0 and player.hp > 0,
            "rounds": rounds,
            "player_hp": player.hp,
            "enemy_hp": enemy.hp,
            "log": log,
        }
