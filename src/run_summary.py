from __future__ import annotations

from typing import Any


def collect_combat_loot(decision_log: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    loot: list[dict[str, int | str]] = []
    for entry in decision_log:
        combat_loot = entry.get("combat_loot", [])
        if not isinstance(combat_loot, list):
            continue
        for item in combat_loot:
            if not isinstance(item, dict):
                continue
            resource = item.get("resource")
            amount = item.get("amount")
            if isinstance(resource, str) and isinstance(amount, int) and amount > 0:
                loot.append({"resource": resource, "amount": amount})
    return loot


def summarize_loot_by_resource(loot: list[dict[str, int | str]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for item in loot:
        resource = item["resource"]
        amount = item["amount"]
        if isinstance(resource, str) and isinstance(amount, int):
            totals[resource] = totals.get(resource, 0) + amount
    return totals


def infer_route_family(route: list[str]) -> str:
    has_north = any("north" in node for node in route)
    has_south = any("south" in node for node in route)
    if has_north and has_south:
        return "mixed"
    if has_north:
        return "north"
    if has_south:
        return "south"
    return "unknown"


def collect_equipment_items(decision_log: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for entry in decision_log:
        equipment_change = entry.get("equipment_change")
        if not isinstance(equipment_change, dict):
            continue
        item = equipment_change.get("item")
        if isinstance(item, str) and item not in seen:
            seen.add(item)
            items.append(item)
    return items


def collect_low_resource_flags(decision_log: list[dict[str, Any]], player_final: dict[str, Any]) -> list[str]:
    min_hp = min([max(0, int(entry["player_after"]["hp"])) for entry in decision_log] + [max(0, int(player_final["hp"]))])
    min_food = min([max(0, int(entry["player_after"]["food"])) for entry in decision_log] + [max(0, int(player_final["food"]))])
    min_ammo = min([max(0, int(entry["player_after"]["ammo"])) for entry in decision_log] + [max(0, int(player_final["ammo"]))])
    flags: list[str] = []
    if min_hp <= 3:
        flags.append("low_hp")
    if min_food <= 2:
        flags.append("low_food")
    if min_ammo <= 1:
        flags.append("low_ammo")
    if int(player_final.get("radiation", 0)) >= 2:
        flags.append("high_radiation")
    return flags


def collect_risk_tags(
    decision_log: list[dict[str, Any]],
    end_reason: str | None,
    failure_analysis: dict[str, Any],
    player_final: dict[str, Any],
) -> list[str]:
    tags: list[str] = []
    if any(bool(entry.get("combat_triggered")) for entry in decision_log):
        tags.append("combat_seen")
    if any(int(entry["player_after"].get("radiation", 0)) > 0 for entry in decision_log):
        tags.append("radiation_pressure")
    if any("food" in str(entry.get("warning_signals", [])) for entry in decision_log):
        tags.append("food_pressure")
    if any(entry.get("equipment_change") for entry in decision_log):
        tags.append("equipment_arc")
    if end_reason:
        tags.append(f"end_{end_reason}")
    if bool(failure_analysis.get("is_trash_time_death")):
        tags.append("trash_time_risk")
    if int(player_final.get("radiation", 0)) >= 2:
        tags.append("radiation_carryover")
    return tags


def determine_turning_point(
    decision_log: list[dict[str, Any]],
    failure_analysis: dict[str, Any],
) -> str | None:
    regret_nodes = failure_analysis.get("regret_nodes", [])
    if regret_nodes:
        top_regret = regret_nodes[0]
        return f"{top_regret['node_id']} ({top_regret['description']})"
    for entry in decision_log:
        if entry.get("equipment_summary"):
            return f"{entry['node']} ({entry['equipment_summary']})"
    high_pressure = [entry for entry in decision_log if entry.get("pressure")]
    if high_pressure:
        return str(high_pressure[-1]["node"])
    return None


def collect_equipment_details(decision_log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for entry in decision_log:
        change = entry.get("equipment_change")
        if not isinstance(change, dict):
            continue
        item_data = change.get("item_data")
        if isinstance(item_data, dict):
            details.append(item_data)
        elif isinstance(change.get("item"), str):
            # Fallback for old logs or simple ID references
            details.append({"id": change["item"], "rarity": "common", "affixes": {}})
    return details


def build_run_summary(
    *,
    run_id: str,
    route: list[str],
    ended: bool,
    victory: bool,
    end_reason: str | None,
    player_final: dict[str, Any],
    decision_log: list[dict[str, Any]],
    summary: dict[str, Any],
    failure_analysis: dict[str, Any],
) -> dict[str, Any]:
    equipment_details = collect_equipment_details(decision_log)
    equipment_ids = [d["id"] for d in equipment_details]
    
    combat_loot = collect_combat_loot(decision_log)
    loot_totals = summarize_loot_by_resource(combat_loot)
    low_resource_flags = collect_low_resource_flags(decision_log, player_final)
    risk_tags = collect_risk_tags(decision_log, end_reason, failure_analysis, player_final)
    route_family = infer_route_family(route)
    combat_count = sum(1 for entry in decision_log if bool(entry.get("combat_triggered")))
    max_radiation = max([max(0, int(entry["player_after"].get("radiation", 0))) for entry in decision_log] + [max(0, int(player_final.get("radiation", 0)))])
    min_food = min([max(0, int(entry["player_after"].get("food", 0))) for entry in decision_log] + [max(0, int(player_final.get("food", 0)))])
    min_hp = min([max(0, int(entry["player_after"].get("hp", 0))) for entry in decision_log] + [max(0, int(player_final.get("hp", 0)))])
    pressure_count = int(summary.get("pressure_count", 0))
    turning_point = determine_turning_point(decision_log, failure_analysis)

    # Rarity and Affix aggregation
    rarity_counts = {}
    total_atk_affix = 0
    total_def_affix = 0
    for d in equipment_details:
        r = d.get("rarity", "common")
        rarity_counts[r] = rarity_counts.get(r, 0) + 1
        affixes = d.get("affixes", {})
        total_atk_affix += affixes.get("atk", 0)
        total_def_affix += affixes.get("def", 0)

    headline = (
        f"{run_id}: {'victory' if victory else 'loss'} via "
        f"{end_reason or 'in_progress'} after {len(decision_log)} steps"
    )
    return {
        "headline": headline,
        "route_family": route_family,
        "outcome": "victory" if victory else (end_reason or ("ended" if ended else "in_progress")),
        "key_turning_point": turning_point,
        "notable_equipment": list(set(equipment_ids)),
        "telemetry": {
            "total_steps": len(decision_log),
            "pressure_count": pressure_count,
            "combat_count": combat_count,
            "loot_drop_count": len(combat_loot),
            "loot_total_amount": sum(loot_totals.values()),
            "equipment_change_count": len(equipment_details),
            "rarity_distribution": rarity_counts,
            "total_atk_affix_gain": total_atk_affix,
            "total_def_affix_gain": total_def_affix,
            "equipment_ids": list(set(equipment_ids)),
            "loot_resources": loot_totals,
            "max_radiation": max_radiation,
            "min_food": min_food,
            "min_hp": min_hp,
            "low_resource_flags": low_resource_flags,
            "risk_tags": risk_tags,
            "character": {
                "background_id": player_final.get("character", {}).get("background_id"),
                "traits": player_final.get("character", {}).get("traits", []),
                "special": player_final.get("character", {}).get("special", {})
            } if player_final.get("character") else None
        },
    }
