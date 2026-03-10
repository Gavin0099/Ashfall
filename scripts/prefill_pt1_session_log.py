#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAYTEST_DIR = ROOT / "playtests"
CLI_OUTPUT_DIR = ROOT / "output" / "cli"
ANALYTICS_DIR = ROOT / "output" / "analytics"
PLACEHOLDER = "TBD"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def is_placeholder_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == PLACEHOLDER


def find_best_run_id(cli_payload: dict[str, Any]) -> str:
    cli_signature = [(entry["node"], int(entry["option_index"])) for entry in cli_payload.get("decision_log", [])]
    best_run_id: str | None = None
    best_score: tuple[int, int] | None = None

    for path in sorted(ANALYTICS_DIR.glob("run_*.json")):
        payload = load_json(path)
        machine_signature = [(entry["node"], int(entry["option_index"])) for entry in payload.get("decision_log", [])]
        matches = sum(1 for left, right in zip(cli_signature, machine_signature) if left == right)
        length_gap = abs(len(cli_signature) - len(machine_signature))
        score = (matches, -length_gap)
        if best_score is None or score > best_score:
            best_score = score
            best_run_id = str(payload["run_id"])

    if best_run_id is None:
        raise FileNotFoundError("No machine analytics runs found for run_id matching")
    return best_run_id


def build_event_entries(cli_payload: dict[str, Any], existing_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_by_node = {str(entry.get("node_id", "")): entry for entry in existing_events if isinstance(entry, dict)}
    entries: list[dict[str, Any]] = []
    for index, decision in enumerate(cli_payload.get("decision_log", []), start=1):
        node_id = str(decision["node"])
        existing = existing_by_node.get(node_id, {})
        entries.append(
            {
                "timestamp": (
                    str(existing.get("timestamp"))
                    if existing.get("timestamp") and not is_placeholder_string(existing.get("timestamp"))
                    else f"AUTO_STEP_{index}"
                ),
                "node_id": node_id,
                "decision_time_ms": int(existing.get("decision_time_ms", 0) or 0),
                "selected_option": int(decision["option_index"]),
                "hesitation_flag": bool(existing.get("hesitation_flag", False)),
                "confusion_flag": bool(existing.get("confusion_flag", False)),
                "what_i_thought_happened": str(existing.get("what_i_thought_happened", "")),
                "why_im_salty": str(existing.get("why_im_salty", "")),
                "verbal_note": str(existing.get("verbal_note", "")),
            }
        )
    return entries


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/prefill_pt1_session_log.py <session_log.json> <seed>")
        return 1

    session_path = Path(sys.argv[1])
    if not session_path.is_absolute():
        session_path = ROOT / session_path
    seed = int(sys.argv[2])

    cli_path = CLI_OUTPUT_DIR / f"latest_seed_{seed}.json"
    if not cli_path.exists():
        print(f"Missing CLI output: {cli_path}")
        return 1
    if not session_path.exists():
        print(f"Missing session log: {session_path}")
        return 1

    session = load_json(session_path)
    cli_payload = load_json(cli_path)

    session["run_id"] = find_best_run_id(cli_payload)
    session["events"] = build_event_entries(cli_payload, session.get("events", []))

    post_run = dict(session.get("post_run", {}))
    session["post_run"] = {
        "hardest_choice": str(post_run.get("hardest_choice", PLACEHOLDER)),
        "perceived_death_cause": str(post_run.get("perceived_death_cause", PLACEHOLDER)),
        "regret_choice": str(post_run.get("regret_choice", PLACEHOLDER)),
        "replay_intent": bool(post_run.get("replay_intent", False)),
        "judgment_regret_note": str(post_run.get("judgment_regret_note", PLACEHOLDER)),
        "frustration_regret_note": str(post_run.get("frustration_regret_note", PLACEHOLDER)),
        "immediate_replay_reason": str(post_run.get("immediate_replay_reason", PLACEHOLDER)),
    }

    write_json(session_path, session)
    print(f"Prefilled PT-1 session log from {cli_path.name} -> {session_path}")
    print(f"Inferred run_id: {session['run_id']}")
    print("Objective fields filled: run_id, events[].node_id, events[].selected_option")
    print("Still fill manually: decision_time_ms, hesitation/confusion, post_run interview fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
