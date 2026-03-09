"""
Unit tests for governance_tools/contract_validator.py

Test groups:
  A. extract_contract_block   — markdown code block / plain text / missing
  B. parse_contract_fields    — key=value parsing edge cases
  C. validate_contract        — field-level validation (LANG/LEVEL/SCOPE/
                                PLAN/LOADED/CONTEXT/PRESSURE/AGENT_ID/SESSION)
  D. validate_contract        — compliant full contracts
  E. format_json              — output structure
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from governance_tools.contract_validator import (
    extract_contract_block,
    parse_contract_fields,
    validate_contract,
    format_json,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_contract(**overrides) -> str:
    """Build a minimal compliant contract string."""
    fields = {
        "LANG": "C++",
        "LEVEL": "L2",
        "SCOPE": "feature",
        "PLAN": "PLAN.md",
        "LOADED": "SYSTEM_PROMPT, HUMAN-OVERSIGHT",
        "CONTEXT": "ai-governance — GavinWu; NOT: fine-tuning",
        "PRESSURE": "SAFE (45/200)",
    }
    fields.update(overrides)
    body = "\n".join(f"{k} = {v}" for k, v in fields.items())
    return f"[Governance Contract]\n{body}\n"


# ── A. extract_contract_block ─────────────────────────────────────────────────

class TestExtractContractBlock:
    def test_plain_text_format(self):
        text = "[Governance Contract]\nLANG = C++\nLEVEL = L2\n"
        assert extract_contract_block(text) is not None

    def test_markdown_code_block_format(self):
        text = "```\n[Governance Contract]\nLANG = C++\n```"
        assert extract_contract_block(text) is not None

    def test_missing_returns_none(self):
        assert extract_contract_block("no contract here") is None

    def test_empty_string_returns_none(self):
        assert extract_contract_block("") is None

    def test_contract_in_surrounding_text(self):
        text = "Some preamble\n[Governance Contract]\nLANG = C++\nLEVEL = L1\n\nMore text."
        assert extract_contract_block(text) is not None

    def test_markdown_block_with_language_hint(self):
        text = "```markdown\n[Governance Contract]\nLANG = JS\n```"
        assert extract_contract_block(text) is not None


# ── B. parse_contract_fields ──────────────────────────────────────────────────

class TestParseContractFields:
    def test_basic_key_value(self):
        block = "[Governance Contract]\nLANG = C++\nLEVEL = L2\n"
        fields = parse_contract_fields(block)
        assert fields["LANG"] == "C++"
        assert fields["LEVEL"] == "L2"

    def test_value_with_spaces(self):
        block = "[Governance Contract]\nCONTEXT = foo — bar; NOT: baz\n"
        fields = parse_contract_fields(block)
        assert "foo" in fields["CONTEXT"]

    def test_ignores_bracket_lines(self):
        block = "[Governance Contract]\nLANG = C#\n"
        fields = parse_contract_fields(block)
        assert "[Governance Contract]" not in fields

    def test_ignores_backtick_lines(self):
        block = "```\n[Governance Contract]\nLANG = Swift\n```\n"
        fields = parse_contract_fields(block)
        assert "```" not in fields

    def test_empty_block(self):
        assert parse_contract_fields("") == {}


# ── C. validate_contract — invalid cases ────────────────────────────────────

class TestValidateContractInvalid:
    def test_no_contract_block(self):
        result = validate_contract("no contract here")
        assert not result.contract_found
        assert not result.compliant

    def test_invalid_lang(self):
        text = _make_contract(LANG="Python")
        result = validate_contract(text)
        assert not result.compliant
        assert any("LANG" in e for e in result.errors)

    def test_invalid_level(self):
        text = _make_contract(LEVEL="L5")
        result = validate_contract(text)
        assert not result.compliant
        assert any("LEVEL" in e for e in result.errors)

    def test_invalid_scope(self):
        text = _make_contract(SCOPE="deployment")
        result = validate_contract(text)
        assert not result.compliant
        assert any("SCOPE" in e for e in result.errors)

    def test_missing_lang(self):
        text = _make_contract(LANG="")
        result = validate_contract(text)
        assert not result.compliant

    def test_missing_level(self):
        text = _make_contract(LEVEL="")
        result = validate_contract(text)
        assert not result.compliant

    def test_missing_scope(self):
        text = _make_contract(SCOPE="")
        result = validate_contract(text)
        assert not result.compliant

    def test_missing_loaded(self):
        text = _make_contract(LOADED="")
        result = validate_contract(text)
        assert not result.compliant
        assert any("LOADED" in e for e in result.errors)

    def test_loaded_missing_system_prompt(self):
        text = _make_contract(LOADED="HUMAN-OVERSIGHT")
        result = validate_contract(text)
        assert not result.compliant
        assert any("SYSTEM_PROMPT" in e for e in result.errors)

    def test_loaded_missing_human_oversight(self):
        text = _make_contract(LOADED="SYSTEM_PROMPT")
        result = validate_contract(text)
        assert not result.compliant
        assert any("HUMAN-OVERSIGHT" in e for e in result.errors)

    def test_context_missing_separator(self):
        text = _make_contract(CONTEXT="some context; NOT: excluded")
        result = validate_contract(text)
        assert not result.compliant
        assert any("CONTEXT" in e for e in result.errors)

    def test_context_missing_not_clause(self):
        text = _make_contract(CONTEXT="project — owner")
        result = validate_contract(text)
        assert not result.compliant
        assert any("NOT:" in e for e in result.errors)

    def test_missing_context(self):
        text = _make_contract(CONTEXT="")
        result = validate_contract(text)
        assert not result.compliant

    def test_invalid_pressure_level(self):
        text = _make_contract(PRESSURE="UNKNOWN (10/200)")
        result = validate_contract(text)
        assert not result.compliant
        assert any("PRESSURE" in e for e in result.errors)

    def test_missing_pressure(self):
        text = _make_contract(PRESSURE="")
        result = validate_contract(text)
        assert not result.compliant

    def test_agent_id_without_session(self):
        text = _make_contract(AGENT_ID="claude-sonnet-4-6")
        result = validate_contract(text)
        assert not result.compliant
        assert any("SESSION" in e for e in result.errors)

    def test_agent_id_with_invalid_session_format(self):
        text = _make_contract(AGENT_ID="claude-sonnet-4-6", SESSION="2026/03/05")
        result = validate_contract(text)
        assert not result.compliant
        assert any("SESSION" in e for e in result.errors)


# ── D. validate_contract — compliant cases ───────────────────────────────────

class TestValidateContractCompliant:
    @pytest.mark.parametrize("lang", ["C++", "C#", "ObjC", "Swift", "JS"])
    def test_all_valid_langs(self, lang):
        result = validate_contract(_make_contract(LANG=lang))
        assert result.compliant

    @pytest.mark.parametrize("level", ["L0", "L1", "L2"])
    def test_all_valid_levels(self, level):
        result = validate_contract(_make_contract(LEVEL=level))
        assert result.compliant

    @pytest.mark.parametrize("scope", ["feature", "refactor", "bugfix", "I/O", "tooling", "review"])
    def test_all_valid_scopes(self, scope):
        result = validate_contract(_make_contract(SCOPE=scope))
        assert result.compliant

    @pytest.mark.parametrize("pressure", ["SAFE", "WARNING", "CRITICAL", "EMERGENCY"])
    def test_all_valid_pressure_levels(self, pressure):
        result = validate_contract(_make_contract(PRESSURE=f"{pressure} (50/200)"))
        assert result.compliant

    def test_compliant_with_agent_id_and_session(self):
        text = _make_contract(AGENT_ID="claude-sonnet-4-6", SESSION="2026-03-06-01")
        result = validate_contract(text)
        assert result.compliant

    def test_missing_plan_is_warning_not_error(self):
        text = _make_contract(PLAN="")
        result = validate_contract(text)
        assert result.compliant  # PLAN is optional (warning only)
        assert any("PLAN" in w for w in result.warnings)

    def test_session_without_agent_id_is_warning(self):
        text = _make_contract(SESSION="2026-03-06-01")
        result = validate_contract(text)
        assert result.compliant
        assert any("SESSION" in w for w in result.warnings)

    def test_pressure_without_line_count_is_warning(self):
        text = _make_contract(PRESSURE="SAFE")
        result = validate_contract(text)
        assert result.compliant
        assert any("PRESSURE" in w for w in result.warnings)

    def test_full_compliant_contract(self):
        result = validate_contract(_make_contract())
        assert result.compliant
        assert result.contract_found
        assert result.errors == []

    def test_contract_found_true_on_compliant(self):
        result = validate_contract(_make_contract())
        assert result.contract_found is True


# ── E. format_json ────────────────────────────────────────────────────────────

class TestFormatJson:
    def test_json_output_has_required_keys(self):
        result = validate_contract(_make_contract())
        output = json.loads(format_json(result))
        assert "compliant" in output
        assert "contract_found" in output
        assert "fields" in output
        assert "errors" in output
        assert "warnings" in output

    def test_json_compliant_true_for_valid_contract(self):
        result = validate_contract(_make_contract())
        output = json.loads(format_json(result))
        assert output["compliant"] is True

    def test_json_compliant_false_for_invalid_contract(self):
        result = validate_contract(_make_contract(LANG="Python"))
        output = json.loads(format_json(result))
        assert output["compliant"] is False
        assert len(output["errors"]) > 0

    def test_json_is_valid_json(self):
        result = validate_contract("no contract")
        output_str = format_json(result)
        # Should not raise
        parsed = json.loads(output_str)
        assert isinstance(parsed, dict)
