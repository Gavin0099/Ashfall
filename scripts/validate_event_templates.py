#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.event_templates import instantiate_event_catalog, load_template_catalog


class ValidationError(Exception):
    pass


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_event(event_id: str, payload: dict[str, Any]) -> None:
    ensure(isinstance(payload.get("id"), str) and payload["id"] == event_id, f"{event_id}: id mismatch")
    ensure(isinstance(payload.get("description"), str) and payload["description"], f"{event_id}: empty description")
    options = payload.get("options")
    ensure(isinstance(options, list) and len(options) >= 2, f"{event_id}: options must have at least 2 entries")
    tradeoff_found = False
    for index, option in enumerate(options):
        ensure(isinstance(option.get("text"), str) and option["text"], f"{event_id}: option {index} missing text")
        effects = option.get("effects", {})
        ensure(isinstance(effects, dict), f"{event_id}: option {index} effects must be object")
        chance = option.get("combat_chance", 0.0)
        ensure(isinstance(chance, (int, float)) and 0 <= float(chance) <= 1, f"{event_id}: option {index} combat_chance invalid")
        has_positive = any(value > 0 for value in effects.values())
        has_negative = any(value < 0 for value in effects.values())
        if has_positive or has_negative or float(chance) > 0:
            tradeoff_found = True
    ensure(tradeoff_found, f"{event_id}: no measurable tradeoff in options")


def main() -> int:
    try:
        catalog = load_template_catalog(ROOT / "schemas" / "event_template_catalog.json")
        events = instantiate_event_catalog(101, catalog)
        ensure(len(events) >= 5, "too few generated events")
        for event_id, payload in events.items():
            validate_event(event_id, payload)
        print("Event template validation passed")
        return 0
    except ValidationError as exc:
        print(f"Event template validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
