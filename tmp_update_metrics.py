import sys
from pathlib import Path

file_path = Path("scripts/run_balance_metrics.py")
content = file_path.read_text(encoding="utf-8")

# 1. Update build_balance_plans to cross-reference backgrounds
new_plans_fn = """BACKGROUNDS = ["soldier", "medic", "scavenger", "pathfinder", None]

def build_balance_plans() -> list[RoutePlan]:
    plans: list[RoutePlan] = []
    for bg in BACKGROUNDS:
        for batch_index, seed_offset in enumerate(SEED_OFFSETS, start=1):
            for base_plan in route_plans():
                bg_label = bg if bg else "none"
                plans.append(
                    RoutePlan(
                        name=f"{base_plan.name}_{bg_label}_batch_{batch_index}",
                        seed=base_plan.seed + seed_offset,
                        route=list(base_plan.route),
                        options=dict(base_plan.options),
                        difficulty=base_plan.difficulty,
                        background=bg,
                        travel_mode_strategy="dynamic"
                    )
                )
    return plans
"""

old_plans_fn_start = "def build_balance_plans()"
# We'll replace the whole function. Finding the end is tricky without a parser, 
# so we'll look for the next def.
import re
content = re.sub(r"def build_balance_plans\(\).*?return plans", new_plans_fn, content, flags=re.DOTALL)

# 2. Add summarize_backgrounds function
new_summary_fns = """
def summarize_backgrounds(results: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for result in results:
        # Use analytics player_final to get the background used in sim
        bg = result["analytics"]["player_final"].get("background") or "none"
        grouped[bg].append(result)

    for bg, bg_results in grouped.items():
        summary[bg] = {
            "runs": len(bg_results),
            "victory_rate": average([1.0 if item["victory"] else 0.0 for item in bg_results]),
            "avg_pressure_count": average([float(item["pressure_count"]) for item in bg_results]),
            "avg_final_hp": average([float(item["player_final"]["hp"]) for item in bg_results]),
            "avg_final_food": average([float(item["player_final"]["food"]) for item in bg_results]),
            "avg_final_scrap": average([float(item["player_final"]["scrap"]) for item in bg_results]),
        }
    return summary
"""

# Insert before summarize_results
content = content.replace("def summarize_results(results: list[dict]) -> dict:", new_summary_fns + "\ndef summarize_results(results: list[dict]) -> dict:")

# 3. Call summarize_backgrounds in summarize_results
content = content.replace('"route_family_summary": summarize_family(results),', '"route_family_summary": summarize_family(results),\n        "background_summary": summarize_backgrounds(results),')

file_path.write_text(content, encoding="utf-8")
print("Successfully updated scripts/run_balance_metrics.py")
