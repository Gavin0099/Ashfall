from __future__ import annotations

import random
from typing import Any, Dict

from .state_models import NodeState, PlayerState, apply_effects, equip_item
from .progression import gain_xp


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


def get_available_options(player: PlayerState, event_payload: Dict[str, Any], run_flags: Dict[str, Any] | None = None) -> list[Dict[str, Any]]:
    """回傳玩家目前可選的選項清單（包含標註是否符合職業與旗標條件）。"""
    run_flags = run_flags or {}
    options = event_payload.get("options", [])
    available = []
    for opt in options:
        req = opt.get("archetype_requirement")
        is_met = (req is None or player.archetype == req)

        # Flag requirement check
        required_flags = opt.get("required_flags", {})
        for f_key, f_val in required_flags.items():
            if run_flags.get(f_key) != f_val:
                is_met = False
                break
        
        # Resource requirement check
        resource_req = opt.get("resource_requirement", {})
        for res_key, res_val in resource_req.items():
            current_val = getattr(player, res_key, 0)
            if current_val < res_val:
                is_met = False
                break

        if not is_met:
             # If combined requirements already failed, skip further checks
             pass
        else:
            # v1.0 Character Filters
            filters = opt.get("character_filters")
            if filters:
                # Tag check
                req_tags = filters.get("require_any_tag", [])
                if req_tags:
                    player_tags = set(player.character.tags) if (player.character and player.character.tags) else set()
                    if not any(t in player_tags for t in req_tags):
                        is_met = False
                
                # SPECIAL check
                req_special = filters.get("require_special", {})
                if req_special and player.character:
                    for attr, limits in req_special.items():
                        val = player.character.special.get(attr, 5)
                        if "min" in limits and val < limits["min"]:
                            is_met = False
                        if "max" in limits and val > limits["max"]:
                            is_met = False
        
        # Pick display text
        display_text = opt.get("text", "")
        if not display_text and "text_variants" in opt:
            # We use a stable pick if possible or just random for now
            # For simplicity in CLI, random is fine as it's called once per event
            display_text = random.choice(opt["text_variants"])

        available.append({
            "option": opt,
            "text": display_text,
            "is_met": is_met,
            "requirement": req
        })
    return available

def resolve_event_choice(
    player: PlayerState,
    event_payload: Dict[str, Any],
    option_index: int,
    rng: random.Random,
    run_flags: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    run_flags = run_flags or {}
    options = event_payload.get("options")
    if not isinstance(options, list) or not options:
        raise ValueError(f"Event {event_payload.get('id', '<unknown>')} has no options")
    if option_index < 0 or option_index >= len(options):
        raise IndexError(f"Option index out of range: {option_index}")

    option = options[option_index]
    
    # Flag requirement check
    required_flags = option.get("required_flags", {})
    for f_key, f_val in required_flags.items():
        if run_flags.get(f_key) != f_val:
            raise ValueError(f"Flag requirement failed: {f_key} expected {f_val}")

    # Resource requirement check
    resource_req = option.get("resource_requirement", {})
    for res_key, res_val in resource_req.items():
        if getattr(player, res_key, 0) < res_val:
            raise ValueError(f"Insufficient {res_key}: required {res_val}")

    # Archetype check
    req = option.get("archetype_requirement")
    if req and player.archetype != req:
        raise ValueError(f"Archetype {player.archetype} does not meet requirement {req}")

    # v1.0 Character Filters
    filters = option.get("character_filters")
    if filters:
        # Tag check
        req_tags = filters.get("require_any_tag", [])
        if req_tags:
            player_tags = set(player.character.tags) if (player.character and player.character.tags) else set()
            if not any(t in player_tags for t in req_tags):
                raise ValueError(f"Requirement failed: require_any_tag {req_tags}")
        
        # SPECIAL check
        req_special = filters.get("require_special", {})
        if req_special and player.character:
            for attr, limits in req_special.items():
                val = player.character.special.get(attr, 5)
                if ("min" in limits and val < limits["min"]) or ("max" in limits and val > limits["max"]):
                    raise ValueError(f"SPECIAL property {attr} value {val} outside required range {limits}")

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

    # v1.1 Progression: Check for level up if XP was added
    leveled_up = False
    if player.character:
        # Pass 0 to just trigger the rollover logic if apply_effects already added XP
        leveled_up = gain_xp(player, 0)

    return {
        "event_id": event_payload.get("id"),
        "option_index": option_index,
        "option_text": option.get("text", ""),
        "combat_triggered": combat_triggered,
        "equipment_reward": equipment_reward,
        "equipment_change": equipment_change,
        "scavenger_bonus": scavenger_bonus,
        "leveled_up": leveled_up,
        "set_flags": option.get("set_flags", {}),
    }
