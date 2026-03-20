import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_simulator import run_sim

res = run_sim("survival", num_steps=30, seed=42)
print(f"Survived: {res['survived']}")
print(f"Perks: {res['perks']}")
print(f"Food history: {res['stats']['history']['food']}")
print(f"HP history: {res['stats']['history']['hp']}")
