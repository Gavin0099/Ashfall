# Combat System Specification

## Overview

Combat is a simple turn-based system.

Player and enemy take turns attacking.

---

## Player Actions

- Attack (requires ammo)
- Use Medkit

---

## Combat Variables

Player:

- hp
- ammo

Enemy:

- hp
- damage_range

---

## Damage Formula

Player Damage:
random(1-3)

Enemy Damage:
random(1-2)

---

## Combat End Conditions

Victory:
enemy_hp <= 0

Defeat:
player_hp <= 0