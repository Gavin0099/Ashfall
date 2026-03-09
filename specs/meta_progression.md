# Meta Progression Specification

## Overview

Meta progression defines persistent growth across runs.

Players earn scrap from each run and spend it to unlock passive upgrades.

Meta progression must not change the core run loop rules. It only modifies starting conditions or reward multipliers.

---

## Core Concepts

Persistent Currency:
- scrap

Persistent Unlock Categories:
- caravan_upgrades
- combat_upgrades
- scouting_upgrades

Run Result Inputs:
- reached_final_node (bool)
- nodes_visited (int)
- enemies_defeated (int)
- ending_hp (int)

---

## Reward Formula

Base reward:
- scrap = 2 + nodes_visited

Bonus rewards:
- +5 if reached_final_node == true
- +enemies_defeated
- +2 if ending_hp >= 6

Minimum reward:
- reward is clamped to >= 1

---

## Unlock Rules

Unlock item fields:
- id
- category
- cost
- max_level
- effects_per_level

Category examples:
- caravan_upgrades: +starting_food, +starting_medkits
- combat_upgrades: +starting_ammo, +player_damage_bonus
- scouting_upgrades: +event_visibility, +resource_node_bonus

Rules:
- Player can only buy one level at a time.
- Cost is paid immediately from persistent scrap.
- Current level cannot exceed max_level.
- Effects are applied at run start unless explicitly marked as run_end modifiers.

---

## Save Data Structure

Persistent meta profile fields:
- profile_id
- total_scrap
- lifetime_scrap_earned
- unlock_levels
- unlocked_at_version

Example:

{
  "profile_id": "default",
  "total_scrap": 14,
  "lifetime_scrap_earned": 39,
  "unlock_levels": {
    "up_food_ration": 2,
    "up_sharpshooter": 1
  },
  "unlocked_at_version": "0.1"
}

---

## Integration Points

At run start:
- Resolve all unlocked passive effects into initial player state.

At run end:
- Compute scrap reward from final run stats.
- Add reward to total_scrap and lifetime_scrap_earned.

At upgrade purchase:
- Validate cost and max_level, then mutate unlock_levels.

---

## Failure Cases

- Unknown unlock id: reject purchase.
- Insufficient scrap: reject purchase with explicit reason.
- Level overflow: reject purchase and keep previous state.
- Corrupt save data: fallback to safe defaults and log validation error.

---

## Non-Goals (Phase A)

- No prestige/reset loop.
- No branching tech tree dependencies.
- No live-ops balancing pipeline.
