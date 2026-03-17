#!/usr/bin/env python3
"""
Summarize whether an external repo is ready to participate in AI Governance runtime flows.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from governance_tools.contract_resolver import resolve_contract
from governance_tools.domain_contract_loader import load_domain_contract
from governance_tools.hook_install_validator import validate_hook_install
from governance_tools.plan_freshness import check_freshness


@dataclass
class ExternalRepoReadiness:
    ready: bool
    repo_root: str
    checks: dict[str, bool] = field(default_factory=dict)
    contract: dict[str, object] | None = None
    plan: dict[str, object] | None = None
    hooks: dict[str, object] | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def assess_external_repo(repo_root: Path, contract_path: str | Path | None = None) -> ExternalRepoReadiness:
    repo_root = repo_root.resolve()
    checks: dict[str, bool] = {}
    warnings: list[str] = []
    errors: list[str] = []

    checks["git_repo_present"] = (repo_root / ".git").exists()
    if not checks["git_repo_present"]:
        errors.append(f"找不到 git repo: {repo_root}")
        return ExternalRepoReadiness(
            ready=False,
            repo_root=str(repo_root),
            checks=checks,
            warnings=warnings,
            errors=errors,
        )

    hook_result = validate_hook_install(repo_root)
    hooks = {
        "valid": hook_result.valid,
        "framework_root": hook_result.framework_root,
        "checks": hook_result.checks,
        "errors": hook_result.errors,
        "warnings": hook_result.warnings,
    }
    checks["hooks_ready"] = hook_result.valid
    warnings.extend(f"hooks: {item}" for item in hook_result.warnings)
    errors.extend(f"hooks: {item}" for item in hook_result.errors)

    plan_path = repo_root / "PLAN.md"
    plan: dict[str, object] | None = None
    if plan_path.exists():
        plan_result = check_freshness(plan_path)
        plan = {
            "path": str(plan_path),
            "status": plan_result.status,
            "days_since_update": plan_result.days_since_update,
            "threshold_days": plan_result.threshold_days,
            "errors": plan_result.errors,
            "warnings": plan_result.warnings,
        }
        checks["plan_present"] = True
        checks["plan_fresh_enough"] = plan_result.status in {"FRESH", "STALE"}
        warnings.extend(f"plan: {item}" for item in plan_result.warnings)
        errors.extend(f"plan: {item}" for item in plan_result.errors)
    else:
        plan = None
        checks["plan_present"] = False
        checks["plan_fresh_enough"] = False
        warnings.append("plan: 找不到 PLAN.md")

    resolution = resolve_contract(contract_path, project_root=repo_root)
    contract: dict[str, object] | None = None
    checks["contract_resolved"] = resolution.path is not None
    if resolution.error:
        errors.append(f"contract: {resolution.error}")
    warnings.extend(f"contract: {item}" for item in resolution.warnings)

    if resolution.path is not None:
        loaded = load_domain_contract(resolution.path)
        missing_docs = [item["path"] for item in loaded["documents"] if not item["exists"]]
        missing_overrides = [item["path"] for item in loaded["ai_behavior_override"] if not item["exists"]]
        missing_validators = [item["path"] for item in loaded["validators"] if not item["exists"]]
        contract = {
            "source": resolution.source,
            "path": str(resolution.path),
            "name": loaded["name"],
            "domain": loaded["raw"].get("domain"),
            "plugin_version": loaded["raw"].get("plugin_version"),
            "documents": len(loaded["documents"]),
            "rule_roots": len(loaded["rule_roots"]),
            "validators": len(loaded["validators"]),
            "missing_documents": missing_docs,
            "missing_behavior_overrides": missing_overrides,
            "missing_validators": missing_validators,
        }
        checks["contract_files_complete"] = not (missing_docs or missing_overrides or missing_validators)
        if missing_docs:
            errors.extend(f"contract: missing document {item}" for item in missing_docs)
        if missing_overrides:
            errors.extend(
                f"contract: missing behavior override {item}" for item in missing_overrides
            )
        if missing_validators:
            errors.extend(f"contract: missing validator {item}" for item in missing_validators)
    else:
        checks["contract_files_complete"] = False
        warnings.append("contract: 尚未解析到 contract.yaml")

    ready = (
        checks["git_repo_present"]
        and checks["hooks_ready"]
        and checks["plan_fresh_enough"]
        and checks["contract_resolved"]
        and checks["contract_files_complete"]
    )

    return ExternalRepoReadiness(
        ready=ready,
        repo_root=str(repo_root),
        checks=checks,
        contract=contract,
        plan=plan,
        hooks=hooks,
        warnings=warnings,
        errors=errors,
    )


def format_human(result: ExternalRepoReadiness) -> str:
    lines = [
        "External Repo Readiness",
        "",
        f"ready              = {result.ready}",
        f"repo_root          = {result.repo_root}",
        "",
        "[checks]",
    ]
    for key in sorted(result.checks):
        lines.append(f"{key:<24} = {result.checks[key]}")

    if result.contract:
        lines.extend(
            [
                "",
                "[contract]",
                f"source             = {result.contract.get('source')}",
                f"path               = {result.contract.get('path')}",
                f"name               = {result.contract.get('name')}",
                f"domain             = {result.contract.get('domain')}",
                f"plugin_version     = {result.contract.get('plugin_version')}",
                f"documents          = {result.contract.get('documents')}",
                f"rule_roots         = {result.contract.get('rule_roots')}",
                f"validators         = {result.contract.get('validators')}",
            ]
        )

    if result.plan:
        lines.extend(
            [
                "",
                "[plan]",
                f"status             = {result.plan.get('status')}",
                f"days_since_update  = {result.plan.get('days_since_update')}",
                f"threshold_days     = {result.plan.get('threshold_days')}",
            ]
        )

    if result.hooks:
        lines.extend(
            [
                "",
                "[hooks]",
                f"valid              = {result.hooks.get('valid')}",
                f"framework_root     = {result.hooks.get('framework_root')}",
            ]
        )

    if result.errors:
        lines.append("")
        lines.append(f"errors: {len(result.errors)}")
        for item in result.errors:
            lines.append(f"- {item}")

    if result.warnings:
        lines.append("")
        lines.append(f"warnings: {len(result.warnings)}")
        for item in result.warnings:
            lines.append(f"- {item}")

    return "\n".join(lines)


def format_json(result: ExternalRepoReadiness) -> str:
    return json.dumps(
        {
            "ready": result.ready,
            "repo_root": result.repo_root,
            "checks": result.checks,
            "contract": result.contract,
            "plan": result.plan,
            "hooks": result.hooks,
            "errors": result.errors,
            "warnings": result.warnings,
        },
        ensure_ascii=False,
        indent=2,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess whether an external repo is ready for AI Governance integration."
    )
    parser.add_argument("--repo", default=".", help="Target repo root.")
    parser.add_argument("--contract", help="Optional explicit contract.yaml path.")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = assess_external_repo(Path(args.repo), contract_path=args.contract)
    if args.format == "json":
        print(format_json(result))
    else:
        print(format_human(result))
    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
