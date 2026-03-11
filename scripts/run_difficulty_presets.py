#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
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


OUTPUT_PATH = ROOT / "output" / "analytics" / "difficulty_presets.json"
DIFFICULTIES = ("easy", "normal", "hard")
SEED_OFFSETS = (0, 100, 200, 300, 400)


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


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


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    death_reasons = Counter(result["end_reason"] for result in results if not result["victory"])
    return {
        "run_count": len(results),
        "victory_rate": average([1.0 if result["victory"] else 0.0 for result in results]),
        "avg_pressure_count": average([float(result["pressure_count"]) for result in results]),
        "avg_final_hp": average([float(result["player_final"]["hp"]) for result in results]),
        "avg_final_food": average([float(result["player_final"]["food"]) for result in results]),
        "avg_final_radiation": average([float(result["player_final"]["radiation"]) for result in results]),
        "avg_combat_count": average([float(result["analytics"]["run_summary"]["telemetry"]["combat_count"]) for result in results]),
        "death_reasons": dict(death_reasons),
    }


def main() -> int:
    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    plans = build_plans()

    grouped: dict[str, list[dict[str, Any]]] = {difficulty: [] for difficulty in DIFFICULTIES}
    for plan in plans:
        result = run_plan(plan, nodes, build_event_catalog(plan.seed), enemies)
        grouped[plan.difficulty].append(result)

    summary = {difficulty: summarize(grouped[difficulty]) for difficulty in DIFFICULTIES}
    deltas = {
        "easy_vs_normal": {
            "delta_victory_rate": round(summary["easy"]["victory_rate"] - summary["normal"]["victory_rate"], 3),
            "delta_avg_final_hp": round(summary["easy"]["avg_final_hp"] - summary["normal"]["avg_final_hp"], 3),
            "delta_avg_final_food": round(summary["easy"]["avg_final_food"] - summary["normal"]["avg_final_food"], 3),
        },
        "hard_vs_normal": {
            "delta_victory_rate": round(summary["hard"]["victory_rate"] - summary["normal"]["victory_rate"], 3),
            "delta_avg_final_hp": round(summary["hard"]["avg_final_hp"] - summary["normal"]["avg_final_hp"], 3),
            "delta_avg_final_food": round(summary["hard"]["avg_final_food"] - summary["normal"]["avg_final_food"], 3),
        },
    }

    verdict = {
        "status": (
            "SUPPORTED"
            if summary["easy"]["victory_rate"] > summary["normal"]["victory_rate"] > summary["hard"]["victory_rate"]
            else "WEAK"
        ),
        "summary": "Difficulty presets separate run outcomes in the expected direction."
        if summary["easy"]["victory_rate"] > summary["normal"]["victory_rate"] > summary["hard"]["victory_rate"]
        else "Difficulty presets do not cleanly separate run outcomes yet.",
    }

    payload = {
        "difficulties": summary,
        "deltas_vs_normal": deltas,
        "verdict": verdict,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Difficulty preset evaluation completed")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
