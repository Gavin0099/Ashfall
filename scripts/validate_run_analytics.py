#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = ROOT / "output" / "analytics"


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_player_final(data: dict[str, Any], src: Path) -> None:
    required = {"hp", "food", "ammo", "medkits", "scrap", "radiation"}
    ensure(required.issubset(data.keys()), f"{src}: player_final missing keys")
    for key in required:
        ensure(isinstance(data[key], int), f"{src}: player_final.{key} must be integer")
    for key in ("weapon_slot", "armor_slot", "tool_slot"):
        ensure(isinstance(data.get(key), (str, type(None))), f"{src}: player_final.{key} must be string|null")


def validate_decision_log(entries: list[dict[str, Any]], src: Path) -> None:
    ensure(isinstance(entries, list), f"{src}: decision_log must be array")
    ensure(len(entries) >= 1, f"{src}: decision_log must not be empty")
    for index, entry in enumerate(entries, start=1):
        ensure(entry.get("step") == index, f"{src}: decision_log step sequence invalid at {index}")
        ensure(isinstance(entry.get("node"), str) and entry["node"], f"{src}: node missing")
        ensure(isinstance(entry.get("event_id"), str) and entry["event_id"], f"{src}: event_id missing")
        ensure(isinstance(entry.get("option_index"), int) and entry["option_index"] >= 0, f"{src}: option_index invalid")
        ensure(isinstance(entry.get("warning_signals"), list), f"{src}: warning_signals must be array")
        pre_choice_state = entry.get("pre_choice_state")
        ensure(isinstance(pre_choice_state, dict), f"{src}: pre_choice_state missing")
        for key in ("hp", "food", "ammo", "medkits", "radiation"):
            ensure(isinstance(pre_choice_state.get(key), int), f"{src}: pre_choice_state.{key} must be integer")
        for key in ("weapon_slot", "armor_slot", "tool_slot"):
            ensure(isinstance(pre_choice_state.get(key), (str, type(None))), f"{src}: pre_choice_state.{key} must be string|null")
        ensure(isinstance(entry.get("pressure"), bool), f"{src}: pressure must be boolean")
        ensure(isinstance(entry.get("combat_triggered"), bool), f"{src}: combat_triggered must be boolean")
        ensure(isinstance(entry.get("combat_loot", []), list), f"{src}: combat_loot must be array")
        ensure(isinstance(entry.get("effects", {}), dict), f"{src}: effects must be object")
        ensure(isinstance(entry.get("equipment_change"), (dict, type(None))), f"{src}: equipment_change must be object|null")
        ensure(isinstance(entry.get("equipment_summary"), (str, type(None))), f"{src}: equipment_summary must be string|null")
        player_after = entry.get("player_after")
        ensure(isinstance(player_after, dict), f"{src}: player_after missing")
        for key in ("hp", "food", "ammo", "medkits", "radiation"):
            ensure(isinstance(player_after.get(key), int), f"{src}: player_after.{key} must be integer")
        for key in ("weapon_slot", "armor_slot", "tool_slot"):
            ensure(isinstance(player_after.get(key), (str, type(None))), f"{src}: player_after.{key} must be string|null")


def validate_summary(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("pressure_count"), int) and data["pressure_count"] >= 0, f"{src}: pressure_count invalid")
    ensure(isinstance(data.get("death_cause_attribution"), bool), f"{src}: death_cause_attribution invalid")
    ensure(isinstance(data.get("resource_signature"), str) and data["resource_signature"], f"{src}: resource_signature invalid")


