# Ashfall

Ashfall is a CLI-first roguelite survival prototype used to validate a spec-driven AI development workflow.

The project focuses on a single gameplay question:

Can route choice reliably create repeatable high-stakes tension?

The repository therefore serves two purposes:

1. validating the Ashfall gameplay prototype
2. exercising a governance model for AI-assisted development

## Primary Goal

Validate the Ashfall core gameplay loop in a text/CLI prototype.

## Secondary Goal

If the prototype proves replayable, prepare the project for Steam release.

## Current Status

- Phase A complete: specs and schemas are defined and validated.
- Phase B complete: deterministic run loop works from start to victory/death.
- Phase C complete: combat, event-triggered combat, pressure validation, and run analytics are working.
- Phase D in progress: analytics-driven balancing and the first irreversible-state signal are complete; balancing notes and external playtest remain.

Prototype contract:
- [PROTOTYPE_SUCCESS_CRITERIA.md](PROTOTYPE_SUCCESS_CRITERIA.md)

AI change boundaries:
- [SYSTEM_CONSTRAINTS.md](SYSTEM_CONSTRAINTS.md)

Manual playtest protocol:
- [PLAYTEST_PROTOCOL.md](PLAYTEST_PROTOCOL.md)
- [schemas/human_playtest_log_schema.json](schemas/human_playtest_log_schema.json)
- [BALANCING_NOTES_v0_1.md](BALANCING_NOTES_v0_1.md)

## What v0.1 Must Prove

- full run completion in CLI mode
- deterministic seed reproducibility
- route divergence creates meaningfully different outcomes
- death reasons are attributable from run logs
- each run contains at least 3 meaningful pressure choices

## Out of Scope for v0.1

- Steamworks setup
- store page work
- achievements
- polished UI
- large-scale content writing
- advanced meta progression

## Key Files

- [PLAN.md](PLAN.md): strategy truth for phases, gates, milestones
- [tasks/TASKS.md](tasks/TASKS.md): execution truth for sprint/task state
- [PLAYTEST_PROTOCOL.md](PLAYTEST_PROTOCOL.md): first-round human playtest procedure
- [specs/human_playtest_analytics.md](specs/human_playtest_analytics.md): machine-vs-human tension comparison rules
- [BALANCING_NOTES_v0_1.md](BALANCING_NOTES_v0_1.md): current balance conclusions and next controlled experiments
- [specs/](specs): gameplay and system specs
- [schemas/](schemas): data contracts
- [src/](src): runtime prototype code
- [output/playability/](output/playability): playability run artifacts
- [output/analytics/](output/analytics): machine-readable run analytics

## Prototype Validation Scripts

Run the current validation pipeline:

```bash
python scripts/validate_phase_a.py
python scripts/test_failure_paths.py
python scripts/play_cli_run.py 103
python scripts/run_playability_check.py
python scripts/run_balance_metrics.py
python scripts/validate_run_analytics.py
python scripts/validate_event_templates.py
python scripts/validate_human_playtest_logs.py
python scripts/compare_playtest_vs_machine.py
```

What they cover:

- `validate_phase_a.py`: spec/schema baseline
- `test_failure_paths.py`: invalid input, boundary, and failure-path checks
- `play_cli_run.py`: interactive CLI run with pre-choice and travel warnings
- `run_playability_check.py`: 5-run playability evaluation with deterministic routes
- `run_balance_metrics.py`: 50-run balancing sample with route-family summaries
- `validate_run_analytics.py`: validates analytics output contract
- `validate_event_templates.py`: validates deterministic event template generation
- `validate_human_playtest_logs.py`: validates human playtest session logs
- `compare_playtest_vs_machine.py`: compares human hesitation/regret against machine analytics

## Current Prototype Metrics

From `output/analytics/summary.json`:

- `distinct_outcome_signatures = 5`
- `death_runs = 3`
- `rerun_signal_runs = 5`

Current playability gate status:

- `pressure_choices_per_run`: pass
- `route_diversity`: pass
- `death_explainable_from_logs`: pass
- `rerun_signal_3_of_5`: pass

From `output/analytics/balance_summary.json`:

- `run_count = 50`
- `victory_rate = 0.24`
- `avg_pressure_count = 3.28`
- `avg_final_radiation = 0.78`
- `distinct_outcome_signatures = 28`
- `resource_divergence.pairwise_average = 10.98`
- `death_reasons = {starvation: 10, radiation_death: 21, event_or_resource_death: 7}`
- `trash_time_death_rate = 0.0`
- `avg_steps_from_regret_to_death = 0.26`
- `failure_analysis` records weighted regret nodes, regret distance, and `is_trash_time_death`

## Event Entropy Strategy

Replayability is not based on hand-writing many static events first.

Current direction:
- deterministic event template catalog
- seeded event instantiation
- analytics-backed divergence checks

Reference:
- [specs/event_template_system.md](specs/event_template_system.md)
- [schemas/event_template_catalog.json](schemas/event_template_catalog.json)

## Run Analytics Contract

Analytics output is formalized and validated.

Reference:
- [schemas/run_analytics_schema.json](schemas/run_analytics_schema.json)

Generated artifacts:
- `output/analytics/run_*.json`
- `output/analytics/summary.json`
- `output/analytics/balance/run_*.json`
- `output/analytics/balance_summary.json`
- `output/cli/latest_seed_*.json`

## Development Principles

- protect deterministic behavior
- do not mutate core state contracts casually
- prefer validation gates over subjective judgment
- optimize for gameplay proof before productization

## Next Work

- PT-1: run first external playtest round using `PLAYTEST_PROTOCOL.md`
- PT-2: compare human hesitation/regret logs against machine `failure_analysis`
- D1/D2: connect run-end rewards and meta progression state transitions
- EXP-1: evaluate explicit irreversible trade only after Blind CLI results

## Repository Note

The governance files in this repo are part of the working method, but Ashfall itself is the product under validation. This repo is currently exercising both:

- a game prototype experiment
- a spec-driven AI development workflow
