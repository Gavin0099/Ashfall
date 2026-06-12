from __future__ import annotations

import random
from typing import Any, Dict

from .progression import gain_xp
from .state_models import NodeState, PlayerState, apply_effects, equip_item


ATTRIBUTE_ALIASES: Dict[str, str] = {
    "STR": "strength",
    "PER": "perception",
    "INT": "intelligence",
    "CHA": "charisma",
    "SUR": "endurance",
}


def pick_event_id(
    node: NodeState,
    rng: random.Random,
    run_flags: Dict[str, Any] | None = None,
    event_catalog: Dict[str, Dict[str, Any]] | None = None,
) -> str:
    if not node.event_pool:
        raise ValueError(f"Node {node.id} has empty event_pool")

    if run_flags is None:
        run_flags = {}
    candidates = node.event_pool

    if event_catalog:
        filtered = []
        for eid in node.event_pool:
            event_data = event_catalog.get(eid, {})
            conditions = event_data.get("conditions", {})
            required_flags = conditions.get("required_flags", {})

            match = True
            for flag_key, flag_value in required_flags.items():
                if run_flags.get(flag_key) != flag_value:
                    match = False
                    break
            if match:
                filtered.append(eid)
        candidates = filtered if filtered else node.event_pool

    return rng.choice(candidates)


def _normalize_special_key(key: str) -> str:
    return ATTRIBUTE_ALIASES.get(str(key).upper(), str(key))


def _normalize_minimum_requirement(value: Any) -> Dict[str, int]:
    if isinstance(value, dict):
        return dict(value)
    return {"min": int(value)}


def _merged_character_filters(option: Dict[str, Any]) -> Dict[str, Any]:
    filters = dict(option.get("character_filters") or {})
    requirements = option.get("requirements") or {}
    if not isinstance(requirements, dict):
        return filters

    attributes = requirements.get("attribute") or {}
    if isinstance(attributes, dict):
        special = dict(filters.get("require_special") or {})
        for raw_key, raw_value in attributes.items():
            special[_normalize_special_key(raw_key)] = _normalize_minimum_requirement(raw_value)
        if special:
            filters["require_special"] = special

    traits = requirements.get("trait") or []
    if isinstance(traits, str):
        traits = [traits]
    if isinstance(traits, list):
        tags = list(filters.get("require_any_tag") or [])
        for trait in traits:
            if trait not in tags:
                tags.append(trait)
        if tags:
            filters["require_any_tag"] = tags

    return filters


def _evaluate_option_requirements(
    player: PlayerState,
    option: Dict[str, Any],
    run_flags: Dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    is_met = True
    lock_reasons: list[str] = []
    consumed_flags: list[str] = []

    req = option.get("archetype_requirement")
    if req is not None and player.archetype != req:
        is_met = False
        lock_reasons.append(f"archetype {req}")

    required_flags = option.get("required_flags", {})
    for flag_key, flag_value in required_flags.items():
        consumed_flags.append(flag_key)
        if run_flags.get(flag_key) != flag_value:
            is_met = False
            lock_reasons.append(f"flag {flag_key}={flag_value}")

    resource_req = option.get("resource_requirement", {})
    for res_key, res_val in resource_req.items():
        current_val = getattr(player, res_key, 0)
        if current_val < res_val:
            is_met = False
            lock_reasons.append(f"{res_key} >= {res_val}")

    filters = _merged_character_filters(option)
    req_tags = filters.get("require_any_tag", [])
    if req_tags:
        player_tags = set(player.character.tags) if (player.character and player.character.tags) else set()
        if not any(tag in player_tags for tag in req_tags):
            is_met = False
            lock_reasons.extend(f"tag {tag}" for tag in req_tags)

    req_special = filters.get("require_special", {})
    if req_special:
        if not player.character:
            is_met = False
            for attr, raw_limits in req_special.items():
                limits = _normalize_minimum_requirement(raw_limits)
                if "min" in limits:
                    lock_reasons.append(f"{attr} >= {limits['min']}")
                if "max" in limits:
                    lock_reasons.append(f"{attr} <= {limits['max']}")
        else:
            for attr, raw_limits in req_special.items():
                limits = _normalize_minimum_requirement(raw_limits)
                val = player.character.special.get(attr, 5)
                if "min" in limits and val < limits["min"]:
                    is_met = False
                    lock_reasons.append(f"{attr} >= {limits['min']}")
                if "max" in limits and val > limits["max"]:
                    is_met = False
                    lock_reasons.append(f"{attr} <= {limits['max']}")

    return is_met, lock_reasons, consumed_flags


def get_available_options(
    player: PlayerState,
    event_payload: Dict[str, Any],
    run_flags: Dict[str, Any] | None = None,
) -> list[Dict[str, Any]]:
    if run_flags is None:
        run_flags = {}
    options = event_payload.get("options", [])
    available = []
    for opt in options:
        is_met, lock_reasons, consumed_flags = _evaluate_option_requirements(player, opt, run_flags)
        if not is_met and opt.get("visible_if_locked", True) is False:
            continue

        display_text = opt.get("text", "")
        if not display_text and "text_variants" in opt:
            display_text = random.choice(opt["text_variants"])

        available.append(
            {
                "option": opt,
                "text": display_text,
                "is_met": is_met,
                "requirement": opt.get("archetype_requirement"),
                "locked": not is_met,
                "locked_text": opt.get("locked_text", ""),
                "lock_reasons": lock_reasons,
                "consumed_flags": consumed_flags,
            }
        )
    return available


def resolve_event_choice(
    player: PlayerState,
    event_payload: Dict[str, Any],
    option_index: int,
    rng: random.Random,
    run_flags: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if run_flags is None:
        run_flags = {}
    options = event_payload.get("options")
    if not isinstance(options, list) or not options:
        raise ValueError(f"Event {event_payload.get('id', '<unknown>')} has no options")
    if option_index < 0 or option_index >= len(options):
        raise IndexError(f"Option index out of range: {option_index}")

    option = options[option_index]
    is_met, lock_reasons, consumed_flags = _evaluate_option_requirements(player, option, run_flags)
    if not is_met:
        raise ValueError(f"Requirement failed: {', '.join(lock_reasons)}")

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

        affixes = {}
        if rng.random() < 0.5:
            if slot == "weapon":
                affixes["atk"] = 1
            elif slot == "armor":
                affixes["def"] = 1

        from .state_models import EquipmentState

        equipment = EquipmentState(id=item_id, slot=slot, affixes=affixes)
        equipment_change = equip_item(player, slot=slot, equipment=equipment)

    leveled_up = False
    if player.character:
        leveled_up = gain_xp(player, 0)

    set_flags = option.get("set_flags", {})
    if set_flags:
        run_flags.update(set_flags)

    return {
        "event_id": event_payload.get("id"),
        "option_index": option_index,
        "option_id": option.get("id"),
        "option_text": option.get("text", ""),
        "combat_triggered": combat_triggered,
        "equipment_reward": equipment_reward,
        "equipment_change": equipment_change,
        "scavenger_bonus": scavenger_bonus,
        "leveled_up": leveled_up,
        "set_flags": set_flags,
        "flags_consumed": consumed_flags,
        "effects": effects,
    }
