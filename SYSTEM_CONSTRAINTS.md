# SYSTEM_CONSTRAINTS.md

## Purpose

Guard Ashfall prototype contracts from accidental drift while deterministic rendering and audio layers are prepared.

## AI MUST NOT

- change core `RunState` fields or semantics without explicit plan update
- change deterministic seed logic or random initialization behavior
- add/remove core resource types beyond the approved v0.1 set (`hp`, `food`, `ammo`, `medkits`, `scrap`, `radiation`)
- change map topology invariants (reachable final node, directed graph contract)
- bypass or weaken phase gates in `PLAN.md`
- reference or import external `.png` assets
- reference or import external `.wav` assets

## AI MUST

- keep render and audio generation deterministic from seed-driven inputs
- ensure every new render class exposes `get_hash()` so identical seeds can be verified for visual consistency
- treat governance documents under `governance/` as the authoritative operating rules before implementation

## AI MAY

- add scripts/tests/logging that improve prototype validation
- tune event parameters to satisfy playability gates
- refactor internals if external state contracts remain unchanged
- generate procedural render/audio artifacts in code at runtime or into disposable cache directories

## Change Control

Any proposal that touches forbidden items must:
1. create a plan change note in `PLAN.md` change history
2. update `PROTOTYPE_SUCCESS_CRITERIA.md` if validation assumptions change
3. mark related tasks in `tasks/TASKS.md`
4. explain why deterministic verification still holds
