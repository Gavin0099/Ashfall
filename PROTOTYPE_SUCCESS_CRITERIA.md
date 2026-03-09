# Prototype Success Criteria - Ashfall v0.1

## Goal
Validate whether route choice can create repeatable high-stakes tension in a CLI wasteland roguelite prototype.

## A prototype is successful if

1. A full run can be completed in CLI mode (to death or victory).
2. At least 3 route-choice moments per run create meaningful trade-offs.
3. Different routes produce different resource states and outcomes.
4. Death reasons are explainable from the run log.
5. Same seed produces same map and same deterministic result under same choices.
6. AI agents can implement new tasks without changing core state contracts.

## Must Build (v0.1)

- deterministic map generation
- node traversal
- event resolution
- combat trigger from events
- ammo / medkit constraints
- death / victory conditions
- run summary
- seed reproducibility
- run log
- decision log

## Defer (not prototype-blocking)

- Steamworks setup
- store page
- achievements
- multiple difficulties
- many enemy archetype mechanics
- complex meta progression
- polished UI
- large worldbuilding text expansion

## Optional (only if they improve core validation)

- trade node (event-only or lightweight variant)
- clue fragments
- caravan/fuel
- faction reputation

## Validation Metrics

### Metric 1: Full Run Completion Rate
- Runs must reliably terminate with victory or explainable death.

### Metric 2: Route Divergence Effectiveness
- Under same map seed, different route choices should produce clearly different outcomes.

### Metric 3: Attributable Death
- Run summary must explain failure chain with concrete node/event/action causality.

## Current Status (2026-03-09)

- Metric 1: PASS (run completion path available)
- Metric 2: PASS (playability v1 shows 5 distinct outcome signatures)
- Metric 3: PASS (death reasons recorded in logs)
- Playability Threshold ">=3 pressure choices per run": PASS (v2 = 5/5 runs passing)
- Analytics Contract: PASS (`schemas/run_analytics_schema.json` + `output/analytics/run_*.json`)
- Balance Sampling: PASS (`scripts/run_balance_metrics.py` captured 20 deterministic analytics runs)
- Irreversible-State Signal: PASS (`radiation` integrated into event effects, travel attrition, and death attribution)
