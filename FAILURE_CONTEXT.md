# FAILURE_CONTEXT

- overall_status: FAIL
- governance_contract: PASS
- plan_freshness: FAIL

## Immediate Focus
- Refresh PLAN/PT-1 evidence before trusting downstream playtest conclusions.

## Contract Findings
- skipped: True
- reason: no response file supplied for contract validation

## Freshness Findings
- status: CRITICAL
- threshold_days: 7
- days_since_update: 0
- pt1_completed_count: 6
- latest_balance_mtime: 1773738637.7295024
- pt1_latest_mtime: 1773727402.2667387
- errors:
  - PT-1 data is older than most recent balance adjustment. Balance: 2026-03-17 17:10, PT-1: 2026-03-17 14:03

## Next Session Prompt
- Prioritize the failing governance gates before adding new systems.
- If regret gate failed, rebalance events so avg_steps_from_regret_to_death stays at or above the threshold.
- If PT-1 freshness failed, collect or refresh completed playtest logs after the latest balance change.
- Do not treat stale PT-1 results as evidence for new balance decisions.
