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
from src.event_engine import pick_event_id, resolve_event_choice, get_available_options
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState
from src.meta_progression import MetaProfile, RewardCalculator, UPGRADE_METADATA, get_upgrade_cost, ARCHETYPE_UNLOCK_METADATA
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
    "node_start": "出發點", "node_north_1": "北線廢車場", "node_north_2": "北線隧道",
    "node_south_1": "南線村落", "node_south_2": "南線氾濫平原", "node_mid": "檢查站",
    "node_final": "終點山脊",
}
ENEMY_LABELS = {"enemy_raider_scout": "掠奪者斥候", "enemy_mutant_brute": "變異巨漢"}
RESOURCE_LABELS = {
    "hp": "生命", "food": "食物", "ammo": "彈藥", "medkits": "醫療包", "scrap": "零件", "radiation": "輻射",
}
END_REASON_LABELS = {
    "reached_final_node": "抵達終點", "starvation": "飢餓而死", "radiation_death": "死於輻射",
    "combat_death": "戰鬥死亡", "event_or_resource_death": "死於事件或資源耗盡", "death": "死亡",
}
ITEM_LABELS = {
    "makeshift_blade": "簡陋刀刃", "rust_rifle": "鏽蝕步槍", "hardened_blade": "強化刃",
    "plate_armor": "板甲", "gas_mask": "防毒面具", "scavenger_kit": "拾荒工具組", "field_pack": "野外背包",
}
SLOT_LABELS = {"weapon": "武器", "armor": "護甲", "tool": "工具"}
LOOT_LINE_RE = re.compile(r"^戰利品：([a-z_]+) \+(\d+)$")

def format_equipment_item(equipment: Any) -> str:
    if not equipment: return "-"
    item_id = equipment.id if hasattr(equipment, "id") else str(equipment)
    base_name = ITEM_LABELS.get(item_id, item_id)
    affixes = getattr(equipment, "affixes", {})
    if not affixes: return base_name
    
    affix_parts = []
    affix_map = {"atk": "⚔️", "def": "🛡️", "hp": "❤️"}
    for k, v in affixes.items():
        label = affix_map.get(k, k)
        affix_parts.append(f"{label}+{v}")
    return f"{base_name} {C_CYAN}({', '.join(affix_parts)}){C_END}"

def format_equipment(player: PlayerState) -> str:
    return (
        f"武器={format_equipment_item(player.weapon_slot)} "
        f"護甲={format_equipment_item(player.armor_slot)} "
        f"工具={format_equipment_item(player.tool_slot)}"
    )

def format_effects(effects: dict[str, int]) -> str:
    parts = [f"{RESOURCE_LABELS.get(k, k)} {v:+d}" for k, v in effects.items()]
    return "，".join(parts)

def format_loot(loot: list[dict[str, Any]]) -> str:
    parts = []
    for item in loot:
        if isinstance(item, dict):
            res, amt = item.get("resource"), item.get("amount")
            if res and amt: parts.append(f"{RESOURCE_LABELS.get(res, res)} +{amt}")
    return "，".join(parts) if parts else "無"

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
    layers = [["node_start"], ["node_north_1", "node_south_1"], ["node_north_2", "node_south_2", "node_mid"], ["node_final"]]
    print(f"\n{C_CYAN}【 區域分佈圖 】{C_END}")
    for i, layer in enumerate(layers):
        line = ""
        for node_id in layer:
            label = NODE_LABELS.get(node_id, node_id)
            if node_id == current_node_id:
                formatted = f"{BG_RED}{C_WHITE} {label} {C_END}"
            else:
                formatted = f"{C_CYAN}[ {label} ]{C_END}"
            line += formatted + "   "
        indent = " " * (i * 4)
        print(f"{indent}{line}")
        if i < len(layers) - 1: print(f"{indent}    │")

def localize_combat_log_line(line: str) -> str:
    match = LOOT_LINE_RE.match(line)
    if not match: return line
    res, amt = match.groups()
    return f"戰利品：{RESOURCE_LABELS.get(res, res)} +{amt}"

def infer_archetype(enemy_id: str) -> str | None:
    if "raider" in enemy_id: return "raider"
    if "mutant" in enemy_id: return "mutant"
    return None

def format_main_archetype(counter: Counter[str]) -> str:
    if not counter: return "無"
    return counter.most_common(1)[0][0]

