#!/usr/bin/env python3
"""run_exp3_character_background.py - EXP-3: Character Background prototype.

Design question:
  Does a passive background chosen at run start make the player ask
  "which route fits this background?" - strengthening route tension
  without replacing it?

Backgrounds (all passive, no leveling):
  none        - control baseline
  scavenger   - any positive resource gain from event effects: +1 to that resource
  soldier     - after surviving combat (not combat_death): +1 hp (max 10)
  pathfinder  - first node entry (not start) costs 0 food (skip node food cost once)
  medic       - medkit heal value: +1 (3 -> 4 hp per medkit use)

Groups (background x route):
  For each background: simulate north route (node_north_1->north_2->mid->final)
  and south route (node_south_1->south_2->mid->final).
  All with option_index=0 (aggressive) - same decision policy across all groups.

Seeds: 101..150 (50 seeds per group)

Output: output/analytics/exp/exp3_character_background.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
)
from src.combat_engine import CombatEngine
from src.run_engine import RunEngine, build_map, _enemy_from_payload
from src.state_models import PlayerState, RunState

OUTPUT_DIR = ROOT / "output" / "analytics" / "exp"

BACKGROUNDS = ("none", "scavenger", "soldier", "pathfinder", "medic")
ROUTES = {
    "north": ["node_north_1", "node_north_2", "node_mid", "node_final"],
    "south": ["node_south_1", "node_south_2", "node_mid", "node_final"],
}


@dataclass
class RunRecord:
    seed: int
    background: str
    route: str
    victory: bool = False
    end_reason: str = ""
    steps: int = 0
    final_hp: int = 0
    final_food: int = 0
    final_ammo: int = 0
    final_radiation: int = 0
    background_activations: int = 0   # times the background passive triggered


def _initial_player() -> PlayerState:
    return PlayerState(hp=10, food=6, ammo=4, medkits=2, scrap=0, radiation=0)


# ---------------------------------------------------------------------------
# Background-aware CombatEngine wrapper
# ---------------------------------------------------------------------------

class BackgroundCombatEngine(CombatEngine):
    """CombatEngine subclass that applies background passives during combat."""

    def __init__(self, seed: int, background: str) -> None:
        super().__init__(seed)
        self.background = background
        self.activations = 0

    def player_use_medkit(self, player: PlayerState) -> int:
        """Medic: heal 4 instead of 3."""
        if player.medkits <= 0:
            raise ValueError("Cannot use medkit without medkits")
        player.medkits -= 1
        heal = 4 if self.background == "medic" else 3
        player.hp += heal
        if self.background == "medic":
            self.activations += 1
        return heal


# ---------------------------------------------------------------------------
# Background-aware RunEngine wrapper
# ---------------------------------------------------------------------------

class BackgroundRunEngine(RunEngine):
    """RunEngine wrapper that applies background passives around core calls."""

    def __init__(self, map_state, seed: int, event_catalog, enemy_catalog, background: str) -> None:
        super().__init__(map_state, seed, event_catalog=event_catalog, enemy_catalog=enemy_catalog)
        self.background = background
        self.bg_activations = 0
        self._pathfinder_used = False   # tracks first-travel bonus

    def apply_node_cost(self, run: RunState, node) -> None:
        """Pathfinder: skip food cost on first non-start node entry."""
        if self.background == "pathfinder" and not self._pathfinder_used and not node.is_start:
            self._pathfinder_used = True
            self.bg_activations += 1
            # Skip the first node's food deduction while preserving other costs.
            cost = dict(node.resource_cost) if node.resource_cost else {"food": 1}
            patched_cost = {k: (0 if k == "food" else v) for k, v in cost.items()}
            for key, amount in patched_cost.items():
                if amount <= 0:
                    continue
                if key == "food":
                    run.player.food = max(0, run.player.food - amount)
                elif key == "hp":
                    run.player.hp = max(0, run.player.hp - amount)
                elif key == "ammo":
                    run.player.ammo = max(0, run.player.ammo - amount)
                elif key == "medkits":
                    run.player.medkits = max(0, run.player.medkits - amount)
                elif key == "scrap":
                    run.player.scrap = max(0, run.player.scrap - amount)
                elif key == "radiation":
                    run.player.radiation = max(0, run.player.radiation - amount)
        else:
            super().apply_node_cost(run, node)

    def resolve_node_event(self, node, run: RunState, option_index: int = 0) -> dict:
        outcome = super().resolve_node_event(node, run, option_index=option_index)

        # Scavenger: +1 to any positive resource gain from event effects
        if self.background == "scavenger":
            effects = outcome.get("effects", {})
            bonus_applied = False
            for key in ("food", "ammo", "scrap", "medkits"):
                if effects.get(key, 0) > 0 and not bonus_applied:
                    if key == "food":
                        run.player.food += 1
                    elif key == "ammo":
                        run.player.ammo += 1
                    elif key == "scrap":
                        run.player.scrap += 1
                    elif key == "medkits":
                        run.player.medkits += 1
                    bonus_applied = True
                    self.bg_activations += 1
                    break

        # Soldier: +1 hp after surviving combat (not already dead)
        if self.background == "soldier":
            combat_result = outcome.get("combat", {})
            if outcome.get("combat_triggered") and not run.ended:
                if combat_result.get("victory", False):
                    run.player.hp = min(10, run.player.hp + 1)
                    self.bg_activations += 1

        return outcome

    def resolve_combat(self, run: RunState) -> dict:
        """Use BackgroundCombatEngine for medic passive."""
        if not self.enemy_catalog:
            return {"skipped": True, "reason": "enemy_catalog_empty"}
        enemy_id = self.rng.choice(sorted(self.enemy_catalog.keys()))
        enemy = _enemy_from_payload(self.enemy_catalog[enemy_id])

        combat_seed = run.map_seed + len(run.visited_nodes)
        engine = BackgroundCombatEngine(seed=combat_seed, background=self.background)
        result = engine.run_auto_combat(run.player, enemy)
        self.bg_activations += engine.activations

        if not result["victory"]:
            run.end(victory=False, reason="combat_death")
        return {"skipped": False, "enemy_id": enemy_id, **result}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def simulate_run(seed: int, background: str, route: list[str],
                 node_payloads: dict, enemy_catalog: dict) -> RunRecord:
    event_catalog = build_event_catalog(seed)
    map_state = build_map(node_payloads, "node_start")
    engine = BackgroundRunEngine(
        map_state, seed, event_catalog=event_catalog,
        enemy_catalog=enemy_catalog, background=background
    )

    player = _initial_player()
    run = engine.create_run(player, seed)

    record = RunRecord(seed=seed, background=background, route=route[0].split("_")[1])

    # resolve start node event
    start_node = map_state.get_node("node_start")
    engine.resolve_node_event(start_node, run, option_index=0)

    step = 0
    for next_node_id in route:
        if run.ended:
            break
        step += 1
        node = engine.move_to(run, next_node_id)
        if run.ended:
            break
        engine.resolve_node_event(node, run, option_index=0)

    record.steps = step
    record.victory = run.victory
    record.end_reason = run.end_reason or ""
    record.final_hp = run.player.hp
    record.final_food = run.player.food
    record.final_ammo = run.player.ammo
    record.final_radiation = run.player.radiation
    record.background_activations = engine.bg_activations
    return record


def run_group(background: str, route_name: str, seeds: list[int],
              node_payloads: dict, enemy_catalog: dict) -> list[RunRecord]:
    route = ROUTES[route_name]
    return [
        simulate_run(seed, background, route, node_payloads, enemy_catalog)
        for seed in seeds
    ]


def summarize(records: list[RunRecord]) -> dict[str, Any]:
    n = len(records)
    wins = sum(1 for r in records if r.victory)
    deaths = [r for r in records if not r.victory]
    rad_deaths = sum(1 for r in deaths if "radiation" in r.end_reason)
    starv_deaths = sum(1 for r in deaths if "starv" in r.end_reason)
    combat_deaths = sum(1 for r in deaths if "combat" in r.end_reason)
    activations = [r.background_activations for r in records]
    return {
        "n": n,
        "win_rate": round(wins / n, 3),
        "radiation_death_rate": round(rad_deaths / n, 3),
        "starvation_death_rate": round(starv_deaths / n, 3),
        "combat_death_rate": round(combat_deaths / n, 3),
        "avg_final_hp": round(sum(r.final_hp for r in records) / n, 2),
        "avg_final_food": round(sum(r.final_food for r in records) / n, 2),
        "avg_final_ammo": round(sum(r.final_ammo for r in records) / n, 2),
        "avg_bg_activations": round(sum(activations) / n, 2),
    }


def main() -> int:
    seeds = list(range(101, 151))
    node_payloads = build_node_payloads()
    enemy_catalog = build_enemy_catalog()

    print("EXP-3: Character Background experiment")
    print(f"  Seeds: {seeds[0]}..{seeds[-1]}  Backgrounds: {BACKGROUNDS}  Routes: north/south")

    results: dict[str, Any] = {}

    for bg in BACKGROUNDS:
        for route_name in ("north", "south"):
            key = f"{bg}_{route_name}"
            records = run_group(bg, route_name, seeds, node_payloads, enemy_catalog)
            summary = summarize(records)
            results[key] = summary
            print(f"  {key:30s}: win={summary['win_rate']:.0%}  "
                  f"rad={summary['radiation_death_rate']:.0%}  "
                  f"starv={summary['starvation_death_rate']:.0%}  "
                  f"combat={summary['combat_death_rate']:.0%}  "
                  f"bg_activations={summary['avg_bg_activations']}")

    # --- Route affinity analysis ---
    # For each background, which route wins more?
    print("\n  Route affinity (win_rate north vs south):")
    route_affinity: dict[str, Any] = {}
    for bg in BACKGROUNDS:
        north_wr = results[f"{bg}_north"]["win_rate"]
        south_wr = results[f"{bg}_south"]["win_rate"]
        preferred = "north" if north_wr > south_wr else "south" if south_wr > north_wr else "tie"
        delta = round(north_wr - south_wr, 3)
        route_affinity[bg] = {
            "north_win_rate": north_wr,
            "south_win_rate": south_wr,
            "preferred_route": preferred,
            "win_delta_north_minus_south": delta,
        }
        print(f"  {bg:12s}: north={north_wr:.0%}  south={south_wr:.0%}  preferred={preferred}  delta={delta:+.3f}")

    # --- Delta vs baseline (none background) ---
    print("\n  Win rate delta vs baseline (none):")
    deltas: dict[str, Any] = {}
    for bg in BACKGROUNDS:
        if bg == "none":
            continue
        d: dict[str, Any] = {}
        for route_name in ("north", "south"):
            key = f"{bg}_{route_name}"
            base_key = f"none_{route_name}"
            delta_wr = round(results[key]["win_rate"] - results[base_key]["win_rate"], 3)
            d[f"delta_win_{route_name}"] = delta_wr
            print(f"  {bg:12s} {route_name}: {delta_wr:+.3f}")
        deltas[bg] = d

    impactful_backgrounds = [
        bg
        for bg, delta in deltas.items()
        if abs(delta["delta_win_north"]) >= 0.1 or abs(delta["delta_win_south"]) >= 0.1
    ]
    verdict = {
        "status": "SUPPORTED" if impactful_backgrounds else "WEAK",
        "impactful_backgrounds": impactful_backgrounds,
        "summary": (
            "Character backgrounds create meaningful route-specific impact in at least one case."
            if impactful_backgrounds
            else "Character backgrounds do not create meaningful route-specific impact."
        ),
    }

    output = {
        "experiment": "EXP-3",
        "description": "Character Background: none / scavenger / soldier / pathfinder / medic",
        "seeds": f"{seeds[0]}..{seeds[-1]}",
        "n_per_group": len(seeds),
        "backgrounds": {bg: {"north": results[f"{bg}_north"], "south": results[f"{bg}_south"]}
                        for bg in BACKGROUNDS},
        "route_affinity": route_affinity,
        "deltas_vs_none": deltas,
        "hypothesis": (
            "Each background should show route affinity: "
            "a background that amplifies a route's strength should win more on that route. "
            "Scavenger->north (ammo/food), Soldier->north (combat), "
            "Pathfinder->south (food-safe), Medic->neutral or combat-heavy."
        ),
        "verdict": verdict,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "exp3_character_background.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults written to {out_path}")

    # --- Verdict ---
    print("\nVerdict:")
    if impactful_backgrounds:
        print(f"  SUPPORTED - backgrounds with >=10% win-rate impact vs baseline: {impactful_backgrounds}")
    else:
        print("  WEAK - no background changes route win rate by >= 10% vs baseline")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
