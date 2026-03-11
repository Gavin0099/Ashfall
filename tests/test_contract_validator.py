import json
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance_tools.contract_validator import (
    extract_contract_block,
    format_json,
    parse_contract_fields,
    validate_contract,
)

RUNTIME_ROOT = Path("tests") / "_runtime"
RUNTIME_ROOT.mkdir(exist_ok=True)


def make_contract(**overrides: str) -> str:
    fields = {
        "LANG": "C++",
        "LEVEL": "L2",
        "SCOPE": "feature",
        "PLAN": "PLAN.md",
        "LOADED": "SYSTEM_PROMPT, HUMAN-OVERSIGHT",
        "CONTEXT": "Ashfall route balance -> governance checks; NOT: renderer work",
        "PRESSURE": "SAFE (45/200)",
    }
    fields.update(overrides)
    body = "\n".join(f"{key} = {value}" for key, value in fields.items())
    return f"[Governance Contract]\n{body}\n"


def make_runtime_dir() -> Path:
    path = RUNTIME_ROOT / f"contract_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def cleanup_runtime_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def write_balance_summary(base: Path, avg_regret: float) -> Path:
    path = base / "balance_summary.json"
    path.write_text(json.dumps({"avg_steps_from_regret_to_death": avg_regret}), encoding="utf-8")
    return path


def test_extract_contract_block_from_markdown() -> None:
    text = "```text\n[Governance Contract]\nLANG = C++\n```"
    assert extract_contract_block(text) is not None


def test_parse_contract_fields_basic() -> None:
    fields = parse_contract_fields(make_contract())
    assert fields["LANG"] == "C++"
    assert fields["LEVEL"] == "L2"


def test_validate_contract_compliant() -> None:
    result = validate_contract(make_contract())
    assert result.compliant is True
    assert result.errors == []


def test_validate_contract_missing_not_clause_fails() -> None:
    result = validate_contract(make_contract(CONTEXT="Ashfall scope only"))
    assert result.compliant is False
    assert any("NOT:" in item for item in result.errors)


def test_validate_contract_regret_gate_fails() -> None:
    runtime = make_runtime_dir()
    try:
        balance_summary = write_balance_summary(runtime, 0.4)
        result = validate_contract(
            make_contract(),
            balance_summary_path=balance_summary,
            regret_threshold=0.5,
        )
    finally:
        cleanup_runtime_dir(runtime)
    assert result.compliant is False
    assert result.metrics["avg_steps_from_regret_to_death"] == 0.4
    assert any("avg_steps_from_regret_to_death=0.4 < 0.5" in item for item in result.errors)


def test_validate_contract_regret_gate_passes() -> None:
    runtime = make_runtime_dir()
    try:
        balance_summary = write_balance_summary(runtime, 1.0)
        result = validate_contract(
            make_contract(),
            balance_summary_path=balance_summary,
            regret_threshold=0.5,
        )
    finally:
        cleanup_runtime_dir(runtime)
    assert result.compliant is True
    assert result.metrics["avg_steps_from_regret_to_death"] == 1.0


def test_format_json_contains_metrics() -> None:
    output = json.loads(format_json(validate_contract(make_contract())))
    assert set(["compliant", "contract_found", "fields", "errors", "warnings", "metrics"]).issubset(output)
