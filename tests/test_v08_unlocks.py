from pathlib import Path
import sys
import os

# Add root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.meta_progression import MetaProfile, ARCHETYPE_UNLOCK_METADATA

def test_archetype_unlock_logic():
    print("Testing Archetype Unlock Logic...")
    # Give enough scrap for one unlock
    profile = MetaProfile(total_scrap=50)
    
    # Check constants
    assert "medic" in ARCHETYPE_UNLOCK_METADATA
    assert ARCHETYPE_UNLOCK_METADATA["medic"]["cost"] == 30
    
    # Initial state
    assert profile.is_archetype_unlocked("medic") is False
    assert "soldier" in profile.unlocked_archetypes
    
    # Unlock medic
    success = profile.unlock_archetype("medic")
    assert success is True
    assert profile.is_archetype_unlocked("medic") is True
    assert profile.total_scrap == 50 - 30
    
    # Try unlock again (should fail)
    success_repeat = profile.unlock_archetype("medic")
    assert success_repeat is False
    assert profile.total_scrap == 20
    
    # Try unlock scavenger with insufficient scrap
    success_insufficient = profile.unlock_archetype("scavenger")
    assert success_insufficient is False
    assert profile.is_archetype_unlocked("scavenger") is False
    
    print("✅ Archetype Unlock Logic passed.")

def test_profile_persistence_with_unlocks(tmp_path):
    print("Testing Profile Persistence with Unlocks...")
    test_file = tmp_path / "test_meta.json"
    profile = MetaProfile(total_scrap=100)
    profile.unlock_archetype("medic")
    profile.save(test_file)
    
    # Load back
    loaded = MetaProfile.load(test_file)
    assert loaded.is_archetype_unlocked("medic") is True
    assert loaded.total_scrap == 70
    
    print("✅ Profile Persistence passed.")

if __name__ == "__main__":
    import tempfile
    from pathlib import Path
    
    try:
        test_archetype_unlock_logic()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_profile_persistence_with_unlocks(Path(tmpdir))
        print("\nAll v0.8 unit verifications PASSED.")
    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
