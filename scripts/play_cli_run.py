#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import (
    analyze_failure,
    build_enemy_catalog,
    build_event_catalog,
    build_node_payloads,
    build_warning_signals,
)
from src.difficulty import build_starting_player, get_difficulty_profile
from src.event_engine import pick_event_id, resolve_event_choice
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState
from src.meta_progression import MetaProfile, RewardCalculator
from src.help_system import get_help_text, list_topics

# --- UI CONSTANTS ---
C_END = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
BG_RED = "\033[41m"
BG_BLACK = "\033[40m"

# UI Symbols
SYM_HP = "❤"
SYM_FOOD = "🍞"
SYM_AMMO = "🔫"
SYM_MEDKIT = "🩹"
SYM_SCRAP = "⚙"
SYM_RAD = "☢"

# Archetype Display Info
ARCHETYPE_INFO = {
    "soldier": {"name": "士兵", "icon": "🎖️", "desc": "戰後存活可回復 1 HP，且戰鬥防禦較高。"},
    "pathfinder": {"name": "開路者", "icon": "🧭", "desc": "精於規劃。首次旅行不消耗食物。"},
    "medic": {"name": "醫護兵", "icon": "⚕️", "desc": "專業治療。醫療包回復量 +1 且初始附帶 1 個。"},
    "scavenger": {"name": "拾荒者", "icon": "🎒", "desc": "資源直覺。事件獲得資源時額外 +1 且初始帶 5 廢料。"},
}

def clear_screen():
    print("\033[H\033[J", end="")

def draw_header(title: str):
    width = 60
    print(f"\n{C_CYAN}╔{'═' * (width-2)}╗{C_END}")
    print(f"{C_CYAN}║{C_BOLD}{title:^{width-2}}{C_CYAN}║{C_END}")
    print(f"{C_CYAN}╚{'═' * (width-2)}╝{C_END}")

def boxed_text(text: str, color=C_WHITE, width=60):
    lines = text.split("\n")
    print(f"{color}┌{'─' * (width-2)}┐{C_END}")
    for line in lines:
        # Simple wrap handling would be better, but for now:
        print(f"{color}│ {line:<{width-4}} │{C_END}")
    print(f"{color}└{'─' * (width-2)}┘{C_END}")

def format_status_bar(player: PlayerState) -> str:
    hp_c = C_GREEN if player.hp > 5 else C_RED
    food_c = C_GREEN if player.food > 2 else C_YELLOW
    rad_c = C_RED if player.radiation > 0 else C_CYAN
    
    arch_info = ARCHETYPE_INFO.get(player.archetype, {"name": "生存者", "icon": "👤"})
    
    return (
        f"{C_BOLD}{arch_info['icon']} {arch_info['name']}｜{C_END} "
        f"{hp_c}{SYM_HP} {player.hp}{C_END}  "
        f"{food_c}{SYM_FOOD} {player.food}{C_END}  "
        f"{C_YELLOW}{SYM_AMMO} {player.ammo}{C_END}  "
        f"{C_GREEN}{SYM_MEDKIT} {player.medkits}{C_END}  "
        f"{C_CYAN}{SYM_SCRAP} {player.scrap}{C_END}  "
        f"{rad_c}{SYM_RAD} {player.radiation}{C_END}"
    )


