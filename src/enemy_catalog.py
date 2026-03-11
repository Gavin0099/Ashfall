from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
ENEMY_CATALOG_PATH = ROOT / "schemas" / "enemy_catalog.json"


def load_enemy_catalog() -> Dict[str, Dict[str, Any]]:
    data = json.loads(ENEMY_CATALOG_PATH.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("enemy_catalog.json must be a JSON object")
    catalog: Dict[str, Dict[str, Any]] = {}
    for enemy_id, payload in data.items():
        if not isinstance(enemy_id, str) or not isinstance(payload, dict):
            raise ValueError("enemy catalog entry invalid")
        catalog[enemy_id] = payload
    return catalog