def show_help_menu():
    topics = list_topics()
    while True:
        print(f"\n{C_CYAN}=== 廢土生存手冊 ==={C_END}")
        for i, tid in enumerate(topics): print(f"  [{i}] {tid.capitalize()}")
        print(f"  [{len(topics)}] 離開 (Exit)")
        raw = input(f"\n{C_YELLOW}請選擇主題 > {C_END}").strip()
        if raw.isdigit():
            idx = int(raw)
            if idx == len(topics): break
            if 0 <= idx < len(topics):
                text = get_help_text(topics[idx])
                if text: print(f"\n{C_GREEN}{'═' * 40}{C_END}\n{text}\n{C_GREEN}{'═' * 40}{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續...{C_END}")
        clear_screen()

def prompt_index(label: str, options: list[str]) -> int:
    while True:
        print(f"\n{C_BOLD}{C_CYAN}▶ {label}{C_END}")
        for idx, opt in enumerate(options): print(f"  {C_CYAN}[{idx}]{C_END} {opt}")
        print(f"  {C_DIM}[H] 幫助/說明 (Help){C_END}")
        raw = input(f"\n{C_YELLOW}指令 > {C_END}").strip().upper()
        if raw == "H":
            show_help_menu()
            continue
        if raw.isdigit() and 0 <= int(raw) < len(options): return int(raw)
        print(f"{C_RED}輸入無效，請重新輸入。{C_END}")

def estimate_remaining_steps(map_state: Any, node_id: str) -> int:
    visited, queue = set(), [(node_id, 0)]
    while queue:
        curr, depth = queue.pop(0)
        if curr in visited: continue
        visited.add(curr)
        node = map_state.get_node(curr)
        if node.is_final: return depth
        for nxt in node.connections: queue.append((nxt, depth + 1))
    return 0

def show_meta_upgrade_menu(meta_profile: MetaProfile, meta_path: Path):
    while True:
        clear_screen()
        draw_header("🛠️ 基地設施 - 永久強化")
        print(f"  {C_CYAN}當前廢料持用量：{C_END} {C_YELLOW}{SYM_SCRAP} {meta_profile.total_scrap}{C_END}\n")
        main_options = ["強化基礎屬性 (Base Upgrades)", "招募專業人才 (Recruit Archetypes)", "離開基地 (Exit)"]
        choice = prompt_index("請選擇設施部門：", main_options)
        if choice == 0: show_attribute_upgrades(meta_profile, meta_path)
        elif choice == 1: show_archetype_unlock_menu(meta_profile, meta_path)
        else: break

def show_attribute_upgrades(meta_profile: MetaProfile, meta_path: Path):
    while True:
        clear_screen()
        draw_header("💉 醫療與訓練中心")
        print(f"  {C_CYAN}當前廢料持用量：{C_END} {C_YELLOW}{SYM_SCRAP} {meta_profile.total_scrap}{C_END}\n")
        up_ids = list(UPGRADE_METADATA.keys())
        opts = []
        for uid in up_ids:
            meta = UPGRADE_METADATA[uid]
            lvl, max_lvl = meta_profile.get_level(uid), meta["max_level"]
            if lvl < max_lvl: opts.append(f"{meta['name']} (Lv.{lvl}/{max_lvl}) - {meta['desc']} | {C_YELLOW}成本: {get_upgrade_cost(lvl)}{C_END}")
            else: opts.append(f"{meta['name']} (Lv.{lvl}/{max_lvl}) - {C_GREEN}[已達最大等級]{C_END}")
        opts.append("返回上一層 (Back)")
        choice = prompt_index("請選擇強化項目：", opts)
        if choice == len(up_ids): break
        uid = up_ids[choice]
        if meta_profile.purchase_upgrade(uid):
            meta_profile.save(meta_path)
            print(f"\n{C_GREEN}✅ 強化成功！{C_END}")
        else: print(f"\n{C_RED}❌ 強化失敗：廢料不足或已達等級上限。{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續...{C_END}")

def show_archetype_unlock_menu(meta_profile: MetaProfile, meta_path: Path):
    while True:
        clear_screen()
        draw_header("🤝 隊友招募中心")
        print(f"  {C_CYAN}當前廢料持用量：{C_END} {C_YELLOW}{SYM_SCRAP} {meta_profile.total_scrap}{C_END}\n")
        locked_ids = [uid for uid in ARCHETYPE_UNLOCK_METADATA.keys() if uid not in meta_profile.unlocked_archetypes]
        if not locked_ids:
            print(f"{C_GREEN}所有的專業人才都已加入你的基地！{C_END}")
            input(f"\n{C_DIM}按 Enter 返回...{C_END}")
            break
        opts = [f"{ARCHETYPE_UNLOCK_METADATA[uid]['name']} - {ARCHETYPE_UNLOCK_METADATA[uid]['desc']} | {C_YELLOW}成本: {ARCHETYPE_UNLOCK_METADATA[uid]['cost']}{C_END}" for uid in locked_ids]
        opts.append("返回上一層 (Back)")
        choice = prompt_index("請選擇要解鎖的職業：", opts)
        if choice == len(locked_ids): break
        uid = locked_ids[choice]
        if meta_profile.unlock_archetype(uid):
            meta_profile.save(meta_path)
            print(f"\n{C_GREEN}✅ 招募成功！{uid.capitalize()} 已加入你的隊伍。{C_END}")
        else: print(f"\n{C_RED}❌ 招募失敗：廢料不足。{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續...{C_END}")

