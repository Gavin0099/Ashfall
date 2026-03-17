import sys
from pathlib import Path

file_path = Path("scripts/run_playability_check.py")
content = file_path.read_text(encoding="utf-8")

# 1. Add Optional to typing
content = content.replace("from typing import Dict, List", "from typing import Dict, List, Optional")

# 2. Update RoutePlan
route_plan_old = """@dataclass
class RoutePlan:
    name: str
    seed: int
    route: List[str]
    options: Dict[str, int]
    difficulty: str = "normal\""""

route_plan_new = """@dataclass
class RoutePlan:
    name: str
    seed: int
    route: List[str]
    options: Dict[str, int]
    difficulty: str = "normal"
    background: Optional[str] = None
    travel_mode_strategy: str = "normal"  # normal, rush, careful, dynamic\""""

if route_plan_old in content:
    content = content.replace(route_plan_old, route_plan_new)
else:
    # Try with different line endings or variations if needed, but the above should match the view_file output
    print("Warning: RoutePlan match failed, trying fallback")
    content = content.replace("difficulty: str = \"normal\"", "difficulty: str = \"normal\"\n    background: Optional[str] = None\n    travel_mode_strategy: str = \"normal\"")

# 3. Update run_plan engine setup
old_engine = "run = engine.create_run(build_starting_player(plan.difficulty), seed=plan.seed)"
new_engine = """player = build_starting_player(plan.difficulty)
    player.background = plan.background
    run = engine.create_run(player, seed=plan.seed)"""
content = content.replace(old_engine, new_engine)

# 4. Update move_to loop
old_move = "node = engine.move_to(run, next_node)"
new_move = """# Strategy-based travel mode
        current_travel_mode = plan.travel_mode_strategy
        if plan.travel_mode_strategy == "dynamic":
            if run.player.food <= 2 and (len(plan.route) - len(decision_log) > 1):
                current_travel_mode = "rush"
            elif run.player.hp <= 3:
                current_travel_mode = "careful"
            else:
                current_travel_mode = "normal"
        
        node = engine.move_to(run, next_node, travel_mode=current_travel_mode)"""
content = content.replace(old_move, new_move)

file_path.write_text(content, encoding="utf-8")
print("Successfully updated scripts/run_playability_check.py")
