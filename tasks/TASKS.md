# TASKS.md — Ashfall Execution Board

Last Updated: 2026-03-11
Owner: GavinWu
Execution Truth (Sprint/Task): `tasks/TASKS.md`
Phase/Gate/Milestone Truth: `PLAN.md`

---

## Current Sprint (2026/03/09 - 2026/03/15)

### In Progress
- [ ] BAL-1 Run machine-side balance iteration only; do not cite stale PT-1 evidence for current tuning decisions
Artifact status: `north=0.55`, `south=0.40`, `mixed=0.40`, `avg_steps_from_regret_to_death=0.67`; regret gate remains recovered, south still reads `ammo / raider`, and north now leans `mutant`
- [ ] GOV-2 Keep old PT-1 evidence quarantined until a post-balance refresh is collected

### Ready
- [ ] BAL-3 Tighten route identity after regret recovery without erasing south `ammo / raider` identity
Artifact target: `output/analytics/balance_summary.json` / `output/summaries/balance_tuning_dashboard.md` with south still dominant in `ammo / raider`, north clearly mutant-leaning, `mixed` held near current band, and `avg_steps_from_regret_to_death >= 0.5`
- [x] GOV-3 Wire governance CI checks into repository enforcement and keep `FAILURE_CONTEXT.md` in failure artifacts
- [ ] PT-2 Compare human playtest logs against machine `failure_analysis`
Artifact target: `output/playtests/comparison_summary.json` with hesitation/regret mismatch breakdowns, machine blame breakdown, and equipment-arc notice rate; `output/playtests/PT2_action_report.md` for direct follow-up recommendations
- [x] OBS-1 Run first-node dominance test from `SEED_101_OBSERVATION.md`
- [x] OBS-2 Test conservative survivability across multiple seeds
- [x] OBS-3 Compare high-risk vs low-risk event payoff across >=100 runs
Artifacts: `output/analytics/obs/obs_combined_summary.json`, `scripts/run_obs_experiments.py`
- [x] EXP-1 Prototype explicit irreversible trade (`max_hp` sacrifice for short-term survival)
Artifacts: `output/analytics/exp/exp1_max_hp_trade.json`, `scripts/run_exp1_max_hp_trade.py`
- [x] EXP-2 Evaluate `travel mode` as a controlled decision-depth experiment
  Artifact: `scripts/run_exp2_travel_mode.py`, `output/analytics/exp/exp2_travel_mode.json`
  Verdict: REJECTED — travel mode shifts death vector but does not extend consequence arc (map too short, consequence_len=0 across all groups)
- [x] EXP-3 Prototype character background as a run-identity layer
  Artifact: `scripts/run_exp3_character_background.py`, `output/analytics/exp/exp3_character_background.json`
  Verdict: SUPPORTED — `soldier` strengthens north-route survivability (+18% win vs baseline), `pathfinder` flips south from 0% to 62% win by removing starvation; `scavenger` and `medic` are too weak to matter
- [x] EXP-4 Prototype minimal equipment slots (weapon / armor / tool)
  Artifact: `scripts/run_exp4_equipment_slots.py`, `output/analytics/exp/exp4_equipment_slots.json`
  Verdict: SUPPORTED — under real event acquisition/replacement, enabling equipment raises north win rate from 28% to 40% (`makeshift_blade` -> `rust_rifle`) and south from 0% to 66% (`scavenger_kit` -> `field_pack`); the strongest effect is still food slack, not combat scaling

### Playability Check
- [x] PLY-1 Run 5 manual playthroughs with different route choices
- [x] PLY-2 Record 3 moments of meaningful tension per run
- [x] PLY-3 Verify different paths produce different resource states or outcomes
- [x] PLY-4 Verify death causes are explainable from run logs
Artifacts: `output/playability/summary.json`, `output/playability/run_*.json`

