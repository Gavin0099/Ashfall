#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    RoutePlan,
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
    route_plans,
    run_plan,
)


OUTPUT_JSON = ROOT / "output" / "analytics" / "loot_economy.json"
OUTPUT_MD = ROOT / "output" / "summaries" / "loot_economy_report.md"
DIFFICULTIES = ("easy", "normal", "hard")
ROUTE_FAMILIES = ("north", "south", "mixed")
SEED_OFFSETS = (0, 100, 200, 300, 400)
RESOURCE_ORDER = ("food", "ammo", "medkits", "scrap")
ARCHETYPE_ORDER = ("raider", "mutant")


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def route_family(plan_name: str) -> str:
    if plan_name.startswith("north"):
        return "north"
    if plan_name.startswith("south"):
        return "south"
    return "mixed"


def build_plans() -> list[RoutePlan]:
    plans: list[RoutePlan] = []
    for difficulty in DIFFICULTIES:
        for offset in SEED_OFFSETS:
            for base in route_plans():
                plans.append(
                    RoutePlan(
                        name=f"{base.name}_{difficulty}_{offset}",
                        seed=base.seed + offset,
                        route=list(base.route),
                        options=dict(base.options),
                        difficulty=difficulty,
                    )
                )
    return plans


def empty_resource_totals() -> dict[str, int]:
    return {resource: 0 for resource in RESOURCE_ORDER}


