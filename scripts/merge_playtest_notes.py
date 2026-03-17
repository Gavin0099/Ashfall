import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def parse_markdown_notes(md_path):
    """Parses the observation sheet Markdown to extract flags and interview notes."""
    content = md_path.read_text(encoding="utf-8")
    
    # Extract Interview Answers
    interview = {}
    patterns = {
        "hardest_choice": r"Hardest Choice:\s*(.*)",
        "perceived_death_cause": r"Perceived Death Cause:\s*(.*)",
        "regret_choice": r"Regret Choice:\s*(.*)",
        "judgment_regret_note": r"Judgment Regret Note.*:\s*(.*)",
        "frustration_regret_note": r"Frustration Regret Note.*:\s*(.*)",
        "immediate_replay_reason": r"Immediate Replay Reason.*:\s*(.*)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        interview[key] = match.group(1).strip() if match else "TBD"
        
    # Replay intent
    replay_match = re.search(r"Replay Intent:\s*(yes|no)", content, re.I)
    interview["replay_intent"] = (replay_match.group(1).lower() == "yes") if replay_match else False
    
    # Metadata
    meta = {}
    exp_match = re.search(r"Roguelite Experience:\s*(yes|no)", content, re.I)
    meta["roguelite_experience"] = (exp_match.group(1).lower() == "yes") if exp_match else False
    bg_match = re.search(r"Game-dev Background:\s*(yes|no)", content, re.I)
    meta["game_dev_background"] = (bg_match.group(1).lower() == "yes") if bg_match else False

    # Event Table Parsing
    events_flags = {}
    # | Timestamp | Node ID | Decision Time (ms) | Selected Option | Hesitation | Confusion | ...
    # Column mapping: 1=Node ID, 4=Hesitation, 5=Confusion
    for line in content.splitlines():
        if "|" in line and "Selected Option" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                node_id = parts[2]
                hesitation = parts[5].lower() == "yes"
                confusion = parts[6].lower() == "yes"
                if node_id:
                    events_flags[node_id] = {"hesitation": hesitation, "confusion": confusion}

    return meta, interview, events_flags

def merge(json_path, md_path):
    if not json_path.exists() or not md_path.exists():
        print(f"Error: Path not found. JSON: {json_path}, MD: {md_path}")
        return

    meta, interview, events_flags = parse_markdown_notes(md_path)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Update Metadata
    data["roguelite_experience"] = meta["roguelite_experience"]
    data["game_dev_background"] = meta["game_dev_background"]
    data["post_run"].update(interview)
    
    # Update Event Flags
    for event in data["events"]:
        node_id = event["node_id"]
        if node_id in events_flags:
            event["hesitation_flag"] = events_flags[node_id]["hesitation"]
            event["confusion_flag"] = events_flags[node_id]["confusion"]
    
    target_path = json_path.parent / f"final_{json_path.name}"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully merged notes into: {target_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/merge_playtest_notes.py <json_log> <markdown_notes>")
    else:
        merge(Path(sys.argv[1]), Path(sys.argv[2]))
