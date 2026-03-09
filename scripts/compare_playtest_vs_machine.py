#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAYTEST_DIR = ROOT / "playtests"
ANALYTICS_DIR = ROOT / "output" / "analytics"
OUTPUT_PATH = ROOT / "output" / "playtests" / "comparison_summary.json"
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


def find_machine_run(run_id: str) -> dict[str, Any]:
    for path in ANALYTICS_DIR.glob("run_*.json"):
        payload = load_json(path)
        if payload["run_id"] == run_id:
            return payload
    raise FileNotFoundError(f"Machine analytics run not found for run_id={run_id}")


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    logs: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(PLAYTEST_DIR.glob("*_session_log.json")):
        if path.name == "sample_session_log.json":
            continue
        payload = load_json(path)
        if is_completed_log(payload):
            logs.append((path, payload))
    if not logs:
        logs = [PLAYTEST_DIR / "sample_session_log.json"] if (PLAYTEST_DIR / "sample_session_log.json").exists() else []
        logs = [(logs[0], load_json(logs[0]))] if logs else []
    if not logs:
        print("No human playtest logs found")
        return 1

    comparisons: list[dict[str, Any]] = []
    hesitation_match_count = 0
    regret_match_count = 0
    replay_true_count = 0

    for log_path, human in logs:
        machine = find_machine_run(human["run_id"])

        human_hesitation_nodes = {entry["node_id"] for entry in human["events"] if entry["hesitation_flag"]}
        machine_pressure_nodes = {entry["node"] for entry in machine["decision_log"] if entry["pressure"]}
        hesitation_overlap = sorted(human_hesitation_nodes & machine_pressure_nodes)
        hesitation_match = len(hesitation_overlap) > 0
        if hesitation_match:
            hesitation_match_count += 1

        machine_regret_nodes = {entry["node_id"] for entry in machine["failure_analysis"]["regret_nodes"]}
        regret_choice = human["post_run"]["regret_choice"]
        regret_match = regret_choice in machine_regret_nodes
        if regret_match:
            regret_match_count += 1

        replay_intent = bool(human["post_run"]["replay_intent"])
        if replay_intent:
            replay_true_count += 1

        comparisons.append(
            {
                "player_id": human["player_id"],
                "session_id": human["session_id"],
                "run_id": human["run_id"],
                "human_hesitation_nodes": sorted(human_hesitation_nodes),
                "machine_pressure_nodes": sorted(machine_pressure_nodes),
                "hesitation_overlap": hesitation_overlap,
                "hesitation_match": hesitation_match,
                "human_regret_choice": regret_choice,
                "machine_regret_nodes": sorted(machine_regret_nodes),
                "regret_match": regret_match,
                "machine_primary_blame_factor": machine["failure_analysis"]["primary_blame_factor"],
                "machine_steps_from_regret_to_death": machine["failure_analysis"]["steps_from_regret_to_death"],
                "replay_intent": replay_intent,
                "avg_decision_time_ms": average([float(event["decision_time_ms"]) for event in human["events"]]),
            }
        )

    summary = {
        "log_count": len(comparisons),
        "hesitation_match_rate": round(hesitation_match_count / len(comparisons), 2),
        "regret_match_rate": round(regret_match_count / len(comparisons), 2),
        "replay_intent_rate": round(replay_true_count / len(comparisons), 2),
        "avg_decision_time_ms": average([entry["avg_decision_time_ms"] for entry in comparisons]),
        "comparisons": comparisons,
    }
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Playtest vs machine comparison completed")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