def summarize_loot(results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = empty_resource_totals()
    archetype_counts = {archetype: 0 for archetype in ARCHETYPE_ORDER}
    runs_with_loot = 0
    loot_drop_counts: list[float] = []
    loot_total_amounts: list[float] = []
    encounter_counts: list[float] = []

    for result in results:
        telemetry = result["analytics"]["run_summary"]["telemetry"]
        loot_resources = telemetry.get("loot_resources", {})
        loot_drop_counts.append(float(telemetry.get("loot_drop_count", 0)))
        loot_total_amounts.append(float(telemetry.get("loot_total_amount", 0)))
        encounter_total = 0
        for moment in result.get("moments", []):
            combat = moment.get("event_outcome", {}).get("combat", {})
            enemy_id = combat.get("enemy_id")
            if not isinstance(enemy_id, str):
                continue
            encounter_total += 1
            if "raider" in enemy_id:
                archetype_counts["raider"] += 1
            elif "mutant" in enemy_id:
                archetype_counts["mutant"] += 1
        encounter_counts.append(float(encounter_total))
        if any(int(loot_resources.get(resource, 0)) > 0 for resource in RESOURCE_ORDER):
            runs_with_loot += 1
        for resource in RESOURCE_ORDER:
            totals[resource] += int(loot_resources.get(resource, 0))

    total_encounters = sum(archetype_counts.values())

    return {
        "run_count": len(results),
        "runs_with_loot_rate": round(runs_with_loot / len(results), 3) if results else 0.0,
        "avg_encounter_count": average(encounter_counts),
        "avg_loot_drop_count": average(loot_drop_counts),
        "avg_loot_total_amount": average(loot_total_amounts),
        "resource_totals": totals,
        "resource_per_run": {
            resource: round(totals[resource] / len(results), 3) if results else 0.0
            for resource in RESOURCE_ORDER
        },
        "archetype_encounters": archetype_counts,
        "archetype_encounter_rate": {
            archetype: round(archetype_counts[archetype] / total_encounters, 3) if total_encounters else 0.0
            for archetype in ARCHETYPE_ORDER
        },
        "dominant_archetype": max(ARCHETYPE_ORDER, key=lambda archetype: archetype_counts[archetype]) if total_encounters else None,
        "dominant_resource": max(RESOURCE_ORDER, key=lambda resource: totals[resource]) if results else None,
    }


def bullets_from_totals(totals: dict[str, float | int]) -> str:
    return "\n".join(f"- {resource}: {totals[resource]}" for resource in RESOURCE_ORDER)


def bullets_from_archetypes(totals: dict[str, float | int]) -> str:
    return "\n".join(f"- {archetype}: {totals[archetype]}" for archetype in ARCHETYPE_ORDER)


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Loot Economy Report",
        "",
        "## Overall",
        "",
    ]
    overall = payload["overall"]
    lines.extend(
        [
            f"- run_count: {overall['run_count']}",
            f"- runs_with_loot_rate: {overall['runs_with_loot_rate']}",
            f"- avg_encounter_count: {overall['avg_encounter_count']}",
            f"- avg_loot_drop_count: {overall['avg_loot_drop_count']}",
            f"- avg_loot_total_amount: {overall['avg_loot_total_amount']}",
            f"- dominant_resource: {overall['dominant_resource']}",
            f"- dominant_archetype: {overall['dominant_archetype']}",
            "",
            "### Overall Totals",
            "",
            bullets_from_totals(overall["resource_totals"]),
            "",
            "### Overall Per Run",
            "",
            bullets_from_totals(overall["resource_per_run"]),
            "",
            "### Overall Encounter Rate",
            "",
            bullets_from_archetypes(overall["archetype_encounter_rate"]),
            "",
            "## By Difficulty",
            "",
        ]
    )

    for difficulty in DIFFICULTIES:
        summary = payload["by_difficulty"][difficulty]
        lines.extend(
            [
                f"### {difficulty}",
                "",
                f"- runs_with_loot_rate: {summary['runs_with_loot_rate']}",
                f"- avg_encounter_count: {summary['avg_encounter_count']}",
                f"- avg_loot_drop_count: {summary['avg_loot_drop_count']}",
                f"- avg_loot_total_amount: {summary['avg_loot_total_amount']}",
                f"- dominant_resource: {summary['dominant_resource']}",
                f"- dominant_archetype: {summary['dominant_archetype']}",
                "",
                bullets_from_totals(summary["resource_per_run"]),
                "",
                bullets_from_archetypes(summary["archetype_encounter_rate"]),
                "",
            ]
        )

    lines.extend(["## By Route Family", ""])
    for family in ROUTE_FAMILIES:
        summary = payload["by_route_family"][family]
        lines.extend(
            [
                f"### {family}",
                "",
                f"- runs_with_loot_rate: {summary['runs_with_loot_rate']}",
                f"- avg_encounter_count: {summary['avg_encounter_count']}",
                f"- avg_loot_drop_count: {summary['avg_loot_drop_count']}",
                f"- avg_loot_total_amount: {summary['avg_loot_total_amount']}",
                f"- dominant_resource: {summary['dominant_resource']}",
                f"- dominant_archetype: {summary['dominant_archetype']}",
                "",
                bullets_from_totals(summary["resource_per_run"]),
                "",
                bullets_from_archetypes(summary["archetype_encounter_rate"]),
                "",
            ]
        )

    lines.extend(["## Difficulty x Route", ""])
    for difficulty in DIFFICULTIES:
        lines.extend([f"### {difficulty}", ""])
        for family in ROUTE_FAMILIES:
            summary = payload["by_difficulty_and_route"][difficulty][family]
            lines.append(
                f"- {family}: dominant={summary['dominant_resource']}, "
                f"archetype={summary['dominant_archetype']}, "
                f"loot/run={summary['avg_loot_total_amount']}, "
                f"food={summary['resource_per_run']['food']}, "
                f"ammo={summary['resource_per_run']['ammo']}, "
                f"medkits={summary['resource_per_run']['medkits']}, "
                f"scrap={summary['resource_per_run']['scrap']}, "
                f"raider_rate={summary['archetype_encounter_rate']['raider']}, "
                f"mutant_rate={summary['archetype_encounter_rate']['mutant']}"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    plans = build_plans()

    results: list[dict[str, Any]] = []
    for plan in plans:
        results.append(run_plan(plan, nodes, build_event_catalog(plan.seed), enemies))

    by_difficulty_raw: dict[str, list[dict[str, Any]]] = {difficulty: [] for difficulty in DIFFICULTIES}
    by_route_raw: dict[str, list[dict[str, Any]]] = {family: [] for family in ROUTE_FAMILIES}
    by_difficulty_route_raw: dict[str, dict[str, list[dict[str, Any]]]] = {
        difficulty: {family: [] for family in ROUTE_FAMILIES} for difficulty in DIFFICULTIES
    }

    for result in results:
        difficulty = result["analytics"]["run_id"].split("_")[-2]
        family = route_family(result["plan"])
        by_difficulty_raw[difficulty].append(result)
        by_route_raw[family].append(result)
        by_difficulty_route_raw[difficulty][family].append(result)

    payload = {
        "overall": summarize_loot(results),
        "by_difficulty": {
            difficulty: summarize_loot(group)
            for difficulty, group in by_difficulty_raw.items()
        },
        "by_route_family": {
            family: summarize_loot(group)
            for family, group in by_route_raw.items()
        },
        "by_difficulty_and_route": {
            difficulty: {
                family: summarize_loot(group)
                for family, group in grouped.items()
            }
            for difficulty, grouped in by_difficulty_route_raw.items()
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(build_markdown(payload), encoding="utf-8")

    print("Loot economy report completed")
    print(json.dumps(payload["overall"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
