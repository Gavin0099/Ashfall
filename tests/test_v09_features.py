from pathlib import Path
import sys
import random

# Add root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_engine import pick_event_id, resolve_event_choice, get_available_options
from src.state_models import PlayerState, NodeState
from src.event_templates import instantiate_event_catalog

def test_archetype_options():
    print("Testing Archetype Options...")
    player = PlayerState(hp=10, food=10, ammo=10, medkits=1, archetype="soldier")
    event = {
        "id": "test_evt",
        "description": "Test Event",
        "options": [
            {"text": "Generic Option", "effects": {}},
            {"text": "Medic Option", "archetype_requirement": "medic", "effects": {}},
            {"text": "Soldier Option", "archetype_requirement": "soldier", "effects": {}}
        ]
    }
    
    avail = get_available_options(player, event)
    assert len(avail) == 3
    assert avail[0]["is_met"] is True
    assert avail[1]["is_met"] is False
    assert avail[2]["is_met"] is True
    
    # Try resolving
    rng = random.Random(42)
    resolve_event_choice(player, event, 0, rng) # Should pass
    resolve_event_choice(player, event, 2, rng) # Should pass
    try:
        resolve_event_choice(player, event, 1, rng)
        assert False, "Should have raised ValueError for Medic option"
    except ValueError:
        pass
    
    print("✅ Archetype Options passed.")

def test_quest_chain_filtering():
    print("Testing Quest Chain Filtering...")
    
    # Catalog with quest logic
    catalog = {
        "events": [
            {
                "event_id": "start_quest",
                "options": [{"text": "Accept", "set_flags": {"q1": True}}]
            },
            {
                "event_id": "quest_step",
                "conditions": {"required_flags": {"q1": True}},
                "options": [{"text": "Continue"}]
            },
            {
                "event_id": "random_evt",
                "options": [{"text": "Normal"}]
            }
        ]
    }
    
    inst_catalog = instantiate_event_catalog(42, catalog)
    node = NodeState(id="node", node_type="story", event_pool=["quest_step", "random_evt"], connections=[])
    
    rng = random.Random(42)
    # Without flag
    picked = pick_event_id(node, rng, run_flags={}, event_catalog=inst_catalog)
    assert picked == "random_evt" # quest_step should be filtered out
    
    # With flag
    picked_with_flag = pick_event_id(node, rng, run_flags={"q1": True}, event_catalog=inst_catalog)
    # Since both are possible, it might pick either. But pick_event_id picks from pool.
    # In my logic: candidates = filtered if filtered else node.event_pool
    # If filtered is not empty, it picks from filtered.
    assert picked_with_flag in ["quest_step", "random_evt"]
    
    print("✅ Quest Chain Filtering passed.")

if __name__ == "__main__":
    try:
        test_archetype_options()
        test_quest_chain_filtering()
        print("\nAll v0.9 unit verifications PASSED.")
    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
