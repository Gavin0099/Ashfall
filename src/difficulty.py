from __future__ import annotations

from dataclasses import dataclass

from .state_models import PlayerState
from .meta_progression import MetaProfile


DifficultyName = str


@dataclass(frozen=True)
class RegionProfile:
    name: str             # 區域代碼 (e.g. fringe)
    display_name: str    # UI 顯示名稱
    min_depth: int       # 起始深度 (inclusive)
    max_depth: int       # 結束深度 (inclusive)
    base_radiation: int  # 該區域基礎輻射值
    stat_multiplier: float  # 敵人數值加成係數
    elite_chance_multiplier: float # 精英出現率加成


REGIONAL_PROFILES = [
    RegionProfile("fringe", "邊緣地帶 (Fringe)", 0, 3, 0, 1.0, 1.0),
    RegionProfile("dead_zone", "死亡禁區 (Dead Zone)", 4, 7, 1, 1.2, 1.3),
    RegionProfile("the_ridge", "山脊之巔 (The Ridge)", 8, 999, 1, 1.5, 2.0),
]


def get_region_at_depth(depth: int) -> RegionProfile:
    for profile in REGIONAL_PROFILES:
        if profile.min_depth <= depth <= profile.max_depth:
            return profile
    return REGIONAL_PROFILES[0]


def scale_enemy_stat(base_val: int, depth: int) -> int:
    region = get_region_at_depth(depth)
    # 複合縮放：區域權重 + 深度線性增長 (2%/depth)
    multiplier = region.stat_multiplier * (1.0 + (depth * 0.02))
    return max(1, int(base_val * multiplier))


@dataclass(frozen=True)
class DifficultyProfile:
    name: DifficultyName
    starting_hp: int
    starting_food: int
    starting_ammo: int
    starting_medkits: int
    event_combat_delta: float = 0.0


DIFFICULTY_PROFILES: dict[str, DifficultyProfile] = {
    "easy": DifficultyProfile(
        name="easy",
        starting_hp=25,
        starting_food=12,
        starting_ammo=4,
        starting_medkits=4,
        event_combat_delta=-0.1,
    ),
    "normal": DifficultyProfile(
        name="normal",
        starting_hp=20,
        starting_food=10,
        starting_ammo=7,
        starting_medkits=5,
        event_combat_delta=0.0,
    ),
    "hard": DifficultyProfile(
        name="hard",
        starting_hp=15,
        starting_food=8,
        starting_ammo=3,
        starting_medkits=1,
        event_combat_delta=0.1,
    ),
}


def get_difficulty_profile(name: str) -> DifficultyProfile:
    key = name.strip().lower()
    if key not in DIFFICULTY_PROFILES:
        raise ValueError(f"Unknown difficulty preset: {name}")
    return DIFFICULTY_PROFILES[key]


def build_starting_player(
    name: str = "normal", 
    character: CharacterProfile | None = None,
    meta_profile: MetaProfile | None = None,
    resource_bias: Dict[str, int] | None = None
) -> PlayerState:
    profile = get_difficulty_profile(name)
    player = PlayerState(
        hp=profile.starting_hp,
        food=profile.starting_food,
        ammo=profile.starting_ammo,
        medkits=profile.starting_medkits,
        character=character,
    )
    
    # Meta Upgrades
    if meta_profile:
        player.hp += meta_profile.get_level("up_health_boost")
        player.food += meta_profile.get_level("up_food_ration")
        player.ammo += meta_profile.get_level("up_ammo_belt")
        player.medkits += meta_profile.get_level("up_medkit_stash")

    # Character Background / Archetype Initial Bonuses
    if resource_bias:
        player.hp += resource_bias.get("hp", 0)
        player.food += resource_bias.get("food", 0)
        player.ammo += resource_bias.get("ammo", 0)
        player.medkits += resource_bias.get("medkits", 0)
        player.scrap += resource_bias.get("scrap", 0)

    # Compatibility for old archetype system if character is None but we logic it
    # For now, let's assume v1.0 uses character. 
    # If character has granted_tags, they are already in the object.
    
    return player
