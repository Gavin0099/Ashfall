from __future__ import annotations

import random
from typing import Any, Dict

from .state_models import NodeState, PlayerState, apply_effects, equip_item


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
    equipped_tool_before = player.tool_slot
    apply_effects(player, effects)

    scavenger_bonus: Dict[str, int] = {}
    if equipped_tool_before == "scavenger_kit":
        for key in ("food", "ammo", "scrap", "medkits"):
            if int(effects.get(key, 0)) > 0:
                if key == "food":
                    player.food += 1
                elif key == "ammo":
                    player.ammo += 1
                elif key == "scrap":
                    player.scrap += 1
                elif key == "medkits":
                    player.medkits += 1
                scavenger_bonus = {key: 1}
                break

    chance = float(option.get("combat_chance", 0.0))
    if chance < 0 or chance > 1:
        raise ValueError("combat_chance must be between 0 and 1")

    combat_triggered = rng.random() < chance
    equipment_change = None
    equipment_reward = option.get("equipment_reward")
    if equipment_reward is not None:
        if not isinstance(equipment_reward, dict):
            raise ValueError("equipment_reward must be an object")
        slot = equipment_reward.get("slot")
        item = equipment_reward.get("item")
        if not isinstance(slot, str) or not isinstance(item, str):
            raise ValueError("equipment_reward requires string slot and item")
        equipment_change = equip_item(player, slot=slot, item=item)

    return {
        "event_id": event_payload.get("id"),
        "option_index": option_index,
        "option_text": option.get("text", ""),
        "combat_triggered": combat_triggered,
        "equipment_reward": equipment_reward,
        "equipment_change": equipment_change,
        "scavenger_bonus": scavenger_bonus,
    }
