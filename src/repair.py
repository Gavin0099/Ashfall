from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .state_models import PlayerState, EquipmentState

def get_repair_cost_per_point() -> int:
    return 2

def calculate_full_repair_cost(equipment: EquipmentState) -> int:
    points_to_repair = equipment.max_durability - equipment.durability
    return points_to_repair * get_repair_cost_per_point()

def can_afford_repair(player: PlayerState, cost: int) -> bool:
    return player.scrap >= cost

def repair_equipment(player: PlayerState, slot: str) -> bool:
    equipment = None
    if slot == "weapon":
        equipment = player.weapon_slot
    elif slot == "armor":
        equipment = player.armor_slot
    elif slot == "tool":
        equipment = player.tool_slot
    
    if not equipment:
        return False
    
    cost = calculate_full_repair_cost(equipment)
    if cost <= 0:
        return False
    
    if not can_afford_repair(player, cost):
        return False
    
    player.scrap -= cost
    equipment.durability = equipment.max_durability
    return True
