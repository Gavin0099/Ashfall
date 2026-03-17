import json
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState
from src.event_engine import resolve_event_choice
from scripts.play_cli_run import build_node_payloads, build_enemy_catalog, build_event_catalog

def run_obs_1(first_choice_idx: int):
    seed = 101
    nodes = build_node_payloads()
    enemies = build_enemy_catalog()
    events = build_event_catalog(seed)
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    
    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies)
    
    # Use a dummy player with standard stats
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1)
    run = engine.create_run(player, seed=seed)
    
    # Step 1: Start -> North Scrapyard
    node = engine.move_to(run, "node_north_1")
    
    # Scrapyard Event: evt_scrapyard
    # Choice 0: Salvage
    # Choice 1: Skip
    event_id = "evt_scrapyard"
    if event_id in events:
        resolve_event_choice(run.player, events[event_id], first_choice_idx, engine.rng)
    
    # Predefined Route: Tunnel -> Checkpoint -> Approach -> Final
    route = ["node_north_2", "node_mid", "node_approach", "node_final"]
    for target in route:
        if run.ended:
            break
        node = engine.move_to(run, target)
        if not run.ended:
            # Tunnel: evt_tunnel
            # Checkpoint: evt_military_checkpoint
            if target == "node_north_2":
                event_id = "evt_tunnel"
            elif target == "node_mid":
                event_id = "evt_military_checkpoint"
            else:
                event_id = None
                
            if event_id and event_id in events:
                resolve_event_choice(run.player, events[event_id], 0, engine.rng)
                
    return {
        "victory": run.victory,
        "end_reason": run.end_reason,
        "hp": run.player.hp,
        "food": run.player.food,
        "ammo": run.player.ammo,
        "radiation": run.player.radiation
    }

if __name__ == "__main__":
    print("Running OBS-1: First-node Dominance Test (Seed 101)")
    
    print("\nScenario A: First Choice = Skip (Index 1)")
    result_a = run_obs_1(1)
    print(json.dumps(result_a, indent=2))
    
    print("\nScenario B: First Choice = Salvage (Index 0)")
    result_b = run_obs_1(0)
    print(json.dumps(result_b, indent=2))
    
    if result_a["victory"] != result_b["victory"]:
        print("\n[RESULT] FIRST-NODE DOMINANCE CONFIRMED. Early resource swing changed outcome.")
    else:
        print("\n[RESULT] NO DOMINANCE DETECTED. Outcome identical despite choice change.")
