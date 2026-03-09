#!/usr/bin/env python3
"""Validate Phase A schema files and sample payloads without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "event": ROOT / "schemas" / "event_schema.json",
    "enemy": ROOT / "schemas" / "enemy_schema.json",
    "node": ROOT / "schemas" / "node_schema.json",
}
SAMPLES = {
    "event": ROOT / "schemas" / "samples" / "events",
    "enemy": ROOT / "schemas" / "samples" / "enemies",
    "node": ROOT / "schemas" / "samples" / "nodes",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def check_schema_skeleton(name: str, schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ValidationError(f"{name} schema: top-level type must be object")
    if "required" not in schema or not isinstance(schema["required"], list):
        raise ValidationError(f"{name} schema: missing required[]")
    if "properties" not in schema or not isinstance(schema["properties"], dict):
        raise ValidationError(f"{name} schema: missing properties{{}}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_event(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("id"), str) and data["id"], f"{src}: invalid id")
    ensure(isinstance(data.get("description"), str) and data["description"], f"{src}: invalid description")
    options = data.get("options")
    ensure(isinstance(options, list) and len(options) > 0, f"{src}: options must be non-empty array")

    for i, opt in enumerate(options):
        ensure(isinstance(opt, dict), f"{src}: options[{i}] must be object")
        ensure(isinstance(opt.get("text"), str) and opt["text"], f"{src}: options[{i}].text is required")
        if "effects" in opt:
            ensure(isinstance(opt["effects"], dict), f"{src}: options[{i}].effects must be object")
            for key, value in opt["effects"].items():
                ensure(key in {"food", "ammo", "medkits", "hp", "scrap"}, f"{src}: effects key {key!r} not allowed")
                ensure(isinstance(value, int), f"{src}: effects[{key}] must be integer")
        if "combat_chance" in opt:
            chance = opt["combat_chance"]
            ensure(isinstance(chance, (int, float)), f"{src}: combat_chance must be number")
            ensure(0 <= float(chance) <= 1, f"{src}: combat_chance must be between 0 and 1")


def validate_enemy(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("id"), str) and data["id"], f"{src}: invalid id")
    ensure(isinstance(data.get("name"), str) and data["name"], f"{src}: invalid name")
    ensure(isinstance(data.get("hp"), int) and data["hp"] >= 1, f"{src}: hp must be integer >= 1")

    dr = data.get("damage_range")
    ensure(isinstance(dr, dict), f"{src}: damage_range must be object")
    ensure(isinstance(dr.get("min"), int) and isinstance(dr.get("max"), int), f"{src}: damage_range min/max must be integers")
    ensure(dr["min"] >= 0 and dr["max"] >= 0, f"{src}: damage_range min/max must be >= 0")
    ensure(dr["min"] <= dr["max"], f"{src}: damage_range min must be <= max")

    if "loot_table" in data:
        lt = data["loot_table"]
        ensure(isinstance(lt, list), f"{src}: loot_table must be array")
        for i, item in enumerate(lt):
            ensure(isinstance(item, dict), f"{src}: loot_table[{i}] must be object")
            ensure(item.get("resource") in {"food", "ammo", "medkits", "scrap"}, f"{src}: loot resource invalid")
            ensure(isinstance(item.get("amount"), int) and item["amount"] >= 1, f"{src}: loot amount invalid")
            if "chance" in item:
                chance = item["chance"]
                ensure(isinstance(chance, (int, float)), f"{src}: loot chance must be number")
                ensure(0 <= float(chance) <= 1, f"{src}: loot chance must be between 0 and 1")


def validate_node(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("id"), str) and data["id"], f"{src}: invalid id")
    ensure(data.get("node_type") in {"resource", "combat", "trade", "story"}, f"{src}: node_type invalid")

    conns = data.get("connections")
    ensure(isinstance(conns, list), f"{src}: connections must be array")
    ensure(len(conns) == len(set(conns)), f"{src}: connections must be unique")
    for i, conn in enumerate(conns):
        ensure(isinstance(conn, str) and conn, f"{src}: connections[{i}] invalid")

    event_pool = data.get("event_pool")
    ensure(isinstance(event_pool, list) and len(event_pool) >= 1, f"{src}: event_pool must be non-empty array")
    ensure(len(event_pool) == len(set(event_pool)), f"{src}: event_pool must be unique")
    for i, ev in enumerate(event_pool):
        ensure(isinstance(ev, str) and ev, f"{src}: event_pool[{i}] invalid")

    for flag in ("is_start", "is_final"):
        if flag in data:
            ensure(isinstance(data[flag], bool), f"{src}: {flag} must be boolean")


def main() -> int:
    validators = {
        "event": validate_event,
        "enemy": validate_enemy,
        "node": validate_node,
    }

    try:
        for name, schema_path in SCHEMAS.items():
            schema = load_json(schema_path)
            if not isinstance(schema, dict):
                raise ValidationError(f"{name} schema: top-level must be object")
            check_schema_skeleton(name, schema)

        for name, sample_dir in SAMPLES.items():
            files = sorted(sample_dir.glob("*.json"))
            ensure(len(files) >= 2, f"{name} samples: at least 2 json files required")
            for file_path in files:
                payload = load_json(file_path)
                ensure(isinstance(payload, dict), f"{file_path}: sample root must be object")
                validators[name](payload, file_path)

        print("Phase A validation passed")
        return 0
    except ValidationError as e:
        print(f"Phase A validation failed: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
