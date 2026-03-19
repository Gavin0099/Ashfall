from __future__ import annotations

from pathlib import Path

from governance_tools.external_repo_readiness import assess_external_repo, format_human


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_framework(repo_root: Path) -> None:
    _write(repo_root / "scripts/lib/python.sh", "")
    _write(repo_root / "scripts/run-runtime-governance.sh", "")
    _write(repo_root / "governance_tools/plan_freshness.py", "")
    _write(repo_root / "governance_tools/contract_validator.py", "")


def test_assess_external_repo_returns_ready_for_complete_repo(tmp_path: Path) -> None:
    framework_root = tmp_path / "framework"
    target_root = tmp_path / "target"
    hook_dir = target_root / ".git" / "hooks"

    _make_framework(framework_root)
    _write(hook_dir / "pre-commit", "# AI Governance Framework\n")
    _write(hook_dir / "pre-push", "# AI Governance Framework\n")
    _write(hook_dir / "ai-governance-framework-root", str(framework_root))
    _write(
        target_root / "PLAN.md",
        "> **最後更新**: 2026-03-14\n> **Owner**: test\n> **Freshness**: Sprint (7d)\n",
    )
    _write(target_root / "AGENTS.md", "# Agents\n")
    _write(target_root / "CHECKLIST.md", "# Checklist\n")
    _write(target_root / "rules/domain/safety.md", "# rule\n")
    _write(target_root / "validators/checker.py", "print('ok')\n")
    _write(
        target_root / "contract.yaml",
        "\n".join(
            [
                "name: sample-contract",
                "domain: firmware",
                "plugin_version: \"1.0.0\"",
                "documents:",
                "  - CHECKLIST.md",
                "ai_behavior_override:",
                "  - AGENTS.md",
                "rule_roots:",
                "  - rules",
                "validators:",
                "  - validators/checker.py",
            ]
        ),
    )

    result = assess_external_repo(target_root)

    assert result.ready is True
    assert result.checks["hooks_ready"] is True
    assert result.checks["contract_resolved"] is True
    assert result.contract["name"] == "sample-contract"


def test_assess_external_repo_reports_missing_contract_and_hooks(tmp_path: Path) -> None:
    target_root = tmp_path / "target"
    _write(target_root / ".git" / "HEAD", "ref: refs/heads/main\n")
    _write(
        target_root / "PLAN.md",
        "> **最後更新**: 2026-03-14\n> **Owner**: test\n> **Freshness**: Sprint (7d)\n",
    )

    result = assess_external_repo(target_root)

    assert result.ready is False
    assert result.checks["hooks_ready"] is False
    assert result.checks["contract_resolved"] is False
    assert any("尚未解析到 contract.yaml" in item for item in result.warnings)


def test_format_human_surfaces_contract_plan_and_hook_sections(tmp_path: Path) -> None:
    target_root = tmp_path / "target"
    _write(target_root / ".git" / "HEAD", "ref: refs/heads/main\n")

    result = assess_external_repo(target_root)
    rendered = format_human(result)

    assert "External Repo Readiness" in rendered
    assert "[checks]" in rendered
    assert "[hooks]" in rendered
    assert "errors:" in rendered
