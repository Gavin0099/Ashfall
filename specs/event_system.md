# Event System Specification

## Overview

Events represent narrative encounters that occur when entering a node.

Each event presents the player with choices that modify game state.

---

## Event Structure

Fields:

- id
- description
- options

Example:

{
  "id": "abandoned_store",
  "description": "You discover an abandoned supermarket.",
  "options": [
    {
      "text": "Search the shelves",
      "effects": {
        "food": +3
      },
      "combat_chance": 0.3
    },
    {
      "text": "Leave immediately"
    }
  ]
}