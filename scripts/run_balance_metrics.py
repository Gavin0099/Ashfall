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
SEED_OFFSETS = (0, 100, 200, 300)


def build_balance_plans() -> list[RoutePlan]:
    plans: list[RoutePlan] = []
    for batch_index, seed_offset in enumerate(SEED_OFFSETS, start=1):
        for base_plan in route_plans():
            plans.append(
                RoutePlan(
                    name=f"{base_plan.name}_batch_{batch_index}",
                    seed=base_plan.seed + seed_offset,
                    route=list(base_plan.route),
                    options=dict(base_plan.options),
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
        )
        for result in results
    ]
    distances = [
        sum(abs(left[i] - right[i]) for i in range(len(left)))
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
            "avg_final_radiation": average([float(item["player_final"]["radiation"]) for item in family_results]),
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
            "radiation": average([float(result["player_final"]["radiation"]) for result in results]),
        },
        "death_reasons": dict(death_reasons),
        "decision_trace_coverage_rate": round(decision_trace_coverage / len(results), 2) if results else 0.0,
        "death_cause_attribution_rate": round(len(attributable_deaths) / max(1, sum(1 for result in results if not result["victory"])), 2),
        "distinct_outcome_signatures": len(outcome_signatures),
        "resource_divergence": pairwise_resource_distance(results),
        "route_family_summary": summarize_family(results),
    }
    summary["balance_gate"] = {
        "twenty_runs_captured": summary["run_count"] >= 20,
        "decision_trace_complete": summary["decision_trace_coverage_rate"] == 1.0,
        "death_attribution_complete": summary["death_cause_attribution_rate"] == 1.0,
        "route_divergence_visible": summary["resource_divergence"]["pairwise_average"] >= 3.0,
    }
    return summary


def main() -> int:
    BALANCE_DIR.mkdir(parents=True, exist_ok=True)

    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    plans = build_balance_plans()

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

    if not all(summary["balance_gate"].values()):
        failed = [name for name, passed in summary["balance_gate"].items() if not passed]
        raise ValidationError(f"Balance metrics gate failed: {', '.join(failed)}")

    print("Balance metrics completed")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
