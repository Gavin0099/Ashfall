# TASKS.md — Ashfall Execution Board

Last Updated: 2026-03-19
Owner: GavinWu
Execution Truth (Sprint/Task): `tasks/TASKS.md`
Phase/Gate/Milestone Truth: `PLAN.md`

---

## Current Sprint (2026/03/16 - 2026/03/22)

### In Progress
- [ ] DOC-1 Fix document drift (README / PLAN / implementation)
- [ ] PT-2 Compare human playtest logs against machine `failure_analysis`
- [ ] GOV-4 Verify Phase 11.0 gates (Human validation closure)

### Ready
- [x] P9-1 Implement Quest Flags and event branching logic
- [x] P9-2 Integrate Merchant/Barter nodes
- [x] P10-1 Initialize Interactive UI (Vite + React)
- [x] P10-2 Implement FastAPI backend (RunEngine Bridge)
- [x] P10-3 Basic Resource/Story Dashboard implementation

### Playability Check
- [x] PLY-5 Verify UI run flow (Start -> Move -> Event -> Resolve)
- [x] PLY-6 Verify Merchant trade logic via UI Interaction

### Done
- [x] BAL-1 Run machine-side balance iteration
- [x] GOV-2 PT-1 Quarantine enforcement
- [x] BAL-3 Tighten route identity
- [x] GOV-3 CI Integration
- [x] OBS-1/2/3 Machine Observations (Combined)
- [x] EXP-1/2/3/4 Experimental Prototyping
- [x] GOV-1 Governance gate upgrade
- [x] B1-B5 Core Run Loop
- [x] C1-C6 Combat and Resource Integration
- [x] D3-D7 Meta and Balancing (v0.1)
- [x] P0 Save/Load implementation

---

## Phase Breakdown

### Phase 11.0 — Human Validation & Narrative Alignment
- [ ] DOC-1 Align README, PLAN, and implementation narrative
- [ ] PT-2 Merge human playtest logs with machine comparison output
- [ ] VAL-1 Confirm tension proxy metrics against player feedback
- [ ] VAL-2 Prune/Upgrade metrics based on PT-2 results

Gate:
- [ ] README.md, PLAN.md, and TASKS.md are synchronized
- [ ] Human playtest evidence captured and summarized
- [ ] 5/5 Phase Gates pass for Phase 11.0

### Phase 10.0 — Interactive Dashboard (UI)
- [x] P10-1 Setup Vite + React + Tailwind (Optional)
- [x] P10-2 Implement API server for RunEngine
- [x] P10-3 Build Resource/Action/Story components

Gate:
- [x] UI can complete a full run without backend crashes or UI state desync

---

## Backlog

### Long-term
- [ ] SR-1 Steamworks foundation setup
- [ ] SR-2 Store page and media draft
- [ ] SR-3 Build/depot upload pipeline
- [ ] SR-4 Release QA and go/no-go checklist
- Details: `tasks/task_steam_release.md`

---

## Risks

- R1: Document drift leads to feature-creep ignoring key goal: "high-stakes tension validation"
- R2: UI implementation adds technical debt to core engine
- R3: Stale machine analytics might hide shifting human feedback
