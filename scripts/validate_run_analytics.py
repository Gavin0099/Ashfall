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
    required = {"hp", "food", "ammo", "medkits", "scrap"}
    ensure(required.issubset(data.keys()), f"{src}: player_final missing keys")
    for key in required:
        ensure(isinstance(data[key], int), f"{src}: player_final.{key} must be integer")


def validate_decision_log(entries: list[dict[str, Any]], src: Path) -> None:
    ensure(isinstance(entries, list), f"{src}: decision_log must be array")
    ensure(len(entries) >= 1, f"{src}: decision_log must not be empty")
    for index, entry in enumerate(entries, start=1):
        ensure(entry.get("step") == index, f"{src}: decision_log step sequence invalid at {index}")
        ensure(isinstance(entry.get("node"), str) and entry["node"], f"{src}: node missing")
        ensure(isinstance(entry.get("event_id"), str) and entry["event_id"], f"{src}: event_id missing")
        ensure(isinstance(entry.get("option_index"), int) and entry["option_index"] >= 0, f"{src}: option_index invalid")
        ensure(isinstance(entry.get("pressure"), bool), f"{src}: pressure must be boolean")
        ensure(isinstance(entry.get("combat_triggered"), bool), f"{src}: combat_triggered must be boolean")
        player_after = entry.get("player_after")
        ensure(isinstance(player_after, dict), f"{src}: player_after missing")
        for key in ("hp", "food", "ammo", "medkits"):
            ensure(isinstance(player_after.get(key), int), f"{src}: player_after.{key} must be integer")


def validate_summary(data: dict[str, Any], src: Path) -> None:
    ensure(isinstance(data.get("pressure_count"), int) and data["pressure_count"] >= 0, f"{src}: pressure_count invalid")
    ensure(isinstance(data.get("death_cause_attribution"), bool), f"{src}: death_cause_attribution invalid")
    ensure(isinstance(data.get("resource_signature"), str) and data["resource_signature"], f"{src}: resource_signature invalid")


def validate_run_file(path: Path) -> None:
    data = load_json(path)
    for key in ("run_id", "seed", "route", "ended", "victory", "end_reason", "player_final", "decision_log", "summary"):
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
