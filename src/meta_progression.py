from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

@dataclass
class MetaProfile:
    profile_id: str = "default"
    total_scrap: int = 0
    lifetime_scrap_earned: int = 0
    unlock_levels: Dict[str, int] = field(default_factory=dict)
    unlocked_archetypes: List[str] = field(default_factory=lambda: ["soldier", "pathfinder"])
    unlocked_at_version: str = "0.5"

    def get_level(self, upgrade_id: str) -> int:
        return self.unlock_levels.get(upgrade_id, 0)

    def is_archetype_unlocked(self, archetype_id: str) -> bool:
        return archetype_id in self.unlocked_archetypes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "total_scrap": self.total_scrap,
            "lifetime_scrap_earned": self.lifetime_scrap_earned,
            "unlock_levels": dict(self.unlock_levels),
            "unlocked_archetypes": list(self.unlocked_archetypes),
            "unlocked_at_version": self.unlocked_at_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetaProfile:
        return cls(
            profile_id=data.get("profile_id", "default"),
            total_scrap=data.get("total_scrap", 0),
            lifetime_scrap_earned=data.get("lifetime_scrap_earned", 0),
            unlock_levels=dict(data.get("unlock_levels", {})),
            unlocked_archetypes=list(data.get("unlocked_archetypes", ["soldier", "pathfinder"])),
            unlocked_at_version=data.get("unlocked_at_version", "0.5"),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> MetaProfile:
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

class RewardCalculator:
    @staticmethod
    def calculate_scrap_reward(
        nodes_visited: int,
        reached_final_node: bool,
        enemies_defeated: int,
        ending_hp: int
    ) -> int:
        # Base reward
        scrap = 2 + nodes_visited
        
        # Bonus rewards
        if reached_final_node:
            scrap += 5
        
        scrap += enemies_defeated
        
        if ending_hp >= 6:
            scrap += 2
            
        return max(1, scrap)
