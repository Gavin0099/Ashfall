# Current Task: Governance Gate Upgrade and PT-1 Evidence Recovery

## Progress
- [x] Governance regret gate added to `governance_tools/contract_validator.py`
- [x] PT-1 freshness gate added to `governance_tools/plan_freshness.py`
- [x] `FAILURE_CONTEXT.md` auto-generation added
- [x] `memory_janitor.py` upgraded to clean `__pycache__` and generated render/audio caches
- [x] Governance CI workflow updated to run governance tests, phase gates, memory pressure, and failure-context upload
- [x] Cross-platform `scripts/verify_phase_gates.py` added and validated
- [ ] Refresh completed PT-1 evidence after the latest balance change
- [ ] Re-run PT-1 comparison and summary once fresh human logs exist

## Context
- **Recent achievements**: governance tooling now enforces regret distance, PT-1 freshness, failure-context handoff, generated-artifact cleanup, and CI phase gates. `SYSTEM_CONSTRAINTS.md` now explicitly forbids external `.png` / `.wav` usage and requires render classes to expose `get_hash()`.
- **Remaining issues**: `PLAN freshness` is currently `CRITICAL` because completed PT-1 evidence predates the latest balance update. This is now a real gate, not an advisory warning.
- **Next steps**: either refresh PT-1 human evidence after the latest balance change or explicitly stop using stale PT-1 results as balance evidence. After that, re-run `compare_playtest_vs_machine.py`, `generate_pt1_summary.py`, and `generate_failure_context.py` to confirm the governance gate returns to non-critical status.
