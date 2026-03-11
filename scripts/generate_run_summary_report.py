#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = ROOT / "output" / "analytics"
OUTPUT_DIR = ROOT / "output" / "summaries"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bullets(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def kv_bullets(items: dict[str, int]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {key}: {value}" for key, value in sorted(items.items()))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_run_summary_report.py <run_json_or_run_id>")
        return 1

    target = sys.argv[1]
    path = Path(target)
    if not path.is_absolute():
        candidate = ANALYTICS_DIR / target
        if candidate.exists():
            path = candidate
        else:
            recursive_matches = list(ANALYTICS_DIR.rglob(target))
            if recursive_matches:
                path = recursive_matches[0]
            else:
                recursive_json_matches = list(ANALYTICS_DIR.rglob(f"{target}.json"))
                path = recursive_json_matches[0] if recursive_json_matches else (ANALYTICS_DIR / f"{target}.json")
    if not path.exists():
        print(f"Run analytics file not found: {path}")
        return 1

    data = load_json(path)
    run_summary = data["run_summary"]
    telemetry = run_summary["telemetry"]
    failure = data["failure_analysis"]
    out_path = OUTPUT_DIR / f"{data['run_id']}_summary.md"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = f"""# Run Summary

## Headline

- {run_summary['headline']}

## Route

- run_id: {data['run_id']}
- route_family: {run_summary['route_family']}
- path: {', '.join(data['route'])}

## Outcome

- outcome: {run_summary['outcome']}
- end_reason: {data['end_reason']}
- key_turning_point: {run_summary['key_turning_point']}

## Telemetry

- total_steps: {telemetry['total_steps']}
- pressure_count: {telemetry['pressure_count']}
- combat_count: {telemetry['combat_count']}
- loot_drop_count: {telemetry['loot_drop_count']}
- loot_total_amount: {telemetry['loot_total_amount']}
- equipment_change_count: {telemetry['equipment_change_count']}
- max_radiation: {telemetry['max_radiation']}
- min_food: {telemetry['min_food']}
- min_hp: {telemetry['min_hp']}

## Equipment

{bullets(run_summary['notable_equipment'])}

## Low Resource Flags

{bullets(telemetry['low_resource_flags'])}

## Combat Loot

{kv_bullets(telemetry['loot_resources'])}

## Risk Tags

{bullets(telemetry['risk_tags'])}

## Failure Read

- primary_blame_factor: {failure['primary_blame_factor']}
- steps_from_regret_to_death: {failure['steps_from_regret_to_death']}
- is_trash_time_death: {failure['is_trash_time_death']}
"""
    out_path.write_text(report, encoding="utf-8")
    print(f"Run summary report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
