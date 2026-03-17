import random
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from src.state_models import EquipmentState, ITEM_SLOT_BY_ID

class ItemFactory:
    def __init__(self, item_catalog_path: str, affix_catalog_path: str):
        self.item_catalog = self._load_json(item_catalog_path)
        self.affix_catalog = self._load_json(affix_catalog_path)

    def _load_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_random_equipment(self, base_id: str, rarity_override: Optional[str] = None, seed: Optional[int] = None) -> EquipmentState:
        rng = random.Random(seed) if seed is not None else random.Random()
        
        base_data = self.item_catalog.get(base_id)
        if not base_data:
            raise KeyError(f"Item ID {base_id} not found in catalog.")

        # Determine Rarity
        rarity = rarity_override
        if not rarity:
            roll = rng.random()
            if roll < 0.05:
                rarity = "legendary"
            elif roll < 0.30:
                rarity = "rare"
            else:
                rarity = "common"

        # Initialize State
        state = EquipmentState(
            id=base_id,
            slot=base_data["slot"],
            durability=base_data.get("max_durability", 10),
            max_durability=base_data.get("max_durability", 10),
            rarity=rarity,
            requirements=dict(base_data.get("requirements", {})),
            scaling=dict(base_data.get("scaling", {})),
            affixes=dict(base_data.get("affixes", {})),
            tags=list(base_data.get("tags", []))
        )

        # Apply Affixes based on Rarity
        num_affixes = 0
        if rarity == "rare":
            num_affixes = 1
        elif rarity == "legendary":
            num_affixes = 2

        if num_affixes > 0:
            self._apply_random_affixes(state, num_affixes, rng)

        return state

    def _apply_random_affixes(self, state: EquipmentState, count: int, rng: random.Random):
        # Flatten all possible affixes for sampling
        all_affixes = []
        for category in ["prefix", "suffix"]:
            for aid, data in self.affix_catalog[category].items():
                all_affixes.append((category, aid, data))
        
        # Unique affixes only for legendary or as special chance
        if state.rarity == "legendary":
            for aid, data in self.affix_catalog["unique"].items():
                all_affixes.append(("unique", aid, data))

        # Sample without replacement
        if count > len(all_affixes):
            count = len(all_affixes)
        
        chosen = rng.sample(all_affixes, count)
        
        for category, aid, data in chosen:
            # Apply bonuses to affixes dict
            if "bonus" in data:
                for b_type, b_val in data["bonus"].items():
                    state.affixes[b_type] = state.affixes.get(b_type, 0) + b_val
            
            # Apply requirements offset
            if "requirements_offset" in data:
                for req_key in state.requirements:
                    state.requirements[req_key] = max(1, state.requirements[req_key] + data["requirements_offset"])
            
            # Apply tags
            if "tag" in data:
                if data["tag"] not in state.tags:
                    state.tags.append(data["tag"])
            
            # Note: We current store the original base_id. 
            # In a full impl, we might want to change the display name.
            # For this prototype, we rely on UI to render prefixes/suffixes.
    def refine_equipment(self, state: EquipmentState, seed: Optional[int] = None) -> Dict[str, Any]:
        """Upgrade equipment rarity or power up existing stats."""
        rng = random.Random(seed) if seed is not None else random.Random()
        
        old_rarity = state.rarity
        state.refinement_count += 1
        
        # Determine if rarity improves
        promoted = False
        if state.rarity == "common" and state.refinement_count >= 1:
            state.rarity = "rare"
            promoted = True
            self._apply_random_affixes(state, 1, rng)
        elif state.rarity == "rare" and state.refinement_count >= 3:
            state.rarity = "legendary"
            promoted = True
            self._apply_random_affixes(state, 1, rng) # Add a second affix

        # Basic stat scaling on refinement
        # Every refinement increases base effectiveness by ~10%
        if "base_dmg" in self.item_catalog.get(state.id, {}):
             # For weapons, increase min/max dmg slightly every 2 levels
             if state.refinement_count % 2 == 0:
                 state.affixes["atk"] = state.affixes.get("atk", 0) + 1
        
        if state.slot == "armor":
             # For armor, increase def every 2 levels
             if state.refinement_count % 2 == 0:
                 state.affixes["def"] = state.affixes.get("def", 0) + 1

        return {
            "success": True,
            "old_rarity": old_rarity,
            "new_rarity": state.rarity,
            "promoted": promoted,
            "refinement_count": state.refinement_count
        }
