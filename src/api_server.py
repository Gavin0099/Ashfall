import sys
import random
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState, RunState, CharacterProfile, MapState, EquipmentState
from src.difficulty import build_starting_player
from src.event_templates import instantiate_event_catalog, load_template_catalog
from src.enemy_catalog import load_enemy_catalog
from src.event_engine import get_available_options, resolve_event_choice
from src.meta_progression import MetaProfile, UPGRADE_METADATA, ARCHETYPE_UNLOCK_METADATA, get_upgrade_cost

app = FastAPI(title="Ashfall API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class MoveRequest(BaseModel):
    next_node_id: str

class SelectRequest(BaseModel):
    option_index: int

# --- Global State ---
class GameSession:
    def __init__(self):
        self.engine: Optional[RunEngine] = None
        self.run: Optional[RunState] = None
        self.event_catalog: Dict[str, Any] = {}
        self.meta_path = ROOT / "output" / "meta_profile.json"
        self.meta_profile = MetaProfile.load(self.meta_path)

session = GameSession()

def init_engine(seed: int = 42):
    # Match logic from run_playability_check.py
    node_payloads = {
        "node_start": {"id": "node_start", "node_type": "story", "connections": ["node_fringe_1"], "event_pool": ["evt_departure"], "is_start": True},
        "node_fringe_1": {"id": "node_fringe_1", "node_type": "resource", "connections": ["node_fringe_2"], "event_pool": ["evt_scrapyard", "evt_factory_ruins"]},
        "node_fringe_2": {"id": "node_fringe_2", "node_type": "combat", "connections": ["node_trade_1"], "event_pool": ["evt_tunnel", "evt_mutant_burrow"]},
        "node_trade_1": {"id": "node_trade_1", "node_type": "trade", "connections": ["node_fringe_3"], "event_pool": ["evt_merchant_caravan", "evt_village"]},
        "node_fringe_3": {"id": "node_fringe_3", "node_type": "camp", "connections": ["node_boss_gatekeeper"], "event_pool": ["evt_tech_vault"], "metadata": {"facilities": {"repair_bench": True}}},
        "node_boss_gatekeeper": {"id": "node_boss_gatekeeper", "node_type": "combat", "connections": ["node_deadzone_1"], "event_pool": ["evt_boss_gatekeeper"]},
        "node_deadzone_1": {"id": "node_deadzone_1", "node_type": "resource", "connections": ["node_trade_2"], "event_pool": ["evt_floodplain", "evt_radioactive_orchard"]},
        "node_trade_2": {"id": "node_trade_2", "node_type": "trade", "connections": ["node_deadzone_2"], "event_pool": ["evt_merchant_caravan", "evt_isolated_farm"]},
        "node_deadzone_2": {"id": "node_deadzone_2", "node_type": "combat", "connections": ["node_deadzone_3"], "event_pool": ["evt_sniper_nest", "evt_checkpoint"]},
        "node_deadzone_3": {"id": "node_deadzone_3", "node_type": "camp", "connections": ["node_boss_overseer"], "event_pool": ["evt_tech_vault"]},
        "node_boss_overseer": {"id": "node_boss_overseer", "node_type": "combat", "connections": ["node_final"], "event_pool": ["evt_boss_overseer"]},
        "node_final": {"id": "node_final", "node_type": "story", "connections": [], "event_pool": ["evt_final"], "is_final": True},
    }
    session.map_state = build_map(node_payloads, start_node_id="node_start", final_node_id="node_final")
    
    catalog_path = ROOT / "schemas" / "event_template_catalog.json"
    template_catalog = load_template_catalog(catalog_path)
    session.event_catalog = instantiate_event_catalog(seed, template_catalog)
    
    enemy_catalog = load_enemy_catalog()
    
    session.engine = RunEngine(
        map_state=session.map_state,
        seed=seed,
        event_catalog=session.event_catalog,
        enemy_catalog=enemy_catalog
    )

def state_to_dict(run: RunState) -> Dict[str, Any]:
    p = run.player
    items = {}
    for slot in ["weapon", "armor", "tool"]:
        eq = getattr(p, f"{slot}_slot")
        items[slot] = eq.__dict__ if eq else None

    # Current event info
    current_node = session.map_state.get_node(run.current_node)
    event_id = run.node_events.get(run.current_node)
    
    # If no event in state yet, pick one (unless it's a new node move pending selection)
    if not event_id:
        # In this prototype, we'll pick it if we're at a node
        event_id = random.choice(current_node.event_pool)
        run.node_events[run.current_node] = event_id
    
    event_payload = session.event_catalog.get(event_id)
    options = get_available_options(p, event_payload, run_flags=run.flags)

    return {
        "run": {
            "current_node": run.current_node,
            "visited_nodes": run.visited_nodes,
            "is_ended": run.ended,
            "victory": run.victory,
            "end_reason": run.end_reason,
            "flags": run.flags
        },
        "player": {
            "hp": p.hp,
            "max_hp": p.max_hp,
            "food": p.food,
            "ammo": p.ammo,
            "medkits": p.medkits,
            "scrap": p.scrap,
            "radiation": p.radiation,
            "archetype": p.archetype,
            "character": p.character.to_dict() if p.character else None,
            "items": items
        },
        "event": {
            "id": event_id,
            "title": event_payload.get("id", "Unknown"),
            "description": event_payload.get("options")[0].get("text") if event_payload.get("options") else "No description", # Simplified
            "options": options
        },
        "map": {
            "connections": current_node.connections,
            "node_type": current_node.node_type
        }
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/run/start")
def start_run(seed: int = 42, profile_data: Optional[Dict[str, Any]] = None):
    init_engine(seed)
    
    if profile_data:
        # Translate frontend keys (name, background, traits) to model keys
        char_data = {
            "background_id": profile_data.get("background"),
            "display_name": profile_data.get("name"),
            "traits": profile_data.get("traits", [])
        }
        char = CharacterProfile.from_dict(char_data)
        player = build_starting_player("normal", char, session.meta_profile)
    else:
        player = build_starting_player(meta_profile=session.meta_profile)
        
    session.run = session.engine.create_run(player, seed)
    return state_to_dict(session.run)

@app.get("/api/character/options")
def get_character_options():
    bg_path = ROOT / "data" / "backgrounds.json"
    tr_path = ROOT / "data" / "traits.json"
    
    backgrounds = []
    if bg_path.exists():
        backgrounds = json.loads(bg_path.read_text(encoding="utf-8"))
        
    traits = []
    if tr_path.exists():
        traits = json.loads(tr_path.read_text(encoding="utf-8"))
        
    return {
        "backgrounds": backgrounds,
        "traits": traits
    }

@app.get("/api/run/state")
def get_state():
    if not session.run:
        raise HTTPException(status_code=400, detail="No active run")
    return state_to_dict(session.run)

@app.post("/api/run/move")
def move(req: MoveRequest):
    if not session.run:
        raise HTTPException(status_code=400, detail="No active run")
    try:
        session.engine.move_to(session.run, req.next_node_id)
        return state_to_dict(session.run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/run/select")
def select_option(req: SelectRequest):
    if not session.run:
        raise HTTPException(status_code=400, detail="No active run")
    
    event_id = session.run.node_events.get(session.run.current_node)
    if not event_id:
        raise HTTPException(status_code=400, detail="No active event at current node")
    
    current_node = session.map_state.get_node(session.run.current_node)
    
    try:
        # Use RunEngine for full resolution (including combat)
        outcome = session.engine.resolve_node_event_with_id(
            current_node, 
            session.run, 
            event_id=event_id, 
            option_index=req.option_index
        )
        
        return {
            "outcome": outcome,
            "state": state_to_dict(session.run)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class CampRequest(BaseModel):
    option: int

@app.post("/api/run/camp")
def camp_action(req: CampRequest):
    if not session.run:
        raise HTTPException(status_code=400, detail="No active run")
    res = session.engine.rest_at_camp(session.run, req.option)
    if res["success"]:
        return {"success": True, "detail": res, "state": state_to_dict(session.run)}
    raise HTTPException(status_code=400, detail=res["reason"])

class RefineRequest(BaseModel):
    slot: str
    action: str

@app.post("/api/run/refine")
def refine_action(req: RefineRequest):
    if not session.run:
        raise HTTPException(status_code=400, detail="No active run")
    res = session.engine.refine_equipment(session.run, req.slot, req.action)
    if res["success"]:
        return {"success": True, "detail": res, "state": state_to_dict(session.run)}
    raise HTTPException(status_code=400, detail=res["reason"])

# --- Level Up Endpoints ---
PERKS_DATA = []
perk_file = ROOT / "data" / "perks.json"
if perk_file.exists():
    try:
        with open(perk_file, "r", encoding="utf-8") as f:
            PERKS_DATA = json.load(f)
    except Exception as e:
        print(f"Error loading perks: {e}")

@app.get("/api/run/level_up/options")
def get_levelup_options():
    if not session.run or not session.run.player.character:
        raise HTTPException(status_code=400, detail="No active character")
    
    char = session.run.player.character
    
    # Filter perks: not already owned AND meets requirements
    eligible = []
    for perk in PERKS_DATA:
        if perk["id"] in char.perks: continue
        
        reqs = perk.get("requirements", {})
        # Level requirement (checks if eligible for current level target)
        if char.level + 1 < reqs.get("level", 0): continue
        
        # SPECIAL requirement
        special_reqs = reqs.get("special", {})
        met_special = True
        for stat, bounds in special_reqs.items():
            val = char.special.get(stat, 5)
            if "min" in bounds and val < bounds["min"]: met_special = False; break
            if "max" in bounds and val > bounds["max"]: met_special = False; break
        
        if met_special:
            eligible.append(perk)
            
    # Pick up to 3 random selection
    import random as py_random
    py_random.seed(random.randint(0, 1000000)) # Use shared seed or local for variety
    count = min(3, len(eligible))
    options = py_random.sample(eligible, count) if eligible else []
    return {"options": options}

class LevelUpSelectRequest(BaseModel):
    perk_id: str

@app.post("/api/run/level_up/select")
def select_perk(req: LevelUpSelectRequest):
    if not session.run or not session.run.player.character:
        raise HTTPException(status_code=400, detail="No active character")
    
    char = session.run.player.character
    player = session.run.player
    
    if not char.can_level_up():
        raise HTTPException(status_code=400, detail="Not eligible for level-up")
        
    perk = next((p for p in PERKS_DATA if p["id"] == req.perk_id), None)
    if not perk:
        raise HTTPException(status_code=400, detail="Invalid perk ID")
        
    # Apply perk
    char.perks.append(perk["id"])
    char.level += 1
    
    # Apply effects
    effects = perk.get("effects", {})
    if "max_hp_bonus" in effects:
        player.max_hp += effects["max_hp_bonus"]
        player.hp += effects["max_hp_bonus"]
    if "max_food_bonus" in effects:
        # Placeholder for future expansion
        pass
        
    return {"success": True, "level": char.level, "state": state_to_dict(session.run)}

# --- Meta Progression Endpoints ---
@app.get("/api/meta/profile")
def get_meta_profile():
    return session.meta_profile.to_dict()

@app.get("/api/meta/metadata")
def get_meta_metadata():
    return {
        "upgrades": UPGRADE_METADATA,
        "archetypes": ARCHETYPE_UNLOCK_METADATA,
        "upgrade_costs": {lvl: get_upgrade_cost(lvl) for lvl in range(6)}
    }

class UpgradeRequest(BaseModel):
    upgrade_id: str

@app.post("/api/meta/upgrade")
def upgrade_meta(req: UpgradeRequest):
    success = session.meta_profile.purchase_upgrade(req.upgrade_id)
    if success:
        session.meta_profile.save(session.meta_path)
        return {"success": True, "profile": session.meta_profile.to_dict()}
    raise HTTPException(status_code=400, detail="Upgrade failed (insufficient scrap or max level)")

class UnlockRequest(BaseModel):
    archetype_id: str

@app.post("/api/meta/unlock")
def unlock_archetype(req: UnlockRequest):
    success = session.meta_profile.unlock_archetype(req.archetype_id)
    if success:
        session.meta_profile.save(session.meta_path)
        return {"success": True, "profile": session.meta_profile.to_dict()}
    raise HTTPException(status_code=400, detail="Unlock failed (insufficient scrap or already unlocked)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
