#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

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
from src.event_engine import pick_event_id, resolve_event_choice
from src.run_engine import RunEngine, build_map
from src.state_models import PlayerState


OUTPUT_DIR = ROOT / "output" / "cli"
NODE_LABELS = {
    "node_start": "出發點",
    "node_north_1": "北線廢車場",
    "node_north_2": "北線崩塌隧道",
    "node_south_1": "南線荒村集市",
    "node_south_2": "南線泥濘氾濫地",
    "node_mid": "中央檢查站",
    "node_final": "終點山脊",
}

ENEMY_LABELS = {
    "enemy_raider_scout": "掠奪者斥候",
    "enemy_mutant_brute": "變種蠻兵",
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
    "starvation": "食物耗盡",
    "radiation_death": "死於輻射",
    "combat_death": "死於戰鬥",
    "event_or_resource_death": "死於事件或資源耗盡",
    "death": "死亡",
}


def format_status(player: PlayerState) -> str:
    return (
        f"生命={player.hp} 食物={player.food} 彈藥={player.ammo} "
        f"醫療包={player.medkits} 輻射={player.radiation}"
    )


def format_effects(effects: dict[str, int]) -> str:
    parts = []
    for key, value in effects.items():
        label = RESOURCE_LABELS.get(key, key)
        parts.append(f"{label} {value:+d}")
    return "，".join(parts)


def format_node(node_id: str) -> str:
    return NODE_LABELS.get(node_id, node_id)


def localize_warning(text: str) -> str:
    replacements = {
        "WARNING: radiation will continue to threaten future travel.": "警告：輻射會持續威脅後續移動。",
        "WARNING: this option adds radiation and increases long-term risk.": "警告：這個選項會增加輻射，拉高長期風險。",
        "CRITICAL: another irradiated move may kill you.": "危急：再進行一次帶輻射的移動，你可能會死亡。",
        "WARNING: food is low and route slack is nearly gone.": "警告：食物偏低，路線容錯已經快耗盡。",
        "DANGER: this choice carries a high combat risk.": "危險：這個選項有很高的戰鬥風險。",
        "CRITICAL: no medkits remain to buffer future radiation attrition.": "危急：你已經沒有醫療包，之後很難承受輻射消耗。",
        "radiation will burn you for 1 HP on travel": "移動時會受到 1 點輻射傷害",
        "Current radiation": "目前輻射值",
        "another irradiated move may kill you": "再移動一次你可能就會死",
        "high radiation risk": "高輻射風險",
        "low food": "食物偏低",
        "low hp": "生命偏低",
        "low ammo": "彈藥偏低",
        "medkit last charge": "醫療包只剩最後一次",
    }
    localized = text
    for source, target in replacements.items():
        localized = localized.replace(source, target)
    return localized


def prompt_index(label: str, options: list[str]) -> int:
    while True:
        print(label)
        for index, option in enumerate(options):
            print(f"  [{index}] {option}")
        raw = input("> ").strip()
        if raw.isdigit() and 0 <= int(raw) < len(options):
            return int(raw)
        print("無效選項，請輸入對應的數字。")


def estimate_remaining_steps(map_state, node_id: str) -> int:
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
    nodes = build_node_payloads()
    events = build_event_catalog(seed)
    enemies = build_enemy_catalog()
    map_state = build_map(nodes, start_node_id="node_start", final_node_id="node_final")
    engine = RunEngine(map_state=map_state, seed=seed, event_catalog=events, enemy_catalog=enemies)
    run = engine.create_run(PlayerState(hp=10, food=7, ammo=3, medkits=1), seed=seed)

    print("Ashfall 文字原型")
    print(f"Seed: {seed}")
    print("目標：活到終點。")

    decision_log: list[dict] = []

    while not run.ended:
        current = map_state.get_node(run.current_node)
        if current.connections:
            if run.player.radiation > 0:
                print(f"警告：移動時會受到 1 點輻射傷害。 目前輻射值：{run.player.radiation}")
                if run.player.hp <= run.player.radiation + 1:
                    print("危急：再進行一次帶輻射的移動，你可能會死亡。")
            route_choice = prompt_index(
                f"\n目前節點：{format_node(run.current_node)}\n狀態：{format_status(run.player)}\n請選擇下一條路線：",
                [format_node(node_id) for node_id in current.connections],
            )
            next_node = current.connections[route_choice]
            hp_before_move = run.player.hp
            food_before_move = run.player.food
            node = engine.move_to(run, next_node)
            if run.player.radiation > 0 and run.player.hp < hp_before_move:
                print(f"移動途中受到輻射灼傷，失去 {hp_before_move - run.player.hp} 點生命。")
            if run.player.food < food_before_move:
                print(f"移動消耗了 {food_before_move - run.player.food} 點食物。")
            if run.ended:
                break
        else:
            node = current

        event_id = pick_event_id(node, engine.rng)
        event_payload = events[event_id]
        remaining_steps = estimate_remaining_steps(map_state, node.id)
        print(f"\n事件：{event_payload['description']}")

        option_lines = []
        warning_cache: list[list[str]] = []
        for index, option in enumerate(event_payload["options"]):
            warnings = build_warning_signals(run.player, event_payload, index, remaining_steps)
            warning_cache.append(warnings)
            localized_warnings = [localize_warning(warning) for warning in warnings]
            warning_label = f" [{'; '.join(localized_warnings)}]" if localized_warnings else ""
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
            outcome["combat"] = combat
            enemy_label = ENEMY_LABELS.get(combat["enemy_id"], combat["enemy_id"])
            print(f"觸發戰鬥：{enemy_label}")
            for line in combat["log"]:
                print(f"  {line}")
        if run.player.is_dead():
            run.end(victory=False, reason=engine._resolve_noncombat_death_reason(run))

        effects = dict(event_payload["options"][option_index].get("effects", {}))
        if effects:
            print(f"效果：{format_effects(effects)}")
        if run.player.radiation > pre_choice_state["radiation"]:
            print(f"警告：輻射上升到 {run.player.radiation}。之後移動會更危險。")
        if run.player.hp <= 3 and run.player.radiation > 0:
            print("危急：你的生命已經很低，而且仍處於輻射狀態。")

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
                "effects": effects,
                "player_after": {
                    "hp": run.player.hp,
                    "food": run.player.food,
                    "ammo": run.player.ammo,
                    "medkits": run.player.medkits,
                    "radiation": run.player.radiation,
                },
            }
        )

        if node.is_final and not run.ended:
            run.end(victory=True, reason="reached_final_node")

    failure_analysis = analyze_failure(decision_log, run.ended, run.victory, run.end_reason)
    result = {
        "seed": seed,
        "ended": run.ended,
        "victory": run.victory,
        "end_reason": run.end_reason,
        "player_final": {
            "hp": run.player.hp,
            "food": run.player.food,
            "ammo": run.player.ammo,
            "medkits": run.player.medkits,
            "scrap": run.player.scrap,
            "radiation": run.player.radiation,
        },
        "decision_log": decision_log,
        "failure_analysis": failure_analysis,
    }
    output_path = OUTPUT_DIR / f"latest_seed_{seed}.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\n本局結束")
    print(
        json.dumps(
            {
                "勝利": run.victory,
                "結束原因": END_REASON_LABELS.get(run.end_reason or "", run.end_reason),
                "失敗分析": failure_analysis,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"已儲存：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
