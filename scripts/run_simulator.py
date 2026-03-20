import sys
import os
import random
from typing import List, Dict, Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.run_engine import RunEngine
from src.state_models import PlayerState, CharacterProfile, MapState, NodeState
from src.meta_progression import MetaProfile
from src.difficulty import build_starting_player
from src.modifiers import ModifierRegistry, apply_modifier

def create_mock_map(num_nodes: int = 100) -> MapState:
    nodes = {}
    for i in range(num_nodes):
        node_id = f"node_{i}"
        next_id = f"node_{i+1}" if i < num_nodes - 1 else None
        nodes[node_id] = NodeState(
            id=node_id,
            node_type="resource" if i % 3 != 0 else "combat",
            connections=[next_id] if next_id else [],
            event_pool=["evt_scavenge_basic"],
            is_start=(i == 0),
            is_final=(i == num_nodes - 1)
        )
    return MapState(nodes=nodes, start_node_id="node_0", final_node_id=f"node_{num_nodes-1}")

class SimulationPlayer:
    def __init__(self, strategy: str = "random"):
        self.strategy = strategy # "random", "combat", "scavenge", "survival", "hybrid_scav_surv"
        
    def select_perk(self, options: List[Dict[str, Any]], current_step: int) -> str:
        if not options: return None
        
        if self.strategy == "random":
            return random.choice(options)['id']
            
        # Determine current target tags based on strategy and time
        target_strat = self.strategy
        if self.strategy == "hybrid_scav_surv":
            # Start scavenge, pivot to survival after step 20
            target_strat = "scavenge" if current_step < 20 else "survival"

        tag_map = {
            "combat": ["combat", "efficiency", "hp", "ammo", "speed"],
            "scavenge": ["scavenge", "economy", "repair", "loot", "luck", "tech"],
            "survival": ["survival", "support", "exploration", "food", "hp", "radiation", "healing"]
        }
        
        target_tags = tag_map.get(target_strat, [])
        scored_options = []
        for opt in options:
            score = 0
            # Support both primary_tag (string or list) and secondary_tags
            p_tag = opt.get("primary_tag")
            tags = []
            if isinstance(p_tag, list): tags.extend(p_tag)
            elif p_tag: tags.append(p_tag)
            tags.extend(opt.get("secondary_tags", []))
            
            for t in tags:
                if t in target_tags:
                    score += 1
            scored_options.append((score, opt['id']))
            
        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

def get_death_taxonomy(run, i, stats) -> str:
    """Categorizes the reason for death into a diagnostic taxonomy."""
    hp_history = stats["history"]["hp"]
    food_history = stats["history"]["food"]
    
    # 1. Hunger Collapse
    if run.player.food <= 0:
        return "HUNGER_COLLAPSE"
        
    # 2. Combat Spike (Sudden massive damage)
    if len(hp_history) >= 2:
        last_hp = hp_history[-1]
        prev_hp = hp_history[-2]
        if prev_hp - last_hp > run.player.max_hp * 0.4:
            return "COMBAT_SPIKE"
            
    # 3. Attrition Crisis (Long term low HP)
    if len(hp_history) >= 5:
        recent_avg = sum(hp_history[-5:]) / 5
        if recent_avg < run.player.max_hp * 0.25:
            return "ATTRITION_CRISIS"
            
    # 4. Synergy Miss (Bad build scaling)
    t1_synergies = [k for k in stats["synergy_times"].keys() if "_T1" in k]
    if run.player.character.level >= 5 and len(t1_synergies) == 0:
        return "SYNERGY_MISS"
        
    return "GENERAL_FAILURE"

