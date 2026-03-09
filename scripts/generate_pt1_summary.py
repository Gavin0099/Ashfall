#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAYTEST_DIR = ROOT / "playtests"
COMPARISON_PATH = ROOT / "output" / "playtests" / "comparison_summary.json"
OUTPUT_PATH = ROOT / "output" / "playtests" / "PT1_summary.md"
PLACEHOLDER = "TBD"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def is_placeholder_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == PLACEHOLDER


def is_completed_log(data: dict[str, Any]) -> bool:
    if is_placeholder_string(data.get("run_id")):
        return False
    events = data.get("events", [])
    if not events:
        return False
    return all(not is_placeholder_string(entry.get("node_id")) for entry in events)


def collect_completed_logs() -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for path in sorted(PLAYTEST_DIR.glob("*_session_log.json")):
        if path.name == "sample_session_log.json":
            continue
        payload = load_json(path)
        if is_completed_log(payload):
            logs.append(payload)
    if logs:
        return logs
    sample = PLAYTEST_DIR / "sample_session_log.json"
    if sample.exists():
        payload = load_json(sample)
        if is_completed_log(payload):
            return [payload]
    return logs


def first_n_bullets(items: list[str], limit: int = 3) -> str:
    values = [item for item in items if item and not is_placeholder_string(item)]
    if not values:
        return "- TBD"
    return "\n".join(f"- {item}" for item in values[:limit])


def main() -> int:
    if not COMPARISON_PATH.exists():
        print("Missing comparison summary. Run compare_playtest_vs_machine.py first.")
        return 1

    logs = collect_completed_logs()
    if not logs:
        print("No completed PT-1 session logs found.")
        return 1

    comparison = load_json(COMPARISON_PATH)
    players_with_roguelite = sum(1 for log in logs if log.get("roguelite_experience") is True)
    players_without_game_dev = sum(1 for log in logs if log.get("game_dev_background") is False)
    confusion_sessions = sum(
        1 for log in logs if any(bool(event.get("confusion_flag")) for event in log.get("events", []))
    )
    avg_hesitation_nodes = average(
        [sum(1 for event in log["events"] if bool(event.get("hesitation_flag"))) for log in logs]
    )
    judgment_notes = [str(log["post_run"].get("judgment_regret_note", "")).strip() for log in logs]
    frustration_notes = [str(log["post_run"].get("frustration_regret_note", "")).strip() for log in logs]
    replay_reasons = [str(log["post_run"].get("immediate_replay_reason", "")).strip() for log in logs]
    perceived_death_causes = [str(log["post_run"].get("perceived_death_cause", "")).strip() for log in logs]
    run_ids = sorted(str(log.get("run_id", "")).strip() for log in logs if str(log.get("run_id", "")).strip())

    output = f"""# PT-1 Summary

Date: TBD
Operator: TBD
Sessions completed: {len(logs)}

## Sample

- Player count: {len(logs)}
- Seeds used / run ids: {", ".join(run_ids)}
- Players with roguelite experience: {players_with_roguelite}
- Players without game-dev background: {players_without_game_dev}

## Quantitative Readout

From `output/playtests/comparison_summary.json`:

- hesitation match rate: {comparison["hesitation_match_rate"]}
- regret match rate: {comparison["regret_match_rate"]}
- replay intent rate: {comparison["replay_intent_rate"]}
- avg decision time ms: {comparison["avg_decision_time_ms"]}
- avg hesitation nodes per player: {avg_hesitation_nodes}
- sessions with confusion flagged: {confusion_sessions}

## Qualitative Readout

### Judgment Regret

- Common "my mistake" pattern:
{first_n_bullets(judgment_notes)}

### Frustration Regret

- Common "this felt unfair" pattern:
{first_n_bullets(frustration_notes)}

### Replay Signal

- Why players wanted another run:
{first_n_bullets(replay_reasons)}

## Machine vs Human Alignment

- See `output/playtests/comparison_summary.json`
- Manual callout: review sessions where `hesitation_match` or `regret_match` is false.

## Radiation Read

- Perceived death causes:
{first_n_bullets(perceived_death_causes, limit=5)}

## Decision

Choose one:

- Keep current route-pressure shape for next round
- Adjust south-route pressure
- Reduce radiation dominance
- Improve warning clarity before any balance change

## Next Action

1. TBD
2. TBD
3. TBD
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"PT-1 summary written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
