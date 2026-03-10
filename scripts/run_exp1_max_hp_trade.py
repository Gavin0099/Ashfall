#!/usr/bin/env python3
"""EXP-1: Explicit Irreversible Trade — max_hp sacrifice for short-term survival.

Design intent
-------------
Tests whether offering players an explicit, permanent trade
(sacrifice 2 max HP in exchange for 3 food) increases meaningful tension
without breaking run viability.

This experiment is self-contained: it does NOT modify state_models.py or
any v0.1 core contracts.  It wraps PlayerState with a thin extension that
tracks max_hp as a ceiling, and simulates the ceiling enforcement after
each resource-gain event.

Experiment design
-----------------
All runs use the same route (north), same starting resources, same seeds.

Group A — Trade accepted:
  At first available node (node_north_1), player takes the max_hp trade:
    max_hp -2, food +3
  All subsequent node options are cautious (option 1).
  After each event, hp is clamped to max_hp.

Group B — Trade declined:
  At first node, player takes the normal cautious option (option 1).
  All subsequent node options are cautious (option 1).
  max_hp stays at 10.

Comparison metrics
------------------
- Win rate
- Avg final hp margin (hp / max_hp — how close to ceiling at end)
- Avg food at end (was the trade "worth it" resource-wise?)
- Primary death cause distribution
- Pressure count

Interpretation thresholds
--------------------------
- If Group A win_rate >= Group B win_rate: trade is viable, not a trap
- If Group A avg_final_food > Group B avg_final_food: food gain pays off
- If Group A has more radiation deaths and Group B more starvation deaths:
  trade shifts death cause toward a different failure mode
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    RoutePlan,
    analyze_failure,
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
    build_warning_signals,
    is_pressure_moment,
)
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState, RunState

EXP_DIR = ROOT / "output" / "analytics" / "exp"
NORTH_ROUTE = ["node_north_1", "node_north_2", "node_mid", "node_final"]

# Trade parameters
TRADE_MAX_HP_DELTA = -2   # permanent ceiling reduction
TRADE_FOOD_GAIN = +3      # immediate food gain

# Seeds: 50 pairs = 100 runs
EXP1_SEEDS = list(range(101, 151))

# Starting player state (same as run_playability_check)
START_HP = 10
START_FOOD = 7
START_AMMO = 3
START_MEDKITS = 1


# ---------------------------------------------------------------------------
# Extended player wrapper
# ---------------------------------------------------------------------------

@dataclass
class PlayerExt:
    """Thin wrapper around PlayerState that tracks max_hp ceiling."""
    player: PlayerState
    max_hp: int = START_HP

    def apply_max_hp_trade(self) -> None:
        """Reduce max_hp permanently and grant food in exchange."""
        self.max_hp = max(1, self.max_hp + TRADE_MAX_HP_DELTA)
        self.player.food += TRADE_FOOD_GAIN
        self.player.food = max(0, self.player.food)
        # Clamp current hp to new ceiling immediately
        self.enforce_ceiling()

    def enforce_ceiling(self) -> None:
        """Ensure current hp never exceeds max_hp."""
        if self.player.hp > self.max_hp:
            self.player.hp = self.max_hp

    @property
    def hp_margin(self) -> float:
        """Ratio of current hp to max_hp (0.0 – 1.0)."""
        if self.max_hp <= 0:
            return 0.0
        return round(self.player.hp / self.max_hp, 3)


# ---------------------------------------------------------------------------
# Run logic
# ---------------------------------------------------------------------------

def run_exp1_plan(
    seed: int,
    nodes: dict,
    enemies: dict,
    take_trade: bool,
    cautious_options: Dict[str, int],
) -> dict:
    """Run one north-route plan for EXP-1.

    take_trade: if True, the first-node option is replaced by the max_hp trade.
    cautious_options: option index per node for all non-trade nodes.
    """
    events = build_event_catalog(seed)
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies)

    start_player = PlayerState(hp=START_HP, food=START_FOOD, ammo=START_AMMO, medkits=START_MEDKITS)
    run = engine.create_run(start_player, seed=seed)
    ext = PlayerExt(player=run.player, max_hp=START_HP)

    # Apply trade at node_north_1 before route simulation if accepted
    trade_applied = False

    pressure_count = 0
    moments: List[dict] = []
    decision_log: List[dict] = []

    for step_index, next_node in enumerate(NORTH_ROUTE):
        if run.ended:
            break

        node = engine.move_to(run, next_node)
        if run.ended:
            # Travel attrition killed the player before the event resolved
            ext.enforce_ceiling()
            break

        # Apply max_hp ceiling after travel
        ext.enforce_ceiling()
        if run.player.is_dead():
            run.end(victory=False, reason="radiation_death" if run.player.radiation > 0 else "event_or_resource_death")
            break

        # Determine option
        if take_trade and not trade_applied and next_node == NORTH_ROUTE[0]:
            # Replace first-node event with the trade
            option_index = 0  # recorded as "option 0" in the decision log
            trade_applied = True
            pre_choice_state = _snapshot(run.player, ext)
            ext.apply_max_hp_trade()
            ext.enforce_ceiling()
            outcome = {
                "event_id": "trade_max_hp",
                "option_index": 0,
                "option_text": f"Sacrifice {abs(TRADE_MAX_HP_DELTA)} max HP for {TRADE_FOOD_GAIN} food",
                "combat_triggered": False,
                "trade_applied": True,
                "effects": {"max_hp": TRADE_MAX_HP_DELTA, "food": TRADE_FOOD_GAIN},
            }
            pressure = True  # this is always a pressure moment
        else:
            option_index = cautious_options.get(next_node, 1)
            event_payload = events[node.event_pool[0]]
            pre_choice_state = _snapshot(run.player, ext)
            warning_signals = build_warning_signals(
                run.player, event_payload, option_index,
                len(NORTH_ROUTE) - len(decision_log) - 1,
            )
            outcome = engine.resolve_node_event(node, run, option_index=option_index)
            ext.enforce_ceiling()
            if run.player.is_dead():
                run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))
            pressure = is_pressure_moment(run, events[outcome["event_id"]], option_index, outcome)

        if pressure:
            pressure_count += 1

        effects = outcome.get("effects", {})
        if not effects and "event_id" in outcome and outcome["event_id"] in events:
            ev_opts = events[outcome["event_id"]].get("options", [])
            effects = ev_opts[option_index].get("effects", {}) if option_index < len(ev_opts) else {}

        entry: dict = {
            "step": len(decision_log) + 1,
            "node": next_node,
            "event_id": outcome.get("event_id", "trade_max_hp"),
            "option_index": option_index,
            "trade_applied": outcome.get("trade_applied", False),
            "pre_choice_state": pre_choice_state,
            "pressure": pressure,
            "combat_triggered": bool(outcome.get("combat_triggered", False)),
            "effects": dict(effects),
            "player_after": _snapshot(run.player, ext),
        }
        decision_log.append(entry)
        moments.append(entry)

    if not run.ended and run.current_node == "node_final":
        run.end(victory=True, reason="reached_final_node")

    failure = analyze_failure(
        decision_log=[{k: v for k, v in e.items() if k != "trade_applied"} for e in decision_log],
        ended=run.ended,
        victory=run.victory,
        end_reason=run.end_reason,
    )

    return {
        "seed": seed,
        "take_trade": take_trade,
        "max_hp_at_end": ext.max_hp,
        "hp_margin": ext.hp_margin,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "pressure_count": pressure_count,
        "player_final": {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "radiation": run.player.radiation,
            "max_hp": ext.max_hp,
        },
        "decision_log": decision_log,
        "failure_analysis": failure,
    }


def _snapshot(player: PlayerState, ext: PlayerExt) -> dict:
    return {
        "hp": player.hp,
        "food": player.food,
        "ammo": player.ammo,
        "medkits": player.medkits,
        "radiation": player.radiation,
        "max_hp": ext.max_hp,
    }


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _count_reasons(results: list[dict]) -> dict[str, int]:
    from collections import defaultdict
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[r.get("end_reason") or "unknown"] += 1
    return dict(counts)


def summarize_group(results: list[dict], label: str) -> dict:
    wins = [r for r in results if r["victory"]]
    losses = [r for r in results if not r["victory"]]
    return {
        "label": label,
        "run_count": len(results),
        "win_rate": average([1.0 if r["victory"] else 0.0 for r in results]),
        "avg_pressure_count": average([float(r["pressure_count"]) for r in results]),
        "avg_final_food": average([float(r["player_final"]["food"]) for r in results]),
        "avg_final_hp": average([float(r["player_final"]["hp"]) for r in results]),
        "avg_max_hp_at_end": average([float(r["max_hp_at_end"]) for r in results]),
        "avg_hp_margin": average([r["hp_margin"] for r in results]),
        "avg_final_radiation": average([float(r["player_final"]["radiation"]) for r in results]),
        "end_reasons": _count_reasons(results),
        "death_reasons": _count_reasons(losses),
        "avg_steps_from_regret_to_death": average(
            [float(r["failure_analysis"].get("steps_from_regret_to_death", 0)) for r in losses]
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    nodes = build_node_payloads()
    enemies = build_enemy_catalog()

    # Cautious options for all nodes (option 1 = safe choice)
    cautious = {node: 1 for node in NORTH_ROUTE}

    group_a: list[dict] = []   # trade accepted
    group_b: list[dict] = []   # trade declined

    print("Running EXP-1: max_hp trade experiment...")
    print(f"  Trade: max_hp {TRADE_MAX_HP_DELTA:+d}, food {TRADE_FOOD_GAIN:+d}")
    print(f"  Seeds: {len(EXP1_SEEDS)} × 2 groups = {len(EXP1_SEEDS) * 2} total runs\n")

    for seed in EXP1_SEEDS:
        group_a.append(run_exp1_plan(seed, nodes, enemies, take_trade=True, cautious_options=cautious))
        group_b.append(run_exp1_plan(seed, nodes, enemies, take_trade=False, cautious_options=cautious))

    summary_a = summarize_group(group_a, "Group A: trade accepted (max_hp -2, food +3)")
    summary_b = summarize_group(group_b, "Group B: trade declined (control)")

    win_delta = round(summary_a["win_rate"] - summary_b["win_rate"], 3)
    food_delta = round(summary_a["avg_final_food"] - summary_b["avg_final_food"], 3)
    pressure_delta = round(summary_a["avg_pressure_count"] - summary_b["avg_pressure_count"], 3)

    # Interpretation
    trade_viable = summary_a["win_rate"] >= summary_b["win_rate"]
    food_gain_pays_off = food_delta > 0
    trade_shifts_death_cause = summary_a["death_reasons"] != summary_b["death_reasons"]

    result = {
        "experiment": "EXP-1 max_hp trade",
        "description": (
            "Tests whether a permanent max_hp sacrifice (+food) increases meaningful tension "
            "and remains a viable player choice. Implemented as a self-contained simulation "
            "experiment without modifying v0.1 core state contracts."
        ),
        "trade_parameters": {
            "max_hp_delta": TRADE_MAX_HP_DELTA,
            "food_gain": TRADE_FOOD_GAIN,
            "trade_node": NORTH_ROUTE[0],
        },
        "seeds_used": EXP1_SEEDS,
        "group_a": summary_a,
        "group_b": summary_b,
        "comparison": {
            "win_rate_delta_A_minus_B": win_delta,
            "avg_food_delta_A_minus_B": food_delta,
            "avg_pressure_delta_A_minus_B": pressure_delta,
        },
        "interpretation": {
            "trade_is_viable": trade_viable,
            "food_gain_pays_off": food_gain_pays_off,
            "trade_shifts_death_cause": trade_shifts_death_cause,
        },
        "design_recommendation": _design_recommendation(
            trade_viable, food_gain_pays_off, win_delta, food_delta, summary_a, summary_b
        ),
    }

    out_path = EXP_DIR / "exp1_max_hp_trade.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("Results:")
    print(f"  Group A win rate: {summary_a['win_rate']:.0%}  (trade accepted)")
    print(f"  Group B win rate: {summary_b['win_rate']:.0%}  (control)")
    print(f"  Win delta: {win_delta:+.0%}")
    print(f"  Food delta at end: {food_delta:+.2f}")
    print(f"  Trade viable: {trade_viable}")
    print(f"  Death cause shift: {trade_shifts_death_cause}")
    print()
    print(f"  Death causes A: {summary_a['death_reasons']}")
    print(f"  Death causes B: {summary_b['death_reasons']}")
    print()
    print("Design recommendation:")
    for line in result["design_recommendation"]:
        print(f"  - {line}")
    print(f"\nResult written to: {out_path}")
    return 0


def _design_recommendation(
    trade_viable: bool,
    food_pays_off: bool,
    win_delta: float,
    food_delta: float,
    a: dict,
    b: dict,
) -> list[str]:
    recs: list[str] = []

    if trade_viable and food_pays_off:
        recs.append(
            "Trade appears balanced: win rate holds and food gain provides real buffer. "
            "Candidate for integration into trade-node event pool."
        )
    elif trade_viable and not food_pays_off:
        recs.append(
            "Trade is viable (win rate holds) but food gain evaporates before run end. "
            "Consider increasing food_gain to +4 or adding a secondary effect (ammo +1)."
        )
    elif not trade_viable and food_pays_off:
        recs.append(
            "Trade reduces win rate despite food gain — max_hp ceiling creates lethal fragility. "
            "Consider reducing max_hp_delta to -1 (instead of -2)."
        )
    else:
        recs.append(
            "Trade is not viable: both win rate and food margin are worse. "
            "EXP-1 in current form should NOT be integrated into the main event catalog."
        )

    if abs(win_delta) < 0.05:
        recs.append(
            "Win rate difference is within noise margin (<5%). "
            "Trade may be roughly neutral — which is acceptable if tension increases."
        )

    radiation_a = a.get("avg_final_radiation", 0)
    radiation_b = b.get("avg_final_radiation", 0)
    if radiation_a > radiation_b + 0.3:
        recs.append(
            "Group A accumulates significantly more radiation, suggesting max_hp trade "
            "leads to riskier follow-up choices or less hp buffer for radiation attrition. "
            "This is an interesting design signal — radiation pressure escalates."
        )

    starvation_a = a.get("death_reasons", {}).get("starvation", 0)
    starvation_b = b.get("death_reasons", {}).get("starvation", 0)
    if starvation_a < starvation_b:
        recs.append(
            f"Starvation deaths drop from {starvation_b} to {starvation_a} when trade is taken. "
            "Food gain is successfully resolving the starvation pressure from OBS-2."
        )

    return recs if recs else ["No strong design signal — expand seed range before deciding."]


if __name__ == "__main__":
    raise SystemExit(main())
