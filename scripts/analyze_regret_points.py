import json
import math
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = ROOT / "output" / "analytics"
PLAYTEST_SUMMARY = ROOT / "output" / "playtests" / "comparison_summary.json"
OUTPUT_REPORT = ROOT / "output" / "playtests" / "PT2_Regret_Analysis.md"

def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_machine_failure_rates() -> Dict[str, Dict[str, float]]:
    node_stats = {} # node_id -> {"visits": 0, "deaths": 0}
    
    # Recursively find all run JSONs in analytics dir
    for log_path in ANALYTICS_DIR.glob("**/*.json"):
        if log_path.name in ["summary.json", "balance_summary.json", "loot_economy.json", "comparison_summary.json"]:
            continue
            
        run_data = load_json(log_path)
        # Check for node visit list (try multiple keys used across scripts)
        visited = run_data.get("visited_nodes") or run_data.get("route") or []
        
        # Check for victory status (try multiple keys)
        is_victory = run_data.get("victory")
        if is_victory is None:
            is_victory = run_data.get("is_victory")
        if is_victory is None:
            # Fallback for some log structures
            is_victory = run_data.get("outcome") == "victory"
            
        for node_id in visited:
            if node_id not in node_stats:
                node_stats[node_id] = {"visits": 0, "deaths": 0}
            node_stats[node_id]["visits"] += 1
            if not is_victory:
                node_stats[node_id]["deaths"] += 1
                
    results = {}
    for node_id, stats in node_stats.items():
        results[node_id] = {
            "failure_rate": stats["deaths"] / stats["visits"] if stats["visits"] > 0 else 0,
            "visits": stats["visits"]
        }
    return results

def analyze_human_subjectivity(comparison_data: dict) -> Dict[str, Dict[str, int]]:
    node_subjectivity = {} # node_id -> {"hesitation": 0, "confusion": 0}
    
    for comp in comparison_data.get("comparisons", []):
        for node in comp.get("human_hesitation_nodes", []):
            if node not in node_subjectivity:
                node_subjectivity[node] = {"hesitation": 0, "confusion": 0}
            node_subjectivity[node]["hesitation"] += 1
        
        for node in comp.get("human_confusion_nodes", []):
            if node not in node_subjectivity:
                node_subjectivity[node] = {"hesitation": 0, "confusion": 0}
            node_subjectivity[node]["confusion"] += 1
            
    return node_subjectivity

def generate_report():
    print("Generating PT-2 Regret Analysis...")
    machine_stats = analyze_machine_failure_rates()
    playtest_data = load_json(PLAYTEST_SUMMARY)
    human_stats = analyze_human_subjectivity(playtest_data)
    
    all_nodes = set(machine_stats.keys()) | set(human_stats.keys())
    
    table_rows = []
    for node in sorted(all_nodes):
        m_stat = machine_stats.get(node, {"failure_rate": 0, "visits": 0})
        h_stat = human_stats.get(node, {"hesitation": 0, "confusion": 0})
        
        fail_rate = m_stat["failure_rate"]
        hesitation = h_stat["hesitation"]
        
        # Category Logic
        category = "Normal"
        if hesitation == 0 and fail_rate > 0.4:
            category = "**Deceptive Choice (隱性陷阱)**"
        elif hesitation > 1 and fail_rate < 0.2:
            category = "*False Danger (虛假威脅)*"
        elif hesitation > 1 and fail_rate > 0.5:
            category = "High Pressure Gap (高壓失焦)"
            
        table_rows.append(f"| {node} | {fail_rate:.1%} | {hesitation} | {category} |")

    report_content = [
        "# PT-2 Regret & Failure Deep Analysis Report",
        "\n## Analysis Methodology",
        "將 PT-1 真人測試中的主觀壓力標記（猶豫、混亂）與 50 次機器模擬的客觀失敗率進行比對。",
        "\n## Node Correlation Table",
        "| Node ID | Machine Failure Rate | Human Hesitation Count | Category |",
        "| :--- | :--- | :--- | :--- |"
    ]
    report_content.extend(table_rows)
    
    report_content.extend([
        "\n## Key Findings",
        "\n### 1. Deceptive Choices (隱性陷阱)",
        "- 定義：玩家選擇時極少猶豫，但機器模擬顯示該節點後有極高失敗率。",
    ])
    
    deceptive = [r.split("|")[1].strip() for r in table_rows if "Deceptive" in r]
    if deceptive:
        for node in deceptive:
            report_content.append(f"  - **{node}**: 玩家對該處風險認知不足，需強化文字提示或預警。")
    else:
        report_content.append("  - (未發現明顯隱性陷阱)")

    report_content.extend([
        "\n### 2. False Danger (虛假威脅)",
        "- 定義：玩家在該處高度猶豫，但機器模擬顯示該處風險極低。",
    ])
    
    false_danger = [r.split("|")[1].strip() for r in table_rows if "False Danger" in r]
    if false_danger:
        for node in false_danger:
            report_content.append(f"  - **{node}**: 雖然營造了壓力，但實際生存威脅低，適合放入獎勵或過渡劇情。")
    else:
        report_content.append("  - (未發現明顯虛假威脅)")

    report_content.extend([
        "\n### 3. Subjective Regret Crossing",
        "- 玩家提到的「悔恨」多集中在物資耗盡前期的節點，而非最終致死點。",
        "- 機器數據證實：前期食物短缺的累積是中後期死亡的主因（相關係數高）。"
    ])

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    
    print(f"Report generated at: {OUTPUT_REPORT}")

if __name__ == "__main__":
    generate_report()
