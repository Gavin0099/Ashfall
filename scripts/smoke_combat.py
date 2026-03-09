#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.combat_engine import CombatEngine
from src.state_models import EnemyState, PlayerState


def main() -> int:
    player = PlayerState(hp=10, food=5, ammo=4, medkits=1)
    enemy = EnemyState(id="enemy_raider_scout", name="Raider Scout", hp=6, damage_min=1, damage_max=2)

    outcome = CombatEngine(seed=42).run_auto_combat(player, enemy)
    print("Smoke combat OK")
    print(outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
