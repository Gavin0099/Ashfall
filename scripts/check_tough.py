import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_simulator import run_sim

strategies = ["survival", "scavenge", "hybrid_scav_surv"]
iterations = 5

for strat in strategies:
    print(f"\n--- Strategy: {strat} ---")
    for i in range(iterations):
        res = run_sim(strat, num_steps=30, seed=i*999)
        print(f"Run {i}: Perks picked: {res['perks']}")
