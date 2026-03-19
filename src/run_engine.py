from __future__ import annotations

import json
import random
from pathlib import Path
from dataclasses import replace
from typing import Any, Dict, Optional

from .combat_engine import CombatEngine
from .encounter_tables import ENCOUNTER_WEIGHTS, encounter_bucket_for_node
from .difficulty import DifficultyProfile, get_difficulty_profile, scale_enemy_stat, get_region_at_depth
from .event_engine import pick_event_id, resolve_event_choice

from .state_models import EnemyState, MapState, NodeState, PlayerState, RunState, apply_loot, EquipmentState
from .item_factory import ItemFactory


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
        self.item_factory = ItemFactory("data/item_catalog.json", "data/affix_catalog.json")

    def create_run(self, player: PlayerState, seed: int) -> RunState:
        start = self.map_state.start_node_id
        player_copy = replace(player)
        player_copy.max_hp = self.difficulty_profile.starting_hp
        run = RunState(player=player_copy, map_seed=seed, current_node=start)
        run.visit(start)
        return run

    def move_to(self, run: RunState, next_node_id: str, travel_mode: str | None = None) -> NodeState:
        if travel_mode:
            run.travel_mode = travel_mode
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

        self.tick_buffs(run)
        return node

    def tick_buffs(self, run: RunState) -> None:
        """Decrease duration of active buffs and remove expired ones."""
        expired = []
        for buff_id in run.player.buffs:
            run.player.buffs[buff_id] -= 1
            if run.player.buffs[buff_id] <= 0:
                expired.append(buff_id)
        
        for buff_id in expired:
            del run.player.buffs[buff_id]

    def refine_equipment(self, run: RunState, slot: str, action: str) -> Dict[str, Any]:
        """Repair or upgrade equipment in a specific slot.
           action: 'repair' or 'refine' (Phase 6.0)
        """
        player = run.player
        equipment = getattr(player, f"{slot}_slot")
        if not equipment:
            return {"success": False, "reason": "no_equipment"}

        if action == "repair":
            cost = 2
            if player.character and "scrappie_perk" in player.character.perks:
                cost = 1
            elif player.character and player.character.special.get("intelligence", 5) >= 7:
                cost = 1
            
            current_node = self.map_state.get_node(run.current_node)
            if current_node.node_type == "camp" and current_node.metadata.get("facilities", {}).get("repair_bench"):
                if cost > 1: cost = 1
                
            needed = equipment.max_durability - equipment.durability
            if needed <= 0: return {"success": False, "reason": "already_max"}
            actual = min(player.scrap // cost, needed)
            if actual <= 0: return {"success": False, "reason": "insufficient_scrap"}
            
            player.scrap -= actual * cost
            equipment.repair(actual)
            return {"success": True, "action": "repair", "amount": actual, "cost": actual * cost}
        
        elif action == "refine":
            cost = equipment.get_refine_cost()
            if player.scrap < cost:
                return {"success": False, "reason": "insufficient_scrap"}
            
            player.scrap -= cost
            res = self.item_factory.refine_equipment(equipment, seed=self.rng.randint(0, 9999))
            res["action"] = "refine"
            res["cost"] = cost
            return res
            
        return {"success": False, "reason": "invalid_action"}

    def rest_at_camp(self, run: RunState, option: int) -> Dict[str, Any]:
        """Perform rest action at a camp node.
           option 0: 1 Food -> 2 HP
           option 1: 2 Food -> 3 HP, -1 Radiation
        """
        player = run.player
        current_node = self.map_state.get_node(run.current_node)
        if current_node.node_type != "camp":
            return {"success": False, "reason": "not_at_camp"}
        
        if option == 0:
            if player.food < 1: return {"success": False, "reason": "insufficient_food"}
            player.food -= 1
            gain = 2
            player.hp = min(player.max_hp, player.hp + gain)
            return {"success": True, "gain_hp": gain, "cost_food": 1}
        elif option == 1:
            if player.food < 2: return {"success": False, "reason": "insufficient_food"}
            player.food -= 2
            gain_hp = 3
            player.hp = min(player.max_hp, player.hp + gain_hp)
            old_rad = player.radiation
            player.radiation = max(0, player.radiation - 1)
            gain_rad = old_rad - player.radiation
            return {"success": True, "gain_hp": gain_hp, "gain_rad": gain_rad, "cost_food": 2}
        
        return {"success": False, "reason": "invalid_option"}

    def add_to_temporary_loot(self, run: RunState, effects: Dict[str, int]) -> None:
        """Accumulate loot into temporary storage during ruins exploration."""
        for key, val in effects.items():
            if key in ("scrap", "medkits", "ammo", "food", "xp"):
                run.temporary_loot[key] = run.temporary_loot.get(key, 0) + val

    def finalize_ruins_loot(self, run: RunState, retreat_penalty: bool = False) -> Dict[str, int]:
        """Apply temporary loot to player, potentially with a penalty for retreating."""
        final_loot = {}
        for key, val in run.temporary_loot.items():
            amount = val
            if retreat_penalty and amount > 0:
                # 30% penalty for retreating
                amount = int(amount * 0.7)
            
            # Apply to player
            if key == "xp":
                if run.player.character: run.player.character.xp += amount
            else:
                setattr(run.player, key, getattr(run.player, key) + amount)
            
            final_loot[key] = amount
        
        run.temporary_loot.clear()
        run.current_ruins_stage = 0
        return final_loot
 
    def save_run(self, run: RunState, path: str | Path) -> None:
        """Serialize and save run state to a JSON file."""
        data = run.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
 
    def load_run(self, path: str | Path) -> RunState:
        """Load and reconstruct run state from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RunState.from_dict(data)

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
            event_id = pick_event_id(node, self.rng, run_flags=run.flags, event_catalog=self.event_catalog)
            
        if event_id not in self.event_catalog:
            raise KeyError(f"Missing event payload for event_id: {event_id}")
        event_payload = self.event_catalog[event_id]
        event_payload = self._event_payload_for_difficulty(event_payload, run.player)
        event_payload = self._patch_event_for_travel_mode(event_payload, run.travel_mode)
        
        outcome = resolve_event_choice(run.player, event_payload, option_index, self.rng)
        
        # Phase 5.0: Equipment reward
        if "equipment_reward" in outcome:
            rew = outcome["equipment_reward"]
            if isinstance(rew, dict) and "item" in rew:
                st = self.item_factory.create_random_equipment(rew["item"], seed=self.rng.randint(0, 9999))
                run.player.equip(st)
                outcome["equipment_change"] = {"slot": st.slot, "item": st.id, "item_data": st.to_dict(), "changed": True}
        
        # Scavenger passive: +1 to any positive resource gain from event effects
        if run.player.archetype == "scavenger" and not run.player.is_dead():
            effects = outcome.get("effects", {})
            scavenged = False
            for res_key in ("food", "ammo", "scrap", "medkits"):
                if effects.get(res_key, 0) > 0:
                    setattr(run.player, res_key, getattr(run.player, res_key) + 1)
                    scavenged = True
                    break
            if scavenged:
                # Add a note to the outcome for the UI (optional display)
                outcome["scavenger_bonus_active"] = True

        # Apply flag updates from event
        if outcome.get("set_flags"):
            run.flags.update(outcome["set_flags"])

        if outcome["combat_triggered"]:
            option = event_payload.get("options", [])[option_index]
            encounter_bias = option.get("encounter_bias")
            fixed_enemy_id = option.get("fixed_enemy_id")
            outcome["combat"] = self.resolve_combat(run, encounter_bias=encounter_bias, fixed_enemy_id=fixed_enemy_id)
        if run.player.is_dead():
            reason = self._resolve_noncombat_death_reason(run)
            if outcome.get("combat_triggered") and not outcome.get("combat", {}).get("victory"):
                reason = "combat_death"
            run.end(victory=False, reason=reason)
            
        # Record to decision_log
        log_entry = {
            "step": len(run.visited_nodes),
            "node": node.id,
            "event_id": event_id,
            "option_index": option_index,
            "effects": event_payload["options"][option_index].get("effects", {}),
            "combat_triggered": outcome["combat_triggered"],
            "player_after": run.player.to_dict()
        }
        if "equipment_change" in outcome:
            log_entry["equipment_change"] = outcome["equipment_change"]
        if outcome.get("combat") and outcome["combat"].get("equipment_change"):
            log_entry["equipment_change"] = outcome["combat"]["equipment_change"]
            
        run.decision_log.append(log_entry)
        
        return outcome

    def resolve_combat(self, run: RunState, encounter_bias: Dict[str, float] | None = None, fixed_enemy_id: str | None = None) -> Dict[str, Any]:
        if not self.enemy_catalog:
            return {"skipped": True, "reason": "enemy_catalog_empty"}
        
        enemy_id = fixed_enemy_id if fixed_enemy_id else self._pick_enemy_id(run, encounter_bias=encounter_bias)
        enemy = _enemy_from_payload(self.enemy_catalog[enemy_id])
        
        # Phase 4.0: Regional Scaling (Exclude bosses for direct control)
        if enemy.archetype != "boss":
            depth = len(run.visited_nodes)
            enemy.hp = scale_enemy_stat(enemy.hp, depth)
            enemy.damage_min = scale_enemy_stat(enemy.damage_min, depth)
            enemy.damage_max = scale_enemy_stat(enemy.damage_max, depth)
        
        result = CombatEngine(seed=run.map_seed + len(run.visited_nodes)).run_auto_combat(run.player, enemy)
        loot = []
        if result["victory"]:
            # Soldier Passive: recover 1hp after victory
            if run.player.archetype == "soldier":
                run.player.hp = min(run.player.max_hp, run.player.hp + 1)
                result["log"].append("守衛士兵：戰鬥後的磨練讓你恢復了 1 點生命值")

            # Phase 5.0: Boss Legendary Drop
            if fixed_enemy_id in ["boss_gatekeeper", "boss_overseer"]:
                wid = "hardened_blade" if fixed_enemy_id == "boss_gatekeeper" else "sledgehammer"
                loot_item = self.item_factory.create_random_equipment(wid, rarity_override="legendary", seed=self.rng.randint(0, 9999))
                run.player.equip(loot_item)
                result["log"].append(f"首領隕落：你獲得了傳奇獎備 【{loot_item.id}】 ({loot_item.rarity})！")
                result["equipment_change"] = {"slot": loot_item.slot, "item": loot_item.id, "item_data": loot_item.to_dict(), "changed": True}

            # Check for Combat-specific Buffs (Adrenaline, etc)
            if "adrenaline" in run.player.buffs:
               result["log"].append("腎上腺素：你在戰鬥中感受到感官的強化")

            for item in enemy.loot_table:
                chance = float(item.get("chance", 1.0))
                if self.rng.random() <= chance:
                    resource = str(item["resource"])
                    amount = int(item["amount"])
                    
                    # Scavenger Ability: +1 Scrap from loot
                    if resource == "scrap":
                        all_tags = []
                        if run.player.tool_slot: all_tags.extend(run.player.tool_slot.tags)
                        if "scavenger" in all_tags:
                            amount += 1
                            result["log"].append("拾荒者：改裝工具助你發現了更多廢料 (+1)")
                    
                    apply_loot(run.player, resource, amount)
                    loot.append({"resource": resource, "amount": amount})
                    result["log"].append(f"戰利品：{resource} +{amount}")
        
        if run.player.weapon_slot:
            # Sturdy Ability: 50% chance to ignore durability loss
            if "sturdy" in run.player.weapon_slot.tags and self.rng.random() < 0.5:
                pass 
            else:
                run.player.weapon_slot.durability = max(0, run.player.weapon_slot.durability - 1)
                if run.player.weapon_slot.durability == 0:
                    result["log"].append(f"⚠️ 你的武器 {run.player.weapon_slot.id} 已損壞！")

        if run.player.armor_slot:
            if "sturdy" in run.player.armor_slot.tags and self.rng.random() < 0.5:
                pass
            else:
                run.player.armor_slot.durability = max(0, run.player.armor_slot.durability - 1)
                if run.player.armor_slot.durability == 0:
                    result["log"].append(f"⚠️ 你的護甲 {run.player.armor_slot.id} 已損壞！")

        if not result["victory"]:
            run.end(victory=False, reason="combat_death")
        else:
            # Vampiric Ability: Heal 1 HP on victory
            all_tags = []
            if run.player.weapon_slot: all_tags.extend(run.player.weapon_slot.tags)
            if run.player.armor_slot: all_tags.extend(run.player.armor_slot.tags)
            
            if "vampiric" in all_tags:
                run.player.hp = min(10, run.player.hp + 1)
                result["log"].append("吸血：裝備的微弱生命脈衝治癒了你的傷口 (+1 HP)")

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
        # Phase 4.0: Regional Base Radiation
        depth = len(run.visited_nodes)
        region = get_region_at_depth(depth)
        
        if run.player.radiation > 0 or region.base_radiation > 0:
            # Total radiation effects = regional base + player's accumulated radiation
            # But the core logic is: every move costs -1 HP per radiation level.
            # Regional base radiation acts as a floor or addition?
            # v7.1: Added 1-point grace to allow low rad survival
            total_rad = run.player.radiation + region.base_radiation
            damage = (total_rad - 1) // 2 if total_rad > 1 else 0

            armor = run.player.armor_slot
            if armor and armor.id == "gas_mask" and armor.durability > 0:
                damage = max(0, damage - 1)
                # v7.1: 50% chance to take health durability hit when protecting
                if random.random() < 0.5:
                    armor.durability = max(0, armor.durability - 1)
            
            if damage > 0:
                run.player.hp -= damage
                run.player.hp = max(0, run.player.hp)

    def apply_node_cost(self, run: RunState, node: NodeState) -> None:
        cost = dict(node.resource_cost) if node.resource_cost else {"food": 1}
        for key, amount in cost.items():
            if amount < 0:
                raise ValueError(f"Node resource_cost must be non-negative: {node.id} {key}={amount}")
            
            # Travel Mode Modifier
            if key == "food":
                if run.travel_mode == "rush":
                    amount = max(0, amount - 1)
                elif run.travel_mode == "careful":
                    amount += 1
                
                # Pack Rat Trait: extra food cost
                if run.player.character and "pack_rat" in run.player.character.tags:
                    amount += 1

            # Phase 4.0: Regional Radiation Scaling in Resource Cost
            if key == "radiation":
                depth = len(run.visited_nodes)
                region = get_region_at_depth(depth)
                # Regional environment adds additional radiation gain
                amount += region.base_radiation

            # Pathfinder Archetype: ignore food cost on first travel
            if key == "food" and run.player.archetype == "pathfinder" and len(run.visited_nodes) == 1:
                continue

            if key == "food":
                run.player.food = max(0, run.player.food - amount)
            elif key == "hp":
                run.player.hp = max(0, run.player.hp - amount)
            elif key == "radiation":
                # Lead-lined: reduce radiation increase
                all_tags = []
                if run.player.armor_slot: all_tags.extend(run.player.armor_slot.tags)
                if run.player.tool_slot: all_tags.extend(run.player.tool_slot.tags)
                
                if "lead_lined" in all_tags:
                    amount = max(0, amount - 1)
                run.player.radiation = max(0, run.player.radiation + amount)
            elif key == "ammo":
                run.player.ammo = max(0, run.player.ammo - amount)
            elif key == "medkits":
                run.player.medkits = max(0, run.player.medkits - amount)
            elif key == "scrap":
                run.player.scrap = max(0, run.player.scrap - amount)
            else:
                raise ValueError(f"Unsupported resource_cost key: {key}")

    def _resolve_noncombat_death_reason(self, run: RunState) -> str:
        if run.player.food <= 0:
            return "starvation"
        if run.player.hp <= 0 and run.player.radiation > 0:
            return "radiation_death"
        return "event_or_resource_death"

    def _event_payload_for_difficulty(self, event_payload: Dict[str, Any], player: PlayerState | None = None) -> Dict[str, Any]:
        delta = self.difficulty_profile.event_combat_delta
        
        # Eagle Eye Perk or High Perception effect
        encounter_multiplier = 1.0
        if player and player.character:
            if "eagle_eye_perk" in player.character.perks:
                encounter_multiplier = 0.75
            elif player.character.special.get("perception", 5) >= 8:
                encounter_multiplier = 0.9

        if delta == 0.0 and encounter_multiplier == 1.0:
            return event_payload
            
        patched = dict(event_payload)
        patched_options = []
        for option in event_payload.get("options", []):
            new_option = dict(option)
            chance = float(new_option.get("combat_chance", 0.0))
            # Apply difficulty delta and perk multiplier
            new_option["combat_chance"] = max(0.0, min(1.0, (chance + delta) * encounter_multiplier))
            patched_options.append(new_option)
        patched["options"] = patched_options
        return patched

    def _patch_event_for_travel_mode(self, event_payload: Dict[str, Any], travel_mode: str) -> Dict[str, Any]:
        delta = 0.0
        if travel_mode == "rush":
            delta = 0.2
        elif travel_mode == "careful":
            delta = -0.2
        
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
            metadata=payload.get("metadata", {}),
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
        is_elite=payload.get("is_elite", False),
        loot_table=list(payload.get("loot_table", [])),
    )
