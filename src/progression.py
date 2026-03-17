import json
from pathlib import Path
from typing import List, Dict, Any
from src.state_models import PlayerState, CharacterProfile

PERK_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "perks.json"

def load_perk_catalog() -> List[Dict[str, Any]]:
    if not PERK_CATALOG_PATH.exists():
        return []
    with open(PERK_CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def xp_to_next_level(level: int) -> int:
    """Simple XP curve: Level 1->2 needs 10, 2->3 needs 20, etc."""
    return level * 10

def gain_xp(player: PlayerState, amount: int) -> bool:
    """Adds XP and checks for level up. Returns True if leveled up."""
    if not player.character:
        return False
        
    player.character.xp += amount
    leveled_up = False
    
    while True:
        req = xp_to_next_level(player.character.level)
        if player.character.xp >= req:
            player.character.xp -= req
            player.character.level += 1
            leveled_up = True
            # Level Up effects could go here (e.g. heal 10%)
        else:
            break
            
    return leveled_up

def get_eligible_perks(player: PlayerState, catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Returns perks that the player meets requirements for and doesn't already have."""
    if not player.character:
        return []
        
    char = player.character
    owned = set(char.perks)
    eligible = []
    
    for perk in catalog:
        if perk["id"] in owned:
            continue
            
        reqs = perk.get("requirements", {})
        
        # Level check
        if char.level < reqs.get("level", 1):
            continue
            
        # SPECIAL check
        spec_reqs = reqs.get("special", {})
        met_special = True
        for attr, limits in spec_reqs.items():
            val = char.special.get(attr, 5)
            if "min" in limits and val < limits["min"]:
                met_special = False
                break
            if "max" in limits and val > limits["max"]:
                met_special = False
                break
        
        if met_special:
            eligible.append(perk)
            
    return eligible

def apply_perk(player: PlayerState, perk_id: str, catalog: List[Dict[str, Any]]):
    """Applies the static bonus of a perk to the player state."""
    perk = next((p for p in catalog if p["id"] == perk_id), None)
    if not perk or not player.character:
        return
        
    if perk_id not in player.character.perks:
        player.character.perks.append(perk_id)
        
    effects = perk.get("effects", {})
    
    # Static HP bonus
    if "max_hp_bonus" in effects:
        # Note: We need a max_hp concept in PlayerState if we want this to be robust.
        # Currently PlayerState just has 'hp' (starting at 10).
        # We can simulate by just adding current HP if we assume 10 is the base.
        player.hp += effects["max_hp_bonus"]
