import json
import os
import shutil
import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance_tools.plan_freshness import (
    STATUS_CRITICAL,
    STATUS_ERROR,
    STATUS_FRESH,
    STATUS_STALE,
    check_freshness,
    format_json,
    parse_header_fields,
    parse_policy,
)

TODAY = date(2026, 3, 11)
RUNTIME_ROOT = Path("tests") / "_runtime"
RUNTIME_ROOT.mkdir(exist_ok=True)


def make_runtime_dir() -> Path:
    path = RUNTIME_ROOT / f"freshness_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def cleanup_runtime_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def make_plan(last_updated: str, owner: str = "Tester", freshness: str = "Sprint (7d)") -> str:
    return "\n".join(
        [
            f"> **Last Updated**: {last_updated}",
            f"> **Owner**: {owner}",
            f"> **Freshness**: {freshness}",
        ]
    ) + "\n"


def write_completed_log(path: Path) -> None:
    payload = {
        "player_id": "P1",
        "session_id": "S1",
        "roguelite_experience": True,
        "game_dev_background": False,
        "run_id": "north_aggressive",
        "events": [
            {
                "timestamp": "2026-03-11T10:00:00",
                "node_id": "node_north_1",
                "decision_time_ms": 1200,
                "selected_option": 0,
                "hesitation_flag": True,
                "confusion_flag": False,
                "what_i_thought_happened": "pressure",
                "why_im_salty": "risk",
                "verbal_note": "",
            }
        ],
        "post_run": {
            "hardest_choice": "node_north_1",
            "perceived_death_cause": "radiation",
            "regret_choice": "node_north_1 option 0",
            "replay_intent": True,
            "judgment_regret_note": "too greedy",
            "frustration_regret_note": "clear enough",
            "immediate_replay_reason": "test",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_parse_header_fields_extracts_fields() -> None:
    fields = parse_header_fields(make_plan("2026-03-11"))
    assert fields["Last Updated"] == "2026-03-11"
    assert fields["Owner"] == "Tester"


def test_parse_policy_variants() -> None:
    assert parse_policy("Sprint (7d)") == 7
    assert parse_policy("Phase") == 30
    assert parse_policy("Unknown") is None


def test_missing_plan_returns_error() -> None:
    runtime = make_runtime_dir()
    try:
        result = check_freshness(runtime / "PLAN.md", today=TODAY)
    finally:
        cleanup_runtime_dir(runtime)
    assert result.status == STATUS_ERROR


def test_stale_and_critical_boundaries() -> None:
    runtime = make_runtime_dir()
    try:
        plan = runtime / "PLAN.md"
        plan.write_text(make_plan("2026-03-03"), encoding="utf-8")
        stale_result = check_freshness(plan, today=TODAY)
        plan.write_text(make_plan("2026-02-20"), encoding="utf-8")
        critical_result = check_freshness(plan, today=TODAY)
    finally:
        cleanup_runtime_dir(runtime)
    assert stale_result.status == STATUS_STALE
    assert critical_result.status == STATUS_CRITICAL


def test_phase_policy_stays_fresh() -> None:
    runtime = make_runtime_dir()
    try:
        plan = runtime / "PLAN.md"
        plan.write_text(make_plan("2026-02-20", freshness="Phase (30d)"), encoding="utf-8")
        result = check_freshness(plan, today=TODAY)
    finally:
        cleanup_runtime_dir(runtime)
    assert result.status == STATUS_FRESH
    assert result.threshold_days == 30


def test_pt1_logs_older_than_balance_change_is_critical() -> None:
    runtime = make_runtime_dir()
    try:
        plan = runtime / "PLAN.md"
        plan.write_text(make_plan("2026-03-11"), encoding="utf-8")

        playtests = runtime / "playtests"
        playtests.mkdir()
        log_path = playtests / "P1_session_log.json"
        write_completed_log(log_path)

        balance_summary = runtime / "balance_summary.json"
        balance_summary.write_text(json.dumps({"summary": {}}), encoding="utf-8")

        old_time = 1_700_000_000
        new_time = old_time + 100
        os.utime(log_path, (old_time, old_time))
        os.utime(balance_summary, (new_time, new_time))

        result = check_freshness(
            plan,
            today=TODAY,
            pt1_dir=playtests,
            balance_summary_path=balance_summary,
        )
    finally:
        cleanup_runtime_dir(runtime)
    assert result.status == STATUS_CRITICAL
    assert result.pt1_completed_count == 1
    assert any("PT-1 data is older" in item for item in result.errors)


def test_format_json_contains_pt1_fields() -> None:
    runtime = make_runtime_dir()
    try:
        plan = runtime / "PLAN.md"
        plan.write_text(make_plan("2026-03-11"), encoding="utf-8")
        result = check_freshness(plan, today=TODAY)
        output = json.loads(format_json(result, plan))
    finally:
        cleanup_runtime_dir(runtime)
    assert output["status"] == STATUS_FRESH
    assert "pt1_completed_count" in output
    assert "latest_balance_mtime" in output
