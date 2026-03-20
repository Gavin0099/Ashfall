import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

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
            res = run_sim(strat, num_steps=30, seed=i*111, luck_mode="normal")
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

    # KPI 7: Gameplay Drift - Impact Analysis (v2.6)
    print(f"\n[KPI] Gameplay Drift & Impact Analysis (Win Contribution)")
    all_perks = set([p for s in strategies for r in results[s] for p in r['perks']])
    drift_found = False
    
    total_runs_list = [r for s in strategies for r in results[s]]
    
    impact_data = []
    for p_id in all_perks:
        runs_with = [r for r in total_runs_list if p_id in r['perks']]
        runs_without = [r for r in total_runs_list if p_id not in r['perks']]
        
        wr_with = sum(1 for r in runs_with if r['survived']) / len(runs_with) if runs_with else 0
        wr_without = sum(1 for r in runs_without if r['survived']) / len(runs_without) if runs_without else 0
        win_contrib = wr_with - wr_without
        
        avg_step_with = sum(r['step'] for r in runs_with) / len(runs_with) if runs_with else 0
        avg_step_without = sum(r['step'] for r in runs_without) / len(runs_without) if runs_without else 0
        step_delta = avg_step_with - avg_step_without
        
        pick_rate = len(runs_with) / len(total_runs_list)
        impact_data.append({
            "id": p_id, 
            "pick_rate": pick_rate, 
            "win_contrib": win_contrib,
            "step_delta": step_delta
        })
    
    # Sort by impact
    for d in sorted(impact_data, key=lambda x: x['win_contrib'], reverse=True):
        p_id = d['id']
        rate = d['pick_rate']
        contrib = d['win_contrib']
        delta = d['step_delta']
        
        status = "Healthy"
        if rate > 0.8:
            status = "CRITICAL_DRIFT (Meta Collapse)"
            drift_found = True
        elif rate > 0.6:
            status = "WARNING (Dominant Meta)"
            drift_found = True
        elif contrib > 0.20:
            status = "WARNING (High Impact Drift)"
            drift_found = True
        elif contrib < -0.15:
            status = "WARNING (Trap Perk / Negative Impact)"
            drift_found = True
            
        print(f"  -- Perk '{p_id:16}': Pick:{rate:5.1%} | WinContrib:{contrib:+6.1%} | StepDelta:{delta:+4.1f} [{status}]")
    
    if not drift_found:
        print("\n  >> OK: All perks are within stability and impact bounds.")

if __name__ == "__main__":
    analyze_build_v2()
