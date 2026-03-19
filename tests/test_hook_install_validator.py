from __future__ import annotations

from pathlib import Path

from governance_tools.hook_install_validator import format_human, validate_hook_install


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_validate_hook_install_accepts_framework_backed_external_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "target"
    hook_dir = repo_root / ".git" / "hooks"
    framework_root = tmp_path / "framework"

    _write(hook_dir / "pre-commit", "# AI Governance Framework\n")
    _write(hook_dir / "pre-push", "# AI Governance Framework\n")
    _write(hook_dir / "ai-governance-framework-root", str(framework_root))

    _write(framework_root / "scripts/lib/python.sh", "")
    _write(framework_root / "scripts/run-runtime-governance.sh", "")
    _write(framework_root / "governance_tools/plan_freshness.py", "")
    _write(framework_root / "governance_tools/contract_validator.py", "")

    result = validate_hook_install(repo_root)

    assert result.valid is True
    assert result.framework_root == str(framework_root.resolve())
    assert result.checks["pre_commit_installed"] is True
    assert result.checks["pre_push_installed"] is True
    assert result.checks["framework_file:scripts/lib/python.sh"] is True


def test_validate_hook_install_reports_missing_framework_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "target"
    hook_dir = repo_root / ".git" / "hooks"

    _write(hook_dir / "pre-commit", "# AI Governance Framework\n")
    _write(hook_dir / "pre-push", "# AI Governance Framework\n")

    result = validate_hook_install(repo_root)

    assert result.valid is False
    assert result.framework_root == str(repo_root.resolve())
    assert result.checks["framework_root_config_present"] is False
    assert any("ai-governance-framework-root" in warning for warning in result.warnings)


def test_validate_hook_install_accepts_self_hosted_framework_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "framework"
    hook_dir = repo_root / ".git" / "hooks"

    _write(hook_dir / "pre-commit", "# AI Governance Framework\n")
    _write(hook_dir / "pre-push", "# AI Governance Framework\n")
    _write(repo_root / "scripts/lib/python.sh", "")
    _write(repo_root / "scripts/run-runtime-governance.sh", "")
    _write(repo_root / "governance_tools/plan_freshness.py", "")
    _write(repo_root / "governance_tools/contract_validator.py", "")

    result = validate_hook_install(repo_root)

    assert result.valid is True
    assert result.framework_root == str(repo_root.resolve())
    assert result.checks["framework_root_config_present"] is False


def test_format_human_includes_framework_root_and_errors(tmp_path: Path) -> None:
    repo_root = tmp_path / "target"
    hook_dir = repo_root / ".git" / "hooks"
    _write(hook_dir / "pre-commit", "not ours\n")

    result = validate_hook_install(repo_root)
    rendered = format_human(result)

    assert "framework_root" in rendered
    assert "errors:" in rendered
    assert "缺少 AI Governance pre-push hook" in rendered
