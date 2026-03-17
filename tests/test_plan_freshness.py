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
    # Notice: Now using Traditional Chinese headers
    return "\n".join(
        [
            f"> **最後更新**: {last_updated}",
            f"> **Owner**: {owner}",
            f"> **Freshness**: {freshness}",
        ]
    ) + "\n"


def test_parse_header_fields_extracts_fields() -> None:
    fields = parse_header_fields(make_plan("2026-03-11"))
    assert fields["最後更新"] == "2026-03-11"
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


def test_format_json_contains_basic_fields() -> None:
    runtime = make_runtime_dir()
    try:
        plan = runtime / "PLAN.md"
        plan.write_text(make_plan("2026-03-11"), encoding="utf-8")
        result = check_freshness(plan, today=TODAY)
        output = json.loads(format_json(result, plan))
    finally:
        cleanup_runtime_dir(runtime)
    assert output["status"] == STATUS_FRESH
    assert "last_updated" in output
