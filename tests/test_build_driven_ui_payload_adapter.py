import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "ui" / "src" / "components" / "BuildDrivenPrototype.jsx"
EVENT_DIR = ROOT / "experiments" / "build_driven_slice" / "events"


def test_build_driven_ui_imports_p3_payloads() -> None:
    text = COMPONENT.read_text(encoding="utf-8")

    for event_file in sorted(EVENT_DIR.glob("*.json")):
        assert f"../../../experiments/build_driven_slice/events/{event_file.name}" in text


def test_build_driven_ui_preserves_choice_view_contract() -> None:
    text = COMPONENT.read_text(encoding="utf-8")

    assert "function toChoiceView" in text
    assert "choiceKind(option, available)" in text
    assert "lockedText" in text
    assert "consequencePreview" in text
    assert "requirementLabel" in text


def test_build_driven_payloads_still_have_visible_locked_options() -> None:
    for event_file in EVENT_DIR.glob("*.json"):
        payload = json.loads(event_file.read_text(encoding="utf-8"))
        locked_visible = [
            option
            for option in payload["options"]
            if option.get("requirements") or option.get("required_flags")
        ]

        assert locked_visible, event_file.name
        assert all(option.get("visible_if_locked", True) for option in locked_visible), event_file.name
        assert all(option.get("locked_text") for option in locked_visible), event_file.name


def test_build_driven_ui_exposes_instrumented_summary_contract() -> None:
    text = COMPONENT.read_text(encoding="utf-8")

    assert "function buildInstrumentedSummary" in text
    assert "build_options_taken" in text
    assert "locked_options_seen" in text
    assert "flags_triggered" in text
    assert "flags_consumed" in text
    assert "ending_id" in text
    assert "death_or_win_reason" in text
    assert "Machine Summary" in text
    assert "Instrumented Summary" in text


def test_build_driven_ui_exposes_steam_demo_flow_contract() -> None:
    text = COMPONENT.read_text(encoding="utf-8")

    assert "Steam Demo Web Prototype Flow" in text
    assert "function startRun" in text
    assert "function handleChooseOption" in text
    assert "function buildDemoRunSummary" in text
    assert "Demo Start" in text
    assert "Demo Ending" in text
    assert "開始 Steam Demo Flow" in text
