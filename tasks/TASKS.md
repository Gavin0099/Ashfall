# TASKS.md — Ashfall Execution Board

Last Updated: 2026-03-09
Owner: GavinWu
Execution Truth (Sprint/Task): `tasks/TASKS.md`
Phase/Gate/Milestone Truth: `PLAN.md`

---

## Current Sprint (2026/03/09 - 2026/03/15)

### In Progress
- [ ] PT-1 Run first manual playtest round with 5-8 players using `PLAYTEST_PROTOCOL.md`

### Ready
- [ ] D1 Add run-end reward and unlock rules
- [ ] D2 Add meta progression state transitions
- [ ] PT-2 Compare human playtest logs against machine `failure_analysis`
- [ ] OBS-1 Run first-node dominance test from `SEED_101_OBSERVATION.md`
- [ ] OBS-2 Test conservative survivability across multiple seeds
- [ ] OBS-3 Compare high-risk vs low-risk event payoff across >=100 runs
- [ ] EXP-1 Prototype explicit irreversible trade (`max_hp` sacrifice for short-term survival)
- [ ] EXP-2 Evaluate `travel mode` as a controlled decision-depth experiment

### Playability Check
- [x] PLY-1 Run 5 manual playthroughs with different route choices
- [x] PLY-2 Record 3 moments of meaningful tension per run
- [x] PLY-3 Verify different paths produce different resource states or outcomes
- [x] PLY-4 Verify death causes are explainable from run logs
Artifacts: `output/playability/summary.json`, `output/playability/run_*.json`

### Done
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
- [ ] D1 Add run-end reward and unlock rules
- [ ] D2 Add meta progression state transitions
- [x] D3 Implement run analytics log output + schema validation
- [x] D4 Add event template system (catalog + deterministic generation)
- [x] D5 Run balancing simulations and collect metrics
- [x] D6 Add irreversible-state prototype signal (radiation/injury minimal variant)
- [x] D7 Publish v0.1 balancing notes
- [ ] PT-1 Run first manual playtest round and capture observation sheets
- [ ] PT-2 Merge observation findings with analytics summaries

Gate:
- [x] 50 analytics logs captured and summarized
- [ ] Meta progression rules are documented and tested

---

## Backlog

### P0
- [ ] Formalize `meta_progression` contract freeze criteria (v0.1 gate)
- [ ] Version `enemy` and `node` schemas as v0.1 frozen contracts
- [ ] Define save/load format for run state

### P1
- [ ] Restrict event effect keys by whitelist
- [ ] Add map generation constraints for guaranteed reachability
- [ ] Build initial event content set (30 records)

### P2
- [ ] Difficulty presets
- [ ] Enemy archetypes and special abilities
- [ ] Run summary template and telemetry fields
- [ ] Travel-mode prototype branch if PT-1 confirms low consequence depth

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
