#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


VALID_LANG = {"C++", "C#", "ObjC", "Swift", "JS"}
VALID_LEVEL = {"L0", "L1", "L2"}
VALID_SCOPE = {"feature", "refactor", "bugfix", "I/O", "tooling", "review"}
VALID_PRESSURE_LEVELS = {"SAFE", "WARNING", "CRITICAL", "EMERGENCY"}
REQUIRED_LOADED = {"SYSTEM_PROMPT", "HUMAN-OVERSIGHT"}


@dataclass
class ValidationResult:
    compliant: bool
    contract_found: bool
    fields: dict[str, str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def extract_contract_block(text: str) -> Optional[str]:
    code_block = re.search(r"```[^\n]*\n(\[Governance Contract\]\n.*?)(?:```)", text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    plain = re.search(r"(\[Governance Contract\]\n(?:[A-Z_]+\s*=\s*.+\n?)*)", text)
    return plain.group(1).strip() if plain else None


def parse_contract_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if "=" not in line or line.strip().startswith("["):
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key:
            fields[key] = value
    return fields


def load_balance_metrics(balance_summary_path: Path) -> dict[str, Any]:
    payload = json.loads(balance_summary_path.read_text(encoding="utf-8-sig"))
    return payload.get("summary", payload)


def validate_regret_distance(
    balance_summary_path: Path,
    regret_threshold: float = 0.5,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    if not balance_summary_path.exists():
        errors.append(f"balance summary missing: {balance_summary_path}")
        return errors, metrics

    summary = load_balance_metrics(balance_summary_path)
    avg_regret = float(summary.get("avg_steps_from_regret_to_death", 0.0))
    metrics["avg_steps_from_regret_to_death"] = avg_regret
    metrics["regret_threshold"] = regret_threshold
    if avg_regret < regret_threshold:
        errors.append(
            "balance gate failed: "
            f"avg_steps_from_regret_to_death={avg_regret} < {regret_threshold}"
        )
    return errors, metrics


def validate_contract(
    text: str,
    *,
    balance_summary_path: Path | None = None,
    regret_threshold: float = 0.5,
) -> ValidationResult:
    block = extract_contract_block(text)
    if block is None:
        return ValidationResult(
            compliant=False,
            contract_found=False,
            fields={},
            errors=["missing [Governance Contract] block"],
        )

    fields = parse_contract_fields(block)
    errors: list[str] = []
    warnings: list[str] = []

    lang = fields.get("LANG", "")
    if not lang:
        errors.append("LANG is required")
    elif lang not in VALID_LANG:
        errors.append(f"LANG invalid: {lang}")

    level = fields.get("LEVEL", "")
    if not level:
        errors.append("LEVEL is required")
    elif level not in VALID_LEVEL:
        errors.append(f"LEVEL invalid: {level}")

    scope = fields.get("SCOPE", "")
    if not scope:
        errors.append("SCOPE is required")
    elif scope not in VALID_SCOPE:
        errors.append(f"SCOPE invalid: {scope}")

    if not fields.get("PLAN", ""):
        warnings.append("PLAN is missing")

    loaded_raw = fields.get("LOADED", "")
    if not loaded_raw:
        errors.append("LOADED is required")
    else:
        loaded = {part.strip() for part in loaded_raw.split(",") if part.strip()}
        missing = sorted(REQUIRED_LOADED - loaded)
        if missing:
            errors.append(f"LOADED missing required docs: {missing}")

    context = fields.get("CONTEXT", "")
    if not context:
        errors.append("CONTEXT is required")
    else:
        if "NOT:" not in context:
            errors.append("CONTEXT must include a NOT: clause")
        if "->" not in context and "=>" not in context and "vs" not in context.lower() and "??" not in context:
            warnings.append("CONTEXT should describe allowed vs excluded scope more explicitly")

    pressure = fields.get("PRESSURE", "")
    if not pressure:
        errors.append("PRESSURE is required")
    else:
        level_token = pressure.split("(")[0].strip()
        if level_token not in VALID_PRESSURE_LEVELS:
            errors.append(f"PRESSURE invalid: {level_token}")
        if "(" not in pressure or "/" not in pressure:
            warnings.append("PRESSURE should include capacity notation like SAFE (45/200)")

    agent_id = fields.get("AGENT_ID", "")
    session = fields.get("SESSION", "")
    if agent_id and not session:
        errors.append("SESSION is required when AGENT_ID is present")
    if session and not re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d+", session):
        errors.append(f"SESSION invalid: {session}")
    if session and not agent_id:
        warnings.append("SESSION provided without AGENT_ID")

    metrics: dict[str, Any] = {}
    if balance_summary_path is not None:
        balance_errors, balance_metrics = validate_regret_distance(balance_summary_path, regret_threshold)
        errors.extend(balance_errors)
        metrics.update(balance_metrics)

    return ValidationResult(
        compliant=not errors,
        contract_found=True,
        fields=fields,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )


def format_human(result: ValidationResult) -> str:
    lines = []
    if not result.contract_found:
        lines.append("FAIL: missing [Governance Contract] block")
        return "\n".join(lines)

    lines.append("Governance Contract Validation")
    lines.append("")
    for key in ("LANG", "LEVEL", "SCOPE", "PLAN", "LOADED", "CONTEXT", "PRESSURE", "AGENT_ID", "SESSION"):
        if key in result.fields:
            lines.append(f"- {key}: {result.fields[key]}")
    if result.metrics:
        lines.append("")
        for key, value in result.metrics.items():
            lines.append(f"- {key}: {value}")
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"- {item}" for item in result.errors)
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in result.warnings)
    if result.compliant:
        lines.append("")
        lines.append("Result: COMPLIANT")
    else:
        lines.append("")
        lines.append("Result: FAILED")
    return "\n".join(lines)


def format_json(result: ValidationResult) -> str:
    return json.dumps(
        {
            "compliant": result.compliant,
            "contract_found": result.contract_found,
            "fields": result.fields,
            "errors": result.errors,
            "warnings": result.warnings,
            "metrics": result.metrics,
        },
        ensure_ascii=False,
        indent=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governance contract blocks and regret distance gates.")
    parser.add_argument("--file", "-f", help="Response file to validate. Defaults to stdin.")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument(
        "--balance-summary",
        default="output/analytics/balance_summary.json",
        help="Balance summary used for regret distance gate.",
    )
    parser.add_argument(
        "--regret-threshold",
        type=float,
        default=0.5,
        help="Minimum allowed avg_steps_from_regret_to_death.",
    )
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8-sig")
    else:
        text = sys.stdin.read()

    result = validate_contract(
        text,
        balance_summary_path=Path(args.balance_summary),
        regret_threshold=args.regret_threshold,
    )
    print(format_json(result) if args.format == "json" else format_human(result))

    if not result.contract_found:
        return 2
    if not result.compliant:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
