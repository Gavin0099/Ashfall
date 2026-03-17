#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import time
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
from src.state_models import PlayerState, CharacterProfile
from src.meta_progression import MetaProfile, RewardCalculator, UPGRADE_METADATA, get_upgrade_cost, ARCHETYPE_UNLOCK_METADATA
from src.help_system import get_help_text, list_topics
from src.repair import calculate_full_repair_cost, repair_equipment

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

# Rarity Colors
RARITY_COLORS = {
    "common": C_WHITE,
    "rare": C_BLUE,
    "legendary": C_YELLOW,
}

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

# Trait Display Info
TRAIT_INFO = {
    "rad_resistant": "輻射適應",
    "ammo_efficient": "扳機紀律",
    "solitary": "獨行者",
    "scav_trained": "廢土直覺",
    "bloodlust": "血性爆發",
    "pack_rat": "負重達人",
}

def clear_screen():
    print("\033[H\033[J", end="")

def show_camp_menu(engine, run):
    """Camp interaction menu."""
    clear_screen()
    draw_header("⛺ 荒野營地 ⛺")
    print(f"\n{C_DIM}風聲在營火旁似乎小了一些。你可以在這裡整頓資源。{C_END}")
    
    while True:
        status_bar = format_status_bar(run.player)
        print(f"\n{status_bar}")
        
        options = [
            "簡單休息 (消耗 1 食物，恢復 2 HP)",
            "深度睡眠 (消耗 2 食物，恢復 3 HP 並減輕 1 點輻射)",
            "整備裝備 (進入整備工坊)",
            "離開營地，繼續前進"
        ]
        
        choice = prompt_index("營地行動：", options)
        
        if choice == 0:
            res = engine.rest_at_camp(run, 0)
            if res["success"]:
                print(f"{C_GREEN}✅ 休息完成。恢復了 {res['gain_hp']} 點生命值。{C_END}")
            else:
                print(f"{C_RED}❌ {res['reason']}{C_END}")
        elif choice == 1:
            res = engine.rest_at_camp(run, 1)
            if res["success"]:
                print(f"{C_GREEN}✅ 深度睡眠完成。恢復了 {res['gain_hp']} 點生命值，輻射降低了 {res.get('gain_rad', 0)}。{C_END}")
            else:
                print(f"{C_RED}❌ {res['reason']}{C_END}")
        elif choice == 2:
            show_refine_menu(engine, run)
            clear_screen()
            draw_header("⛺ 荒野營地 ⛺")
        elif choice == 3:
            break

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
    # Logic for critical alerts
    hp_warn = "!!" if player.hp <= 3 else ""
    food_warn = "!!" if player.food <= 1 else ""
    rad_warn = "!!" if player.radiation > 0 else ""
    
    hp_c = C_RED if player.hp <= 3 else (C_YELLOW if player.hp <= 5 else C_GREEN)
    food_c = C_RED if player.food == 0 else (C_YELLOW if player.food <= 2 else C_GREEN)
    rad_c = C_RED if player.radiation > 0 else C_CYAN
    
    name = "生存者"
    icon = "👤"
    if player.character:
        name = player.character.display_name
        bg_icons = {"vault_technician": "🔧", "raider_defector": "💀", "wasteland_medic": "⚕️"}
        icon = bg_icons.get(player.character.background_id, "👤")
    elif player.archetype:
        arch_info = ARCHETYPE_INFO.get(player.archetype, {"name": "生存者", "icon": "👤"})
        name, icon = arch_info["name"], arch_info["icon"]
    
    level_str = ""
    if player.character:
        level_str = f"｜{C_YELLOW}LV.{player.character.level}{C_END} {C_DIM}({player.character.xp}/{player.character.level*10}){C_END}"

    return (
        f"{C_BOLD}{icon} {name}{level_str}｜{C_END} "
        f"{hp_c}{SYM_HP} {player.hp}{hp_warn}{C_END}   "
        f"{food_c}{SYM_FOOD} {player.food}{food_warn}{C_END}   "
        f"{C_YELLOW}{SYM_AMMO} {player.ammo}{C_END}   "
        f"{C_GREEN}{SYM_MEDKIT} {player.medkits}{C_END}   "
        f"{C_CYAN}{SYM_SCRAP} {player.scrap}{C_END}   "
        f"{rad_c}{SYM_RAD} {player.radiation}{rad_warn}{C_END}"
    )

