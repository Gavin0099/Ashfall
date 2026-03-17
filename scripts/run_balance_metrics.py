#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

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
from scripts.validate_run_analytics import ValidationError, validate_run_file


BALANCE_DIR = ROOT / "output" / "analytics" / "balance"
SUMMARY_PATH = ROOT / "output" / "analytics" / "balance_summary.json"
SEED_OFFSETS = (0, 100, 200, 300, 400, 500, 600, 700, 800, 900)


ARCHETYPES = ["vault_technician", "raider_defector", "wasteland_medic", None]

def build_balance_plans() -> list[RoutePlan]:
    plans: list[RoutePlan] = []
    
    # Load dynamic characters from data/characters/
    char_dir = ROOT / "data" / "characters"
    character_samples: list[dict] = []
    if char_dir.exists():
        for f in char_dir.glob("*.json"):
            character_samples.append(json.loads(f.read_text(encoding="utf-8")))

    # Combined pool of archetypes and custom characters
    for batch_index, seed_offset in enumerate(SEED_OFFSETS, start=1):
        for base_plan in route_plans():
            # Standard Archetypes
            for arch in ARCHETYPES:
                arch_label = arch if arch else "none"
                plans.append(
                    RoutePlan(
                        name=f"{base_plan.name}_{arch_label}_batch_{batch_index}",
                        seed=base_plan.seed + seed_offset,
                        route=list(base_plan.route),
                        options=dict(base_plan.options),
                        difficulty=base_plan.difficulty,
                        archetype=arch,
                        travel_mode_strategy="dynamic"
                    )
                )
            # Custom Characters (only use first 5 to avoid exploding run count)
            for char_data in character_samples[:5]:
                char_id = char_data["character_id"]
                plans.append(
                    RoutePlan(
                        name=f"{base_plan.name}_{char_id}_batch_{batch_index}",
                        seed=base_plan.seed + seed_offset,
                        route=list(base_plan.route),
                        options=dict(base_plan.options),
                        difficulty=base_plan.difficulty,
                        character_id=char_id, # This will need run_plan to handle it
                        travel_mode_strategy="dynamic"
                    )
                )
    return plans



def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def route_family(plan_name: str) -> str:
    if plan_name.startswith("north"):
        return "north"
    if plan_name.startswith("south"):
        return "south"
    return "mixed"


def pairwise_resource_distance(results: list[dict]) -> dict:
    resource_vectors = [
        (
            result["player_final"]["hp"],
            result["player_final"]["food"],
            result["player_final"]["ammo"],
            result["player_final"]["medkits"],
            result["player_final"]["radiation"],
            result["player_final"]["weapon_slot"]["id"] if result["player_final"]["weapon_slot"] else None,
            result["player_final"]["armor_slot"]["id"] if result["player_final"]["armor_slot"] else None,
            result["player_final"]["tool_slot"]["id"] if result["player_final"]["tool_slot"] else None,
        )
        for result in results
    ]
    distances = [
        sum(1 if left[i] != right[i] else 0 for i in range(len(left)))
        for left, right in combinations(resource_vectors, 2)
    ]
    return {
        "pairwise_average": average([float(value) for value in distances]),
        "pairwise_max": max(distances) if distances else 0,
        "pairwise_min": min(distances) if distances else 0,
    }


