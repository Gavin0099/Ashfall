import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def bootstrap_sessions():
    """Initializes the directory structure and templates for PT-1 playtest sessions."""
    playtest_root = ROOT / "playtests"
    session_dir = playtest_root / "sessions"
    template_file = playtest_root / "observation_sheet_template.md"
    
    # Define target participants
    participants = ["p1_dev", "p2_gamer", "p3_casual"]
    
    print(f"Bootstrapping PT-1 sessions in {session_dir}...")
    
    if not session_dir.exists():
        session_dir.mkdir(parents=True)
        print(f"Created directory: {session_dir}")

    for p in participants:
        p_dir = session_dir / p
        if not p_dir.exists():
            p_dir.mkdir()
            print(f"  Created participant folder: {p}")
            
        # Copy observation sheet template
        target_sheet = p_dir / f"observation_{p}.md"
        if not target_sheet.exists() and template_file.exists():
            shutil.copy(template_file, target_sheet)
            print(f"    Added observation sheet: {target_sheet.name}")

    print("\n[PT-1 Setup Complete]")
    print("Recommended Seeds for testing:")
    print("  Seed 101: Resource-heavy North, challenging early nodes.")
    print("  Seed 202: Dangerous South, high radiation threat.")
    print("\nUsage example:")
    print("  python scripts/play_cli_run.py 101 --playtest")

if __name__ == "__main__":
    bootstrap_sessions()