OUTPUT_DIR = ROOT / "output" / "cli"
NODE_LABELS = {
    "node_start": "出發點",
    "node_north_1": "北線廢車場",
    "node_north_2": "北線隧道",
    "node_south_1": "南線村落",
    "node_south_2": "南線氾濫平原",
    "node_mid": "檢查站",
    "node_final": "終點山脊",
}
ENEMY_LABELS = {
    "enemy_raider_scout": "掠奪者斥候",
    "enemy_mutant_brute": "變異巨漢",
}
ARCHETYPE_LABELS = {
    "raider": "raider",
    "mutant": "mutant",
}
RESOURCE_LABELS = {
    "hp": "生命",
    "food": "食物",
    "ammo": "彈藥",
    "medkits": "醫療包",
    "scrap": "零件",
    "radiation": "輻射",
}
END_REASON_LABELS = {
    "reached_final_node": "抵達終點",
    "starvation": "飢餓而死",
    "radiation_death": "死於輻射",
    "combat_death": "戰鬥死亡",
    "event_or_resource_death": "死於事件或資源耗盡",
    "death": "死亡",
}
BACKGROUND_LABELS = {
    "soldier": "士兵 (Soldier)",
    "medic": "醫護兵 (Medic)",
    "scavenger": "拾荒者 (Scavenger)",
    "pathfinder": "開拓者 (Pathfinder)",
}
TRAVEL_MODE_LABELS = {
    "normal": "常規 (Normal)",
    "rush": "衝刺 (Rush)",
    "careful": "謹慎 (Careful)",
}
ITEM_LABELS = {
    "makeshift_blade": "簡陋刀刃",
    "rust_rifle": "鏽蝕步槍",
    "hardened_blade": "強化刃",
    "plate_armor": "板甲",
    "gas_mask": "防毒面具",
    "scavenger_kit": "拾荒工具組",
    "field_pack": "野外背包",
}
SLOT_LABELS = {"weapon": "武器", "armor": "護甲", "tool": "工具"}
LOOT_LINE_RE = re.compile(r"^戰利品：([a-z_]+) \+(\d+)$")


def format_status(player: PlayerState) -> str:
    arch_info = ARCHETYPE_INFO.get(player.archetype, {"name": "生存者", "icon": "👤"})
    return (
        f"背景：{arch_info['icon']} {arch_info['name']}\n"
        f"狀態：生命={player.hp} 食物={player.food} 彈藥={player.ammo} "
        f"醫療包={player.medkits} 零件={player.scrap} 輻射={player.radiation}"
    )


def format_equipment_item(equipment: Any) -> str:
    if not equipment:
        return "-"
    # Support both old string format and new EquipmentState object
    item_id = equipment.id if hasattr(equipment, "id") else str(equipment)
    base_name = ITEM_LABELS.get(item_id, item_id)
    
    affixes = getattr(equipment, "affixes", {})
    if not affixes:
        return base_name
    
    affix_parts = []
    for k, v in affixes.items():
        affix_parts.append(f"{k}+{v}")
    return f"{base_name}({', '.join(affix_parts)})"


def format_equipment(player: PlayerState) -> str:
    return (
        f"武器={format_equipment_item(player.weapon_slot)} "
        f"護甲={format_equipment_item(player.armor_slot)} "
        f"工具={format_equipment_item(player.tool_slot)}"
    )


def format_effects(effects: dict[str, int]) -> str:
    parts: list[str] = []
    for key, value in effects.items():
        parts.append(f"{RESOURCE_LABELS.get(key, key)} {value:+d}")
    return "，".join(parts)


