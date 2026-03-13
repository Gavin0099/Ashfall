from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict


def load_template_catalog(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def instantiate_event_catalog(seed: int, catalog: Dict[str, Any]) -> Dict[str, dict]:
    events = catalog.get("events", [])
    result: Dict[str, dict] = {}
    for index, event in enumerate(events):
        event_seed = seed * 1009 + index * 37
        rng = random.Random(event_seed)
        result[event["event_id"]] = instantiate_event(event, rng)
    return result


def instantiate_event(template: Dict[str, Any], rng: random.Random) -> dict:
    description = _pick_variant(template.get("description_variants", []), rng)
    options = []
    for option in template.get("options", []):
        resolved_option = {
            "text": _pick_variant(option.get("text_variants", []), rng),
            "effects": dict(option.get("effects", {})),
            "combat_chance": float(option.get("combat_chance", 0.0)),
        }
        if "encounter_bias" in option:
            resolved_option["encounter_bias"] = dict(option["encounter_bias"])
        if "equipment_reward" in option:
            resolved_option["equipment_reward"] = dict(option["equipment_reward"])
        options.append(resolved_option)
    return {
        "id": template["event_id"],
        "description": description,
        "options": options,
    }


def _pick_variant(variants: list[str], rng: random.Random) -> str:
    if not variants:
        return ""
    return rng.choice(variants)
