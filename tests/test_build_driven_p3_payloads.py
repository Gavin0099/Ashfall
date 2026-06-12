import json
import random
from pathlib import Path

from src.event_engine import get_available_options, resolve_event_choice
from src.state_models import CharacterProfile, PlayerState


ROOT = Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "experiments" / "build_driven_slice" / "events"
EXPECTED_SEQUENCE = [
    "roadside_trap",
    "locked_clinic",
    "infection_checkpoint",
    "underground_market",
    "vault_gate",
]


def _load_events():
    events = {}
    for event_id in EXPECTED_SEQUENCE:
        path = EVENT_DIR / f"{event_id}.json"
        events[event_id] = json.loads(path.read_text(encoding="utf-8"))
    return events


def _player(build_id):
    presets = {
        "vault_mechanic": {
            "display_name": "Vault Mechanic",
            "special": {
                "strength": 2,
                "perception": 5,
                "endurance": 2,
                "charisma": 2,
                "intelligence": 5,
                "agility": 2,
                "luck": 2,
            },
            "tags": ["mechanic", "vault_dweller"],
        },
        "wasteland_grifter": {
            "display_name": "Wasteland Grifter",
            "special": {
                "strength": 2,
                "perception": 3,
                "endurance": 2,
                "charisma": 5,
                "intelligence": 2,
                "agility": 2,
                "luck": 5,
            },
            "tags": ["liar", "trader"],
        },
        "ex_raider": {
            "display_name": "Ex-Raider",
            "special": {
                "strength": 5,
                "perception": 2,
                "endurance": 5,
                "charisma": 2,
                "intelligence": 1,
                "agility": 2,
                "luck": 2,
            },
            "tags": ["ex_raider", "intimidator"],
        },
    }
    preset = presets[build_id]
    return PlayerState(
        hp=10,
        food=10,
        ammo=3,
        medkits=1,
        scrap=3,
        character=CharacterProfile(
            background_id=build_id,
            display_name=preset["display_name"],
            special=preset["special"],
            tags=preset["tags"],
        ),
    )


def _option_ids(options):
    return {entry["option"].get("id") for entry in options}


def _met_option_ids(options):
    return {entry["option"].get("id") for entry in options if entry["is_met"]}


def _locked_option_ids(options):
    return {entry["option"].get("id") for entry in options if entry["locked"]}


def _resolve_by_id(player, event, option_id, flags):
    options = event["options"]
    index = next(i for i, option in enumerate(options) if option.get("id") == option_id)
    return resolve_event_choice(player, event, index, random.Random(11), run_flags=flags)


def test_p3_event_payloads_match_expected_sequence_and_contract_shape():
    events = _load_events()

    assert list(events) == EXPECTED_SEQUENCE

    set_flags = set()
    read_flags = set()
    ending_ids = set()
    for event_id, event in events.items():
        assert event["id"] == event_id
        assert event["description"]
        options = event["options"]
        assert len(options) >= 3

        common = [
            option
            for option in options
            if "requirements" not in option and "required_flags" not in option
        ]
        assert common, f"{event_id} must include a common option"

        gated = [
            option
            for option in options
            if "requirements" in option or "required_flags" in option
        ]
        assert gated, f"{event_id} must include a build/flag-gated option"
        assert any(option.get("visible_if_locked", True) is True for option in gated)
        assert any(option.get("locked_text") for option in gated)

        assert all(option.get("id") for option in options)
        assert all(isinstance(option.get("effects"), dict) for option in options)
        assert all(option.get("summary_consequence") for option in options)

        for option in options:
            set_flags.update((option.get("set_flags") or {}).keys())
            read_flags.update((option.get("required_flags") or {}).keys())
            if option.get("ending_id"):
                ending_ids.add(option["ending_id"])

    assert {"clinic_entered_safely", "market_contact_earned", "raider_debt_called"} <= set_flags
    assert {"clinic_entered_safely", "market_contact_earned", "raider_debt_called"} <= read_flags
    assert len(ending_ids) >= 3


def test_p3_payloads_create_option_divergence_and_locked_temptations():
    events = _load_events()
    builds = {
        build_id: _player(build_id)
        for build_id in ("vault_mechanic", "wasteland_grifter", "ex_raider")
    }

    divergent_events = 0
    locked_seen = {build_id: set() for build_id in builds}

    for event in events.values():
        met_by_build = {}
        for build_id, player in builds.items():
            options = get_available_options(player, event, run_flags={})
            met_by_build[build_id] = _met_option_ids(options)
            locked_seen[build_id].update(_locked_option_ids(options))

        if len({tuple(sorted(ids)) for ids in met_by_build.values()}) > 1:
            divergent_events += 1

    assert divergent_events >= 2
    assert all(len(ids) >= 2 for ids in locked_seen.values())


def test_vault_mechanic_flag_path_reaches_technical_ending():
    events = _load_events()
    player = _player("vault_mechanic")
    flags = {}

    roadside = get_available_options(player, events["roadside_trap"], run_flags=flags)
    assert "detect_tripwire" in _met_option_ids(roadside)
    _resolve_by_id(player, events["roadside_trap"], "detect_tripwire", flags)
    assert flags["trap_disarmed"] is True

    clinic = get_available_options(player, events["locked_clinic"], run_flags=flags)
    assert "repair_clinic_door" in _met_option_ids(clinic)
    _resolve_by_id(player, events["locked_clinic"], "repair_clinic_door", flags)
    assert flags["clinic_entered_safely"] is True

    checkpoint = get_available_options(player, events["infection_checkpoint"], run_flags=flags)
    assert "use_sterile_clinic_supplies" in _met_option_ids(checkpoint)
    _resolve_by_id(player, events["infection_checkpoint"], "use_sterile_clinic_supplies", flags)
    assert flags["infection_screening_passed"] is True

    market = get_available_options(player, events["underground_market"], run_flags=flags)
    assert "repair_vendor_scanner" in _met_option_ids(market)
    _resolve_by_id(player, events["underground_market"], "repair_vendor_scanner", flags)
    assert flags["guard_scanner_disabled"] is True

    gate = get_available_options(player, events["vault_gate"], run_flags=flags)
    assert "technical_override" in _met_option_ids(gate)
    assert {"social_bypass", "raider_pressure"} <= _option_ids(gate)

    outcome = _resolve_by_id(player, events["vault_gate"], "technical_override", flags)
    gate_option = next(
        option for option in events["vault_gate"]["options"] if option["id"] == outcome["option_id"]
    )
    assert gate_option["ending_id"] == "vault_entry_technical_success"
    assert "guard_scanner_disabled" in outcome["flags_consumed"]