def format_loot(loot: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in loot:
        if not isinstance(item, dict):
            continue
        resource = item.get("resource")
        amount = item.get("amount")
        if isinstance(resource, str) and isinstance(amount, int):
            parts.append(f"{RESOURCE_LABELS.get(resource, resource)} +{amount}")
    return "，".join(parts) if parts else "無"


def format_equipment_change(equipment_change: dict[str, Any] | None) -> str | None:
    if not equipment_change or not equipment_change.get("changed"):
        return None
    slot = SLOT_LABELS.get(str(equipment_change["slot"]), str(equipment_change["slot"]))
    item_id = str(equipment_change["item"])
    item_name = ITEM_LABELS.get(item_id, item_id)
    
    # Check for affixes in current player state (since equip_item just happened)
    # This is a bit of a hack but works for the CLI display
    return f"{slot} -> {item_name}"


def localize_warning(text: str) -> str:
    replacements = {
        "WARNING: radiation will continue to threaten future travel.": "警告：輻射會持續威脅後續移動。",
        "WARNING: this option adds radiation and increases long-term risk.": "警告：這個選項會增加輻射，拉高長期風險。",
        "CRITICAL: another irradiated move may kill you.": "危急：再走一次帶輻射的路，你可能會直接死亡。",
        "WARNING: food is low and route slack is nearly gone.": "警告：食物偏低，路線容錯快耗盡了。",
        "DANGER: this choice carries a high combat risk.": "危險：這個選項有很高的戰鬥風險。",
        "CRITICAL: no medkits remain to buffer future radiation attrition.": "危急：你已經沒有醫療包，之後很難承受輻射消耗。",
    }
    return replacements.get(text, text)


def draw_map(engine: RunEngine, current_node_id: str):
    """Simple horizontal ASCII map visualization."""
    # Define layers based on logical progression
    layers = [
        ["node_start"],
        ["node_north_1", "node_south_1"],
        ["node_north_2", "node_south_2", "node_mid"],
        ["node_final"]
    ]
    
    print(f"\n{C_CYAN}【 區域分佈圖 】{C_END}")
    for i, layer in enumerate(layers):
        line = ""
        for node_id in layer:
            label = NODE_LABELS.get(node_id, node_id)
            is_current = node_id == current_node_id
            
            if is_current:
                formatted = f"{BG_RED}{C_WHITE} {label} {C_END}"
            else:
                # Check if it was visited or reachable
                formatted = f"{C_CYAN}[ {label} ]{C_END}"
            
            line += formatted + "   "
        
        indent = " " * (i * 4)
        print(f"{indent}{line}")
        if i < len(layers) - 1:
            print(f"{indent}    │")
    print()


def localize_combat_log_line(line: str) -> str:
    match = LOOT_LINE_RE.match(line)
    if not match:
        return line
    resource, amount = match.groups()
    return f"戰利品：{RESOURCE_LABELS.get(resource, resource)} +{amount}"


def infer_archetype(enemy_id: str) -> str | None:
    if "raider" in enemy_id:
        return "raider"
    if "mutant" in enemy_id:
        return "mutant"
    return None


def format_main_archetype(counter: Counter[str]) -> str:
    if not counter:
        return "無"
    archetype = counter.most_common(1)[0][0]
    return ARCHETYPE_LABELS.get(archetype, archetype)


def show_help_menu():
    topics = list_topics()
    while True:
        print(f"\n{C_CYAN}=== 廢土生存手冊 ==={C_END}")
        for i, tid in enumerate(topics):
            print(f"  [{i}] {tid.capitalize()}")
        print(f"  [{len(topics)}] 離開 (Exit)")
        
        raw = input(f"\n{C_YELLOW}請選擇主題 > {C_END}").strip()
        if raw.isdigit():
            idx = int(raw)
            if idx == len(topics):
                break
            if 0 <= idx < len(topics):
                text = get_help_text(topics[idx])
                if text:
                    print(f"\n{C_GREEN}{'═' * 40}{C_END}")
                    print(text)
                    print(f"{C_GREEN}{'═' * 40}{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續...{C_END}")
        clear_screen()


def prompt_index(label: str, options: list[str]) -> int:
    while True:
        print(f"\n{C_BOLD}{C_CYAN}▶ {label}{C_END}")
        for index, option in enumerate(options):
            print(f"  {C_CYAN}[{index}]{C_END} {option}")
        print(f"  {C_DIM}[H] 幫助/說明 (Help){C_END}")
        
        raw = input(f"\n{C_YELLOW}指令 > {C_END}").strip().upper()
        if raw == "H":
            show_help_menu()
            # Redisplay the prompt
            print(f"\n{C_BOLD}{C_CYAN}▶ {label}{C_END}")
            for index, option in enumerate(options):
                print(f"  {C_CYAN}[{index}]{C_END} {option}")
            print(f"  {C_DIM}[H] 幫助/說明 (Help){C_END}")
            continue
            
        if raw.isdigit() and 0 <= int(raw) < len(options):
            return int(raw)
        print(f"{C_RED}輸入無效，請重新輸入。{C_END}")


def estimate_remaining_steps(map_state: Any, node_id: str) -> int:
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(node_id, 0)]
    while queue:
        current, depth = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = map_state.get_node(current)
        if node.is_final:
            return depth
        for nxt in node.connections:
            queue.append((nxt, depth + 1))
    return 0


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    difficulty = sys.argv[2] if len(sys.argv) > 2 else "normal"
    difficulty_profile = get_difficulty_profile(difficulty)
    nodes = build_node_payloads()
    events = build_event_catalog(seed)
    enemies = build_enemy_catalog()
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    # Meta Progression Load
    meta_path = ROOT / "output" / "meta_profile.json"
    meta_profile = MetaProfile.load(meta_path)

    clear_screen()
    draw_header("ASHFALL — 荒廢世界冒險")
    
    # Archetype Selection
    available_archs = meta_profile.unlocked_archetypes
    arch_options = [f"{ARCHETYPE_INFO[a]['icon']} {ARCHETYPE_INFO[a]['name']} - {ARCHETYPE_INFO[a]['desc']}" for a in available_archs]
    arch_idx = prompt_index("請選擇你的背景職業：", arch_options)
    selected_archetype = available_archs[arch_idx]

    player = build_starting_player(
        name=difficulty, 
        archetype=selected_archetype,
        meta_profile=meta_profile
    )
    
    engine = RunEngine(
        map_state=map_state,
        seed=seed,
        event_catalog=events,
        enemy_catalog=enemies,
        difficulty=difficulty,
    )
    
    run = engine.create_run(player, seed=seed)

    print(f"\n{C_DIM}種子：{seed} | 難度：{difficulty_profile.name}{C_END}")
    print(f"{C_YELLOW}目標：活到終點山脊。{C_END}\n")

    decision_log: list[dict[str, Any]] = []
    encounter_counter: Counter[str] = Counter()
    combat_count = 0

    while not run.ended:
        current = map_state.get_node(run.current_node)
        if current.connections:
            if run.player.radiation > 0:
                print(
                    "警告：每次移動都會因輻射額外失去 1 點生命。"
                    f" 目前輻射={run.player.radiation}"
                )
                if run.player.hp <= run.player.radiation + 1:
                    print("危急：再走一次帶輻射的路，你可能會直接死亡。")

            draw_map(engine, run.current_node)
            
            mode_choice = prompt_index(
                (
                    f"目前位置：{C_YELLOW}{NODE_LABELS.get(run.current_node, run.current_node)}{C_END}\n"
                    f"{format_status_bar(run.player)}\n"
                    f"{C_DIM}裝備：{format_equipment(run.player)}{C_END}\n"
                    "請選擇旅行模式："
                ),
                [TRAVEL_MODE_LABELS[m] for m in ["normal", "rush", "careful"]]
            )
            travel_mode = ["normal", "rush", "careful"][mode_choice]

            route_choice = prompt_index(
                "請選擇下一條路線：",
                [NODE_LABELS.get(node_id, node_id) for node_id in current.connections],
            )
            next_node = current.connections[route_choice]
            hp_before_move = run.player.hp
            food_before_move = run.player.food
            node = engine.move_to(run, next_node, travel_mode=travel_mode)
            if run.player.radiation > 0 and run.player.hp < hp_before_move:
                print(f"移動時因輻射失去了 {hp_before_move - run.player.hp} 點生命。")
            if run.player.food < food_before_move:
                print(f"移動消耗了 {food_before_move - run.player.food} 點食物。")
            if run.ended:
                break
        else:
            node = current

        event_id = pick_event_id(node, engine.rng, run_flags=run.flags, event_catalog=events)
        event_payload = events[event_id]
        remaining_steps = estimate_remaining_steps(map_state, node.id)
        
        # Event Presentation
        print(f"\n{C_CYAN}{'─' * 40}{C_END}")
        print(f"{C_BOLD}【 事件：{event_payload['description']} 】{C_END}")

        option_lines: list[str] = []
        warning_cache: list[list[str]] = []
        for index, option in enumerate(event_payload["options"]):
            warnings = build_warning_signals(run.player, event_payload, index, remaining_steps)
            warning_cache.append(warnings)
            localized_warnings = [localize_warning(warning) for warning in warnings]
            warning_label = f" [{'；'.join(localized_warnings)}]" if localized_warnings else ""
            option_lines.append(f"{option['text']}{warning_label}")

        option_index = prompt_index("請選擇一個行動：", option_lines)
        pre_choice_state = {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "radiation": run.player.radiation,
        }
        outcome = resolve_event_choice(run.player, event_payload, option_index, engine.rng)

        if outcome["combat_triggered"]:
            combat = engine.resolve_combat(run)
            combat_count += 1
            outcome["combat"] = combat
            enemy_id = str(combat["enemy_id"])
            enemy_label = ENEMY_LABELS.get(enemy_id, enemy_id)
            archetype = infer_archetype(enemy_id)
            if archetype:
                encounter_counter[archetype] += 1
            print(f"觸發戰鬥：{enemy_label}")
            for line in combat["log"]:
                print(f"  {localize_combat_log_line(str(line))}")
            loot = list(combat.get("loot", []))
            if loot:
                print(f"戰利品摘要：{format_loot(loot)}")

        if run.player.is_dead():
            run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))

        effects = dict(event_payload["options"][option_index].get("effects", {}))
        if effects:
            print(f"效果：{format_effects(effects)}")

        equipment_change = outcome.get("equipment_change")
        equipment_summary = format_equipment_change(equipment_change)
        if equipment_summary:
            print(f"取得裝備：{equipment_summary}")

        scavenger_bonus = outcome.get("scavenger_bonus", {})
        if scavenger_bonus:
            print(f"背景或工具加成：{format_effects(scavenger_bonus)}")

        if run.player.radiation > pre_choice_state["radiation"]:
            print(f"警告：你的輻射升到 {run.player.radiation}。")
        if run.player.hp <= 3 and run.player.radiation > 0:
            print("危急：你的生命已經很低，現在很難承受後續輻射消耗。")

        decision_log.append(
            {
                "step": len(decision_log) + 1,
                "node": node.id,
                "event_id": event_id,
                "option_index": option_index,
                "warning_signals": warning_cache[option_index],
                "pre_choice_state": pre_choice_state,
                "pressure": bool(warning_cache[option_index]),
                "combat_triggered": bool(outcome.get("combat_triggered", False)),
                "combat_loot": list(outcome.get("combat", {}).get("loot", [])) if outcome.get("combat_triggered", False) else [],
                "effects": effects,
                "equipment_change": equipment_change,
                "equipment_summary": equipment_summary,
                "player_after": {
                    "hp": run.player.hp,
                    "food": run.player.food,
                    "ammo": run.player.ammo,
                    "medkits": run.player.medkits,
                    "radiation": run.player.radiation,
                    "weapon_slot": run.player.weapon_slot,
                    "armor_slot": run.player.armor_slot,
                    "tool_slot": run.player.tool_slot,
                },
            }
        )

        if node.is_final and not run.ended:
            run.end(victory=True, reason="reached_final_node")

    failure_analysis = analyze_failure(decision_log, run.ended, run.victory, run.end_reason)
    result = {
        "seed": seed,
        "difficulty": difficulty_profile.name,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "main_archetype": format_main_archetype(encounter_counter),
        "player_final": {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "scrap": run.player.scrap,
            "radiation": run.player.radiation,
            "weapon_slot": run.player.weapon_slot,
            "armor_slot": run.player.armor_slot,
            "tool_slot": run.player.tool_slot,
        },
        "decision_log": decision_log,
        "failure_analysis": failure_analysis,
    }
    output_path = OUTPUT_DIR / f"latest_seed_{seed}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Meta Progression Reward
    nodes_visited = len(run.visited_nodes)
    enemies_defeated = combat_count
    earned_scrap = RewardCalculator.calculate_scrap_reward(
        nodes_visited=nodes_visited,
        reached_final_node=run.victory,
        enemies_defeated=enemies_defeated,
        ending_hp=run.player.hp
    )
    
    meta_profile.total_scrap += earned_scrap
    meta_profile.lifetime_scrap_earned += earned_scrap
    meta_profile.save(meta_path)

    print("\n本局結束")
    print(
        json.dumps(
            {
                "勝利": run.victory,
                "結束原因": END_REASON_LABELS.get(run.end_reason or "", run.end_reason),
                "獲得廢料 (Meta Scrap)": earned_scrap,
                "累積廢料": meta_profile.total_scrap,
                "失敗分析": failure_analysis,
                "主要遭遇": format_main_archetype(encounter_counter),
                "最終裝備": format_equipment(run.player),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"結果已寫入：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
