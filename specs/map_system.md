# Map System Specification

## Overview

The map is a directed graph of nodes representing locations in the wasteland.

Players move between nodes until reaching the final node.

---

## Map Structure

Prototype map layout:

Start
  |
 A   B
  \ /
   C
  / \
 D   E

---

## Node Types

- resource
- combat
- trade
- story

---

## Node Data Structure

Node fields:

- id
- node_type
- connections
- event_pool

Example:

{
  "id": "node_A",
  "node_type": "resource",
  "connections": ["node_C"]
}