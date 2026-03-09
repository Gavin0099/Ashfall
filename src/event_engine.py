from __future__ import annotations

import random
from typing import Any, Dict

from .state_models import NodeState, PlayerState, apply_effects


def pick_event_id(node: NodeState, rng: random.Random) -> str:
    if not node.event_pool:
        raise ValueError(f"Node {node.id} has empty event_pool")
    return rng.choice(node.event_pool)


def resolve_event_choice(
    player: PlayerState,
    event_payload: Dict[str, Any],
    option_index: int,
    rng: random.Random,
) -> Dict[str, Any]:
    options = event_payload.get("options")
    if not isinstance(options, list) or not options:
        raise ValueError(f"Event {event_payload.get('id', '<unknown>')} has no options")
    if option_index < 0 or option_index >= len(options):
        raise IndexError(f"Option index out of range: {option_index}")

    option = options[option_index]
    effects = option.get("effects", {})
    if not isinstance(effects, dict):
        raise ValueError("Event option effects must be an object")
    apply_effects(player, effects)

    chance = float(option.get("combat_chance", 0.0))
    if chance < 0 or chance > 1:
        raise ValueError("combat_chance must be between 0 and 1")

    combat_triggered = rng.random() < chance
    return {
        "event_id": event_payload.get("id"),
        "option_index": option_index,
        "option_text": option.get("text", ""),
        "combat_triggered": combat_triggered,
    }
