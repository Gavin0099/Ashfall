#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GOVERNANCE_TESTS = [
    [sys.executable, "-m", "pytest", "tests/test_memory_janitor.py", "tests/test_contract_validator.py", "tests/test_plan_freshness.py", "-q", "--tb=short", "-p", "no:cacheprovider"],
]

GAMEPLAY_COMMANDS = [
    [sys.executable, "scripts/test_failure_paths.py"],
    [sys.executable, "scripts/run_playability_check.py"],
    [sys.executable, "scripts/run_balance_metrics.py"],
    [sys.executable, "scripts/validate_run_analytics.py"],
    [sys.executable, "scripts/validate_event_templates.py"],
    [sys.executable, "scripts/verify_deterministic_run.py"],
]

TOOLS = [
    "contract_validator.py",
    "plan_freshness.py",
    "memory_janitor.py",
    "generate_failure_context.py",
    "state_generator.py",
]

DOCS = [
    "README.md",
    "PLAN.md",
    "tasks/TASKS.md",
    "PROTOTYPE_SUCCESS_CRITERIA.md",
    "PLAYTEST_PROTOCOL.md",
    "BALANCING_NOTES_v0_1.md",
]


def run_command(command: list[str], *, quiet: bool = False) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    if not quiet and output.strip():
        print(output.strip())
    return result.returncode == 0, output


def ok(message: str) -> None:
    print(f"  OK   {message}")


def fail(message: str) -> None:
    print(f"  FAIL {message}")


def info(message: str) -> None:
    print(f"\n== {message} ==")


def main() -> int:
    passed = 0
    failed = 0

    print("Phase Gate Verification")
    print("=======================")

    info("Gate 1 / Governance unit tests")
    governance_ok = True
    for command in GOVERNANCE_TESTS:
        success, _ = run_command(command, quiet=False)
        if success:
            ok(" ".join(command[2:]))
        else:
            fail(" ".join(command[2:]))
            governance_ok = False
    if governance_ok:
        passed += 1
    else:
        failed += 1

    info("Gate 2 / Gameplay validation pipeline")
    gameplay_ok = True
    for command in GAMEPLAY_COMMANDS:
        success, _ = run_command(command, quiet=True)
        label = " ".join(command[1:])
        if success:
            ok(label)
        else:
            fail(label)
            gameplay_ok = False
    if gameplay_ok:
        passed += 1
    else:
        failed += 1

    info("Gate 3 / PLAN freshness")
    _, output = run_command([sys.executable, "governance_tools/plan_freshness.py", "--format", "json"], quiet=True)
    import json
    payload = json.loads(output)
    status = payload["status"]
    days = payload.get("days_since_update", "?")
    if status in {"CRITICAL", "ERROR"}:
        fail(f"PLAN.md freshness: {status} ({days}d)")
        failed += 1
    else:
        ok(f"PLAN.md freshness: {status} ({days}d)")
        passed += 1

    info("Gate 4 / Governance tools")
    tools_ok = True
    for tool in TOOLS:
        success, _ = run_command([sys.executable, f"governance_tools/{tool}", "--help"], quiet=True)
        if success:
            ok(tool)
        else:
            fail(f"{tool} --help")
            tools_ok = False
    if tools_ok:
        passed += 1
    else:
        failed += 1

    info("Gate 5 / Required docs")
    docs_ok = True
    for doc in DOCS:
        if (ROOT / doc).exists():
            ok(doc)
        else:
            fail(f"{doc} missing")
            docs_ok = False
    if docs_ok:
        passed += 1
    else:
        failed += 1

    print(f"\nPassed: {passed}/{passed + failed} gates")
    if failed:
        print("Phase gate verification failed.")
        return 1
    print("All phase gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
