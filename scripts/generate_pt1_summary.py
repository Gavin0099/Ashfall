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


def top_breakdown_bullets(counts: dict[str, Any], limit: int = 3) -> str:
    if not counts:
        return "- none"
    ordered = sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))
    return "\n".join(f"- {key}: {value}" for key, value in ordered[:limit])


def pass_fail(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def derive_verdict(hesitation_match_rate: float, regret_match_rate: float, replay_intent_rate: float,
                   avg_hesitation_nodes: float, avg_hesitation_time_ms: float) -> tuple[str, list[str]]:
    checks = {
        "hesitation_match": hesitation_match_rate >= 0.7,
        "regret_match": regret_match_rate >= 0.7,
        "replay_intent": replay_intent_rate >= 0.5,
        "hesitation_density": avg_hesitation_nodes >= 3.0,
        "hesitation_time": avg_hesitation_time_ms >= 5000.0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if not failed:
        return "PASS", failed
    if len(failed) <= 2 and checks["hesitation_match"] and checks["regret_match"]:
        return "MIXED", failed
    return "FAIL", failed


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
    avg_hesitation_time_ms = average(
        [
            float(event["decision_time_ms"])
            for log in logs
            for event in log["events"]
            if bool(event.get("hesitation_flag"))
        ]
    )
    avg_hesitation_nodes = average(
        [sum(1 for event in log["events"] if bool(event.get("hesitation_flag"))) for log in logs]
    )
    judgment_notes = [str(log["post_run"].get("judgment_regret_note", "")).strip() for log in logs]
    frustration_notes = [str(log["post_run"].get("frustration_regret_note", "")).strip() for log in logs]
    replay_reasons = [str(log["post_run"].get("immediate_replay_reason", "")).strip() for log in logs]
    perceived_death_causes = [str(log["post_run"].get("perceived_death_cause", "")).strip() for log in logs]
    run_ids = sorted(str(log.get("run_id", "")).strip() for log in logs if str(log.get("run_id", "")).strip())
    hesitation_breakdown = comparison.get("hesitation_alignment_breakdown", {})
    regret_breakdown = comparison.get("regret_alignment_breakdown", {})
    blame_breakdown = comparison.get("machine_primary_blame_breakdown", {})
    equipment_arc_notice_rate = float(comparison.get("equipment_arc_notice_rate", 0.0))
    verdict, failed_checks = derive_verdict(
        hesitation_match_rate=float(comparison["hesitation_match_rate"]),
        regret_match_rate=float(comparison["regret_match_rate"]),
        replay_intent_rate=float(comparison["replay_intent_rate"]),
        avg_hesitation_nodes=avg_hesitation_nodes,
        avg_hesitation_time_ms=avg_hesitation_time_ms,
    )

    next_actions: list[str] = []
    if "hesitation_density" in failed_checks or "hesitation_time" in failed_checks:
        next_actions.append("Increase visible route pressure earlier; current hesitation density is below PT-1 target.")
    if "regret_match" in failed_checks:
        if regret_breakdown.get("victory_run_has_no_machine_regret_nodes"):
            next_actions.append("Separate victory-run regret from death-chain regret in PT-2 readouts; the current mismatch is coming from a win with no machine regret nodes.")
        else:
            next_actions.append("Review warning clarity and regret distance; human regret is not aligning with machine blame.")
    if "replay_intent" in failed_checks:
        next_actions.append("Strengthen route identity and replay promise before adding content breadth.")
    if not next_actions:
        next_actions.append("Keep current route-pressure shape and proceed to PT-2 comparison work.")
    if confusion_sessions > 0:
        next_actions.append("Review confusion-flagged sessions before making balance changes.")

    output = f"""# PT-1 Summary

Date: TBD
Operator: TBD
Sessions completed: {len(logs)}

## Verdict

- PT-1 verdict: {verdict}
- gate hesitation match (>= 0.7): {comparison["hesitation_match_rate"]} [{pass_fail(float(comparison["hesitation_match_rate"]) >= 0.7)}]
- gate regret match (>= 0.7): {comparison["regret_match_rate"]} [{pass_fail(float(comparison["regret_match_rate"]) >= 0.7)}]
- gate replay intent (>= 0.5): {comparison["replay_intent_rate"]} [{pass_fail(float(comparison["replay_intent_rate"]) >= 0.5)}]
- gate hesitation nodes/player (>= 3): {avg_hesitation_nodes} [{pass_fail(avg_hesitation_nodes >= 3.0)}]
- gate hesitation time ms (>= 5000): {avg_hesitation_time_ms} [{pass_fail(avg_hesitation_time_ms >= 5000.0)}]

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
- avg hesitation time ms: {avg_hesitation_time_ms}
- equipment arc notice rate: {equipment_arc_notice_rate}
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
- hesitation breakdown:
{top_breakdown_bullets(hesitation_breakdown)}
- regret breakdown:
{top_breakdown_bullets(regret_breakdown)}
- machine blame breakdown:
{top_breakdown_bullets(blame_breakdown)}

## PT-2 Read

- If `victory_run_has_no_machine_regret_nodes` dominates, treat regret mismatch separately from death attribution failure.
- If `machine_pressure_but_no_human_hesitation` appears, route pressure is not reading strongly enough in the CLI.
- If `human_hesitation_on_confusion_only` appears, the issue is clarity, not tension.

## Radiation Read

- Perceived death causes:
{first_n_bullets(perceived_death_causes, limit=5)}

## Decision

- Recommended call: {"proceed to PT-2" if verdict == "PASS" else "run another PT-1 iteration"}

## Next Action

1. {next_actions[0]}
2. {next_actions[1] if len(next_actions) > 1 else "Validate logs again after the next completed PT-1 session batch."}
3. {next_actions[2] if len(next_actions) > 2 else "Update tasks/TASKS.md with the PT-1 verdict once operator fields are filled."}
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"PT-1 summary written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
