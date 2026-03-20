import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.run_simulator import run_sim

# --- GUARDRAIL DEFINITION ---
GUARDRAILS = {
    "survival_floor_steps": 15,    # In bad luck, must survive at least X steps
    "max_winrate_disparity": 0.15, # Max survival rate difference between archetypes
    "min_synergy_reach_rate": 0.7  # % of runs that should reach T2 by step 20
}

def analyze_build_v2():
    strategies = ["survival", "scavenge", "hybrid_scav_surv"]
    iterations = 30
    results = {s: [] for s in strategies}
    
    print(f"--- ASHFALL BALANCE AUTO-ANALYSIS (V2 Control Loop) ---")
    print(f"Running {iterations} iterations per strategy...\n")
    
    for strat in strategies:
        for i in range(iterations):
            res = run_sim(strat, num_steps=30, seed=i*111)
            results[strat].append(res)
            
    # KPI 1: Winrate Disparity
    winrates = {s: sum(1 for r in results[s] if r['survived'])/iterations for s in strategies}
    max_w = max(winrates.values())
    min_w = min(winrates.values())
    disparity = max_w - min_w
    
    print(f"[KPI] Winrate Disparity: {disparity:.1%} (Limit: {GUARDRAILS['max_winrate_disparity']:.1%})")
    if disparity > GUARDRAILS["max_winrate_disparity"]:
        print("  >> WARNING: System is diverging! Some builds are significantly weaker.")
    else:
        print("  >> OK: Builds are within healthy competitive bounds.")

    # KPI 2: Death Taxonomy Distribution (v2.2 Diagnosis)
    print(f"\n[KPI] Death Taxonomy Distribution (Why are they dying?)")
    for strat in strategies:
        reasons = [r['stats']['death_reason'] for r in results[strat] if not r['survived']]
        if reasons:
            from collections import Counter
            dist = Counter(reasons)
            dist_str = ", ".join([f"{k}: {v/len(reasons):.0%}" for k, v in dist.most_common()])
            print(f"  {strat:16} | {dist_str}")
        else:
            print(f"  {strat:16} | No deaths recorded")

    # KPI 3: Survival Floor Stress Test
    print(f"\n[KPI] Survival Floor Stress Test (Luck Mode: Bad)")
    floor_ok = True
    for strat in strategies:
        stress_runs = []
        for i in range(5):
            res = run_sim(strat, num_steps=30, seed=i*777, luck_mode="bad")
            stress_runs.append(res)
        avg_lifespan = sum(r['step'] for r in stress_runs) / 5
        print(f"  {strat:16} | Avg Lifespan: {avg_lifespan:.1f} steps")
        if avg_lifespan < GUARDRAILS["survival_floor_steps"]:
            floor_ok = False
            
    if not floor_ok:
        print(f"  >> WARNING: Survival floor below {GUARDRAILS['survival_floor_steps']} steps! Needs bottom-up protection.")
    else:
        print(f"  >> OK: All builds meet the survival floor.")

    # KPI 3: Synergy Reach Rate
    for strat in strategies:
        reached = sum(1 for r in results[strat] if any("_T2" in k for k in r['stats']['synergy_times']))
        rate = reached / iterations
        print(f"\n[KPI] Synergy Reach Rate ({strat}): {rate:.1%} (Target: {GUARDRAILS['min_synergy_reach_rate']:.1%})")
        if rate < GUARDRAILS["min_synergy_reach_rate"]:
            print(f"  >> WARNING: Synergy T2 is too hard to reach! Archetype scaling too slow.")
            
    # KPI 6: Bridge Perk Audit (v2.2 Governance)
    print(f"\n[KPI] Bridge Perk Audit (Are they over-universal?)")
    bridge_ids = ["scout_mechanic"] # For now
    for b_id in bridge_ids:
        picks = sum(1 for s in strategies for r in results[s] if b_id in r['perks'])
        total_runs = len(strategies) * iterations
        pick_rate = picks / total_runs
        
        # Survival impact
        surv_with = sum(1 for s in strategies for r in results[s] if b_id in r['perks'] and r['survived'])
        surv_without = sum(1 for s in strategies for r in results[s] if b_id not in r['perks'] and r['survived'])
        
        print(f"  {b_id:16} | Pick Rate: {pick_rate:.1%} | Survival Impact: {surv_with - surv_with:.1f} (Δ)") # Simplified
        if pick_rate > 0.6:
            print(f"  >> WARNING: Bridge Perk '{b_id}' is too universal! Pick rate is {pick_rate:.1%}.")

if __name__ == "__main__":
    analyze_build_v2()
