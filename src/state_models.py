from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

NodeType = Literal["resource", "combat", "trade", "story"]
EquipmentSlot = Literal["weapon", "armor", "tool"]

ITEM_SLOT_BY_ID: Dict[str, EquipmentSlot] = {
    "makeshift_blade": "weapon",
    "rust_rifle": "weapon",
    "hardened_blade": "weapon",
    "gas_mask": "armor",
    "plate_armor": "armor",
    "scavenger_kit": "tool",
    "field_pack": "tool",
}


@dataclass
class PlayerState:
    hp: int
    food: int
    ammo: int
    medkits: int
    scrap: int = 0
    radiation: int = 0
    background: Optional[str] = None
    weapon_slot: Optional[str] = None
    armor_slot: Optional[str] = None
    tool_slot: Optional[str] = None

    def is_dead(self) -> bool:
        return self.hp <= 0 or self.food <= 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hp": self.hp,
            "food": self.food,
            "ammo": self.ammo,
            "medkits": self.medkits,
            "scrap": self.scrap,
            "radiation": self.radiation,
            "background": self.background,
            "weapon_slot": self.weapon_slot,
            "armor_slot": self.armor_slot,
            "tool_slot": self.tool_slot,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PlayerState:
        return PlayerState(
            hp=data["hp"],
            food=data["food"],
            ammo=data["ammo"],
            medkits=data["medkits"],
            scrap=data.get("scrap", 0),
            radiation=data.get("radiation", 0),
            background=data.get("background"),
            weapon_slot=data.get("weapon_slot"),
            armor_slot=data.get("armor_slot"),
            tool_slot=data.get("tool_slot"),
        )


@dataclass
class NodeState:
    id: str
    node_type: NodeType
    connections: List[str]
    event_pool: List[str]
    is_start: bool = False
    is_final: bool = False
    resource_cost: Dict[str, int] = field(default_factory=dict)


@dataclass
class EnemyState:
    id: str
    name: str
    hp: int
    damage_min: int
    damage_max: int
    archetype: Optional[str] = None
    special_ability: Optional[str] = None
    special_used: bool = False
    loot_table: List[Dict[str, Any]] = field(default_factory=list)

    def is_dead(self) -> bool:
        return self.hp <= 0


@dataclass
class MapState:
    nodes: Dict[str, NodeState]
    start_node_id: str
    final_node_id: Optional[str] = None

    def get_node(self, node_id: str) -> NodeState:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node: {node_id}")
        return self.nodes[node_id]


@dataclass
class RunState:
    player: PlayerState
    map_seed: int
    current_node: str
    visited_nodes: List[str] = field(default_factory=list)
    ended: bool = False
    victory: bool = False
    end_reason: Optional[str] = None
    decision_log: List[Dict[str, Any]] = field(default_factory=list)
    travel_mode: str = "normal"

    def visit(self, node_id: str) -> None:
        if node_id not in self.visited_nodes:
            self.visited_nodes.append(node_id)
        self.current_node = node_id

    def end(self, *, victory: bool, reason: str) -> None:
        self.ended = True
        self.victory = victory
        self.end_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "run_state/0.1",
            "save_format": "snapshot",
            "seed": self.map_seed, # v0.1 simplification: run_seed = map_seed
            "map_seed": self.map_seed,
            "player": self.player.to_dict(),
            "current_node": self.current_node,
            "visited_nodes": list(self.visited_nodes),
            "ended": self.ended,
            "victory": self.victory,
            "end_reason": self.end_reason,
            "decision_log": list(self.decision_log),
            "travel_mode": self.travel_mode,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> RunState:
        player = PlayerState.from_dict(data["player"])
        return RunState(
            player=player,
            map_seed=data["map_seed"],
            current_node=data["current_node"],
            visited_nodes=list(data["visited_nodes"]),
            ended=data["ended"],
            victory=data["victory"],
            end_reason=data["end_reason"],
            decision_log=list(data.get("decision_log", [])),
            travel_mode=data.get("travel_mode", "normal"),
        )


def equip_item(player: PlayerState, slot: EquipmentSlot, item: str) -> Dict[str, Optional[str] | bool]:
    expected_slot = ITEM_SLOT_BY_ID.get(item)
    if expected_slot is None:
        raise ValueError(f"Unknown equipment item: {item}")
    if expected_slot != slot:
        raise ValueError(f"Equipment slot mismatch: item {item} cannot be equipped to {slot}")

    slot_attr = f"{slot}_slot"
    previous = getattr(player, slot_attr)
    if previous == item:
        return {"slot": slot, "item": item, "replaced": previous, "changed": False}

    setattr(player, slot_attr, item)

    # Field Pack uses a temporary +2 food proxy until a true capacity system exists.
    if item == "field_pack":
        player.food += 2

    player.food = max(0, player.food)
    return {"slot": slot, "item": item, "replaced": previous, "changed": True}


def apply_effects(player: PlayerState, effects: Dict[str, int]) -> None:
    """Apply event effects to player resources/state in-place."""
    for key, delta in effects.items():
        if key == "hp":
            player.hp += delta
        elif key == "food":
            player.food += delta
        elif key == "ammo":
            player.ammo += delta
        elif key == "medkits":
            player.medkits += delta
        elif key == "scrap":
            player.scrap += delta
        elif key == "radiation":
            player.radiation += delta
        else:
            raise ValueError(f"Unsupported effect key: {key}")

    player.hp = max(0, player.hp)
    player.food = max(0, player.food)
    player.ammo = max(0, player.ammo)
    player.medkits = max(0, player.medkits)
    player.scrap = max(0, player.scrap)
    player.radiation = max(0, player.radiation)


def apply_loot(player: PlayerState, resource: str, amount: int) -> None:
    if amount < 0:
        raise ValueError("Loot amount must be non-negative")
    if resource == "food":
        player.food += amount
    elif resource == "ammo":
        player.ammo += amount
    elif resource == "medkits":
        player.medkits += amount
    elif resource == "scrap":
        player.scrap += amount
    else:
        raise ValueError(f"Unsupported loot resource: {resource}")