def format_equipment_durability(equipment) -> str:
    if not equipment:
        return ""
    color = C_GREEN
    ratio = equipment.durability / equipment.max_durability
    if ratio <= 0:
        color = C_RED
    elif ratio <= 0.3:
        color = C_YELLOW
    return f"{color}[{equipment.durability}/{equipment.max_durability}] {C_END}"

def format_special(player: PlayerState) -> str:
    if not player.character: return "無"
    s = player.character.special
    return f"{C_RED}S{s['strength']}{C_END} {C_GREEN}P{s['perception']}{C_END} {C_YELLOW}E{s['endurance']}{C_END} {C_MAGENTA}C{s['charisma']}{C_END} {C_CYAN}I{s['intelligence']}{C_END} {C_BLUE}A{s['agility']}{C_END} {C_WHITE}L{s['luck']}{C_END}"

def handle_level_up(player: PlayerState):
    from src.progression import load_perk_catalog, get_eligible_perks, apply_perk
    import random
    
    catalog = load_perk_catalog()
    eligible = get_eligible_perks(player, catalog)
    
    # Visual flair
    clear_screen()
    draw_header("🌟 LEVEL UP! 🌟")
    
    # HP Recovery Reward
    old_hp = player.hp
    player.hp = min(10, player.hp + 2)
    hp_gain = player.hp - old_hp
    
    print(f"\n{C_BOLD}恭喜！你已達到等級 {C_YELLOW}{player.character.level}{C_END}。{C_END}")
    if hp_gain > 0:
        print(f"{C_GREEN}🎁 升級獎勵：恢復了 {hp_gain} 點生命值！{C_END}")
    
    if not eligible:
        print(f"\n{C_DIM}目前沒有可解鎖的新天賦 (Perk)。{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續冒險...{C_END}")
        return

    # Randomly pick up to 3 perks from eligible list
    pool_size = min(3, len(eligible))
    selection_pool = random.sample(eligible, pool_size)
    
    print(f"\n{C_CYAN}請從以下天賦中挑選一項永久加成：{C_END}\n")
    perk_options = [f"{C_BOLD}{p['display_name']}{C_END}\n    {C_DIM}└─ {p['description']}{C_END}" for p in selection_pool]
    
    choice = prompt_index("選擇天賦：", perk_options)
    selected = selection_pool[choice]
    
    apply_perk(player, selected["id"], catalog)
    print(f"\n{C_GREEN}✅ 獲得天賦：{C_BOLD}{selected['display_name']}{C_END}")
    input(f"\n{C_DIM}按 Enter 繼續冒險...{C_END}")

def resolve_event_interactively(engine, run, node, events, map_state, is_ruins=False):
    """
    Handles picking an event, showing options, and resolving choice.
    Returns: outcome, decision_data
    """
    event_id = pick_event_id(node, engine.rng, run_flags=run.flags, event_catalog=events)
    event_payload = events[event_id]
    
    stage_prefix = f"[探索階層 {run.current_ruins_stage + 1}] " if is_ruins else ""
    print(f"\n{C_CYAN}{'─' * 40}{C_END}\n{C_BOLD}【 {stage_prefix}事件：{event_payload['description']} 】{C_END}")
    rem = estimate_remaining_steps(map_state, node.id)
    
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
        
        filters = opt.get("character_filters")
        if filters:
            req_str_list = []
            req_tags = filters.get("require_any_tag", [])
            for tag in req_tags:
                tag_name = TRAIT_INFO.get(tag, tag)
                req_str_list.append(f"特質:{tag_name}")
            
            req_special = filters.get("require_special", {})
            for attr, limits in req_special.items():
                if "min" in limits:
                    req_str_list.append(f"{attr.upper()}>={limits['min']}")
            
            if req_str_list:
                req_label = " & ".join(req_str_list)
                if info["is_met"]:
                    prefix += f"{C_GREEN}[{req_label}]{C_END} "
                else:
                    prefix += f"{C_RED}[需 {req_label}]{C_END} "
        
        option_lines.append(f"{prefix}{info['text']}{warn_str}")

    # Add Retreat option if it's ruins and not the first stage
    retreat_idx = -1
    if is_ruins and run.current_ruins_stage > 0:
        retreat_idx = len(option_lines)
        option_lines.append(f"{C_YELLOW}[撤退] 帶著目前的收獲離開 (警告：撤退將損失 30% 已得物資){C_END}")

    while True:
        start_time = time.time()
        opt_idx = prompt_index("請選擇行動：", option_lines)
        decision_time_ms = int((time.time() - start_time) * 1000)
        
        if opt_idx == retreat_idx:
            return {"retreat": True}, None
        
        if avail_opts[opt_idx]["is_met"]:
            break
        else:
            opt = avail_opts[opt_idx]["option"]
            req = opt.get("archetype_requirement")
            if req and run.player.archetype != req:
                print(f"{C_RED}❌ 你不符合該選項的職業要求！{C_END}")
            else:
                print(f"{C_RED}❌ 你不符合該選項的特質或屬性要求！{C_END}")

    pre_state = {"hp": run.player.hp, "food": run.player.food, "ammo": run.player.ammo, "medkits": run.player.medkits, "radiation": run.player.radiation}
    outcome = resolve_event_choice(run.player, event_payload, opt_idx, engine.rng)
    
    decision_data = {
        "node": node.id,
        "event_id": event_id,
        "option_index": opt_idx,
        "decision_time_ms": decision_time_ms,
        "pre_choice_state": pre_state
    }
    
    return outcome, decision_data

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
    "sledgehammer": "重型大錘", "tactical_visor": "戰術目鏡",
}
SLOT_LABELS = {"weapon": "武器", "armor": "護甲", "tool": "工具"}
LOOT_LINE_RE = re.compile(r"^戰利品：([a-z_]+) \+(\d+)$")

