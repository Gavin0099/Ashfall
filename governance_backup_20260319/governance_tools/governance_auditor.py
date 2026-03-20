#!/usr/bin/env python3
"""
Governance self-auditor for constitution, runtime, and rule-pack alignment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from governance_tools.external_repo_onboarding_index import build_external_repo_onboarding_index
from governance_tools.human_summary import build_summary_line
from governance_tools.release_readiness import assess_release_readiness


REQUIRED_DOCS = [
    "governance/SYSTEM_PROMPT.md",
    "governance/HUMAN-OVERSIGHT.md",
    "governance/AGENT.md",
    "governance/ARCHITECTURE.md",
    "governance/REVIEW_CRITERIA.md",
    "governance/TESTING.md",
    "README.md",
]

REQUIRED_RUNTIME_FILES = [
    "runtime_hooks/core/pre_task_check.py",
    "runtime_hooks/core/post_task_check.py",
    "runtime_hooks/core/session_end.py",
    "runtime_hooks/dispatcher.py",
    "scripts/run-runtime-governance.sh",
]

SEED_RULE_PACKS = ["common", "python", "cpp", "refactor"]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def audit_governance(
    project_root: Path,
    external_repos: list[Path] | None = None,
    release_version: str | None = None,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, object]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            errors.append(f"{name}: {detail}")

    for relative in REQUIRED_DOCS:
        path = project_root / relative
        add_check(f"doc:{relative}", path.is_file(), "required governance doc is missing")

    for relative in REQUIRED_RUNTIME_FILES:
        path = project_root / relative
        add_check(f"runtime:{relative}", path.is_file(), "required runtime enforcement file is missing")

    pack_root = project_root / "governance" / "rules"
    for pack in SEED_RULE_PACKS:
        pack_dir = pack_root / pack
        has_markdown = pack_dir.is_dir() and any(pack_dir.glob("*.md"))
        add_check(f"rule-pack:{pack}", has_markdown, "rule pack directory or markdown content is missing")

    workflow_path = project_root / ".github" / "workflows" / "governance.yml"
    workflow_text = _read_text(workflow_path) if workflow_path.is_file() else ""
    add_check(
        "workflow:runtime-enforcement",
        "scripts/run-runtime-governance.sh --mode ci" in workflow_text,
        "workflow does not invoke shared runtime enforcement script",
    )

    runtime_readme_path = project_root / "runtime_hooks" / "README.md"
    runtime_readme_text = _read_text(runtime_readme_path) if runtime_readme_path.is_file() else ""
    add_check(
        "docs:runtime-readme-enforcement",
        "scripts/run-runtime-governance.sh" in runtime_readme_text,
        "runtime_hooks/README.md does not document the shared enforcement entrypoint",
    )

    readme_path = project_root / "README.md"
    readme_text = _read_text(readme_path) if readme_path.is_file() else ""
    add_check(
        "docs:readme-enforcement",
        "scripts/run-runtime-governance.sh" in readme_text,
        "README.md does not mention the shared runtime enforcement path",
    )

    system_prompt_text = _read_text(project_root / "governance" / "SYSTEM_PROMPT.md") if (project_root / "governance" / "SYSTEM_PROMPT.md").is_file() else ""
    architecture_text = _read_text(project_root / "governance" / "ARCHITECTURE.md") if (project_root / "governance" / "ARCHITECTURE.md").is_file() else ""
    review_text = _read_text(project_root / "governance" / "REVIEW_CRITERIA.md") if (project_root / "governance" / "REVIEW_CRITERIA.md").is_file() else ""
    cpp_pack_text = ""
    cpp_pack_path = project_root / "governance" / "rules" / "cpp" / "build_boundary.md"
    if cpp_pack_path.is_file():
        cpp_pack_text = _read_text(cpp_pack_path)

    add_check(
        "alignment:build-boundary",
        (
            "cross-project private include" in system_prompt_text
            and "AdditionalIncludeDirectories" in architecture_text
            and "C9 Project Include Boundary" in review_text
            and "AdditionalIncludeDirectories" in cpp_pack_text
        ),
        "build-boundary rule is not aligned across constitution, review, and runtime pack",
    )

    refactor_pack_dir = project_root / "governance" / "rules" / "refactor"
    refactor_files = {path.name for path in refactor_pack_dir.glob("*.md")} if refactor_pack_dir.is_dir() else set()
    add_check(
        "alignment:refactor-pack",
        {"behavior_lock.md", "boundary_safety.md"}.issubset(refactor_files),
        "refactor rule pack is incomplete",
    )

    if "runtime-enforcement" not in workflow_text:
        warnings.append("Workflow job name 'runtime-enforcement' was not found; enforcement may be harder to locate.")

    release_readiness = None
    if release_version:
        release_readiness = assess_release_readiness(project_root, version=release_version)
        add_check(
            "release:readiness",
            release_readiness["ok"],
            "release-facing docs are not aligned for the requested version",
        )
        warnings.extend(release_readiness.get("warnings", []))

    external_onboarding = None
    if external_repos:
        external_onboarding = build_external_repo_onboarding_index(external_repos)
        add_check(
            "external:onboarding-index",
            external_onboarding["ok"],
            "one or more external repos are missing onboarding reports or have failing onboarding state",
        )
        for missing in external_onboarding.get("missing_reports", []):
            warnings.append(f"External onboarding report missing: {missing}")

    return {
        "ok": len(errors) == 0,
        "project_root": str(project_root),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "release_readiness": release_readiness,
        "external_onboarding": external_onboarding,
    }


def format_human_result(result: dict) -> str:
    lines = [
        "[governance_auditor]",
    ]
    release_readiness = result.get("release_readiness")
    external_onboarding = result.get("external_onboarding")
    lines.append(
        build_summary_line(
            f"ok={result['ok']}",
            f"checks={len(result['checks'])}",
            (
                f"release={release_readiness['version']}/"
                + ("ready" if release_readiness["ok"] else "not-ready")
            )
            if release_readiness is not None
            else None,
            (
                f"external_repos={external_onboarding['repo_count']}"
                if external_onboarding is not None
                else None
            ),
            (
                f"external_top_issues={len(external_onboarding.get('top_issues') or [])}"
                if external_onboarding is not None
                else None
            ),
        )
    )
    lines.append(f"ok={result['ok']}")
    lines.append(f"checks={len(result['checks'])}")

    if release_readiness is not None:
        lines.append(f"release_version={release_readiness['version']}")
        lines.append(f"release_ready={release_readiness['ok']}")
    if external_onboarding is not None:
        lines.append(f"external_repo_count={external_onboarding['repo_count']}")
        lines.append(f"external_indexed_count={external_onboarding['indexed_count']}")
        top_issues = external_onboarding.get("top_issues") or []
        for item in top_issues:
            lines.append(
                "external_top_issue="
                + " | ".join(
                    [
                        item["repo_root"],
                        f"reasons={','.join(item['reasons'])}",
                        f"contract_path={item.get('contract_path')}",
                        f"suggested_command={item.get('suggested_command')}",
                    ]
                )
            )
    for warning in result["warnings"]:
        lines.append(f"warning: {warning}")
    for error in result["errors"]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit governance constitution/runtime alignment.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--external-repo", action="append", default=[])
    parser.add_argument("--release-version")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    args = parser.parse_args()

    result = audit_governance(
        Path(args.project_root).resolve(),
        external_repos=[Path(item) for item in args.external_repo],
        release_version=args.release_version,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_human_result(result))

    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
