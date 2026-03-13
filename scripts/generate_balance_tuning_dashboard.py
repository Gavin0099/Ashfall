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


def identity_signal(route_metrics: dict[str, Any], loot_metrics: dict[str, Any]) -> dict[str, float]:
    archetype_gap = round(
        loot_metrics["archetype_encounter_rate"]["mutant"] - loot_metrics["archetype_encounter_rate"]["raider"],
        2,
    )
    resource_gap = round(route_metrics["avg_final_scrap"] - route_metrics["avg_final_ammo"], 2)
    return {
        "archetype_gap": archetype_gap,
        "resource_gap": resource_gap,
    }


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
    if north["avg_pressure_count"] < 3.0:
        findings.append(f"north pressure density slipped below target: avg_pressure_count={north['avg_pressure_count']}")
    return findings


def economy_findings(balance: dict[str, Any], loot: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    balance_loot = balance["summary"]["loot_economy"]
    route_summary = balance["summary"]["route_family_summary"]
    north_ammo = balance_loot["north"]["resource_per_run"]["ammo"]
    if balance_loot["north"]["resource_per_run"]["medkits"] < 0.3:
        findings.append("north medkit recovery is still low relative to its mutant pressure")
    if route_summary["north"]["avg_final_scrap"] <= route_summary["north"]["avg_final_ammo"]:
        findings.append(
            "north final-state resource identity still reads too much like ammo; scrap salvage is not yet dominant"
        )
    if balance_loot["south"]["resource_per_run"]["ammo"] <= balance_loot["north"]["resource_per_run"]["ammo"]:
        findings.append("south is not pulling enough extra ammo relative to north")
    if loot["by_difficulty"]["hard"]["avg_loot_total_amount"] < loot["by_difficulty"]["easy"]["avg_loot_total_amount"]:
        findings.append("hard difficulty suppresses loot economy, which can amplify failure noise")
    return findings


def archetype_findings(balance: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    route_summary = balance["summary"]["route_family_summary"]
    by_route = balance["summary"]["loot_economy"]
    north_signal = identity_signal(route_summary["north"], by_route["north"])
    south_signal = identity_signal(route_summary["south"], by_route["south"])
    if north_signal["archetype_gap"] <= 0:
        findings.append("north is no longer mutant-leaning at the encounter layer")
    elif north_signal["archetype_gap"] < 0.1:
        findings.append(
            f"north mutant identity exists but remains narrow at the encounter layer (gap={north_signal['archetype_gap']})"
        )
    if by_route["south"]["archetype_encounter_rate"]["raider"] <= 0.55:
        findings.append("south is not clearly raider-leaning enough to create route identity")
    if by_route["north"]["dominant_resource"] == "scrap" and by_route["north"]["avg_loot_drop_count"] < 1.2:
        findings.append("north loot identity exists, but it is not appearing often enough")
    if south_signal["resource_gap"] >= 0:
        findings.append("south final-state resources no longer favor ammo over scrap")
    return findings


def build_actions(balance: dict[str, Any], loot: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    north = balance["summary"]["route_family_summary"]["north"]
    north_loot = balance["summary"]["loot_economy"]["north"]
    south_loot = balance["summary"]["loot_economy"]["south"]
    north_signal = identity_signal(north, north_loot)

    if north["victory_rate"] <= 0.05:
        actions.append("Reduce `north` mutant weight again or lower mutant brute durability by one more step.")
    if north_loot["resource_per_run"]["medkits"] < 0.3:
        actions.append("Raise mutant medkit drop chance or add one more north-side recovery event.")
    if north["avg_pressure_count"] < 3.0:
        actions.append("Restore one more meaningful pressure moment on north without adding raw lethality.")
    if north["avg_final_scrap"] <= north["avg_final_ammo"]:
        actions.append("Shift one north-only reward from ammo toward scrap so the mutant/salvage identity becomes explicit.")
    if 0 < north_signal["archetype_gap"] < 0.1:
        actions.append("Use north-only event framing or safer mutant-trigger opportunities before increasing encounter weight again.")
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
    north_signal = identity_signal(balance["summary"]["route_family_summary"]["north"], balance["summary"]["loot_economy"]["north"])
    south_signal = identity_signal(balance["summary"]["route_family_summary"]["south"], balance["summary"]["loot_economy"]["south"])

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
        "## Identity Signals",
        "",
        f"- north_archetype_gap: {north_signal['archetype_gap']}",
        f"- north_resource_gap(scrap-ammo): {north_signal['resource_gap']}",
        f"- south_archetype_gap(mutant-raider): {south_signal['archetype_gap']}",
        f"- south_resource_gap(scrap-ammo): {south_signal['resource_gap']}",
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