def run_sim(player_strategy: str, num_steps: int = 30, seed: int = 42, luck_mode: str = "normal"):
    random.seed(seed)
    mock_map = create_mock_map(num_nodes=num_steps + 5)
    engine = RunEngine(map_state=mock_map, seed=seed)
    
    char = CharacterProfile(
        display_name=f"Sim_{player_strategy}",
        background_id="technician",
        traits=["adaptive"],
        special={"strength": 6, "perception": 6, "endurance": 6, "charisma": 6, "intelligence": 6, "agility": 6, "luck": 6},
        xp=0, level=1, perks=[]
    )
    
    player = build_starting_player("normal", char, MetaProfile())
    player.base_max_food = 30 # Super Tuning v2.1
    player.recompute_stats()
    
    run = engine.create_run(player, seed)
    sim_player = SimulationPlayer(player_strategy)
    
    stats = {
        "steps": 0, "xp_gained": 0, "perks_count": 0,
        "death_reason": None,
        "death_snapshot": None,
        "decision_trace": [], # List of {step, options, picked}
        "history": {"scrap": [], "food": [], "hp": []},
        "synergy_times": {}
    }
    
    for i in range(num_steps):
        # Log History
        stats["history"]["scrap"].append(run.player.scrap)
        stats["history"]["food"].append(run.player.food)
        stats["history"]["hp"].append(run.player.hp)

        if run.player.hp <= 0:
            # Record Death Taxonomy (v2.2)
            stats["death_reason"] = get_death_taxonomy(run, i, stats)
            
            # Record Death Snapshot
            from src.modifiers import get_modifier_breakdown
            stats["death_snapshot"] = {
                "step": i,
                "player": run.player.to_dict(),
                "breakdown": get_modifier_breakdown(run.player),
                "last_node": engine.map_state.get_node(run.current_node).node_type
            }
            return {"survived": False, "step": i, "state": run.player.to_dict(), "stats": stats, "perks": run.player.character.perks[:]}
            
        # 1. Level Up (Super Tuning v2.1)
        xp_thresholds = [0, 70, 150, 300, 500, 800]
        cur_lvl = run.player.character.level
        target_xp = xp_thresholds[cur_lvl] if cur_lvl < len(xp_thresholds) else 4000
        
        if run.player.character.xp >= target_xp:
            options = ModifierRegistry.get_available_perks(run.player, count=3, target_level=cur_lvl + 1)
            options = [p for p in options if p['id'] not in run.player.character.perks]
            choice_id = sim_player.select_perk(options, i)
            
            # Record Decision Trace
            stats["decision_trace"].append({
                "step": i,
                "options": [p['id'] for p in options],
                "picked": choice_id
            })
            
            if choice_id:
                run.player.character.perks.append(choice_id)
                run.player.character.level += 1
                run.player.recompute_stats()
                stats["perks_count"] += 1
                
                # Check for synergy lock-in
                bonuses = ModifierRegistry.get_tier_bonuses(run.player)
                for b in bonuses:
                    key = f"{b['archetype']}_T{b['threshold']}"
                    if key not in stats["synergy_times"]:
                        stats["synergy_times"][key] = i
        
        # 2. Travel
        current_node = engine.map_state.get_node(run.current_node)
        if current_node.connections:
            run.current_node = current_node.connections[0]
            run.depth += 1
            stats["steps"] += 1
            
            # Survival mechanics
            food_drain = apply_modifier(run.player, "food_drain_multiplier", 1.0)
            run.player.food -= food_drain
            if run.player.food < 0:
                run.player.hp -= 1
                run.player.food = 0
                
            # Resource gain (Luck Mode affects Range)
            if current_node.node_type == "resource":
                scavenge_bonus = apply_modifier(run.player, "scrap_bonus", 0)
                base_scrap = random.randint(2, 5) if luck_mode == "normal" else 2
                run.player.scrap += base_scrap + int(scavenge_bonus)
                
                food_min, food_max = (1, 4) if luck_mode == "normal" else (1, 2)
                food_gain = random.randint(food_min, food_max)
                if player_strategy == "survival": food_gain += 1
                run.player.food = min(run.player.max_food, run.player.food + food_gain)
                
            # Combat simulation
            if current_node.node_type == "combat":
                dmg_min, dmg_max = (1, 4) if luck_mode == "normal" else (3, 5)
                damage = random.randint(dmg_min, dmg_max)
                dr = apply_modifier(run.player, "damage_reduction", 0)
                run.player.hp -= max(0, damage - int(dr))
                
                # Victory Recovery (v2.2 Context)
                # Helps test medkit_heal_bonus and "Last Stand" protection
                heal_base = 1
                heal_mod = apply_modifier(run.player, "medkit_heal_bonus", 0)
                run.player.hp = min(run.player.max_hp, run.player.hp + heal_base + int(heal_mod))
                
                xp_gain = random.randint(40, 70)
            else:
                xp_gain = random.randint(20, 35)
                
            run.player.character.xp += xp_gain
            stats["xp_gained"] += xp_gain
        else:
            break
            
    return {"survived": True, "step": num_steps, "state": run.player.to_dict(), "stats": stats, "perks": run.player.character.perks[:]}

def main():
    strategies = ["survival", "scavenge", "hybrid_scav_surv"]
    iterations = 50
    results = {}
    
    print(f"Starting Balance Lab v2 ({iterations} iterations per strategy)...")
    
    for strat in strategies:
        results[strat] = []
        for i in range(iterations):
            res = run_sim(strat, num_steps=30, seed=i*2024)
            results[strat].append(res)
            
    # --- Causal Analysis ---
    print("\n" + "="*110)
    print(f"{'STRATEGY':16} | {'SURVIVE':7} | {'AVG STEP':8} | {'TOP DEATH NODE':15} | {'PERK SYNERGY T1/T2'}")
    print("-" * 110)
    
    for strat, data in results.items():
        survived_count = sum(1 for r in data if r['survived'])
        avg_step = sum(r['step'] for r in data) / iterations
        
        # Death snapshot analysis
        death_nodes = [r['stats']['death_snapshot']['last_node'] for r in data if not r['survived'] and r['stats']['death_snapshot']]
        top_death_node = "N/A"
        if death_nodes:
            from collections import Counter
            top_death_node = Counter(death_nodes).most_common(1)[0][0]
            
        # Synergy timing
        t1_times = []
        t2_times = []
        for r in data:
            for k, step in r['stats']['synergy_times'].items():
                if "_T2" in k: t2_times.append(step)
                elif "_T1" in k: t1_times.append(step)
        
        avg_t1 = sum(t1_times)/len(t1_times) if t1_times else 0
        avg_t2 = sum(t2_times)/len(t2_times) if t2_times else 0
        sync_info = f"T1:{avg_t1:2.0f} / T2:{avg_t1+avg_t2:2.0f}" # Cumulative relative to start
        
        print(f"{strat:16} | {survived_count/iterations:6.1%} | {avg_step:8.1f} | {top_death_node:15} | {sync_info}")
    print("="*110)

    # Decision Trace Sample (Scavenge)
    print("\n[DIAGNOSTIC] Decision Trace for Scavenge (Run 1):")
    scav_sample = results['scavenge'][0]['stats']['decision_trace']
    for d in scav_sample:
        print(f"  Step {d['step']:2}: Options {d['options']} -> Picked: {d['picked']}")

if __name__ == "__main__":
    main()
