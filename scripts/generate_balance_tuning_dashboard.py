#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BALANCE_PATH = ROOT / "output" / "analytics" / "balance_summary.json"
LOOT_PATH = ROOT / "output" / "analytics" / "loot_economy.json"
OUTPUT_PATH = ROOT / "output" / "summaries" / "balance_tuning_dashboard.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def route_findings(balance: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    route_summary = balance["summary"]["route_family_summary"]
    loot_summary = balance["summary"]["loot_economy"]

    north = route_summary["north"]
    south = route_summary["south"]
    mixed = route_summary["mixed"]

    if north["victory_rate"] <= 0.05:
        findings.append(
            f"north is still a dead lane: win_rate={north['victory_rate']}, "
            f"dominant_archetype={loot_summary['north']['dominant_archetype']}, "
            f"dominant_resource={loot_summary['north']['dominant_resource']}"
        )
    if south["victory_rate"] - north["victory_rate"] >= 0.2:
        findings.append(
            f"south outperforms north by {round(south['victory_rate'] - north['victory_rate'], 2)} win rate points"
        )
    if mixed["avg_final_hp"] <= 1.0:
        findings.append("mixed runs remain highly volatile and often finish near lethal hp")
    return findings


def economy_findings(balance: dict[str, Any], loot: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    balance_loot = balance["summary"]["loot_economy"]
    if balance_loot["north"]["resource_per_run"]["medkits"] < 0.3:
        findings.append("north medkit recovery is still low relative to its mutant pressure")
    if balance_loot["south"]["resource_per_run"]["ammo"] <= balance_loot["north"]["resource_per_run"]["ammo"]:
        findings.append("south is not pulling enough extra ammo relative to north")
    if loot["by_difficulty"]["hard"]["avg_loot_total_amount"] < loot["by_difficulty"]["easy"]["avg_loot_total_amount"]:
        findings.append("hard difficulty suppresses loot economy, which can amplify failure noise")
    return findings


def archetype_findings(balance: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    by_route = balance["summary"]["loot_economy"]
    if by_route["north"]["archetype_encounter_rate"]["mutant"] <= 0.55:
        findings.append("north is not clearly mutant-leaning enough to create route identity")
    if by_route["south"]["archetype_encounter_rate"]["raider"] <= 0.55:
        findings.append("south is not clearly raider-leaning enough to create route identity")
    if by_route["north"]["dominant_resource"] == "scrap" and by_route["north"]["avg_loot_drop_count"] < 1.2:
        findings.append("north loot identity exists, but it is not appearing often enough")
    return findings


def build_actions(balance: dict[str, Any], loot: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    north = balance["summary"]["route_family_summary"]["north"]
    north_loot = balance["summary"]["loot_economy"]["north"]
    south_loot = balance["summary"]["loot_economy"]["south"]

    if north["victory_rate"] <= 0.05:
        actions.append("Reduce `north` mutant weight again or lower mutant brute durability by one more step.")
    if north_loot["resource_per_run"]["medkits"] < 0.3:
        actions.append("Raise mutant medkit drop chance or add one more north-side recovery event.")
    if south_loot["dominant_resource"] != "ammo":
        actions.append("Increase raider ammo yield so south keeps a clearer raider/ammo identity.")
    if loot["by_difficulty"]["hard"]["avg_loot_total_amount"] < 1.2:
        actions.append("Consider a hard-mode loot floor or lower hard encounter pressure before more user testing.")
    return actions


def main() -> int:
    balance = load_json(BALANCE_PATH)
    loot = load_json(LOOT_PATH)

    route_notes = route_findings(balance)
    economy_notes = economy_findings(balance, loot)
    archetype_notes = archetype_findings(balance)
    actions = build_actions(balance, loot)

    lines = [
        "# Balance Tuning Dashboard",
        "",
        "## Snapshot",
        "",
        f"- victory_rate: {balance['summary']['victory_rate']}",
        f"- north_win_rate: {balance['summary']['route_family_summary']['north']['victory_rate']}",
        f"- south_win_rate: {balance['summary']['route_family_summary']['south']['victory_rate']}",
        f"- mixed_win_rate: {balance['summary']['route_family_summary']['mixed']['victory_rate']}",
        f"- overall_dominant_archetype: {balance['summary']['loot_economy']['overall']['dominant_archetype']}",
        f"- overall_dominant_resource: {balance['summary']['loot_economy']['overall']['dominant_resource']}",
        "",
        "## Route Findings",
        "",
    ]
    lines.extend([f"- {item}" for item in route_notes] or ["- none"])
    lines.extend(["", "## Economy Findings", ""])
    lines.extend([f"- {item}" for item in economy_notes] or ["- none"])
    lines.extend(["", "## Archetype Findings", ""])
    lines.extend([f"- {item}" for item in archetype_notes] or ["- none"])
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend([f"- {item}" for item in actions] or ["- none"])
    lines.append("")
    report = "\n".join(lines)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Balance tuning dashboard written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
