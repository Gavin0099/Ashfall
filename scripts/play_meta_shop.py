#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.meta_progression import MetaProfile

META_PATH = ROOT / "output" / "meta_profile.json"

UPGRADES = {
    "up_health_boost": {"name": "生命上限 (HP Boost)", "desc": "初始生命 +1"},
    "up_food_ration": {"name": "糧食配給 (Food Ration)", "desc": "初始食物 +1"},
    "up_ammo_belt": {"name": "彈藥腰帶 (Ammo Belt)", "desc": "初始彈藥 +1"},
    "up_medkit_stash": {"name": "醫療備品 (Medkit Stash)", "desc": "初始醫療包 +1"},
}

ARCHETYPE_UNLOCKS = {
    "medic": {"name": "醫護兵 (Medic)", "desc": "解鎖醫療背景：醫療包回復量 +1 且初始附帶 1 個。", "cost": 50},
    "scavenger": {"name": "拾荒者 (Scavenger)", "desc": "解鎖拾荒背景：資源獲得加成且初始帶 5 廢料。", "cost": 80},
}

MAX_LEVEL = 5

def get_cost(level: int) -> int:
    return (level + 1) * 10

def main():
    profile = MetaProfile.load(META_PATH)
    
    while True:
        print("\n=== Ashfall Meta Shop ===")
        print(f"擁有廢料 (Available Scrap): {profile.total_scrap}")
        print(f"生涯總收益: {profile.lifetime_scrap_earned}")
        print("-" * 30)
        
        # Upgrades Section
        print("【 基礎升級 (Base Upgrades) 】")
        upgrade_ids = list(UPGRADES.keys())
        for i, uid in enumerate(upgrade_ids):
            details = UPGRADES[uid]
            current_lv = profile.get_level(uid)
            cost = get_cost(current_lv)
            lv_str = f"Lv {current_lv}/{MAX_LEVEL}"
            cost_str = f"Cost: {cost}" if current_lv < MAX_LEVEL else "MAXED"
            print(f"[{i:2d}] {details['name']} ({lv_str})")
            print(f"     {details['desc']} | {cost_str}")
        
        # Archetypes Section
        print("\n【 職業解鎖 (Archetypes) 】")
        arch_ids = list(ARCHETYPE_UNLOCKS.keys())
        arch_offset = len(upgrade_ids)
        for i, aid in enumerate(arch_ids):
            details = ARCHETYPE_UNLOCKS[aid]
            unlocked = profile.is_archetype_unlocked(aid)
            status_str = "OWNED" if unlocked else f"Cost: {details['cost']}"
            index = i + arch_offset
            print(f"[{index:2d}] {details['name']}")
            print(f"     {details['desc']} | {status_str}")
            
        exit_idx = arch_offset + len(arch_ids)
        print(f"\n[{exit_idx:2d}] 離開 (Exit)")
        
        try:
            choice = input(f"\n請輸入序號 (0-{exit_idx})：").strip()
            if not choice: continue
            idx = int(choice)
            
            if idx == exit_idx:
                print("離開商店。")
                break
            
            # Upgrade Branch
            if 0 <= idx < arch_offset:
                uid = upgrade_ids[idx]
                current_lv = profile.get_level(uid)
                if current_lv >= MAX_LEVEL:
                    print("已達到最高等級！")
                    continue
                    
                cost = get_cost(current_lv)
                if profile.total_scrap >= cost:
                    profile.total_scrap -= cost
                    profile.unlock_levels[uid] = current_lv + 1
                    profile.save(META_PATH)
                    print(f"升級成功！{UPGRADES[uid]['name']} 現在等級為 {profile.unlock_levels[uid]}")
                else:
                    print("廢料不足！")
            
            # Archetype Branch
            elif arch_offset <= idx < exit_idx:
                aid = arch_ids[idx - arch_offset]
                if profile.is_archetype_unlocked(aid):
                    print("已經解鎖此職業！")
                    continue
                
                cost = ARCHETYPE_UNLOCKS[aid]["cost"]
                if profile.total_scrap >= cost:
                    profile.total_scrap -= cost
                    profile.unlocked_archetypes.append(aid)
                    profile.save(META_PATH)
                    print(f"解鎖成功！現在可以使用 {ARCHETYPE_UNLOCKS[aid]['name']} 了。")
                else:
                    print("廢料不足！")
            else:
                print("無效的選擇。")
        except ValueError:
            print("請輸入數字。")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
