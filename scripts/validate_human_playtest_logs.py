#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAYTEST_DIR = ROOT / "playtests"
PLACEHOLDER = "TBD"


class ValidationError(Exception):
    pass


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_placeholder_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == PLACEHOLDER


def is_completed_log(data: dict[str, Any]) -> bool:
    if is_placeholder_string(data.get("run_id")):
        return False
    events = data.get("events", [])
    if not events:
        return False
    return all(not is_placeholder_string(entry.get("node_id")) for entry in events)


def validate_log(path: Path) -> None:
    data = load_json(path)
    for key in ("player_id", "session_id", "roguelite_experience", "game_dev_background", "run_id", "events", "post_run"):
        ensure(key in data, f"{path}: missing {key}")

    ensure(isinstance(data["player_id"], str) and data["player_id"], f"{path}: player_id invalid")
    ensure(isinstance(data["session_id"], str) and data["session_id"], f"{path}: session_id invalid")
    ensure(isinstance(data["roguelite_experience"], bool), f"{path}: roguelite_experience invalid")
    ensure(isinstance(data["game_dev_background"], bool), f"{path}: game_dev_background invalid")
    ensure(isinstance(data["run_id"], str) and data["run_id"], f"{path}: run_id invalid")

    events = data["events"]
    ensure(isinstance(events, list) and len(events) >= 1, f"{path}: events must contain at least one entry")
    for entry in events:
        for key in (
            "timestamp",
            "node_id",
            "decision_time_ms",
            "selected_option",
            "hesitation_flag",
            "confusion_flag",
            "what_i_thought_happened",
            "why_im_salty",
        ):
            ensure(key in entry, f"{path}: event missing {key}")
        ensure(isinstance(entry["timestamp"], str) and entry["timestamp"], f"{path}: timestamp invalid")
        ensure(isinstance(entry["node_id"], str) and entry["node_id"], f"{path}: node_id invalid")
        ensure(isinstance(entry["decision_time_ms"], int) and entry["decision_time_ms"] >= 0, f"{path}: decision_time_ms invalid")
        ensure(isinstance(entry["selected_option"], int) and entry["selected_option"] >= 0, f"{path}: selected_option invalid")
        ensure(isinstance(entry["hesitation_flag"], bool), f"{path}: hesitation_flag invalid")
        ensure(isinstance(entry["confusion_flag"], bool), f"{path}: confusion_flag invalid")
        ensure(isinstance(entry["what_i_thought_happened"], str), f"{path}: what_i_thought_happened invalid")
        ensure(isinstance(entry["why_im_salty"], str), f"{path}: why_im_salty invalid")
        ensure(isinstance(entry.get("verbal_note", ""), str), f"{path}: verbal_note invalid")

    post_run = data["post_run"]
    for key in (
        "hardest_choice",
        "perceived_death_cause",
        "regret_choice",
        "replay_intent",
        "judgment_regret_note",
        "frustration_regret_note",
        "immediate_replay_reason",
    ):
        ensure(key in post_run, f"{path}: post_run missing {key}")
    ensure(isinstance(post_run["hardest_choice"], str), f"{path}: hardest_choice invalid")
    ensure(isinstance(post_run["perceived_death_cause"], str), f"{path}: perceived_death_cause invalid")
    ensure(isinstance(post_run["regret_choice"], str), f"{path}: regret_choice invalid")
    ensure(isinstance(post_run["replay_intent"], bool), f"{path}: replay_intent invalid")
    ensure(isinstance(post_run["judgment_regret_note"], str), f"{path}: judgment_regret_note invalid")
    ensure(isinstance(post_run["frustration_regret_note"], str), f"{path}: frustration_regret_note invalid")
    ensure(isinstance(post_run["immediate_replay_reason"], str), f"{path}: immediate_replay_reason invalid")


def main() -> int:
    try:
        log_files = sorted(PLAYTEST_DIR.glob("*_session_log.json"))
        sample = PLAYTEST_DIR / "sample_session_log.json"
        if sample.exists():
            log_files = [sample] + log_files
        ensure(log_files, "No human playtest logs found")
        completed_logs = 0
        placeholder_logs = 0
        for log_file in log_files:
            validate_log(log_file)
            payload = load_json(log_file)
            if is_completed_log(payload):
                completed_logs += 1
            else:
                placeholder_logs += 1
        print(
            "Human playtest log validation passed "
            f"({len(log_files)} files, completed={completed_logs}, placeholders={placeholder_logs})"
        )
        return 0
    except ValidationError as exc:
        print(f"Human playtest log validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