def format_item_name_only(equipment: Any) -> str:
    if not equipment: return f"{C_DIM}-{C_END}"
    item_id = equipment.id if hasattr(equipment, "id") else str(equipment)
    base_name = ITEM_LABELS.get(item_id, item_id)
    rarity = getattr(equipment, "rarity", "common")
    color = RARITY_COLORS.get(rarity, C_WHITE)
    return f"{color}{base_name}{C_END}"

def format_equipment_item(player: PlayerState, equipment: Any) -> str:
    if not equipment: return f"{C_DIM}-{C_END}"
    name_str = format_item_name_only(equipment)
    
    requirements = getattr(equipment, "requirements", {})
    scaling = getattr(equipment, "scaling", {})
    affixes = getattr(equipment, "affixes", {})
    rarity = getattr(equipment, "rarity", "common")
    
    # Rarity Color
    rarity_c = RARITY_COLORS.get(rarity, C_WHITE)
    
    # Check if requirements met
    met_req = True
    req_details = []
    if player.character:
        for stat, val in requirements.items():
            curr = player.character.special.get(stat, 0)
            if curr < val:
                met_req = False
                req_details.append(f"{C_RED}{stat.upper()} {curr}/{val}{C_END}")
            else:
                req_details.append(f"{C_GREEN}{stat.upper()} {val}{C_END}")

    if not met_req:
        name_str = f"{C_DIM}(未達需求) {C_END}{name_str}"
    
    detail_parts = []
    if req_details:
        detail_parts.append(f"需: {', '.join(req_details)}")
        
    if met_req and player.character:
        for stat, mult in scaling.items():
            bonus = int(player.character.special.get(stat, 5) * mult)
            if bonus > 0:
                detail_parts.append(f"{C_YELLOW}+{bonus} ({stat.upper()}){C_END}")

    affix_map = {"atk": "⚔️", "def": "🛡️", "hp": "❤️"}
    for k, v in affixes.items():
        label = affix_map.get(k, k)
        detail_parts.append(f"{C_CYAN}{label}+{v}{C_END}")

    if not detail_parts: return name_str
    return f"{name_str}｜{'; '.join(detail_parts)}"

