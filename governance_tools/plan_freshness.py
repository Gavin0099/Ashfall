#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_human_playtest_logs import is_completed_log, load_json


POLICY_DEFAULTS = {
    "sprint": 7,
    "phase": 30,
}

STATUS_FRESH = "FRESH"
STATUS_STALE = "STALE"
STATUS_CRITICAL = "CRITICAL"
STATUS_ERROR = "ERROR"


@dataclass
class FreshnessResult:
    status: str
    last_updated: Optional[date]
    owner: Optional[str]
    policy: Optional[str]
    threshold_days: Optional[int]
    days_since_update: Optional[int]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latest_balance_mtime: Optional[str] = None
    pt1_latest_mtime: Optional[str] = None
    pt1_completed_count: int = 0


def parse_header_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pattern = re.compile(r">\s*\*\*([^*]+)\*\*:\s*(.+)")
    for match in pattern.finditer(text):
        fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def parse_policy(policy_str: str | None) -> Optional[int]:
    if not policy_str:
        return None
    explicit = re.search(r"\((\d+)d\)", policy_str, re.IGNORECASE)
    if explicit:
        return int(explicit.group(1))
    lowered = policy_str.lower()
    for key, days in POLICY_DEFAULTS.items():
        if key in lowered:
            return days
    return None


def latest_completed_pt1_mtime(playtest_dir: Path) -> tuple[Optional[datetime], int]:
    completed_times: list[datetime] = []
    for path in sorted(playtest_dir.glob("*_session_log.json")):
        payload = load_json(path)
        if is_completed_log(payload):
            completed_times.append(datetime.fromtimestamp(path.stat().st_mtime))
    if not completed_times:
        return None, 0
    return max(completed_times), len(completed_times)


def check_freshness(
    plan_path: Path,
    threshold_override: Optional[int] = None,
    today: Optional[date] = None,
    *,
    pt1_dir: Path | None = None,
    balance_summary_path: Path | None = None,
) -> FreshnessResult:
    if today is None:
        today = date.today()

    if not plan_path.exists():
        return FreshnessResult(
            status=STATUS_ERROR,
            last_updated=None,
            owner=None,
            policy=None,
            threshold_days=None,
            days_since_update=None,
            errors=[f"missing PLAN file: {plan_path}"],
        )

    fields = parse_header_fields(plan_path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    warnings: list[str] = []

    raw_date = fields.get("Last Updated") or fields.get("最後更新")
    last_updated: Optional[date] = None
    if not raw_date:
        errors.append("PLAN header missing Last Updated")
    else:
        try:
            last_updated = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append(f"invalid Last Updated format: {raw_date}")

    owner = fields.get("Owner")
    if not owner:
        warnings.append("PLAN header missing Owner")

    policy = fields.get("Freshness")
    threshold_days = threshold_override if threshold_override is not None else parse_policy(policy)
    if threshold_days is None:
        warnings.append("Freshness policy missing or unknown; defaulting to Sprint (7d)")
        threshold_days = POLICY_DEFAULTS["sprint"]

    if errors:
        return FreshnessResult(
            status=STATUS_ERROR,
            last_updated=last_updated,
            owner=owner,
            policy=policy,
            threshold_days=threshold_days,
            days_since_update=None,
            errors=errors,
            warnings=warnings,
        )

    assert last_updated is not None
    days_since_update = (today - last_updated).days
    if days_since_update <= threshold_days:
        status = STATUS_FRESH
    elif days_since_update <= threshold_days * 2:
        status = STATUS_STALE
        warnings.append(f"PLAN is stale: {days_since_update}d since update > {threshold_days}d threshold")
    else:
        status = STATUS_CRITICAL
        errors.append(f"PLAN is critically stale: {days_since_update}d since update")

    latest_balance_mtime: Optional[datetime] = None
    latest_pt1_mtime: Optional[datetime] = None
    pt1_completed_count = 0

    if balance_summary_path is not None and balance_summary_path.exists():
        latest_balance_mtime = datetime.fromtimestamp(balance_summary_path.stat().st_mtime)

    if pt1_dir is not None and pt1_dir.exists():
        latest_pt1_mtime, pt1_completed_count = latest_completed_pt1_mtime(pt1_dir)
        if latest_balance_mtime and latest_pt1_mtime and latest_pt1_mtime < latest_balance_mtime:
            status = STATUS_CRITICAL
            errors.append(
                "PT-1 data is older than the latest balance change: "
                f"pt1={latest_pt1_mtime.isoformat()} < balance={latest_balance_mtime.isoformat()}"
            )
        elif latest_balance_mtime and pt1_completed_count == 0:
            warnings.append("No completed PT-1 logs found after latest balance change")

    return FreshnessResult(
        status=status,
        last_updated=last_updated,
        owner=owner,
        policy=policy,
        threshold_days=threshold_days,
        days_since_update=days_since_update,
        errors=errors,
        warnings=warnings,
        latest_balance_mtime=latest_balance_mtime.isoformat() if latest_balance_mtime else None,
        pt1_latest_mtime=latest_pt1_mtime.isoformat() if latest_pt1_mtime else None,
        pt1_completed_count=pt1_completed_count,
    )


def format_human(result: FreshnessResult, plan_path: Path) -> str:
    lines = [
        "Plan Freshness Report",
        f"- plan_path: {plan_path}",
        f"- status: {result.status}",
        f"- last_updated: {result.last_updated}",
        f"- owner: {result.owner}",
        f"- policy: {result.policy}",
        f"- threshold_days: {result.threshold_days}",
        f"- days_since_update: {result.days_since_update}",
        f"- pt1_completed_count: {result.pt1_completed_count}",
    ]
    if result.latest_balance_mtime:
        lines.append(f"- latest_balance_mtime: {result.latest_balance_mtime}")
    if result.pt1_latest_mtime:
        lines.append(f"- pt1_latest_mtime: {result.pt1_latest_mtime}")
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {item}" for item in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in result.warnings)
    return "\n".join(lines)


def format_json(result: FreshnessResult, plan_path: Path) -> str:
    return json.dumps(
        {
            "plan_path": str(plan_path),
            "status": result.status,
            "last_updated": result.last_updated.isoformat() if result.last_updated else None,
            "owner": result.owner,
            "policy": result.policy,
            "threshold_days": result.threshold_days,
            "days_since_update": result.days_since_update,
            "errors": result.errors,
            "warnings": result.warnings,
            "latest_balance_mtime": result.latest_balance_mtime,
            "pt1_latest_mtime": result.pt1_latest_mtime,
            "pt1_completed_count": result.pt1_completed_count,
        },
        ensure_ascii=False,
        indent=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PLAN freshness and PT-1 staleness against balance changes.")
    parser.add_argument("--file", "-f", default="PLAN.md")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--threshold", "-t", type=int, default=None)
    parser.add_argument("--pt1-dir", default="playtests")
    parser.add_argument("--balance-summary", default="output/analytics/balance_summary.json")
    args = parser.parse_args()

    plan_path = Path(args.file)
    result = check_freshness(
        plan_path,
        threshold_override=args.threshold,
        pt1_dir=Path(args.pt1_dir),
        balance_summary_path=Path(args.balance_summary),
    )
    print(format_json(result, plan_path) if args.format == "json" else format_human(result, plan_path))

    if result.status in {STATUS_CRITICAL, STATUS_ERROR}:
        return 2
    if result.status == STATUS_STALE:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
