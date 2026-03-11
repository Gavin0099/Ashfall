#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPARISON_PATH = ROOT / "output" / "playtests" / "comparison_summary.json"
OUTPUT_PATH = ROOT / "output" / "playtests" / "PT2_action_report.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def top_items(counts: dict[str, Any], limit: int = 5) -> list[tuple[str, int]]:
    ordered = sorted(
        ((str(key), int(value)) for key, value in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return ordered[:limit]


def bullets_from_counts(counts: dict[str, Any], limit: int = 5) -> str:
    if not counts:
        return "- none"
    return "\n".join(f"- {key}: {value}" for key, value in top_items(counts, limit=limit))


def recommended_actions(summary: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    log_count = int(summary.get("log_count", 0))
    hesitation_match_rate = float(summary.get("hesitation_match_rate", 0.0))
    regret_match_rate = float(summary.get("regret_match_rate", 0.0))
    equipment_arc_notice_rate = float(summary.get("equipment_arc_notice_rate", 0.0))
    hesitation_breakdown = summary.get("hesitation_alignment_breakdown", {})
    regret_breakdown = summary.get("regret_alignment_breakdown", {})

    if log_count < 5:
        actions.append("Complete the remaining PT-1 human sessions before making balance calls; current sample size is below the intended first-round threshold.")
    if int(regret_breakdown.get("victory_run_has_no_machine_regret_nodes", 0)) > 0:
        actions.append("Split victory-run regret from death-chain regret in PT-2 interpretation; this mismatch does not imply failure-analysis misattribution.")
    if int(hesitation_breakdown.get("machine_pressure_but_no_human_hesitation", 0)) > 0:
        actions.append("Increase route-pressure readability in the CLI; machine pressure exists but humans are not hesitating at the same nodes.")
    if int(hesitation_breakdown.get("human_hesitation_on_confusion_only", 0)) > 0:
        actions.append("Clarify warnings and option wording before changing balance; hesitation is being driven by confusion rather than tension.")
    if hesitation_match_rate >= 0.7 and regret_match_rate < 0.7 and not actions:
        actions.append("Pressure is reading, but regret attribution is not. Review regret distance and how failure chains are surfaced to players.")
    if equipment_arc_notice_rate < 0.5:
        actions.append("Make equipment acquisition/replacement more visible in the CLI; players are not noticing route-shaping gear strongly enough.")
    if not actions:
        actions.append("Current PT-2 read looks stable enough to proceed without immediate tooling or clarity changes.")
    return actions[:4]


def main() -> int:
    if not COMPARISON_PATH.exists():
        print("Missing comparison summary. Run compare_playtest_vs_machine.py first.")
        return 1

    summary = load_json(COMPARISON_PATH)
    comparisons = summary.get("comparisons", [])
    action_items = recommended_actions(summary)

    report = f"""# PT-2 Action Report

## Snapshot

- log_count: {summary.get("log_count", 0)}
- hesitation_match_rate: {summary.get("hesitation_match_rate", 0.0)}
- regret_match_rate: {summary.get("regret_match_rate", 0.0)}
- replay_intent_rate: {summary.get("replay_intent_rate", 0.0)}
- avg_decision_time_ms: {summary.get("avg_decision_time_ms", 0.0)}
- equipment_arc_notice_rate: {summary.get("equipment_arc_notice_rate", 0.0)}

## Hesitation Breakdown

{bullets_from_counts(summary.get("hesitation_alignment_breakdown", {}))}

## Regret Breakdown

{bullets_from_counts(summary.get("regret_alignment_breakdown", {}))}

## Machine Blame Breakdown

{bullets_from_counts(summary.get("machine_primary_blame_breakdown", {}))}

## Action Read

1. {action_items[0]}
2. {action_items[1] if len(action_items) > 1 else "Re-run this report after additional human sessions are completed."}
3. {action_items[2] if len(action_items) > 2 else "Keep comparison output under review as PT-1 sample size grows."}
4. {action_items[3] if len(action_items) > 3 else "Update tasks/TASKS.md once PT-2 evidence is strong enough to mark ready/done."}

## Session Notes

"""

    if not comparisons:
        report += "- none\n"
    else:
        for entry in comparisons:
            report += (
                f"- `{entry['player_id']}` / `{entry['run_id']}`: "
                f"hesitation={entry['hesitation_alignment_reason']}, "
                f"regret={entry['regret_alignment_reason']}, "
                f"equipment_arc_noticed={entry['equipment_arc_noticed']}\n"
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"PT-2 action report written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
