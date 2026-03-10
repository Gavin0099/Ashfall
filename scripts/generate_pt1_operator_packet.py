#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED_ASSIGNMENT_PATH = ROOT / "PT1_SEED_ASSIGNMENT.md"
ANALYTICS_DIR = ROOT / "output" / "analytics"
OUTPUT_PATH = ROOT / "output" / "playtests" / "PT1_operator_packet.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_seed_assignments() -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for raw_line in SEED_ASSIGNMENT_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line.startswith("| P"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        player_id, seed, expected_run_id, notes = cells
        if not seed.isdigit():
            continue
        assignments.append(
            {
                "player_id": player_id,
                "seed": int(seed),
                "expected_run_id": expected_run_id,
                "notes": notes,
            }
        )
    return assignments


def find_machine_run(run_id: str) -> dict[str, Any] | None:
    for path in sorted(ANALYTICS_DIR.glob("run_*.json")):
        payload = load_json(path)
        if payload.get("run_id") == run_id:
            return payload
    return None


def format_pressure_nodes(machine_run: dict[str, Any]) -> str:
    pressure_nodes = [entry["node"] for entry in machine_run["decision_log"] if entry.get("pressure")]
    if not pressure_nodes:
        return "- none"
    return ", ".join(pressure_nodes)


def format_equipment_arc(machine_run: dict[str, Any]) -> str:
    moments = []
    for entry in machine_run["decision_log"]:
        summary = entry.get("equipment_summary")
        if summary:
            moments.append(f'{entry["node"]}: {summary}')
    if not moments:
        return "- none"
    return "\n".join(f"- {moment}" for moment in moments)


def format_primary_risk(machine_run: dict[str, Any]) -> str:
    analysis = machine_run.get("failure_analysis", {})
    blame = analysis.get("primary_blame_factor")
    if blame:
        return f"{blame} (steps_from_regret={analysis.get('steps_from_regret_to_death', 0)})"
    if machine_run.get("victory"):
        return "survived reference run"
    return machine_run.get("end_reason", "unknown")


def build_packet(assignments: list[dict[str, Any]]) -> str:
    sections = [
        "# PT-1 Operator Packet",
        "",
        "Use this packet during live sessions so the observer does not need to cross-check seed tables and machine logs by hand.",
        "",
        "## Session Commands",
        "",
        "```bash",
        "python scripts/bootstrap_pt1_sessions.py",
        "python scripts/play_cli_run.py <seed>",
        "python scripts/validate_human_playtest_logs.py",
        "python scripts/compare_playtest_vs_machine.py",
        "python scripts/generate_pt1_summary.py",
        "```",
        "",
        "## Seed Coverage",
        "",
    ]

    for assignment in assignments:
        machine_run = find_machine_run(assignment["expected_run_id"])
        sections.append(f'### {assignment["player_id"]} / seed {assignment["seed"]}')
        sections.append("")
        sections.append(f'- expected run family: `{assignment["expected_run_id"]}`')
        sections.append(f'- operator note: {assignment["notes"]}')
        if machine_run is None:
            sections.append("- machine reference: unavailable")
            sections.append("")
            continue

        player_final = machine_run["player_final"]
        sections.append(f'- machine reference: `{machine_run["run_id"]}`')
        sections.append(f'- pressure nodes: {format_pressure_nodes(machine_run)}')
        sections.append(f'- primary risk read: {format_primary_risk(machine_run)}')
        sections.append(
            "- final state snapshot: "
            f'hp={player_final["hp"]} food={player_final["food"]} ammo={player_final["ammo"]} '
            f'rad={player_final["radiation"]} weapon={player_final["weapon_slot"]} tool={player_final["tool_slot"]}'
        )
        sections.append("- equipment arc:")
        sections.append(format_equipment_arc(machine_run))
        sections.append("")

    sections.extend(
        [
            "## Observer Focus",
            "",
            "- Mark hesitation when the player compares routes, re-reads warnings, or counts food/ammo before committing.",
            "- Copy exact wording for confusion and regret statements. Do not paraphrase if avoidable.",
            "- After the run, make sure `run_id` in the human log matches the closest machine family, not just the seed.",
            "",
        ]
    )
    return "\n".join(sections)


def main() -> int:
    assignments = parse_seed_assignments()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_packet(assignments), encoding="utf-8")
    print(f"PT-1 operator packet written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