def validate_failure_analysis(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("death_chain_length"), int) and data["death_chain_length"] >= 0, f"{src}: death_chain_length invalid")
    ensure(isinstance(data.get("primary_blame_factor"), (str, type(None))), f"{src}: primary_blame_factor invalid")
    regret_nodes = data.get("regret_nodes")
    ensure(isinstance(regret_nodes, list), f"{src}: regret_nodes must be array")
    for entry in regret_nodes:
        ensure(isinstance(entry.get("node_id"), str) and entry["node_id"], f"{src}: regret node_id invalid")
        ensure(isinstance(entry.get("event_id"), str) and entry["event_id"], f"{src}: regret event_id invalid")
        ensure(isinstance(entry.get("blame_score"), (int, float)), f"{src}: regret blame_score invalid")
        ensure(0 <= float(entry["blame_score"]) <= 1, f"{src}: regret blame_score out of range")
        ensure(isinstance(entry.get("description"), str) and entry["description"], f"{src}: regret description invalid")
        ensure(isinstance(entry.get("steps_to_death"), int) and entry["steps_to_death"] >= 0, f"{src}: regret steps_to_death invalid")
    ensure(
        isinstance(data.get("steps_from_regret_to_death"), int) and data["steps_from_regret_to_death"] >= 0,
        f"{src}: steps_from_regret_to_death invalid",
    )
    ensure(isinstance(data.get("is_trash_time_death"), bool), f"{src}: is_trash_time_death invalid")


def validate_run_summary(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("headline"), str) and data["headline"], f"{src}: run_summary.headline invalid")
    ensure(isinstance(data.get("route_family"), str) and data["route_family"], f"{src}: run_summary.route_family invalid")
    ensure(isinstance(data.get("outcome"), str) and data["outcome"], f"{src}: run_summary.outcome invalid")
    ensure(isinstance(data.get("key_turning_point"), (str, type(None))), f"{src}: run_summary.key_turning_point invalid")
    ensure(isinstance(data.get("notable_equipment"), list), f"{src}: run_summary.notable_equipment invalid")
    telemetry = data.get("telemetry")
    ensure(isinstance(telemetry, dict), f"{src}: run_summary.telemetry invalid")
    for key in (
        "total_steps",
        "pressure_count",
        "combat_count",
        "loot_drop_count",
        "loot_total_amount",
        "equipment_change_count",
        "max_radiation",
        "min_food",
        "min_hp",
    ):
        ensure(isinstance(telemetry.get(key), int) and telemetry[key] >= 0, f"{src}: run_summary.telemetry.{key} invalid")
    for key in ("equipment_ids", "low_resource_flags", "risk_tags"):
        ensure(isinstance(telemetry.get(key), list), f"{src}: run_summary.telemetry.{key} invalid")
    loot_resources = telemetry.get("loot_resources")
    ensure(isinstance(loot_resources, dict), f"{src}: run_summary.telemetry.loot_resources invalid")
    for key, value in loot_resources.items():
        ensure(isinstance(key, str) and key, f"{src}: run_summary.telemetry.loot_resources key invalid")
        ensure(isinstance(value, int) and value >= 0, f"{src}: run_summary.telemetry.loot_resources.{key} invalid")


def validate_run_file(path: Path) -> None:
    data = load_json(path)
    for key in ("run_id", "seed", "route", "ended", "victory", "end_reason", "player_final", "decision_log", "summary", "failure_analysis", "run_summary"):
        ensure(key in data, f"{path}: missing {key}")
    ensure(isinstance(data["run_id"], str) and data["run_id"], f"{path}: run_id invalid")
    ensure(isinstance(data["seed"], int), f"{path}: seed invalid")
    ensure(isinstance(data["route"], list) and len(data["route"]) >= 1, f"{path}: route invalid")
    ensure(isinstance(data["ended"], bool), f"{path}: ended invalid")
    ensure(isinstance(data["victory"], bool), f"{path}: victory invalid")
    ensure(isinstance(data["end_reason"], (str, type(None))), f"{path}: end_reason invalid")
    validate_player_final(data["player_final"], path)
    validate_decision_log(data["decision_log"], path)
    validate_summary(data["summary"], path)
    validate_failure_analysis(data["failure_analysis"], path)
    validate_run_summary(data["run_summary"], path)


def main() -> int:
    try:
        run_files = sorted(ANALYTICS_DIR.rglob("run_*.json"))
        ensure(len(run_files) >= 1, "No analytics run files found")
        for run_file in run_files:
            validate_run_file(run_file)
        print(f"Run analytics validation passed ({len(run_files)} files)")
        return 0
    except ValidationError as exc:
        print(f"Run analytics validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
