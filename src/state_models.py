from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

NodeType = Literal["resource", "combat", "trade", "story"]


@dataclass
class PlayerState:
    hp: int
    food: int
    ammo: int
    medkits: int
    scrap: int = 0
    radiation: int = 0

    def is_dead(self) -> bool:
        return self.hp <= 0 or self.food <= 0


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

    def visit(self, node_id: str) -> None:
        if node_id not in self.visited_nodes:
            self.visited_nodes.append(node_id)
        self.current_node = node_id

    def end(self, *, victory: bool, reason: str) -> None:
        self.ended = True
        self.victory = victory
        self.end_reason = reason


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
