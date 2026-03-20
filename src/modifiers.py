from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .state_models import PlayerState

ROOT = Path(__file__).resolve().parents[1]
PERKS_FILE = ROOT / "data" / "perks.json"

class ModifierRegistry:
    _perks_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _load_perks(cls):
        if not cls._perks_cache:
            try:
                with open(PERKS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._perks_cache = {p["id"]: p for p in data}
            except Exception as e:
                print(f"Error loading perks.json: {e}")
                cls._perks_cache = {}

    @classmethod
    def get_perk_definition(cls, perk_id: str) -> Optional[Dict[str, Any]]:
        cls._load_perks()
        return cls._perks_cache.get(perk_id)

    @classmethod
    def get_active_tags(cls, player: PlayerState) -> Dict[str, int]:
        """Counts the occurrences of each tag across all active perks."""
        if not player.character:
            return {}
        
        tags_count: Dict[str, int] = {}
        for perk_id in player.character.perks:
            perk_def = cls.get_perk_definition(perk_id)
            if not perk_def:
                continue
            for tag in perk_def.get("tags", []):
                tags_count[tag] = tags_count.get(tag, 0) + 1
        return tags_count

    @classmethod
    def get_build_archetype(cls, player: PlayerState) -> str:
        """Determines the dominant archetype based on active perks."""
        if not player.character:
            return "neutral"
            
        archetype_counts: Dict[str, int] = {}
        for perk_id in player.character.perks:
            perk_def = cls.get_perk_definition(perk_id)
            if not perk_def:
                continue
            arch = perk_def.get("archetype", "unknown")
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
            
        if not archetype_counts:
            return "neutral"
            
        # Return the one with highest count
        return max(archetype_counts, key=archetype_counts.get)

    @classmethod
    def get_available_perks(cls, player: PlayerState, count: int = 3, target_level: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns a random selection of perks that the player meets requirements for."""
        cls._load_perks()
        owned = player.character.perks if player.character else []
        
        # If no target_level provided, use current level
        check_level = target_level if target_level is not None else (player.character.level if player.character else 0)
        
        eligible = []
        for pid, pdef in cls._perks_cache.items():
            if pid in owned:
                continue
            
            # Requirement check
            reqs = pdef.get("requirements", {})
            if check_level < reqs.get("level", 0):
                continue
                
            # SPECIAL check
            spec_reqs = reqs.get("special", {})
            if spec_reqs and player.character and player.character.special:
                met = True
                for stat, rule in spec_reqs.items():
                    val = player.character.special.get(stat, 0)
                    if val < rule.get("min", 0):
                        met = False
                        break
                if not met: continue
            
            eligible.append(pdef)
            
        if not eligible:
            return []
            
        return random.sample(eligible, min(len(eligible), count))

    @classmethod
    def get_tier_bonuses(cls, player: PlayerState) -> List[Dict[str, Any]]:
        """Calculates global bonuses based on archetype perk counts (Tier 1: 2, Tier 2: 4, Tier 3: 6)."""
        if not player.character: return []
        
        # Count perks per archetype
        arch_counts: Dict[str, int] = {}
        for perk_id in player.character.perks:
            pdef = cls.get_perk_definition(perk_id)
            if pdef:
                arch = pdef.get("archetype", "neutral")
                arch_counts[arch] = arch_counts.get(arch, 0) + 1
        
        bonuses = []
        # Define Tiered Rules
        rules = {
            "survivor": [
                (2, "max_food_bonus", 5, "Survivor Tier 1"),
                (4, "radiation_reduction", 1, "Survivor Tier 2")
            ],
            "scavenger": [
                (2, "scrap_bonus", 2, "Scavenger Tier 1"),
                (4, "scrap_bonus", 3, "Scavenger Tier 2")
            ],
            "hunter": [
                (2, "ammo_save_chance", 0.1, "Hunter Tier 1"),
                (4, "max_hp_bonus", 2, "Hunter Tier 2")
            ]
        }
        
        for arch, count in arch_counts.items():
            if arch in rules:
                for threshold, effect, val, name in rules[arch]:
                    if count >= threshold:
                        bonuses.append({
                            "name": name,
                            "effect": effect,
                            "value": val,
                            "threshold": threshold,
                            "archetype": arch
                        })
        return bonuses

    @classmethod
    def get_modifier(cls, player: PlayerState, effect_key: str, base_value: float = 0.0) -> float:
        """
        Calculates the modified value based on active perks and tiered synergies.
        """
        if not player.character:
            return base_value

        current_value = base_value
        active_perks = player.character.perks
        
        # 1. Accumulate Base Perk Modifiers
        for perk_id in active_perks:
            perk_def = cls.get_perk_definition(perk_id)
            if not perk_def: continue
            
            effects = perk_def.get("effects", {})
            if effect_key in effects:
                mod_val = effects[effect_key]
                if effect_key.endswith("_multiplier"): current_value *= mod_val
                elif effect_key.endswith("_chance"): current_value = max(current_value, mod_val)
                else: current_value += mod_val

        # 2. Accumulate Tiered Synergy Modifiers
        for bonus in cls.get_tier_bonuses(player):
            if bonus["effect"] == effect_key:
                val = bonus["value"]
                if effect_key.endswith("_multiplier"): current_value *= val
                else: current_value += val

        return current_value

def apply_modifier(player: PlayerState, effect_key: str, base_value: float = 0.0) -> float:
    return ModifierRegistry.get_modifier(player, effect_key, base_value)

def get_modifier_breakdown(player: PlayerState) -> Dict[str, Any]:
    """Returns a map of all potentially modified stats and their sources."""
    # This will be used for the Build Debug Panel
    tracked_effects = [
        "max_hp_bonus", "max_food_bonus", "encounter_chance_multiplier",
        "repair_cost_multiplier", "ammo_save_chance", "radiation_reduction",
        "scrap_bonus", "medkit_heal_bonus"
    ]
    
    # Count perks per archetype for UI
    arch_counts: Dict[str, int] = {}
    if player.character:
        for perk_id in player.character.perks:
            pdef = ModifierRegistry.get_perk_definition(perk_id)
            if pdef:
                arch = pdef.get("archetype", "neutral")
                arch_counts[arch] = arch_counts.get(arch, 0) + 1

    breakdown = {
        "archetype": ModifierRegistry.get_build_archetype(player),
        "archetype_counts": arch_counts,
        "tags": ModifierRegistry.get_active_tags(player),
        "stats": {}
    }
    
    # Simple defaults for breakdown calculation
    defaults = {
        "max_hp_bonus": float(player.base_max_hp),
        "max_food_bonus": float(player.base_max_food),
        "encounter_chance_multiplier": 1.0,
        "repair_cost_multiplier": 1.0,
        "ammo_save_chance": 0.0,
        "radiation_reduction": 0.0,
        "scrap_bonus": 0.0,
        "medkit_heal_bonus": 0.0
    }
    
    for effect in tracked_effects:
        base = defaults.get(effect, 0.0)
        final = apply_modifier(player, effect, base)
        
        sources = []
        # Direct Perk Sources
        for perk_id in player.character.perks:
            p_def = ModifierRegistry.get_perk_definition(perk_id)
            if p_def and effect in p_def.get("effects", {}):
                sources.append({
                    "id": perk_id,
                    "name": p_def["display_name"],
                    "value": p_def["effects"][effect],
                    "type": "perk"
                })
        
        # Tier Synergy Sources
        for bonus in ModifierRegistry.get_tier_bonuses(player):
            if bonus["effect"] == effect:
                sources.append({
                    "id": f"tier_{bonus['archetype']}_{bonus['threshold']}",
                    "name": bonus["name"],
                    "value": bonus["value"],
                    "type": "synergy"
                })
                
        breakdown["stats"][effect] = {
            "base": base,
            "final": final,
            "sources": sources
        }
        
    return breakdown