def summarize_family(results: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for result in results:
        grouped[route_family(result["plan"])].append(result)

    for family, family_results in grouped.items():
        summary[family] = {
            "runs": len(family_results),
            "victory_rate": average([1.0 if item["victory"] else 0.0 for item in family_results]),
            "avg_pressure_count": average([float(item["pressure_count"]) for item in family_results]),
            "avg_final_hp": average([float(item["player_final"]["hp"]) for item in family_results]),
            "avg_final_food": average([float(item["player_final"]["food"]) for item in family_results]),
            "avg_final_ammo": average([float(item["player_final"]["ammo"]) for item in family_results]),
            "avg_final_medkits": average([float(item["player_final"]["medkits"]) for item in family_results]),
            "avg_final_scrap": average([float(item["player_final"]["scrap"]) for item in family_results]),
            "avg_final_radiation": average([float(item["player_final"]["radiation"]) for item in family_results]),
        }
    return summary


def summarize_loot(results: list[dict]) -> dict:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    archetype_grouped: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for result in results:
        telemetry = result["analytics"]["run_summary"]["telemetry"]
        route_key = route_family(result["plan"])
        encounter_count = 0.0
        for moment in result.get("moments", []):
            enemy_id = moment.get("event_outcome", {}).get("combat", {}).get("enemy_id")
            if not isinstance(enemy_id, str):
                continue
            encounter_count += 1.0
            if "raider" in enemy_id:
                archetype_grouped["overall"]["raider"] += 1.0
                archetype_grouped[route_key]["raider"] += 1.0
            elif "mutant" in enemy_id:
                archetype_grouped["overall"]["mutant"] += 1.0
                archetype_grouped[route_key]["mutant"] += 1.0
        for resource, amount in telemetry.get("loot_resources", {}).items():
            grouped["overall"][resource] += float(amount)
            grouped[route_key][resource] += float(amount)
        grouped["overall"]["loot_drop_count"] += float(telemetry.get("loot_drop_count", 0))
        grouped["overall"]["loot_total_amount"] += float(telemetry.get("loot_total_amount", 0))
        grouped["overall"]["encounter_count"] += encounter_count
        grouped[route_key]["loot_drop_count"] += float(telemetry.get("loot_drop_count", 0))
        grouped[route_key]["loot_total_amount"] += float(telemetry.get("loot_total_amount", 0))
        grouped[route_key]["encounter_count"] += encounter_count

    summary: dict[str, dict] = {}
    for key in ("overall", "north", "south", "mixed"):
        bucket = grouped[key]
        archetype_bucket = archetype_grouped[key]
        run_total = len(results) if key == "overall" else sum(1 for result in results if route_family(result["plan"]) == key)
        resource_totals = {
            "food": round(bucket.get("food", 0.0), 2),
            "ammo": round(bucket.get("ammo", 0.0), 2),
            "medkits": round(bucket.get("medkits", 0.0), 2),
            "scrap": round(bucket.get("scrap", 0.0), 2),
        }
        archetype_totals = {
            "raider": round(archetype_bucket.get("raider", 0.0), 2),
            "mutant": round(archetype_bucket.get("mutant", 0.0), 2),
        }
        total_encounters = sum(archetype_totals.values())
        dominant_resource = max(resource_totals, key=resource_totals.get) if run_total > 0 else None
        summary[key] = {
            "avg_encounter_count": round(bucket.get("encounter_count", 0.0) / run_total, 2) if run_total else 0.0,
            "avg_loot_drop_count": round(bucket.get("loot_drop_count", 0.0) / run_total, 2) if run_total else 0.0,
            "avg_loot_total_amount": round(bucket.get("loot_total_amount", 0.0) / run_total, 2) if run_total else 0.0,
            "resource_totals": resource_totals,
            "resource_per_run": {
                resource: round(amount / run_total, 2) if run_total else 0.0
                for resource, amount in resource_totals.items()
            },
            "archetype_encounters": archetype_totals,
            "archetype_encounter_rate": {
                archetype: round(amount / total_encounters, 2) if total_encounters else 0.0
                for archetype, amount in archetype_totals.items()
            },
            "dominant_archetype": max(archetype_totals, key=archetype_totals.get) if total_encounters > 0 else None,
            "dominant_resource": dominant_resource,
        }
    return summary



def summarize_archetypes(results: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for result in results:
        # Use character background_id or archetype
        player_final = result["analytics"]["player_final"]
        char = player_final.get("character")
        if char:
            arch = char.get("background_id", "none")
        else:
            arch = player_final.get("archetype") or "none"
        grouped[arch].append(result)

    for arch, arch_results in grouped.items():
        losing_runs = [r for r in arch_results if not r["victory"]]
        regret_distances = [
            float(r["analytics"]["failure_analysis"]["steps_from_regret_to_death"])
            for r in losing_runs
            if r["analytics"]["failure_analysis"]["steps_from_regret_to_death"] >= 0
        ]
        summary[arch] = {
            "runs": len(arch_results),
            "victory_rate": average([1.0 if item["victory"] else 0.0 for item in arch_results]),
            "avg_pressure_count": average([float(item["pressure_count"]) for item in arch_results]),
            "avg_final_hp": average([float(item["player_final"]["hp"]) for item in arch_results]),
            "avg_final_food": average([float(item["player_final"]["food"]) for item in arch_results]),
            "avg_final_scrap": average([float(item["player_final"]["scrap"]) for item in arch_results]),
            "avg_steps_from_regret_to_death": average(regret_distances),
            "death_reasons": dict(Counter(r["end_reason"] for r in losing_runs))
        }
    return summary


def summarize_special_stats(results: list[dict]) -> dict:
    """Analyze correlation between SPECIAL stats and victory."""
    stats = defaultdict(lambda: {"victories": 0, "total": 0, "sum_val": 0})
    
    for result in results:
        char = result["analytics"]["player_final"].get("character")
        if not char or "special" not in char:
            continue
        
        special = char["special"]
        victory = 1 if result["victory"] else 0
        for s_name, s_val in special.items():
            stats[s_name]["total"] += 1
            stats[s_name]["victories"] += victory
            stats[s_name]["sum_val"] += s_val

    summary = {}
    for s_name, data in stats.items():
        if data["total"] > 0:
            summary[s_name] = {
                "avg_value": round(data["sum_val"] / data["total"], 2),
                "victory_rate_at_avg": round(data["victories"] / data["total"], 2)
            }
    return summary

def summarize_results(results: list[dict]) -> dict:
    death_reasons = Counter(result["end_reason"] for result in results if not result["victory"])
    outcome_signatures = {
        (
            result["victory"],
            result["end_reason"],
            result["player_final"]["hp"],
            result["player_final"]["food"],
            result["player_final"]["ammo"],
            result["player_final"]["medkits"],
            result["player_final"]["radiation"],
        )
        for result in results
    }
    decision_trace_coverage = sum(
        1 for result in results if len(result["analytics"]["decision_log"]) == len(result["moments"])
    )
    attributable_deaths = [
        result for result in results if (not result["victory"] and result["analytics"]["summary"]["death_cause_attribution"])
    ]
    losing_runs = [result for result in results if not result["victory"]]
    trash_time_runs = [result for result in losing_runs if result["analytics"]["failure_analysis"]["is_trash_time_death"]]
    regret_distance_values = [
        float(result["analytics"]["failure_analysis"]["steps_from_regret_to_death"])
        for result in losing_runs
        if result["analytics"]["failure_analysis"]["steps_from_regret_to_death"] >= 0
    ]

    summary = {
        "run_count": len(results),
        "victory_rate": average([1.0 if result["victory"] else 0.0 for result in results]),
        "avg_pressure_count": average([float(result["pressure_count"]) for result in results]),
        "avg_decision_count": average([float(len(result["analytics"]["decision_log"])) for result in results]),
        "avg_final_resources": {
            "hp": average([float(result["player_final"]["hp"]) for result in results]),
            "food": average([float(result["player_final"]["food"]) for result in results]),
            "ammo": average([float(result["player_final"]["ammo"]) for result in results]),
            "medkits": average([float(result["player_final"]["medkits"]) for result in results]),
            "scrap": average([float(result["player_final"]["scrap"]) for result in results]),
            "radiation": average([float(result["player_final"]["radiation"]) for result in results]),
        },
        "death_reasons": dict(death_reasons),
        "decision_trace_coverage_rate": round(decision_trace_coverage / len(results), 2) if results else 0.0,
        "death_cause_attribution_rate": round(len(attributable_deaths) / max(1, sum(1 for result in results if not result["victory"])), 2),
        "trash_time_death_rate": round(len(trash_time_runs) / max(1, len(losing_runs)), 2),
        "avg_steps_from_regret_to_death": average(regret_distance_values),
        "distinct_outcome_signatures": len(outcome_signatures),
        "resource_divergence": pairwise_resource_distance(results),
        "route_family_summary": summarize_family(results),
        "archetype_summary": summarize_archetypes(results),
        "special_stats_correlation": summarize_special_stats(results),
        "loot_economy": summarize_loot(results),
    }
    summary["balance_gate"] = {
        "twenty_runs_captured": summary["run_count"] >= 20,
        "decision_trace_complete": summary["decision_trace_coverage_rate"] == 1.0,
        "death_attribution_complete": summary["death_cause_attribution_rate"] == 1.0,
        "route_divergence_visible": summary["resource_divergence"]["pairwise_average"] >= 3.0,
    }
    return summary


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=None, help="Limit number of runs")
    args = parser.parse_args()

    BALANCE_DIR.mkdir(parents=True, exist_ok=True)

    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    plans = build_balance_plans()
    
    if args.runs:
        plans = plans[:args.runs]

    results: list[dict] = []
    for index, plan in enumerate(plans, start=1):
        result = run_plan(plan, nodes, build_event_catalog(plan.seed), enemies)
        results.append(result)
        output_path = BALANCE_DIR / f"run_{index:02d}_{plan.name}.json"
        output_path.write_text(json.dumps(result["analytics"], indent=2), encoding="utf-8")
        validate_run_file(output_path)

    summary = summarize_results(results)
    summary_payload = {
        "run_ids": [result["analytics"]["run_id"] for result in results],
        "summary": summary,
    }
    SUMMARY_PATH.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    if "loot_economy" not in summary:
        raise ValidationError("Balance metrics summary missing loot_economy")

    if not all(summary["balance_gate"].values()):
        failed = [name for name, passed in summary["balance_gate"].items() if not passed]
        raise ValidationError(f"Balance metrics gate failed: {', '.join(failed)}")

    print("Balance metrics completed")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
