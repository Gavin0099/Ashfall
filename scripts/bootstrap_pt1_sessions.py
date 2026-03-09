#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYTEST_DIR = ROOT / "playtests"
TEMPLATE_PATH = PLAYTEST_DIR / "PT1_session_template.json"

ASSIGNMENTS = [
    ("P1", "PT1-001"),
    ("P2", "PT1-002"),
    ("P3", "PT1-003"),
    ("P4", "PT1-004"),
    ("P5", "PT1-005"),
]


def main() -> int:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8-sig"))
    created = []
    for player_id, session_id in ASSIGNMENTS:
        payload = json.loads(json.dumps(template))
        payload["player_id"] = player_id
        payload["session_id"] = session_id
        output_path = PLAYTEST_DIR / f"{player_id}_session_log.json"
        if output_path.exists():
            continue
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        created.append(output_path.name)

    if created:
        print("Created PT-1 session logs:")
        for name in created:
            print(f"- {name}")
    else:
        print("No files created; PT-1 session logs already exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
