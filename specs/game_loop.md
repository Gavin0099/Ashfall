# Game Loop Specification

## Overview

The game is a roguelite survival strategy game where players manage a caravan traveling through a post-apocalyptic wasteland.

Each run consists of moving through nodes on a map, resolving events, managing resources, and attempting to reach the final node.

---

## Run Flow

1. Start Run
2. Generate Map
3. Player selects next node
4. Resolve node event
5. Update resources
6. Check death conditions
7. Repeat until final node or death

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