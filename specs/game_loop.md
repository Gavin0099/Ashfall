# Game Loop Specification

## Overview

The game is a roguelite survival strategy game where players manage a caravan traveling through a post-apocalyptic wasteland.

Each run consists of moving through nodes on a map, resolving events, managing resources, and attempting to reach the final node.

Current validated baseline is a CLI-first v0.1 loop.

Planned v0.2 expansion keeps route choice as the primary tension source while adding:

- character background
- travel mode
- lightweight equipment effects

---

## Run Flow

1. Start Run
2. Generate Map
3. Player selects next node
4. Resolve node event
5. Update resources
6. Check death conditions
7. Repeat until final node or death

### v0.1 Baseline

1. Start Run
2. Generate Map
3. Player selects next node
4. Resolve node event
5. Update resources
6. Check death conditions
7. Repeat until final node or death

### v0.2 Target Shape

1. Start Run
2. Choose character background
3. Generate Map
4. Player selects next node
5. Player selects travel mode
6. Resolve node event
7. Apply equipment modifiers if present
8. Update resources
9. Check death conditions
10. Repeat until final node or death

---

## Death Conditions

A run ends if any of the following occurs:

- Food <= 0
- Player HP <= 0

---

## Victory Condition

Reaching the final node on the map triggers the end event.

---

## Run State Variables

Player State:

- hp
- food
- ammo
- medkits

Run State:

- current_node
- visited_nodes
- map_seed

## v0.2 Planned Additions

Character layer:

- background_id

Travel layer:

- travel_mode

Equipment layer:

- weapon_slot
- armor_slot
- tool_slot
