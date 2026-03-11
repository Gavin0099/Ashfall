from __future__ import annotations

from dataclasses import dataclass

from .state_models import PlayerState


DifficultyName = str


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
        starting_hp=10,
        starting_food=9,
        starting_ammo=4,
        starting_medkits=2,
        event_combat_delta=-0.1,
    ),
    "normal": DifficultyProfile(
        name="normal",
        starting_hp=10,
        starting_food=7,
        starting_ammo=3,
        starting_medkits=1,
        event_combat_delta=0.0,
    ),
    "hard": DifficultyProfile(
        name="hard",
        starting_hp=9,
        starting_food=6,
        starting_ammo=3,
        starting_medkits=0,
        event_combat_delta=0.1,
    ),
}


def get_difficulty_profile(name: str) -> DifficultyProfile:
    key = name.strip().lower()
    if key not in DIFFICULTY_PROFILES:
        raise ValueError(f"Unknown difficulty preset: {name}")
    return DIFFICULTY_PROFILES[key]


def build_starting_player(name: str = "normal") -> PlayerState:
    profile = get_difficulty_profile(name)
    return PlayerState(
        hp=profile.starting_hp,
        food=profile.starting_food,
        ammo=profile.starting_ammo,
        medkits=profile.starting_medkits,
    )
