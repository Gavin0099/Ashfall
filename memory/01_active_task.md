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
- [x] Shift north route identity from `ammo` toward `mutant / scrap` via `evt_tunnel` tuning
- [x] Restore north pressure density to `avg_pressure_count = 3.0` with lighter north encounter weighting
- [x] Upgrade balance dashboard to compare final-state resources instead of loot-only identity
- [x] Reject `north_entry` split-bucket experiment after it reduced `north_victory_rate` from `0.45` to `0.40`
- [x] Upgrade dashboard again to expose identity gaps (`archetype_gap`, `resource_gap`) instead of a single hard mutant threshold
- [x] Shape `evt_tunnel` cautious branch into a safer salvage path (`food -1 / hp -1 / scrap +1 / combat_chance 0.25`)
- [x] Reframe `evt_scrapyard` and `evt_tunnel` text toward explicit mutant-salvage identity without changing machine metrics
- [x] Run PT-1 validation/comparison chain and confirm current evidence is still insufficient for fresh balance decisions
- [x] Reject `evt_scrapyard` cautious combat bump (`0.2 -> 0.3`) after it failed to widen north archetype gap and worsened north aggressive lane
- [x] Add `evt_mutant_burrow` to north event pool; keep it after it strengthened north salvage identity without damaging the stable machine baseline
- [x] Reject `evt_mutant_burrow` cautious combat/medkit bump after it broke playability without improving north mutant gap
- [x] Add event-specific `encounter_bias` support and use it in `evt_mutant_burrow` to sharpen north mutant identity without touching global encounter weights
- [ ] Refresh PT-1 only after the next stable balance pass

## Context
- **Recent achievements**: governance tooling now enforces regret distance, PT-1 freshness, failure-context handoff, generated-artifact cleanup, and CI phase gates. Old PT-1 evidence has been explicitly quarantined for the current tuning cycle. Machine-side balance iteration added a shared `node_approach` buffer, completed a south route identity pass that pushed south toward `ammo / raider`, and then restored the regret gate by combining a small content-side risk shift with carryover-aware failure-analysis scoring.
- **Current machine truth**: `victory_rate = 0.44`, `north = 0.50`, `south = 0.40`, `mixed = 0.40`, `avg_pressure_count = 3.52`, `avg_steps_from_regret_to_death = 0.64`. South reads as `ammo / raider`; north now reads as `mutant / scrap`, with `north_archetype_gap = +0.24` and `north_resource_gap = +2.0`.
- **Remaining issues**: `PLAN freshness` remains `CRITICAL` until fresh PT-1 evidence exists. The current PT-1 chain validates structurally, but it still yields only 1 usable comparison (`sample_session_log.json`), so the verdict remains `FAIL` and cannot support current balance decisions. Machine-side identity sharpening is now good enough; the main risk is over-tuning without fresh human confirmation.
- **Next steps**: freeze this machine-side baseline unless a clear bug appears; prioritize converting the already-played CLI sessions into completed PT-1 logs or running a fresh PT-1 batch against this exact baseline. If machine-side work continues, limit it to tooling and evidence-capture improvements rather than more balance shifts. After fresh PT-1 arrives, re-run `compare_playtest_vs_machine.py`, `generate_pt1_summary.py`, and `generate_failure_context.py`.
