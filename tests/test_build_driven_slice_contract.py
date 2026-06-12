import random

from src.event_engine import get_available_options, resolve_event_choice
from src.state_models import CharacterProfile, PlayerState


def _player(special=None, tags=None):
    return PlayerState(
        hp=10,
        food=10,
        ammo=2,
        medkits=1,
        character=CharacterProfile(
            background_id="vault_mechanic",
            display_name="Vault Mechanic",
            special=special or {
                "strength": 2,
                "perception": 3,
                "endurance": 2,
                "charisma": 1,
                "intelligence": 4,
                "agility": 2,
                "luck": 2,
            },
            tags=["mechanic", "vault_dweller"] if tags is None else tags,
        ),
    )


def test_compact_requirements_map_to_special_and_tags_with_locked_metadata():
    event = {
        "id": "locked_clinic",
        "options": [
            {"text": "Force the side door", "effects": {"hp": -1}},
            {
                "id": "clinic_repair_door",
                "text": "Repair the clinic door relay",
                "requirements": {
                    "attribute": {"INT": 4},
                    "trait": ["mechanic"],
                },
                "visible_if_locked": True,
                "locked_text": "Needs INT 4 and mechanic training.",
                "effects": {"scrap": 1},
            },
        ],
    }

    weak = _player(special={"intelligence": 2}, tags=[])
    weak_options = get_available_options(weak, event)

    assert len(weak_options) == 2
    assert weak_options[1]["is_met"] is False
    assert weak_options[1]["locked"] is True
    assert weak_options[1]["locked_text"] == "Needs INT 4 and mechanic training."
    assert "intelligence >= 4" in weak_options[1]["lock_reasons"]
    assert "tag mechanic" in weak_options[1]["lock_reasons"]

    qualified = _player()
    qualified_options = get_available_options(qualified, event)

    assert qualified_options[1]["is_met"] is True
    assert qualified_options[1]["locked"] is False


def test_unmet_option_can_be_hidden_when_visible_if_locked_is_false():
    event = {
        "id": "underground_market",
        "options": [
            {"text": "Buy water", "effects": {"food": 1}},
            {
                "id": "grifter_fake_documents",
                "text": "Trade fake papers",
                "requirements": {"attribute": {"CHA": 4}},
                "visible_if_locked": False,
                "effects": {"scrap": 2},
            },
        ],
    }

    options = get_available_options(_player(), event)

    assert [entry["option"].get("id") for entry in options] == [None]


def test_resolve_choice_sets_flags_and_later_event_requires_them():
    player = _player()
    run_flags = {}
    clinic = {
        "id": "locked_clinic",
        "options": [
            {
                "id": "clinic_repair_door",
                "text": "Repair the relay",
                "requirements": {"attribute": {"INT": 4}, "trait": ["mechanic"]},
                "set_flags": {"clinic_entered_safely": True},
                "effects": {"scrap": 1},
            }
        ],
    }
    checkpoint = {
        "id": "infection_checkpoint",
        "options": [
            {"id": "wait", "text": "Wait outside", "effects": {"food": -1}},
            {
                "id": "use_clinic_supplies",
                "text": "Use the sterile clinic supplies",
                "required_flags": {"clinic_entered_safely": True},
                "effects": {"medkits": 1},
            },
        ],
    }

    before = get_available_options(player, checkpoint, run_flags=run_flags)
    assert before[1]["is_met"] is False
    assert "flag clinic_entered_safely=True" in before[1]["lock_reasons"]

    outcome = resolve_event_choice(player, clinic, 0, random.Random(7), run_flags=run_flags)

    assert outcome["set_flags"] == {"clinic_entered_safely": True}
    assert run_flags["clinic_entered_safely"] is True

    after = get_available_options(player, checkpoint, run_flags=run_flags)
    assert after[1]["is_met"] is True
