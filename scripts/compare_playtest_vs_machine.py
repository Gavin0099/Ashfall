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


def increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def is_placeholder_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == PLACEHOLDER


def is_completed_log(data: dict[str, Any]) -> bool:
    if is_placeholder_string(data.get("run_id")):
        return False
    events = data.get("events", [])
    if not events:
        return False
    post_run = data.get("post_run", {})
    required_post_run = (
        "hardest_choice",
        "perceived_death_cause",
        "regret_choice",
        "judgment_regret_note",
        "frustration_regret_note",
        "immediate_replay_reason",
    )
    return (
        all(not is_placeholder_string(entry.get("node_id")) for entry in events)
        and all(not is_placeholder_string(entry.get("timestamp")) for entry in events)
        and any(int(entry.get("decision_time_ms", 0) or 0) > 0 for entry in events)
        and all(not is_placeholder_string(post_run.get(key)) for key in required_post_run)
    )


def find_machine_run(human_data: dict[str, Any]) -> dict[str, Any]:
    seed = human_data.get("seed")
    diff = human_data.get("difficulty")
    
    # Try exact run_id first
    run_id = human_data.get("run_id")
    for path in ANALYTICS_DIR.glob("run_*.json"):
        payload = load_json(path)
        if payload.get("run_id") == run_id:
            return payload
            
    # Fallback to Seed/Difficulty match
    for path in ANALYTICS_DIR.glob("run_*.json"):
        payload = load_json(path)
        if payload.get("seed") == seed and payload.get("difficulty") == diff:
            return payload
            
    # Second Fallback: Any run with same seed
    for path in ANALYTICS_DIR.glob("run_*.json"):
        payload = load_json(path)
        if payload.get("seed") == seed:
            return payload

    raise FileNotFoundError(f"Machine analytics run not found for Seed={seed}, Diff={diff}")


def classify_hesitation_alignment(
    human_hesitation_nodes: set[str],
    machine_pressure_nodes: set[str],
    confusion_nodes: set[str],
) -> str:
    if not human_hesitation_nodes and not machine_pressure_nodes:
        return "no_hesitation_no_pressure"
    if human_hesitation_nodes & machine_pressure_nodes:
        return "aligned_pressure_hesitation"
    if not human_hesitation_nodes and machine_pressure_nodes:
        return "machine_pressure_but_no_human_hesitation"
    if human_hesitation_nodes and not machine_pressure_nodes:
        if human_hesitation_nodes & confusion_nodes:
            return "human_hesitation_on_confusion_only"
        return "human_hesitation_outside_machine_pressure"
    return "mixed_hesitation_mismatch"


def classify_regret_alignment(
    human_regret_choice: str,
    machine_regret_nodes: set[str],
    machine: dict[str, Any],
) -> str:
    if human_regret_choice in machine_regret_nodes:
        return "aligned_regret_node"
    if not human_regret_choice or is_placeholder_string(human_regret_choice):
        return "missing_human_regret_choice"
    if not machine_regret_nodes:
        if machine.get("victory"):
            return "victory_run_has_no_machine_regret_nodes"
        if machine["failure_analysis"].get("primary_blame_factor") is None:
            return "death_with_no_machine_blame"
        return "death_with_empty_machine_regret_nodes"
    return "human_regret_not_in_machine_regret_nodes"


def collect_equipment_nodes(machine: dict[str, Any]) -> list[str]:
    return [entry["node"] for entry in machine["decision_log"] if entry.get("equipment_change")]


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
    hesitation_reason_counts: dict[str, int] = {}
    regret_reason_counts: dict[str, int] = {}
    machine_blame_counts: dict[str, int] = {}
    equipment_arc_notice_count = 0

    for log_path, human in logs:
        machine = find_machine_run(human)

        human_hesitation_nodes = {entry["node_id"] for entry in human["events"] if entry["hesitation_flag"]}
        confusion_nodes = {entry["node_id"] for entry in human["events"] if entry["confusion_flag"]}
        machine_pressure_nodes = {entry["node"] for entry in machine["decision_log"] if entry["pressure"]}
        hesitation_overlap = sorted(human_hesitation_nodes & machine_pressure_nodes)
        hesitation_match = len(hesitation_overlap) > 0
        if hesitation_match:
            hesitation_match_count += 1
        hesitation_alignment_reason = classify_hesitation_alignment(
            human_hesitation_nodes=human_hesitation_nodes,
            machine_pressure_nodes=machine_pressure_nodes,
            confusion_nodes=confusion_nodes,
        )
        increment(hesitation_reason_counts, hesitation_alignment_reason)

        machine_regret_nodes = {entry["node_id"] for entry in machine["failure_analysis"]["regret_nodes"]}
        regret_choice = human["post_run"]["regret_choice"]
        regret_match = regret_choice in machine_regret_nodes
        if regret_match:
            regret_match_count += 1
        regret_alignment_reason = classify_regret_alignment(
            human_regret_choice=regret_choice,
            machine_regret_nodes=machine_regret_nodes,
            machine=machine,
        )
        increment(regret_reason_counts, regret_alignment_reason)

        replay_intent = bool(human["post_run"]["replay_intent"])
        if replay_intent:
            replay_true_count += 1

        primary_blame = machine["failure_analysis"]["primary_blame_factor"] or "none"
        increment(machine_blame_counts, primary_blame)

        equipment_nodes = collect_equipment_nodes(machine)
        equipment_arc_noticed = any(
            entry["node_id"] in equipment_nodes and bool(str(entry.get("what_i_thought_happened", "")).strip())
            for entry in human["events"]
        )
        if equipment_arc_noticed:
            equipment_arc_notice_count += 1

        comparisons.append(
            {
                "source_log": log_path.name,
                "player_id": human["player_id"],
                "session_id": human["session_id"],
                "run_id": human["run_id"],
                "human_hesitation_nodes": sorted(human_hesitation_nodes),
                "human_confusion_nodes": sorted(confusion_nodes),
                "machine_pressure_nodes": sorted(machine_pressure_nodes),
                "hesitation_overlap": hesitation_overlap,
                "hesitation_match": hesitation_match,
                "hesitation_alignment_reason": hesitation_alignment_reason,
                "human_regret_choice": regret_choice,
                "machine_regret_nodes": sorted(machine_regret_nodes),
                "regret_match": regret_match,
                "regret_alignment_reason": regret_alignment_reason,
                "machine_primary_blame_factor": machine["failure_analysis"]["primary_blame_factor"],
                "machine_steps_from_regret_to_death": machine["failure_analysis"]["steps_from_regret_to_death"],
                "machine_is_victory": bool(machine.get("victory")),
                "machine_is_trash_time_death": bool(machine["failure_analysis"].get("is_trash_time_death")),
                "machine_pressure_count": int(machine["summary"]["pressure_count"]),
                "machine_equipment_nodes": equipment_nodes,
                "equipment_arc_noticed": equipment_arc_noticed,
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
        "equipment_arc_notice_rate": round(equipment_arc_notice_count / len(comparisons), 2),
        "hesitation_alignment_breakdown": hesitation_reason_counts,
        "regret_alignment_breakdown": regret_reason_counts,
        "machine_primary_blame_breakdown": machine_blame_counts,
        "comparisons": comparisons,
    }
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Playtest vs machine comparison completed")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
