#!/bin/bash

set -euo pipefail

PASS=0
FAIL=0

ok()   { echo "  OK  $1"; }
fail() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }
info() { echo ""; echo "== $1 =="; }

echo "Phase Gate Verification"
echo "======================="

info "Gate 1 / Governance unit tests"
if python -m pytest tests/ -q --tb=short --basetemp .pytest_tmp; then
    ok "governance tests passed"
    PASS=$((PASS + 1))
else
    fail "governance tests failed"
fi

info "Gate 2 / Gameplay validation pipeline"
GAMEPLAY_COMMANDS=(
    "python scripts/test_failure_paths.py"
    "python scripts/run_playability_check.py"
    "python scripts/run_balance_metrics.py"
    "python scripts/validate_run_analytics.py"
    "python scripts/validate_event_templates.py"
    "python scripts/verify_deterministic_run.py"
)

GAMEPLAY_OK=1
for command in "${GAMEPLAY_COMMANDS[@]}"; do
    if bash -lc "$command" > /dev/null 2>&1; then
        ok "$command"
    else
        fail "$command"
        GAMEPLAY_OK=0
    fi
done
if [ "$GAMEPLAY_OK" -eq 1 ]; then
    PASS=$((PASS + 1))
fi

info "Gate 3 / PLAN freshness"
PLAN_OUTPUT=$(python governance_tools/plan_freshness.py --format json) || true
PLAN_STATUS=$(echo "$PLAN_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")
PLAN_DAYS=$(echo "$PLAN_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('days_since_update','?'))")

if [ "$PLAN_STATUS" = "CRITICAL" ] || [ "$PLAN_STATUS" = "ERROR" ]; then
    fail "PLAN.md freshness: $PLAN_STATUS (${PLAN_DAYS}d)"
elif [ "$PLAN_STATUS" = "STALE" ]; then
    ok "PLAN.md freshness: STALE (${PLAN_DAYS}d, advisory)"
    PASS=$((PASS + 1))
else
    ok "PLAN.md freshness: $PLAN_STATUS (${PLAN_DAYS}d)"
    PASS=$((PASS + 1))
fi

info "Gate 4 / Governance tools"
TOOLS=(
    "contract_validator.py"
    "plan_freshness.py"
    "memory_janitor.py"
    "state_generator.py"
)

TOOLS_OK=1
for tool in "${TOOLS[@]}"; do
    if python "governance_tools/$tool" --help > /dev/null 2>&1; then
        ok "$tool"
    else
        fail "$tool --help"
        TOOLS_OK=0
    fi
done
if [ "$TOOLS_OK" -eq 1 ]; then
    PASS=$((PASS + 1))
fi

info "Gate 5 / Required docs"
DOCS=(
    "README.md"
    "PLAN.md"
    "tasks/TASKS.md"
    "PROTOTYPE_SUCCESS_CRITERIA.md"
    "PLAYTEST_PROTOCOL.md"
    "BALANCING_NOTES_v0_1.md"
)

DOCS_OK=1
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        ok "$doc"
    else
        fail "$doc missing"
        DOCS_OK=0
    fi
done
if [ "$DOCS_OK" -eq 1 ]; then
    PASS=$((PASS + 1))
fi

echo ""
TOTAL=$((PASS + FAIL))
echo "Passed: ${PASS}/${TOTAL} gates"

if [ "$FAIL" -eq 0 ]; then
    echo "All phase gates passed."
    exit 0
fi

echo "Phase gate verification failed."
exit 1
