# Event Template System — Ashfall v0.1

## Why

Replayability bottleneck is content entropy. Hand-authoring 30 static events is expensive and low-variance.

## Template Model

An event is generated as:

`template + parameters + risk profile + reward profile`

## Base Templates (v0.1)

- Scavenger Encounter
- Ruined Infrastructure
- Survivor Contact
- Environmental Hazard
- Checkpoint Conflict

## Parameter Slots

- reward_type: `food | ammo | medkits | scrap`
- reward_amount: integer range
- risk_type: `combat | injury | supply_loss`
- risk_intensity: `low | medium | high`
- pressure_label: `safe | risky | desperate`

## Output Contract

Generated event must still conform to `schemas/event_schema.json`.

## Validation Rules

- each generated event must present at least 2 options
- option set must include at least one explicit trade-off (gain vs risk)
- combat chance must remain in `[0,1]`
- generated events must produce measurable divergence in run analytics

## v0.1 Scope

- No procedural text grammar engine
- No localization
- No dynamic narrative memory

## Integration Tasks

1. Define template catalog JSON
2. Add deterministic template instantiation by seed
3. Feed generated events into existing run/event pipeline
4. Measure entropy impact via playability metrics

## Current Implementation (2026-03-09)

- Template catalog: `schemas/event_template_catalog.json`
- Generator: `src/event_templates.py`
- Validation: `scripts/validate_event_templates.py`
- Integrated consumer: `scripts/run_playability_check.py`

Current status:
- Deterministic generation by seed: implemented
- Output compatibility with `schemas/event_schema.json`: validated
- Playability pipeline switched to generated events: implemented