def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    difficulty = sys.argv[2] if len(sys.argv) > 2 else "normal"
    nodes, enemies = build_node_payloads(), build_enemy_catalog()
    events = build_event_catalog(seed)
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    meta_path = ROOT / "output" / "meta_profile.json"
    meta_profile = MetaProfile.load(meta_path)

    while True:
        clear_screen()
        draw_header("ASHFALL — 荒廢世界冒險")
        mc = prompt_index("首頁選單：", ["進入荒野 (Start Run)", "升級基地 (Upgrade Base)", "查看手冊 (Help)"])
        if mc == 0: break
        elif mc == 1: show_meta_upgrade_menu(meta_profile, meta_path)
        elif mc == 2: show_help_menu()

    clear_screen()
    draw_header("背景與職業選擇")
    available_archs = meta_profile.unlocked_archetypes
    arch_options = [f"{ARCHETYPE_INFO[a]['icon']} {ARCHETYPE_INFO[a]['name']} - {ARCHETYPE_INFO[a]['desc']}" for a in available_archs]
    arch_idx = prompt_index("請選擇你的背景職業：", arch_options)
    selected_archetype = available_archs[arch_idx]

    player = build_starting_player(name=difficulty, archetype=selected_archetype, meta_profile=meta_profile)
    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies, difficulty=difficulty)
    run = engine.create_run(player, seed=seed)
    print(f"\n{C_DIM}種子：{seed} | 難度：{get_difficulty_profile(difficulty).name}{C_END}\n{C_YELLOW}目標：活到終點山脊。{C_END}\n")

    decision_log, encounter_counter, combat_count = [], Counter(), 0
    current_travel_mode = "normal"
    TRAVEL_MODE_LABELS = {"normal": "正常 (Normal)", "rush": "衝刺 (Rush)", "careful": "謹慎 (Careful)"}

    while not run.ended:
        current = map_state.get_node(run.current_node)
        if current.connections:
            if run.player.radiation > 0:
                print(f"警告：每次移動都會受輻射失去 1 HP。目前輻射={run.player.radiation}")
                if run.player.hp <= run.player.radiation + 1: print("危急：再走一次你可能會直接死亡。")
            draw_map(engine, run.current_node)
            
            # Persistent Travel Mode UI
            status_header = (
                f"目前地帶：{C_YELLOW}{NODE_LABELS.get(run.current_node, run.current_node)}{C_END}\n"
                f"{format_status_bar(run.player)}\n"
                f"{C_DIM}裝備：{format_equipment(run.player)}{C_END}｜{C_CYAN}旅行模式：{TRAVEL_MODE_LABELS[current_travel_mode]}{C_END}"
            )
            
            # Combine Route Selection and Mode Change
            route_opts = [NODE_LABELS.get(nid, nid) for nid in current.connections]
            route_opts.append(f"{C_BLUE}[修改旅行模式]{C_END}")
            
            while True:
                idx = prompt_index(f"{status_header}\n請選擇行動：", route_opts)
                if idx == len(current.connections):
                    # Change mode
                    new_mode_idx = prompt_index("請選擇新的旅行模式：", list(TRAVEL_MODE_LABELS.values()))
                    current_travel_mode = list(TRAVEL_MODE_LABELS.keys())[new_mode_idx]
                    # Update status header and redisplay
                    status_header = (
                        f"目前地帶：{C_YELLOW}{NODE_LABELS.get(run.current_node, run.current_node)}{C_END}\n"
                        f"{format_status_bar(run.player)}\n"
                        f"{C_DIM}裝備：{format_equipment(run.player)}{C_END}｜{C_CYAN}旅行模式：{TRAVEL_MODE_LABELS[current_travel_mode]}{C_END}"
                    )
                    clear_screen()
                    draw_map(engine, run.current_node)
                    continue
                else:
                    target_node_id = current.connections[idx]
                    break
            
            hp_b, food_b = run.player.hp, run.player.food
            node = engine.move_to(run, target_node_id, travel_mode=current_travel_mode)
            if run.player.radiation > 0 and run.player.hp < hp_b: print(f"因輻射失去 {hp_b - run.player.hp} HP。")
            if run.player.food < food_b: print(f"移動消耗 {food_b - run.player.food} 食物。")
            if run.ended: break
        else: node = current

        event_id = pick_event_id(node, engine.rng, run_flags=run.flags, event_catalog=events)
        event_payload = events[event_id]
        print(f"\n{C_CYAN}{'─' * 40}{C_END}\n{C_BOLD}【 事件：{event_payload['description']} 】{C_END}")
        rem = estimate_remaining_steps(map_state, node.id)
        
        # v0.9 Archetype Options
        from src.event_engine import get_available_options
        avail_opts = get_available_options(run.player, event_payload)
        
        option_lines = []
        for i, info in enumerate(avail_opts):
            opt = info["option"]
            warnings = build_warning_signals(run.player, event_payload, i, rem)
            warn_str = f" [{'；'.join([localize_warning(w) for w in warnings])}]" if warnings else ""
            
            prefix = ""
            if info["requirement"]:
                arch_name = ARCHETYPE_INFO.get(info["requirement"], {}).get("name", info["requirement"])
                if info["is_met"]:
                    prefix = f"{C_GREEN}[{arch_name}專屬]{C_END} "
                else:
                    prefix = f"{C_RED}[僅限 {arch_name}]{C_END} "
            
            option_lines.append(f"{prefix}{info['text']}{warn_str}")

        while True:
            opt_idx = prompt_index("請選擇行動：", option_lines)
            if avail_opts[opt_idx]["is_met"]:
                break
            else:
                print(f"{C_RED}❌ 你不符合該選項的職業要求！{C_END}")

        pre_state = {"hp": run.player.hp, "food": run.player.food, "ammo": run.player.ammo, "medkits": run.player.medkits, "radiation": run.player.radiation}
        outcome = resolve_event_choice(run.player, event_payload, opt_idx, engine.rng)

        if outcome["combat_triggered"]:
            combat = engine.resolve_combat(run)
            combat_count += 1
            enemy_id = str(combat["enemy_id"])
            is_elite = combat.get("log", []) and "⚠️" in str(combat["log"][0])
            arch = infer_archetype(enemy_id)
            if arch: encounter_counter[arch] += 1
            print(f"觸發戰鬥：{f'{BG_RED}{C_WHITE} [精英] {C_END} ' if is_elite else ''}{C_BOLD}{ENEMY_LABELS.get(enemy_id, enemy_id)}{C_END}")
            for l in combat["log"]: print(f"  {C_RED}{C_BOLD}{l}{C_END}" if "⚠️" in str(l) else f"  {localize_combat_log_line(str(l))}")
            if combat.get("loot"): print(f"戰利品：{C_GREEN}{format_loot(combat['loot'])}{C_END}")

        if run.player.is_dead(): run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))
        eff = event_payload["options"][opt_idx].get("effects")
        if eff: print(f"效果：{format_effects(eff)}")
        eq = outcome.get("equipment_change")
        if eq and eq.get("changed"): print(f"取得裝備：{SLOT_LABELS.get(str(eq['slot']))} -> {ITEM_LABELS.get(str(eq['item']), str(eq['item']))}")
        
        # v0.9 Update Run Flags
        if outcome.get("set_flags"):
            run.flags.update(outcome["set_flags"])
            print(f"{C_CYAN}✨ 任務進度已更新！{C_END}")
        
        decision_log.append({"step": len(decision_log)+1, "node": node.id, "event_id": event_id, "option_index": opt_idx, "pre_choice_state": pre_state, "player_after": run.player.to_dict()})
        if node.is_final and not run.ended: run.end(victory=True, reason="reached_final_node")

    earned_scrap = RewardCalculator.calculate_scrap_reward(len(run.visited_nodes), run.victory, combat_count, run.player.hp)
    meta_profile.total_scrap += earned_scrap
    meta_profile.lifetime_scrap_earned += earned_scrap
    meta_profile.save(meta_path)
    print(f"\n本局結束\n{json.dumps({'勝利': run.victory, '原因': END_REASON_LABELS.get(run.end_reason or '', run.end_reason), '獲得廢料': earned_scrap, '累積廢料': meta_profile.total_scrap}, indent=2, ensure_ascii=False)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
