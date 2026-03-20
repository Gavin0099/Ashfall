from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

NodeType = Literal["resource", "combat", "trade", "story", "camp", "ruins"]
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
class EquipmentState:
    id: str
    slot: EquipmentSlot
    durability: int = 10
    max_durability: int = 10
    rarity: str = "common"
    requirements: Dict[str, int] = field(default_factory=dict)
    scaling: Dict[str, float] = field(default_factory=dict)
    affixes: Dict[str, int] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    refinement_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "slot": self.slot,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "rarity": self.rarity,
            "requirements": self.requirements,
            "scaling": self.scaling,
            "affixes": self.affixes,
            "tags": self.tags,
            "refinement_count": self.refinement_count
        }

    def get_refine_cost(self) -> int:
        """Calculate the scrap cost for the next refinement."""
        base_cost = 5
        if self.rarity == "common":
            base_cost = 5 + (self.refinement_count * 2)
        elif self.rarity == "rare":
            base_cost = 15 + (self.refinement_count * 5)
        elif self.rarity == "legendary":
            base_cost = 40 + (self.refinement_count * 10)
        return base_cost

    def repair(self, amount: int):
        self.durability = min(self.max_durability, self.durability + amount)

    def reinforce(self, affix_type: str, value: int):
        self.affixes[affix_type] = self.affixes.get(affix_type, 0) + value

    def refit(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> EquipmentState:
        return EquipmentState(
            id=data["id"],
            slot=data["slot"],
            durability=data.get("durability", 10),
            max_durability=data.get("max_durability", 10),
            rarity=data.get("rarity", "common"),
            requirements=data.get("requirements", {}),
            scaling=data.get("scaling", {}),
            affixes=data.get("affixes", {}),
            tags=data.get("tags", []),
            refinement_count=data.get("refinement_count", 0),
        )

@dataclass
class CharacterProfile:
    background_id: str
    display_name: str
    special: Dict[str, int] = field(default_factory=lambda: {
        "strength": 5, "perception": 5, "endurance": 5,
        "charisma": 5, "intelligence": 5, "agility": 5, "luck": 5
    })
    traits: List[str] = field(default_factory=list)
    perks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    level: int = 1
    xp: int = 0

    XP_THRESHOLDS = {
        2: 100,
        3: 300,
        4: 600,
        5: 1000,
        6: 1500
    }

    def get_xp_for_next_level(self) -> int:
        return self.XP_THRESHOLDS.get(self.level + 1, 999999)

    def can_level_up(self) -> bool:
        return self.xp >= self.get_xp_for_next_level()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "background_id": self.background_id,
            "display_name": self.display_name,
            "special": self.special,
            "traits": self.traits,
            "perks": self.perks,
            "tags": self.tags,
            "level": self.level,
            "xp": self.xp,
            "can_level_up": self.can_level_up()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> CharacterProfile:
        if not data: return None
        return CharacterProfile(
            background_id=data["background_id"],
            display_name=data.get("display_name", data["background_id"]),
            special=data.get("special", {}),
            traits=data.get("traits", []),
            perks=data.get("perks", []),
            tags=data.get("tags", []),
            level=data.get("level", 1),
            xp=data.get("xp", 0)
        )

@dataclass
class PlayerState:
    hp: int
    food: int
    ammo: int
    medkits: int
    scrap: int = 0
    radiation: int = 0
    archetype: Optional[str] = None
    character: Optional[CharacterProfile] = None
    weapon_slot: Optional[EquipmentState] = None
    armor_slot: Optional[EquipmentState] = None
    tool_slot: Optional[EquipmentState] = None
    buffs: Dict[str, int] = field(default_factory=dict) # buff_id: duration_steps
    base_max_hp: int = 20
    base_max_food: int = 20
    max_hp: int = 20
    max_food: int = 20

    def recompute_stats(self) -> None:
        """根據 Perk 與 Buff 重新計算當前屬性上限。"""
        from .modifiers import apply_modifier
        self.max_hp = int(apply_modifier(self, "max_hp_bonus", float(self.base_max_hp)))
        self.max_food = int(apply_modifier(self, "max_food_bonus", float(self.base_max_food)))

        # 確保當前值不超過上限
        self.hp = min(self.hp, self.max_hp)
        self.food = min(self.food, self.max_food)

    def is_dead(self) -> bool:
        return self.hp <= 0 or self.food <= 0

    def equip(self, item: EquipmentState):
        """Equip an item into the correct slot."""
        if item.slot == "weapon":
            self.weapon_slot = item
        elif item.slot == "armor":
            self.armor_slot = item
        elif item.slot == "tool":
            self.tool_slot = item
        else:
            raise ValueError(f"Unknown slot: {item.slot}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hp": self.hp,
            "food": self.food,
            "ammo": self.ammo,
            "medkits": self.medkits,
            "scrap": self.scrap,
            "radiation": self.radiation,
            "archetype": self.archetype,
            "character": self.character.to_dict() if self.character else None,
            "weapon_slot": self.weapon_slot.to_dict() if self.weapon_slot else None,
            "armor_slot": self.armor_slot.to_dict() if self.armor_slot else None,
            "tool_slot": self.tool_slot.to_dict() if self.tool_slot else None,
            "buffs": self.buffs,
            "max_hp": self.max_hp,
            "max_food": self.max_food,
            "base_max_hp": self.base_max_hp,
            "base_max_food": self.base_max_food
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PlayerState:
        w_data = data.get("weapon_slot")
        a_data = data.get("armor_slot")
        t_data = data.get("tool_slot")
        c_data = data.get("character")
        return PlayerState(
            hp=data["hp"],
            food=data["food"],
            ammo=data["ammo"],
            medkits=data["medkits"],
            scrap=data.get("scrap", 0),
            radiation=data.get("radiation", 0),
            archetype=data.get("archetype") or data.get("background"),
            character=CharacterProfile.from_dict(c_data) if isinstance(c_data, dict) else None,
            weapon_slot=EquipmentState.from_dict(w_data) if isinstance(w_data, dict) else None,
            armor_slot=EquipmentState.from_dict(a_data) if isinstance(a_data, dict) else None,
            tool_slot=EquipmentState.from_dict(t_data) if isinstance(t_data, dict) else None,
            buffs=data.get("buffs", {}),
            base_max_hp=data.get("base_max_hp", data.get("max_hp", 20)),
            base_max_food=data.get("base_max_food", data.get("max_food", 20)),
            max_hp=data.get("max_hp", 20),
            max_food=data.get("max_food", 20)
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
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    is_elite: bool = False
    passives: List[str] = field(default_factory=list)
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
    depth: int = 0
    visited_nodes: List[str] = field(default_factory=list)
    ended: bool = False
    victory: bool = False
    end_reason: Optional[str] = None
    node_events: Dict[str, str] = field(default_factory=dict) # node_id -> event_id
    
    # Phase 3.0: Ruins exploration state
    current_ruins_stage: int = 0
    temporary_loot: Dict[str, int] = field(default_factory=dict)
    decision_log: List[Dict[str, Any]] = field(default_factory=list)
    travel_mode: str = "normal"
    flags: Dict[str, Any] = field(default_factory=dict)

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
            "decision_log": self.decision_log,
            "travel_mode": self.travel_mode,
            "flags": self.flags,
            "node_events": self.node_events,
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
            node_events=data.get("node_events", {}),
            decision_log=data.get("decision_log", []),
            travel_mode=data.get("travel_mode", "normal"),
            flags=data.get("flags", {}),
        )


def equip_item(player: PlayerState, slot: EquipmentSlot, equipment: EquipmentState) -> Dict[str, Any]:
    if equipment.slot != slot:
        raise ValueError(f"Equipment slot mismatch: item {equipment.id} cannot be equipped to {slot}")

    slot_attr = f"{slot}_slot"
    previous = getattr(player, slot_attr)
    previous_id = previous.id if previous else None
    
    if previous_id == equipment.id and getattr(previous, "affixes", {}) == equipment.affixes:
        return {"slot": slot, "item": equipment.id, "replaced": previous_id, "changed": False}

    setattr(player, slot_attr, equipment)

    # Field Pack uses a temporary +2 food proxy until a true capacity system exists.
    if equipment.id == "field_pack":
        player.food += 2

    player.food = max(0, player.food)
    return {"slot": slot, "item": equipment.id, "replaced": previous_id, "changed": True}


def apply_effects(player: PlayerState, effects: Dict[str, int]) -> None:
    """Apply event effects to player resources/state in-place."""
    for key, delta in effects.items():
        if key == "hp":
            player.hp = min(player.max_hp, player.hp + delta)
        elif key == "food":
            player.food = min(player.max_food, player.food + delta)
        elif key == "ammo":
            player.ammo += delta
        elif key == "medkits":
            player.medkits += delta
        elif key == "scrap":
            player.scrap += delta
        elif key == "radiation":
            player.radiation += delta
        elif key == "xp":
            if player.character:
                player.character.xp += delta
        elif key == "buffs":
            # delta is expected to be a Dict[buff_id, duration]
            if isinstance(delta, dict):
                player.buffs.update(delta)
        else:
            raise ValueError(f"Unsupported effect key: {key}")

    player.hp = max(0, player.hp)
    player.food = max(0, player.food)
    player.ammo = max(0, player.ammo)
    player.medkits = max(0, player.medkits)
    player.scrap = max(0, player.scrap)
    player.radiation = max(0, player.radiation)

    # Phase 2.2: Perk-based event effect modifiers
    if player.character:
        # Lead Stomach: Reduce radiation gained from events
        if "lead_stomach" in player.character.perks and effects.get("radiation", 0) > 0:
            player.radiation = max(0, player.radiation - 1)
        
        # Scavenger's Luck: Bonus scrap from events
        if "scavengers_luck" in player.character.perks and effects.get("scrap", 0) > 0:
            player.scrap += 2


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
    elif resource == "xp":
        if player.character:
            player.character.xp += amount
    else:
        raise ValueError(f"Unsupported loot resource: {resource}")
