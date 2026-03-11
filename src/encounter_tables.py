from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[1]
ENCOUNTER_TABLE_PATH = ROOT / "schemas" / "encounter_weight_table.json"


def load_encounter_weights() -> Dict[str, Dict[str, float]]:
    data = json.loads(ENCOUNTER_TABLE_PATH.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("encounter_weight_table.json must be a JSON object")
    weights = data.get("weights")
    if not isinstance(weights, dict):
        raise ValueError("encounter_weight_table.json missing weights object")
    normalized: Dict[str, Dict[str, float]] = {}
    for bucket, bucket_weights in weights.items():
        if not isinstance(bucket, str) or not isinstance(bucket_weights, dict):
            raise ValueError("encounter weight bucket invalid")
        normalized[bucket] = {}
        for archetype, weight in bucket_weights.items():
            if not isinstance(archetype, str) or not isinstance(weight, (int, float)):
                raise ValueError("encounter weight entry invalid")
            normalized[bucket][archetype] = float(weight)
    return normalized


ENCOUNTER_WEIGHTS = load_encounter_weights()


def encounter_bucket_for_node(node_id: str) -> str:
    if "north" in node_id:
        return "north"
    if "south" in node_id:
        return "south"
    if node_id == "node_mid":
        return "mid"
    return "default"
