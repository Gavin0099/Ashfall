from __future__ import annotations

import random
from typing import Any, Dict

from .state_models import NodeState, PlayerState, apply_effects, equip_item


def pick_event_id(node: NodeState, rng: random.Random, run_flags: Dict[str, Any] | None = None, event_catalog: Dict[str, Dict[str, Any]] | None = None) -> str:
    if not node.event_pool:
        raise ValueError(f"Node {node.id} has empty event_pool")
    
    run_flags = run_flags or {}
    candidates = node.event_pool
    
    if event_catalog:
        filtered = []
        for eid in node.event_pool:
            event_data = event_catalog.get(eid, {})
            conditions = event_data.get("conditions", {})
            required_flags = conditions.get("required_flags", {})
            
            match = True
            for f_key, f_val in required_flags.items():
                if run_flags.get(f_key) != f_val:
                    match = False
                    break
            if match:
                filtered.append(eid)
        candidates = filtered if filtered else node.event_pool # Fallback to full pool if none match

    return rng.choice(candidates)


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
    equipped_tool_before = player.tool_slot.id if player.tool_slot else None
    apply_effects(player, effects)

    scavenger_bonus: Dict[str, int] = {}
    if equipped_tool_before == "scavenger_kit" or player.archetype == "scavenger":
        for key in ("food", "ammo", "scrap", "medkits"):
            if int(effects.get(key, 0)) > 0:
                amount = 1
                if key == "food":
                    player.food += amount
                elif key == "ammo":
                    player.ammo += amount
                elif key == "scrap":
                    player.scrap += amount
                elif key == "medkits":
                    player.medkits += amount
                scavenger_bonus = {key: amount}
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
        item_id = equipment_reward.get("item")
        if not isinstance(slot, str) or not isinstance(item_id, str):
            raise ValueError("equipment_reward requires string slot and item")
        
        # Roll for affixes
        affixes = {}
        if rng.random() < 0.5: # 50% chance for a basic affix
            if slot == "weapon":
                affixes["atk"] = 1
            elif slot == "armor":
                affixes["def"] = 1
        
        from .state_models import EquipmentState
        equipment = EquipmentState(id=item_id, slot=slot, affixes=affixes)
        equipment_change = equip_item(player, slot=slot, equipment=equipment)

    return {
        "event_id": event_payload.get("id"),
        "option_index": option_index,
        "option_text": option.get("text", ""),
        "combat_triggered": combat_triggered,
        "equipment_reward": equipment_reward,
        "equipment_change": equipment_change,
        "scavenger_bonus": scavenger_bonus,
        "set_flags": option.get("set_flags", {}),
    }
