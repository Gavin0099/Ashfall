#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance_tools.contract_validator import validate_contract
from governance_tools.plan_freshness import check_freshness


def _load_contract_text(response_file: Path | None) -> str:
    if response_file and response_file.exists():
        return response_file.read_text(encoding="utf-8-sig")
    return ""


def _status_line(ok: bool, name: str) -> str:
    return f"- {name}: {'PASS' if ok else 'FAIL'}"


def build_failure_context(
    *,
    response_file: Path | None,
    plan_file: Path,
    balance_summary: Path,
    pt1_dir: Path,
    regret_threshold: float,
    skip_contract: bool,
) -> str:
    if skip_contract:
        contract_result = None
    else:
        contract_text = _load_contract_text(response_file)
        contract_result = validate_contract(
            contract_text,
            balance_summary_path=balance_summary,
            regret_threshold=regret_threshold,
        )
    freshness_result = check_freshness(
        plan_file,
        pt1_dir=pt1_dir,
        balance_summary_path=balance_summary,
    )

    contract_ok = True if skip_contract else bool(contract_result and contract_result.compliant)
    freshness_ok = freshness_result.status == "FRESH"
    overall_ok = contract_ok and freshness_ok

    lines: list[str] = [
        "# FAILURE_CONTEXT",
        "",
        f"- overall_status: {'PASS' if overall_ok else 'FAIL'}",
        _status_line(contract_ok, "governance_contract"),
        _status_line(freshness_ok, "plan_freshness"),
        "",
        "## Immediate Focus",
    ]

    if overall_ok:
        lines.append("- No blocking governance failure detected.")
    else:
        if not contract_ok:
            lines.append("- Fix governance contract violations before continuing feature work.")
        if not freshness_ok:
            lines.append("- Refresh PLAN/PT-1 evidence before trusting downstream playtest conclusions.")

    lines.extend([
        "",
        "## Contract Findings",
        f"- skipped: {skip_contract}",
    ])
    if skip_contract:
        lines.append("- reason: no response file supplied for contract validation")
    else:
        assert contract_result is not None
        lines.append(f"- contract_found: {contract_result.contract_found}")
        lines.append(f"- compliant: {contract_result.compliant}")
        if contract_result.metrics:
            for key, value in contract_result.metrics.items():
                lines.append(f"- {key}: {value}")
        if contract_result.errors:
            lines.append("- errors:")
            lines.extend(f"  - {item}" for item in contract_result.errors)
        if contract_result.warnings:
            lines.append("- warnings:")
            lines.extend(f"  - {item}" for item in contract_result.warnings)

    lines.extend([
        "",
        "## Freshness Findings",
        f"- status: {freshness_result.status}",
        f"- threshold_days: {freshness_result.threshold_days}",
        f"- days_since_update: {freshness_result.days_since_update}",
        f"- pt1_completed_count: {freshness_result.pt1_completed_count}",
    ])
    if freshness_result.latest_balance_mtime:
        lines.append(f"- latest_balance_mtime: {freshness_result.latest_balance_mtime}")
    if freshness_result.pt1_latest_mtime:
        lines.append(f"- pt1_latest_mtime: {freshness_result.pt1_latest_mtime}")
    if freshness_result.errors:
        lines.append("- errors:")
        lines.extend(f"  - {item}" for item in freshness_result.errors)
    if freshness_result.warnings:
        lines.append("- warnings:")
        lines.extend(f"  - {item}" for item in freshness_result.warnings)

    lines.extend([
        "",
        "## Next Session Prompt",
        "- Prioritize the failing governance gates before adding new systems.",
        "- If regret gate failed, rebalance events so avg_steps_from_regret_to_death stays at or above the threshold.",
        "- If PT-1 freshness failed, collect or refresh completed playtest logs after the latest balance change.",
        "- Do not treat stale PT-1 results as evidence for new balance decisions.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FAILURE_CONTEXT.md from governance gates.")
    parser.add_argument("--response-file", default=None, help="Optional assistant response file containing a Governance Contract block.")
    parser.add_argument("--plan-file", default="PLAN.md")
    parser.add_argument("--balance-summary", default="output/analytics/balance_summary.json")
    parser.add_argument("--pt1-dir", default="playtests")
    parser.add_argument("--regret-threshold", type=float, default=0.5)
    parser.add_argument("--output", default="FAILURE_CONTEXT.md")
    parser.add_argument("--skip-contract", action="store_true")
    args = parser.parse_args()

    content = build_failure_context(
        response_file=Path(args.response_file) if args.response_file else None,
        plan_file=Path(args.plan_file),
        balance_summary=Path(args.balance_summary),
        pt1_dir=Path(args.pt1_dir),
        regret_threshold=args.regret_threshold,
        skip_contract=args.skip_contract,
    )
    output_path = Path(args.output)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