### Done
- [x] GOV-1 Upgrade governance gates (`contract_validator`, `plan_freshness`, `generate_failure_context`, `memory_janitor`, CI workflow)
- [x] GOV-3 Enforce governance checks in CI and phase gate workflow
- [x] T-A1 Read and align existing `specs/*.md` + `schemas/*.json`
- [x] T-A2 Draft `specs/meta_progression.md`
- [x] T-A3 Define `schemas/enemy_schema.json`
- [x] T-A4 Define `schemas/node_schema.json`
- [x] T-A5 Add 2 sample files for each schema (event/enemy/node)
- [x] T-A6 Add schema validation script (single command)
- [x] B1 Define state models (player/run/map)
- [x] B2 Implement map generation and connectivity checks
- [x] B3 Implement node enter + event resolve flow
- [x] B4 Implement win/death termination
- [x] B5 Add deterministic run verification (same seed => same result)
- [x] C1 Implement combat turn loop
- [x] C2 Integrate ammo/medkit constraints
- [x] C3 Wire combat chance from events
- [x] C4 Add failure-path tests for combat/resource
- [x] C5 Run playability validation v1 (5 runs + logging, gate 3/4 passed)
- [x] C6 Increase decision pressure density (fix Playability Gate #1)
- [x] Add `SYSTEM_CONSTRAINTS.md` for AI change boundaries
- [x] Add `schemas/run_analytics_schema.json`
- [x] Add `specs/event_template_system.md`
- [x] D3 Implement run analytics log output + schema validation
- [x] D4 Add event template system (catalog + deterministic generation)
- [x] D5 Run balancing simulations and collect metrics
- [x] D6 Add irreversible-state prototype signal (`radiation`) and analytics coverage
- [x] Add weighted regret/blame analysis to `run_analytics`
- [x] Add human playtest log schema and observation template
- [x] D7 Publish v0.1 balancing notes
- [x] Add interactive CLI runner with pre-choice and travel radiation warnings
- [x] Enforce runtime state invariants (`apply_effects`, `create_run`, `resource_cost`)
- [x] Add gameplay validation scripts to phase gate verification
- [x] Add human playtest log validator and comparison script
- [x] Add `PT1_CHECKLIST.md` for live session execution
- [x] Publish `SEED_101_OBSERVATION.md` as deterministic design research note

---

## Phase Breakdown

### Phase A — Spec and Contract Freeze
- [x] A1 Read existing specs and schemas
- [x] A2 Complete meta progression spec
- [x] A3 Complete enemy schema
- [x] A4 Complete node schema
- [x] A5 Build sample data pack
- [x] A6 Add schema validation command

Gate:
- [x] All `specs/*.md` are non-empty and actionable
- [x] All `schemas/*.json` validate with sample data

### Phase B — Core Run Loop
- [x] B1 Define state models (player/run/map)
- [x] B2 Implement map generation and connectivity checks
- [x] B3 Implement node enter + event resolve flow
- [x] B4 Implement win/death termination
- [x] B5 Add deterministic run verification (same seed => same result)

Gate:
- [x] One full run can finish from start to final node or death
- [x] Resource updates are deterministic for same input

### Phase C — Combat and Resource Integration
- [x] C1 Implement combat turn loop
- [x] C2 Integrate ammo/medkit constraints
- [x] C3 Wire combat chance from events
- [x] C4 Add failure-path tests for combat/resource
- [x] C5 Run playability validation v1 (5 runs + death-cause traceability)
- [x] C6 Increase decision pressure density (raise low-pressure routes to >=3)
- [x] PLY-1..PLY-4 Playability Check

Gate:
- [x] Combat always terminates correctly
- [x] Invalid input and boundary tests exist for core modules

### Phase D — Meta and Balancing
- [x] D3 Implement run analytics log output + schema validation
- [x] D4 Add event template system (catalog + deterministic generation)
- [x] D5 Run balancing simulations and collect metrics
- [x] D6 Add irreversible-state prototype signal (radiation/injury minimal variant)
- [x] D7 Publish v0.1 balancing notes
- [x] OBS-1/2/3 Run machine observation experiments (first-node dominance, conservative survivability, risk payoff)
- [x] GOV-1 Governance gate upgrade and CI integration
- [ ] BAL-1 Machine-side balance iteration while PT-1 evidence is quarantined
- [x] BAL-2 Recover regret gate after south identity tuning
- [ ] PT-1 Run first manual playtest round and capture observation sheets
- [ ] PT-2 Merge observation findings with analytics summaries

Gate:
- [x] 50 analytics logs captured and summarized
- [ ] Human playtest evidence captured and summarized
- [ ] Governance freshness gate restored to FRESH after latest balance change

---

## Backlog

### P0
- [x] Formalize `meta_progression` contract freeze criteria (v0.1 gate)
- [x] Version `enemy` and `node` schemas as v0.1 frozen contracts
- [x] Define save/load format for run state
Artifacts: `specs/meta_progression.md` (freeze criteria added), `schemas/enemy_schema.json`, `schemas/node_schema.json` (v0.1 frozen), `schemas/run_state_schema.json` (new)

### P1
- [x] Restrict event effect keys by whitelist
  Artifact: `schemas/event_schema.json` (additionalProperties: false, approved key whitelist)
- [x] Add map generation constraints for guaranteed reachability
  Artifact: `scripts/validate_map_constraints.py` (INV-1 through INV-8, 7/7 nodes pass)
- [x] Build initial event content set (30 records)
  Artifact: `schemas/event_template_catalog.json` (30 events, 5 template_types, all validated)

### P2
- [x] Difficulty presets
  Artifacts: `src/difficulty.py`, `scripts/run_difficulty_presets.py`, `output/analytics/difficulty_presets.json`
- [x] Enemy archetypes and special abilities
  Artifacts: `schemas/enemy_schema.json`, `src/combat_engine.py`, `scripts/test_failure_paths.py`
  Notes: `raider` loot now skews `ammo/food`; `mutant` loot now skews `scrap/medkits`; route-biased encounter weights now live in `schemas/encounter_weight_table.json`
- [x] Run summary template and telemetry fields
  Artifacts: `src/run_summary.py`, `scripts/generate_run_summary_report.py`, `output/summaries/*_summary.md`
  Follow-up artifacts: `scripts/run_loot_economy_report.py`, `output/analytics/loot_economy.json`, `output/summaries/loot_economy_report.md`
- [ ] Travel-mode prototype branch if PT-1 confirms low consequence depth
- [ ] Background/equipment prototype branch if PT-1 and EXP-2 justify more identity depth

---

## Future Product Track (Post-Prototype)

Status: Product tracking only (not sprint-blocking until prototype gates pass).

- [ ] SR-1 Steamworks foundation setup
- [ ] SR-2 Store page and media draft
- [ ] SR-3 Build/depot upload pipeline
- [ ] SR-4 Release QA and go/no-go checklist
- Details: `tasks/task_steam_release.md`

---

## Risks

- R1: Undefined meta schema blocks downstream implementation
- R2: Unbounded event effect keys can corrupt run state
- R3: No deterministic simulation log format slows balancing
