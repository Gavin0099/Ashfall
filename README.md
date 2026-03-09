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
- Phase D in progress: analytics-driven balancing baseline is complete; irreversible-state pressure and meta systems remain.

Prototype contract:
- [PROTOTYPE_SUCCESS_CRITERIA.md](PROTOTYPE_SUCCESS_CRITERIA.md)

AI change boundaries:
- [SYSTEM_CONSTRAINTS.md](SYSTEM_CONSTRAINTS.md)

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
python scripts/run_playability_check.py
python scripts/run_balance_metrics.py
python scripts/validate_run_analytics.py
python scripts/validate_event_templates.py
```

What they cover:

- `validate_phase_a.py`: spec/schema baseline
- `test_failure_paths.py`: invalid input, boundary, and failure-path checks
- `run_playability_check.py`: 5-run playability evaluation with deterministic routes
- `run_balance_metrics.py`: 20-run balancing sample with route-family summaries
- `validate_run_analytics.py`: validates analytics output contract
- `validate_event_templates.py`: validates deterministic event template generation

## Current Prototype Metrics

From `output/analytics/summary.json`:

- `distinct_outcome_signatures = 5`
- `death_runs = 2`
- `rerun_signal_runs = 4`

Current playability gate status:

- `pressure_choices_per_run`: pass
- `route_diversity`: pass
- `death_explainable_from_logs`: pass
- `rerun_signal_3_of_5`: pass

From `output/analytics/balance_summary.json`:

- `run_count = 20`
- `victory_rate = 0.3`
- `avg_pressure_count = 3.35`
- `distinct_outcome_signatures = 14`
- `resource_divergence.pairwise_average = 10.33`

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

## Development Principles

- protect deterministic behavior
- do not mutate core state contracts casually
- prefer validation gates over subjective judgment
- optimize for gameplay proof before productization

## Next Work

- D6: add a minimal irreversible-state signal (`radiation` or `injury`)
- D7: publish v0.1 balancing notes

## Repository Note

The governance files in this repo are part of the working method, but Ashfall itself is the product under validation. This repo is currently exercising both:

- a game prototype experiment
- a spec-driven AI development workflow
