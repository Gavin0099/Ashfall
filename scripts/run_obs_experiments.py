#!/usr/bin/env python3
"""OBS experiments — validate hypotheses from SEED_101_OBSERVATION.md.

OBS-1: First-node dominance test
  Same route, same subsequent choices, only first-node option varies.
  Measures win-rate divergence caused by a single early decision.

OBS-2: Conservative survivability test
  All-cautious play (option 1 at every node) across many seeds.
  Checks whether avoiding all risk still produces viable win paths.

OBS-3: Risk payoff sampling
  Aggressive (option 0) vs Conservative (option 1) across >=100 runs.
  Compares net resource outcomes and win rates to check risk-reward balance.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    RoutePlan,
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
    run_plan,
)

OBS_DIR = ROOT / "output" / "analytics" / "obs"
NORTH_ROUTE = ["node_north_1", "node_north_2", "node_mid", "node_final"]
SOUTH_ROUTE = ["node_south_1", "node_south_2", "node_mid", "node_final"]

# Seeds used for OBS-1 first-node dominance (10 seeds = 10 pair runs each)
OBS1_SEEDS = [101, 201, 301, 401, 501, 601, 701, 801, 901, 1001]

# Seeds used for OBS-2 conservative survivability (20 seeds)
OBS2_SEEDS = list(range(101, 121))

# Seeds used for OBS-3 risk payoff sampling (>=100 runs = 50 seeds × 2 routes)
OBS3_SEEDS = list(range(101, 151))


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def resource_gain(result: dict) -> dict:
    """Net resource delta from start values (hp=10, food=7, ammo=3, medkits=1, radiation=0)."""
    final = result["player_final"]
    return {
        "hp_delta": final["hp"] - 10,
        "food_delta": final["food"] - 7,
        "ammo_delta": final["ammo"] - 3,
        "medkits_delta": final["medkits"] - 1,
        "radiation_delta": final["radiation"] - 0,
        "net_score": (final["hp"] - 10) + (final["food"] - 7) + (final["ammo"] - 3) - (final["radiation"] * 2),
    }


# ---------------------------------------------------------------------------
# OBS-1: First-node dominance
# ---------------------------------------------------------------------------

def run_obs1(nodes: dict, enemies: dict) -> dict:
    """OBS-1: vary only the first node option, hold the rest constant (cautious=1).

    Group A: first node = 0 (risky/aggressive)
    Group B: first node = 1 (safe/cautious)
    All subsequent nodes use option 1 (cautious) to isolate the first-node effect.
    """
    group_a: list[dict] = []  # first node aggressive
    group_b: list[dict] = []  # first node cautious

    first_node = NORTH_ROUTE[0]  # node_north_1
    cautious_tail = {node: 1 for node in NORTH_ROUTE[1:]}

    for seed in OBS1_SEEDS:
        plan_a = RoutePlan(
            name=f"obs1_aggressive_first_{seed}",
            seed=seed,
            route=list(NORTH_ROUTE),
            options={first_node: 0, **cautious_tail},
        )
        plan_b = RoutePlan(
            name=f"obs1_cautious_first_{seed}",
            seed=seed,
            route=list(NORTH_ROUTE),
            options={first_node: 1, **cautious_tail},
        )
        events = build_event_catalog(seed)
        result_a = run_plan(plan_a, nodes, events, enemies)
        result_b = run_plan(plan_b, nodes, events, enemies)
        group_a.append(result_a)
        group_b.append(result_b)

    win_rate_a = average([1.0 if r["victory"] else 0.0 for r in group_a])
    win_rate_b = average([1.0 if r["victory"] else 0.0 for r in group_b])
    win_rate_divergence = round(abs(win_rate_a - win_rate_b), 3)

    avg_net_a = average([resource_gain(r)["net_score"] for r in group_a])
    avg_net_b = average([resource_gain(r)["net_score"] for r in group_b])

    hypothesis_confirmed = win_rate_divergence >= 0.3

    summary = {
        "experiment": "OBS-1 First-node dominance",
        "description": (
            "Same route and same subsequent choices; only the first-node option varies. "
            "Measures how much a single early decision shifts the win rate."
        ),
        "group_a_label": "first node aggressive (option 0)",
        "group_b_label": "first node cautious (option 1)",
        "seeds_used": OBS1_SEEDS,
        "runs_per_group": len(OBS1_SEEDS),
        "group_a": {
            "win_rate": win_rate_a,
            "avg_net_resource_score": avg_net_a,
            "death_reasons": _count_reasons(group_a),
        },
        "group_b": {
            "win_rate": win_rate_b,
            "avg_net_resource_score": avg_net_b,
            "death_reasons": _count_reasons(group_b),
        },
        "win_rate_divergence": win_rate_divergence,
        "hypothesis": "early-node resource swing disproportionately influences run survivability",
        "hypothesis_threshold": "win_rate_divergence >= 0.3",
        "hypothesis_confirmed": hypothesis_confirmed,
        "interpretation": (
            "First node creates strong win-rate divergence — early choice dominates."
            if hypothesis_confirmed
            else "First node divergence is modest — tension may be more distributed across route."
        ),
    }
    return summary


# ---------------------------------------------------------------------------
# OBS-2: Conservative survivability
# ---------------------------------------------------------------------------

def run_obs2(nodes: dict, enemies: dict) -> dict:
    """OBS-2: all-cautious play (option 1 everywhere) across 20 seeds on north route."""
    results: list[dict] = []
    for seed in OBS2_SEEDS:
        plan = RoutePlan(
            name=f"obs2_all_cautious_{seed}",
            seed=seed,
            route=list(NORTH_ROUTE),
            options={node: 1 for node in NORTH_ROUTE},
        )
        events = build_event_catalog(seed)
        results.append(run_plan(plan, nodes, events, enemies))

    win_rate = average([1.0 if r["victory"] else 0.0 for r in results])
    avg_final_food = average([float(r["player_final"]["food"]) for r in results])
    avg_final_hp = average([float(r["player_final"]["hp"]) for r in results])
    avg_pressure = average([float(r["pressure_count"]) for r in results])
    death_reasons = _count_reasons([r for r in results if not r["victory"]])

    # Hypothesis: conservative play is NOT a guaranteed safe path
    hypothesis_confirmed = win_rate < 0.8  # i.e., risk-avoidance alone doesn't ensure survival

    summary = {
        "experiment": "OBS-2 Conservative survivability",
        "description": (
            "All choices set to option 1 (cautious/safe) across 20 seeds on the north route. "
            "Tests whether pure risk-avoidance is a viable strategy."
        ),
        "seeds_used": OBS2_SEEDS,
        "run_count": len(results),
        "win_rate": win_rate,
        "avg_final_food": avg_final_food,
        "avg_final_hp": avg_final_hp,
        "avg_pressure_count": avg_pressure,
        "death_reasons": death_reasons,
        "hypothesis": "risk avoidance != guaranteed survivability",
        "hypothesis_threshold": "conservative win_rate < 0.8",
        "hypothesis_confirmed": hypothesis_confirmed,
        "interpretation": (
            "Conservative play is not a safe default — players must engage with risk."
            if hypothesis_confirmed
            else "Conservative play wins too reliably — reduce safe-path dominance or add passive attrition."
        ),
    }
    return summary


# ---------------------------------------------------------------------------
# OBS-3: Risk payoff sampling
# ---------------------------------------------------------------------------

def run_obs3(nodes: dict, enemies: dict) -> dict:
    """OBS-3: aggressive vs conservative across 50 seeds × 2 routes = 100+ runs each."""
    aggressive: list[dict] = []
    conservative: list[dict] = []

    for seed in OBS3_SEEDS:
        events = build_event_catalog(seed)
        for route, label in [(NORTH_ROUTE, "north"), (SOUTH_ROUTE, "south")]:
            plan_agg = RoutePlan(
                name=f"obs3_aggressive_{label}_{seed}",
                seed=seed,
                route=list(route),
                options={node: 0 for node in route},
            )
            plan_con = RoutePlan(
                name=f"obs3_conservative_{label}_{seed}",
                seed=seed,
                route=list(route),
                options={node: 1 for node in route},
            )
            aggressive.append(run_plan(plan_agg, nodes, events, enemies))
            conservative.append(run_plan(plan_con, nodes, events, enemies))

    agg_wins = average([1.0 if r["victory"] else 0.0 for r in aggressive])
    con_wins = average([1.0 if r["victory"] else 0.0 for r in conservative])
    agg_net = average([resource_gain(r)["net_score"] for r in aggressive])
    con_net = average([resource_gain(r)["net_score"] for r in conservative])
    agg_rad = average([float(r["player_final"]["radiation"]) for r in aggressive])
    con_rad = average([float(r["player_final"]["radiation"]) for r in conservative])

    # Route family breakdown
    route_breakdown = _route_breakdown(aggressive, conservative)

    # Hypothesis: high-risk options currently over-perform relative to conservative
    # Threshold: aggressive wins at least 20% more, or net score is 2+ points higher
    win_gap = round(agg_wins - con_wins, 3)
    net_gap = round(agg_net - con_net, 3)
    hypothesis_confirmed = win_gap >= 0.2 or net_gap >= 2.0

    summary = {
        "experiment": "OBS-3 Risk payoff sampling",
        "description": (
            "Aggressive (all option 0) vs Conservative (all option 1) across "
            f"{len(OBS3_SEEDS)} seeds × 2 routes = {len(aggressive)} runs per group."
        ),
        "seeds_used": OBS3_SEEDS,
        "runs_per_group": len(aggressive),
        "aggressive": {
            "win_rate": agg_wins,
            "avg_net_resource_score": agg_net,
            "avg_final_radiation": agg_rad,
            "death_reasons": _count_reasons([r for r in aggressive if not r["victory"]]),
        },
        "conservative": {
            "win_rate": con_wins,
            "avg_net_resource_score": con_net,
            "avg_final_radiation": con_rad,
            "death_reasons": _count_reasons([r for r in conservative if not r["victory"]]),
        },
        "win_rate_gap_aggressive_minus_conservative": win_gap,
        "net_score_gap_aggressive_minus_conservative": net_gap,
        "route_family_breakdown": route_breakdown,
        "hypothesis": "high-risk options over-perform relative to conservative options",
        "hypothesis_threshold": "win_rate_gap >= 0.2 OR net_score_gap >= 2.0",
        "hypothesis_confirmed": hypothesis_confirmed,
        "interpretation": (
            "Risk dominates reward — balance check recommended before next PT round."
            if hypothesis_confirmed
            else "Risk and conservative paths are comparably viable — tension balance is healthy."
        ),
    }
    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_reasons(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        reason = r.get("end_reason") or "unknown"
        counts[reason] += 1
    return dict(counts)


def _route_breakdown(aggressive: list[dict], conservative: list[dict]) -> dict:
    def by_route(results: list[dict]) -> dict:
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in results:
            name = r["plan"]
            if "north" in name:
                groups["north"].append(r)
            elif "south" in name:
                groups["south"].append(r)
        return {
            route: {
                "win_rate": average([1.0 if item["victory"] else 0.0 for item in items]),
                "avg_net_score": average([resource_gain(item)["net_score"] for item in items]),
            }
            for route, items in groups.items()
        }

    return {
        "aggressive": by_route(aggressive),
        "conservative": by_route(conservative),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    nodes = build_node_payloads()
    enemies = build_enemy_catalog()

    print("Running OBS-1: first-node dominance test...")
    obs1 = run_obs1(nodes, enemies)
    (OBS_DIR / "obs1_first_node_dominance.json").write_text(json.dumps(obs1, indent=2), encoding="utf-8")
    print(f"  win_rate_divergence: {obs1['win_rate_divergence']}  confirmed: {obs1['hypothesis_confirmed']}")
    print(f"  {obs1['interpretation']}\n")

    print("Running OBS-2: conservative survivability test...")
    obs2 = run_obs2(nodes, enemies)
    (OBS_DIR / "obs2_conservative_survivability.json").write_text(json.dumps(obs2, indent=2), encoding="utf-8")
    print(f"  conservative win_rate: {obs2['win_rate']}  confirmed: {obs2['hypothesis_confirmed']}")
    print(f"  {obs2['interpretation']}\n")

    print("Running OBS-3: risk payoff sampling (100+ runs)...")
    obs3 = run_obs3(nodes, enemies)
    (OBS_DIR / "obs3_risk_payoff.json").write_text(json.dumps(obs3, indent=2), encoding="utf-8")
    print(f"  win_rate_gap: {obs3['win_rate_gap_aggressive_minus_conservative']}  confirmed: {obs3['hypothesis_confirmed']}")
    print(f"  {obs3['interpretation']}\n")

    combined = {
        "obs1": obs1,
        "obs2": obs2,
        "obs3": obs3,
        "design_signals": _compile_design_signals(obs1, obs2, obs3),
    }
    (OBS_DIR / "obs_combined_summary.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")

    print("OBS experiments complete.")
    print(f"Results written to: {OBS_DIR}")
    print("\n=== Design Signals ===")
    for signal in combined["design_signals"]:
        print(f"  [{signal['severity']}] {signal['signal']}")
    return 0


def _compile_design_signals(obs1: dict, obs2: dict, obs3: dict) -> list[dict]:
    signals = []

    if obs1["hypothesis_confirmed"]:
        signals.append({
            "source": "OBS-1",
            "severity": "HIGH",
            "signal": (
                f"First-node choice creates {obs1['win_rate_divergence']:.0%} win-rate divergence. "
                "Early resource swing strongly influences run economy."
            ),
            "recommended_action": "Preserve early node weight. Ensure first-node options are legible.",
        })
    else:
        signals.append({
            "source": "OBS-1",
            "severity": "LOW",
            "signal": (
                f"First-node divergence is only {obs1['win_rate_divergence']:.0%}. "
                "Tension appears distributed across the route, not front-loaded."
            ),
            "recommended_action": "Consider amplifying first-node resource swing to strengthen early stakes.",
        })

    if obs2["hypothesis_confirmed"]:
        signals.append({
            "source": "OBS-2",
            "severity": "OK",
            "signal": (
                f"Conservative win rate = {obs2['win_rate']:.0%}. "
                "Risk avoidance is not a safe default — players must engage with risk."
            ),
            "recommended_action": "No immediate action. Monitor if conservative win rate drops below 0.3.",
        })
    else:
        signals.append({
            "source": "OBS-2",
            "severity": "HIGH",
            "signal": (
                f"Conservative win rate = {obs2['win_rate']:.0%}. "
                "Safe play wins too reliably — risk-taking has insufficient incentive."
            ),
            "recommended_action": "Increase passive attrition (food decay, radiation exposure) on cautious paths.",
        })

    if obs3["hypothesis_confirmed"]:
        signals.append({
            "source": "OBS-3",
            "severity": "HIGH",
            "signal": (
                f"Aggressive play out-performs conservative by "
                f"win_gap={obs3['win_rate_gap_aggressive_minus_conservative']:+.0%}, "
                f"net_score_gap={obs3['net_score_gap_aggressive_minus_conservative']:+.1f}. "
                "High-risk options are over-rewarding relative to their cost."
            ),
            "recommended_action": (
                "Reduce aggressive payoff or increase aggressive penalty before next PT round. "
                "Target win_gap < 0.2 and net_score_gap < 2.0."
            ),
        })
    else:
        signals.append({
            "source": "OBS-3",
            "severity": "OK",
            "signal": (
                f"Risk vs conservative balance is within tolerance: "
                f"win_gap={obs3['win_rate_gap_aggressive_minus_conservative']:+.0%}, "
                f"net_score_gap={obs3['net_score_gap_aggressive_minus_conservative']:+.1f}."
            ),
            "recommended_action": "No rebalancing needed. Proceed to PT-2 with current settings.",
        })

    return signals


if __name__ == "__main__":
    raise SystemExit(main())
