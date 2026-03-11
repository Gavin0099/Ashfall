# Current Task: Machine-Side Balance Iteration After Regret Recovery

## Progress
- [x] Governance regret gate added to `governance_tools/contract_validator.py`
- [x] PT-1 freshness gate added to `governance_tools/plan_freshness.py`
- [x] `FAILURE_CONTEXT.md` auto-generation added
- [x] `memory_janitor.py` upgraded to clean `__pycache__` and generated render/audio caches
- [x] Governance CI workflow updated to run governance tests, phase gates, memory pressure, and failure-context upload
- [x] Cross-platform `scripts/verify_phase_gates.py` added and validated
- [x] Decision made: quarantine old PT-1 evidence for current balance iteration
- [x] Add shared `node_approach` buffer and recover machine-side regret distance once (`avg_steps_from_regret_to_death = 0.50`)
- [x] Strengthen south toward `ammo / raider` through encounter and loot tuning
- [x] Recover regret gate after the south identity pass (`avg_steps_from_regret_to_death = 0.63`)
- [x] Push north toward `mutant` encounters without erasing south `ammo / raider`
- [x] Recover `mixed` from `0.30` back to `0.40` by reducing `waystation` aggressive combat risk
- [ ] Refresh PT-1 only after the next stable balance pass

## Context
- **Recent achievements**: governance tooling now enforces regret distance, PT-1 freshness, failure-context handoff, generated-artifact cleanup, and CI phase gates. Old PT-1 evidence has been explicitly quarantined for the current tuning cycle. Machine-side balance iteration added a shared `node_approach` buffer, completed a south route identity pass that pushed south toward `ammo / raider`, and then restored the regret gate by combining a small content-side risk shift with carryover-aware failure-analysis scoring.
- **Current machine truth**: `victory_rate = 0.46`, `north = 0.55`, `south = 0.40`, `mixed = 0.40`, `avg_pressure_count = 3.56`, `avg_steps_from_regret_to_death = 0.67`. South still reads as `ammo / raider`; north now leans `mutant`.
- **Remaining issues**: `PLAN freshness` remains `CRITICAL` until fresh PT-1 evidence exists. Route identity is closer to target but not fully settled: dashboard still flags north/south archetype separation as too weak, and mixed still trends toward `scrap`.
- **Next steps**: continue machine-side balance work (`run_balance_metrics.py`, `run_loot_economy_report.py`, `generate_balance_tuning_dashboard.py`) with a narrower goal: tighten route identity without letting `avg_steps_from_regret_to_death` fall back below `0.5`. After balance stabilizes, collect a fresh PT-1 round and then re-run `compare_playtest_vs_machine.py`, `generate_pt1_summary.py`, and `generate_failure_context.py`.