def format_equipment(player: PlayerState) -> str:
    return (
        f"武器={format_equipment_item(player, player.weapon_slot)} "
        f"護甲={format_equipment_item(player, player.armor_slot)} "
        f"工具={format_equipment_item(player, player.tool_slot)}"
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

def show_refine_menu(engine: RunEngine, run: RunState):
    while True:
        clear_screen()
        draw_header("── 整備工坊 (Workshop) ──")
        print(f"目前廢料：{C_CYAN}{run.player.scrap}{C_END}\n")
        
        slots = []
        if run.player.weapon_slot: slots.append(("weapon", "武器", run.player.weapon_slot))
        if run.player.armor_slot: slots.append(("armor", "護甲", run.player.armor_slot))
        if run.player.tool_slot: slots.append(("tool", "工具", run.player.tool_slot))
        
        if not slots:
            print("你身上沒有任何可以整備的裝備。")
            input("\n按 Enter 返回...")
            return
            
        slot_opts = [f"{label}: {format_item_name_only(item)} {format_equipment_durability(item)}" for _, label, item in slots]
        slot_opts.append("離開工坊 (Exit)")
        
        s_idx = prompt_index("請選擇要整備的部位：", slot_opts)
        if s_idx == len(slots): break
        
        slot_key, slot_label, item = slots[s_idx]
        
        while True:
            clear_screen()
            draw_header(f"── 整備：{slot_label} ──")
            print(f"項目：{format_item_name_only(item)}")
            print(f"狀態：{format_equipment_durability(item)}")
            
            # Ability Localization
            ability_names = {
                "vampiric": "吸血 (戰勝後+1 HP)",
                "lead_lined": "鉛塑 (移動輻射-1)",
                "scavenger": "拾荒者 (額外廢料)",
                "sturdy": "堅固 (耐久損耗減半)"
            }
            tags_str = ", ".join([ability_names.get(t, t) for t in item.tags]) if item.tags else "無"
            print(f"現有詞綴：{', '.join([f'{k}+{v}' for k, v in item.affixes.items()]) if item.affixes else '無'}")
            print(f"特殊能力：{C_CYAN}{tags_str}{C_END}")
            print(f"剩餘廢料：{C_CYAN}{run.player.scrap}{C_END}\n")
            
            actions = [
                "修復耐久 (2 廢料/點)",
                f"精煉裝備 ({C_YELLOW}{item.get_refine_cost()}{C_END} 廢料 - 提升屬性/稀有度)",
                "返回上層 (Back)"
            ]
            
            a_idx = prompt_index("選擇改造項目：", actions)
            if a_idx == 2: break
            
            if a_idx == 0:
                res = engine.refine_equipment(run, slot_key, "repair")
            else:
                res = engine.refine_equipment(run, slot_key, "refine")
            
            if res["success"]:
                print(f"{C_GREEN}✅ 改造成功！{C_END}")
                if res["action"] == "repair": 
                    print(f"修復了 {res['amount']} 點耐久。")
                elif res["action"] == "refine":
                    if res["promoted"]:
                        print(f"{C_BOLD}{C_YELLOW}★ 稀有度晉升！★{C_END} 現在是 {format_item_name_only(item)}")
                    else:
                        print(f"精煉成功！(精煉等級: {res['refinement_count']})")
                    # Show stat changes if possible
            else:
                reason_map = {
                    "insufficient_scrap": "廢料不足！",
                    "already_max": "耐久度已達上限！",
                    "no_equipment": "該部位無裝備！"
                }
                print(f"{C_RED}❌ 改造失敗：{reason_map.get(res['reason'], res['reason'])}{C_END}")
            
            input("\n按 Enter 繼續...")

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

def show_character_creation() -> tuple[CharacterProfile, dict]:
    bg_path = ROOT / "data" / "backgrounds.json"
    tr_path = ROOT / "data" / "traits.json"
    
    backgrounds = json.loads(bg_path.read_text(encoding="utf-8"))
    traits = json.loads(tr_path.read_text(encoding="utf-8"))
    
    # Name selection
    clear_screen()
    draw_header("👤 角色創建：賦予身份")
    
    while True:
        char_name = input(f"\n{C_YELLOW}請輸入你的名字 (直接 Enter 使用隨機名) > {C_END}").strip()
        if not char_name:
            import random
            random_names = ["艾薩克", "米拉", "卡修斯", "薇拉", "巴雷特", "露娜", "凱恩", "索菲亞"]
            char_name = random.choice(random_names)
            print(f"隨機分配名稱：{C_CYAN}{char_name}{C_END}")
        
        confirm = input(f"確認使用名稱「{char_name}」？ (Y/N) > ").strip().upper()
        if confirm != "N":
            break

    clear_screen()
    draw_header("👤 角色創建：選擇出身背景")
    print(f"你的名字：{C_BOLD}{char_name}{C_END}\n")
    bg_opts = [f"{bg['display_name']} - {bg['description']}" for bg in backgrounds]
    bg_idx = prompt_index("請選擇你的出身：", bg_opts)
    selected_bg = backgrounds[bg_idx]
    
    clear_screen()
    draw_header(f"👤 角色創建：選擇特質 (最多 2 個)")
    print(f"當前背景：{C_BOLD}{selected_bg['display_name']}{C_END}\n")
    
    selected_traits = []
    while len(selected_traits) < 2:
        tr_opts = [f"{tr['display_name']} - {tr['description']}" for tr in traits if tr['trait_id'] not in [t['trait_id'] for t in selected_traits]]
        tr_opts.append(f"{C_GREEN}[完成選擇]{C_END}" if selected_traits else "不選擇特質並開始計畫")
        
        t_idx = prompt_index(f"選擇特質 ({len(selected_traits)}/2)：", tr_opts)
        if t_idx == len(tr_opts) - 1:
            break
        
        # Mapping back to the original traits list
        available_traits = [tr for tr in traits if tr['trait_id'] not in [t['trait_id'] for t in selected_traits]]
        selected_traits.append(available_traits[t_idx])
        print(f"已加入特質：{C_CYAN}{selected_traits[-1]['display_name']}{C_END}")

    # Build Tags
    final_tags = list(selected_bg["granted_tags"])
    for tr in selected_traits:
        final_tags.extend(tr.get("granted_tags", []))
    
    profile = CharacterProfile(
        background_id=selected_bg["background_id"],
        display_name=char_name,
        special=selected_bg["special_preset"],
        traits=[tr["trait_id"] for tr in selected_traits],
        tags=final_tags
    )
    
    return profile, selected_bg.get("starting_resource_bias", {}), selected_bg.get("starting_equipment", {})

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

def show_repair_menu(player: PlayerState):
    while True:
        clear_screen()
        draw_header("🔧 裝備維修站")
        print(f"  {C_CYAN}可用廢料：{C_END} {C_YELLOW}{SYM_SCRAP} {player.scrap}{C_END}\n")
        
        repair_slots = []
        if player.weapon_slot: repair_slots.append("weapon")
        if player.armor_slot: repair_slots.append("armor")
        
        if not repair_slots:
            print("你目前沒有任何可維修的裝備。")
            input(f"\n{C_DIM}按 Enter 返回...{C_END}")
            break
            
        opts = []
        for slot in repair_slots:
            eq = getattr(player, f"{slot}_slot")
            cost = calculate_full_repair_cost(eq)
            status = format_equipment_durability(eq)
            name = format_item_name_only(eq)
            opts.append(f"{SLOT_LABELS.get(slot, slot)}: {name} {status} | {C_YELLOW}修復成本: {cost}{C_END}")
        
        opts.append("返回 (Back)")
        choice = prompt_index("請選擇要維修的裝備：", opts)
        
        if choice == len(repair_slots):
            break
            
        slot = repair_slots[choice]
        if repair_equipment(player, slot):
            print(f"\n{C_GREEN}✅ 維修完成！{SLOT_LABELS.get(slot)} 已恢復至最佳狀態。{C_END}")
        else:
            print(f"\n{C_RED}❌ 維修失敗：可能是廢料不足或裝備已滿。{C_END}")
        input(f"\n{C_DIM}按 Enter 繼續...{C_END}")

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=int, nargs="?", default=101)
    parser.add_argument("--difficulty", type=str, default="normal")
    parser.add_argument("--playtest", action="store_true")
    args = parser.parse_args()

    seed = args.seed
    difficulty = args.difficulty
    is_playtest = args.playtest

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    playtest_session = None
    if is_playtest:
        player_id = input("請輸入測試者 ID (Player ID): ").strip() or "anonymous"
        session_id = f"session_{int(time.time())}"
        playtest_session = {
            "player_id": player_id,
            "session_id": session_id,
            "roguelite_experience": False, # TBD by observer
            "game_dev_background": False,  # TBD by observer
            "run_id": session_id,
            "seed": seed,
            "difficulty": difficulty,
            "events": [],
            "post_run": {
                "hardest_choice": "TBD",
                "perceived_death_cause": "TBD",
                "regret_choice": "TBD",
                "replay_intent": False,
                "judgment_regret_note": "TBD",
                "frustration_regret_note": "TBD",
                "immediate_replay_reason": "TBD"
            }
        }

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
    character, res_bias, start_eq = show_character_creation()

    player = build_starting_player(name=difficulty, character=character, meta_profile=meta_profile, resource_bias=res_bias)
    
    # EXP-4: Equip Starting Items from Background
    from src.item_catalog import catalog
    from src.state_models import equip_item
    for slot, item_id in start_eq.items():
        eq_inst = catalog.create_instance(item_id)
        if eq_inst:
            equip_item(player, slot, eq_inst)

    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies, difficulty=difficulty)
    run = engine.create_run(player, seed=seed)
    print(f"\n{C_DIM}種子：{seed} | 難度：{get_difficulty_profile(difficulty).name}{C_END}\n{C_YELLOW}目標：活到終點山脊。{C_END}\n")

    decision_log, encounter_counter, combat_count = [], Counter(), 0
    current_travel_mode = "normal"
    TRAVEL_MODE_LABELS = {"normal": "正常 (Normal)", "rush": "衝刺 (Rush)", "careful": "謹慎 (Careful)"}

    while not run.ended:
        current = map_state.get_node(run.current_node)
        
        # UI: Show Equipment Durability
        eq_status = []
        if run.player.weapon_slot:
            eq_status.append(f"武器: {ITEM_LABELS.get(run.player.weapon_slot.id, run.player.weapon_slot.id)} {format_equipment_durability(run.player.weapon_slot)}")
        if run.player.armor_slot:
            eq_status.append(f"護甲: {ITEM_LABELS.get(run.player.armor_slot.id, run.player.armor_slot.id)} {format_equipment_durability(run.player.armor_slot)}")
        
        if eq_status:
            print(f"{C_DIM}裝備狀態：{'｜'.join(eq_status)}{C_END}")

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
            
            # EXP-5: Add Workshop option for trade/safe nodes
            can_refine = current.node_type == "trade" or current.id == "node_approach"
            if can_refine:
                route_opts.append(f"{C_YELLOW}[進入整備工坊]{C_END}")
            
            route_opts.append(f"{C_BLUE}[修改旅行模式]{C_END}")
            
            while True:
                start_time = time.time()
                idx = prompt_index(f"{status_header}\n請選擇行動：", route_opts)
                decision_time_ms = int((time.time() - start_time) * 1000)

                # Offset for Workshop option
                workshop_idx = len(current.connections) if can_refine else -1
                mode_idx = len(current.connections) + 1 if can_refine else len(current.connections)

                if idx == workshop_idx:
                    show_refine_menu(engine, run)
                    # Update status and redisplay
                    status_header = (
                        f"目前地帶：{C_YELLOW}{NODE_LABELS.get(run.current_node, run.current_node)}{C_END}\n"
                        f"{format_status_bar(run.player)}\n"
                        f"{C_DIM}裝備：{format_equipment(run.player)}{C_END}｜{C_CYAN}旅行模式：{TRAVEL_MODE_LABELS[current_travel_mode]}{C_END}"
                    )
                    clear_screen()
                    draw_map(engine, run.current_node)
                    continue
                elif idx == mode_idx:
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

        # Phase 3.0: Node Type Handling
        if node.node_type == "camp":
            show_camp_menu(engine, run)
            if run.ended: break

        # Ruins multi-stage exploration or single event
        num_stages = 3 if node.node_type == "ruins" else 1
        run.current_ruins_stage = 0
        run.temporary_loot.clear()

        for stage_idx in range(num_stages):
            run.current_ruins_stage = stage_idx
            outcome, d_data = resolve_event_interactively(engine, run, node, events, map_state, is_ruins=(node.node_type == "ruins"))
            
            if "retreat" in outcome:
                final_loot = engine.finalize_ruins_loot(run, retreat_penalty=True)
                print(f"\n{C_YELLOW}⚠️ 你選擇了撤退。在混亂中損失了部分物資。{C_END}")
                if any(final_loot.values()): print(f"最終帶回：{C_GREEN}{format_loot(final_loot)}{C_END}")
                break

            if outcome["combat_triggered"]:
                combat = engine.resolve_combat(run)
                combat_count += 1
                enemy_id = str(combat["enemy_id"])
                is_elite = combat.get("log", []) and "⚠️" in str(combat["log"][0])
                arch = infer_archetype(enemy_id)
                if arch: encounter_counter[arch] += 1
                print(f"觸發戰鬥：{f'{BG_RED}{C_WHITE} [精英] {C_END} ' if is_elite else ''}{C_BOLD}{ENEMY_LABELS.get(enemy_id, enemy_id)}{C_END}")
                for l in combat["log"]: print(f"  {C_RED}{C_BOLD}{l}{C_END}" if "⚠️" in str(l) else f"  {localize_combat_log_line(str(l))}")
                if combat.get("loot"): 
                    print(f"戰利品：{C_GREEN}{format_loot(combat['loot'])}{C_END}")
                    if node.node_type == "ruins":
                        engine.add_to_temporary_loot(run, combat["loot"])

            if run.player.is_dead(): 
                run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))
                break

            # Process effects: Apply immediately to player, but ruins also tracks for "retreat" penalty display
            # Note: resolve_event_choice already called apply_effects(player, effects)
            event_id = d_data["event_id"]
            opt_idx = d_data["option_index"]
            eff = events[event_id]["options"][opt_idx].get("effects", {})
            
            if node.node_type == "ruins":
                # XP is already added to player, we just track it in temporary_loot for total display
                engine.add_to_temporary_loot(run, eff)
                # But since resolve_event_choice already added objects to player, we must "undo" and move to temp?
                # Actually, simple version: ruins loot is accumulated. To implement retreat penalty, we'd need to subtract.
                # Let's simplify: in Ruins, resolve_event_choice DOES NOT add to player, it only adds to temporary_loot.
                # NO, that requires changing event_engine. 
                # Better: for Ruins, we don't apply retreat penalty to XP/HP, only to PHYSICAL loot (scrap, medkits, etc.)
                print(f"{C_CYAN}📦 已將物資存入臨時背包 (探索中)...{C_END}")
            else:
                if eff: print(f"效果：{format_effects(eff)}")

            eq = outcome.get("equipment_change")
            if eq and eq.get("changed"):
                print(f"取得裝備：{SLOT_LABELS.get(str(eq['slot']))} -> {ITEM_LABELS.get(str(eq['item']), str(eq['item']))}")

            if outcome.get("set_flags"):
                run.flags.update(outcome["set_flags"])
                print(f"{C_CYAN}✨ 任務進度已更新！{C_END}")

            if outcome.get("leveled_up"):
                handle_level_up(run.player)

            # Record decision
            d_data["step"] = len(decision_log) + 1
            d_data["player_after"] = run.player.to_dict()
            decision_log.append(d_data)

            # Playtest session
            if is_playtest and playtest_session is not None:
                playtest_session["events"].append({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "node_id": node.id,
                    "event_id": event_id,
                    "decision_time_ms": d_data["decision_time_ms"],
                    "selected_option": opt_idx,
                    "hesitation_flag": False,
                    "confusion_flag": False,
                    "what_i_thought_happened": "TBD",
                    "why_im_salty": "TBD"
                })

            if node.node_type == "ruins" and stage_idx == num_stages - 1:
                final_loot = engine.finalize_ruins_loot(run, retreat_penalty=False)
                print(f"\n{C_GREEN}✨ 遺蹟探索完成！你成功帶出了所有物資。{C_END}")
                if any(v > 0 for v in final_loot.values() if v is not None):
                    print(f"總計獲取：{C_GREEN}{format_loot(final_loot)}{C_END}")

        if node.is_final and not run.ended: run.end(victory=True, reason="reached_final_node")

    earned_scrap = RewardCalculator.calculate_scrap_reward(len(run.visited_nodes), run.victory, combat_count, run.player.hp)
    meta_profile.total_scrap += earned_scrap
    meta_profile.lifetime_scrap_earned += earned_scrap
    meta_profile.save(meta_path)
    print(f"\n本局結束\n{json.dumps({'勝利': run.victory, '原因': END_REASON_LABELS.get(run.end_reason or '', run.end_reason), '獲得廢料': earned_scrap, '累積廢料': meta_profile.total_scrap}, indent=2, ensure_ascii=False)}")
    
    if is_playtest and playtest_session is not None:
        playtest_session["victory"] = run.victory
        playtest_session["end_reason"] = run.end_reason
        log_path = ROOT / "output" / "playtests" / f"playtest_{playtest_session['player_id']}_{playtest_session['session_id']}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(playtest_session, f, indent=2, ensure_ascii=False)
        print(f"\n{C_GREEN}測試數據已儲存至：{log_path}{C_END}")

    return 0

if __name__ == "__main__": raise SystemExit(main())
