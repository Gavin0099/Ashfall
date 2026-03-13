from __future__ import annotations

import random
from dataclasses import replace
from typing import Any, Dict, Optional

from .combat_engine import CombatEngine
from .encounter_tables import ENCOUNTER_WEIGHTS, encounter_bucket_for_node
from .difficulty import DifficultyProfile, get_difficulty_profile
from .event_engine import pick_event_id, resolve_event_choice

from .state_models import EnemyState, MapState, NodeState, PlayerState, RunState, apply_loot


class RunEngine:
    """Minimal run-loop skeleton for Phase B integration."""

    def __init__(
        self,
        map_state: MapState,
        seed: int,
        event_catalog: Optional[Dict[str, Dict[str, Any]]] = None,
        enemy_catalog: Optional[Dict[str, Dict[str, Any]]] = None,
        difficulty: str = "normal",
    ) -> None:
        self.map_state = map_state
        self.rng = random.Random(seed)
        self.event_catalog = event_catalog or {}
        self.enemy_catalog = enemy_catalog or {}
        self.difficulty_profile: DifficultyProfile = get_difficulty_profile(difficulty)

    def create_run(self, player: PlayerState, seed: int) -> RunState:
        start = self.map_state.start_node_id
        run = RunState(player=replace(player), map_seed=seed, current_node=start)
        run.visit(start)
        return run

    def move_to(self, run: RunState, next_node_id: str) -> NodeState:
        current = self.map_state.get_node(run.current_node)
        if next_node_id not in current.connections:
            raise ValueError(f"Invalid move: {run.current_node} -> {next_node_id}")

        node = self.map_state.get_node(next_node_id)
        self.apply_node_cost(run, node)
        run.visit(next_node_id)
        self.apply_travel_attrition(run)

        if run.player.food <= 0:
            run.end(victory=False, reason="starvation")
        elif run.player.hp <= 0:
            run.end(victory=False, reason="radiation_death" if run.player.radiation > 0 else "death")
        elif node.is_final:
            run.end(victory=True, reason="reached_final_node")

        return node

    def resolve_node_event(self, node: NodeState, run: RunState, option_index: int = 0) -> Dict[str, Any]:
        return self.resolve_node_event_with_id(node, run, event_id=None, option_index=option_index)

    def resolve_node_event_with_id(
        self,
        node: NodeState,
        run: RunState,
        event_id: str | None = None,
        option_index: int = 0,
    ) -> Dict[str, Any]:
        if event_id is None:
            event_id = pick_event_id(node, self.rng)
        if event_id not in self.event_catalog:
            raise KeyError(f"Missing event payload for event_id: {event_id}")
        event_payload = self._event_payload_for_difficulty(self.event_catalog[event_id])
        outcome = resolve_event_choice(run.player, event_payload, option_index, self.rng)
        if outcome["combat_triggered"]:
            encounter_bias = event_payload.get("options", [])[option_index].get("encounter_bias")
            outcome["combat"] = self.resolve_combat(run, encounter_bias=encounter_bias)
        if run.player.is_dead():
            run.end(victory=False, reason=self._resolve_noncombat_death_reason(run))
        return outcome

    def resolve_combat(self, run: RunState, encounter_bias: Dict[str, float] | None = None) -> Dict[str, Any]:
        if not self.enemy_catalog:
            return {"skipped": True, "reason": "enemy_catalog_empty"}
        enemy_id = self._pick_enemy_id(run, encounter_bias=encounter_bias)
        enemy = _enemy_from_payload(self.enemy_catalog[enemy_id])
        result = CombatEngine(seed=run.map_seed + len(run.visited_nodes)).run_auto_combat(run.player, enemy)
        loot = []
        if result["victory"]:
            for item in enemy.loot_table:
                chance = float(item.get("chance", 1.0))
                if self.rng.random() <= chance:
                    resource = str(item["resource"])
                    amount = int(item["amount"])
                    apply_loot(run.player, resource, amount)
                    loot.append({"resource": resource, "amount": amount})
                    result["log"].append(f"戰利品：{resource} +{amount}")
        if not result["victory"]:
            run.end(victory=False, reason="combat_death")
        return {"skipped": False, "enemy_id": enemy_id, "loot": loot, **result}

    def _pick_enemy_id(self, run: RunState, encounter_bias: Dict[str, float] | None = None) -> str:
        enemy_ids = sorted(self.enemy_catalog.keys())
        if len(enemy_ids) == 1:
            return enemy_ids[0]

        node_id = run.current_node
        weights = []
        for enemy_id in enemy_ids:
            payload = self.enemy_catalog[enemy_id]
            archetype = str(payload.get("archetype", ""))
            weight = self._enemy_weight_for_node(node_id, archetype)
            if encounter_bias and archetype in encounter_bias:
                weight *= max(0.0, float(encounter_bias[archetype]))
            weights.append(max(0.0, weight))

        if sum(weights) <= 0:
            return self.rng.choice(enemy_ids)
        return self.rng.choices(enemy_ids, weights=weights, k=1)[0]

    def _enemy_weight_for_node(self, node_id: str, archetype: str) -> float:
        bucket = encounter_bucket_for_node(node_id)
        bucket_weights = ENCOUNTER_WEIGHTS.get(bucket, ENCOUNTER_WEIGHTS["default"])
        default_weights = ENCOUNTER_WEIGHTS["default"]
        return bucket_weights.get(archetype, default_weights.get(archetype, 0.1))

    def apply_travel_attrition(self, run: RunState) -> None:
        if run.player.radiation > 0:
            damage = 1
            if run.player.armor_slot == "gas_mask":
                damage = max(0, damage - 1)
            if damage > 0:
                run.player.hp -= damage
                run.player.hp = max(0, run.player.hp)

    def apply_node_cost(self, run: RunState, node: NodeState) -> None:
        cost = dict(node.resource_cost) if node.resource_cost else {"food": 1}
        for key, amount in cost.items():
            if amount < 0:
                raise ValueError(f"Node resource_cost must be non-negative: {node.id} {key}={amount}")
            if key == "food":
                run.player.food = max(0, run.player.food - amount)
            elif key == "hp":
                run.player.hp = max(0, run.player.hp - amount)
            elif key == "ammo":
                run.player.ammo = max(0, run.player.ammo - amount)
            elif key == "medkits":
                run.player.medkits = max(0, run.player.medkits - amount)
            elif key == "scrap":
                run.player.scrap = max(0, run.player.scrap - amount)
            elif key == "radiation":
                run.player.radiation = max(0, run.player.radiation - amount)
            else:
                raise ValueError(f"Unsupported resource_cost key: {key}")

    def _resolve_noncombat_death_reason(self, run: RunState) -> str:
        if run.player.food <= 0:
            return "starvation"
        if run.player.hp <= 0 and run.player.radiation > 0:
            return "radiation_death"
        return "event_or_resource_death"

    def _event_payload_for_difficulty(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        delta = self.difficulty_profile.event_combat_delta
        if delta == 0.0:
            return event_payload
        patched = dict(event_payload)
        patched_options = []
        for option in event_payload.get("options", []):
            new_option = dict(option)
            chance = float(new_option.get("combat_chance", 0.0))
            new_option["combat_chance"] = max(0.0, min(1.0, chance + delta))
            patched_options.append(new_option)
        patched["options"] = patched_options
        return patched


def build_map(node_payloads: Dict[str, dict], start_node_id: str, final_node_id: str | None = None) -> MapState:
    nodes = {}
    for node_id, payload in node_payloads.items():
        nodes[node_id] = NodeState(
            id=payload["id"],
            node_type=payload["node_type"],
            connections=payload.get("connections", []),
            event_pool=payload.get("event_pool", []),
            is_start=payload.get("is_start", False),
            is_final=payload.get("is_final", False),
            resource_cost=payload.get("resource_cost", {}),
        )

    resolved_final = final_node_id
    if resolved_final is None:
        for node in nodes.values():
            if node.is_final:
                resolved_final = node.id
                break

    map_state = MapState(nodes=nodes, start_node_id=start_node_id, final_node_id=resolved_final)
    validate_map_connectivity(map_state)
    return map_state


def validate_map_connectivity(map_state: MapState) -> None:
    if map_state.start_node_id not in map_state.nodes:
        raise ValueError(f"Start node missing: {map_state.start_node_id}")
    if map_state.final_node_id is None:
        raise ValueError("Final node is not defined")
    if map_state.final_node_id not in map_state.nodes:
        raise ValueError(f"Final node missing: {map_state.final_node_id}")

    for node in map_state.nodes.values():
        for connection in node.connections:
            if connection not in map_state.nodes:
                raise ValueError(f"Node {node.id} has unknown connection: {connection}")

    reachable = _bfs_reachable(map_state, map_state.start_node_id)
    if map_state.final_node_id not in reachable:
        raise ValueError("Final node is unreachable from start node")


def _bfs_reachable(map_state: MapState, start_node_id: str) -> set[str]:
    visited: set[str] = set()
    queue = [start_node_id]
    while queue:
        node_id = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        queue.extend(map_state.get_node(node_id).connections)
    return visited


def _enemy_from_payload(payload: Dict[str, Any]) -> EnemyState:
    damage = payload.get("damage_range", {})
    return EnemyState(
        id=payload["id"],
        name=payload.get("name", payload["id"]),
        hp=int(payload["hp"]),
        damage_min=int(damage.get("min", 1)),
        damage_max=int(damage.get("max", 2)),
        archetype=payload.get("archetype"),
        special_ability=payload.get("special_ability"),
        loot_table=list(payload.get("loot_table", [])),
    )
