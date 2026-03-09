# SYSTEM_CONSTRAINTS.md

## Purpose

Guard Ashfall v0.1 prototype contracts from accidental AI-driven drift.

## AI MUST NOT

- change core `RunState` fields or semantics without explicit plan update
- change deterministic seed logic or random initialization behavior
- add/remove core resource types beyond the approved v0.1 set (`hp`, `food`, `ammo`, `medkits`, `scrap`, `radiation`)
- change map topology invariants (reachable final node, directed graph contract)
- bypass or weaken phase gates in `PLAN.md`

## AI MAY

- add scripts/tests/logging that improve prototype validation
- tune event parameters to satisfy playability gate
- refactor internals if external state contracts remain unchanged

## Change Control

Any proposal that touches forbidden items must:
1. create a plan change note in `PLAN.md` change history
2. update `PROTOTYPE_SUCCESS_CRITERIA.md` if validation assumptions change
3. mark related tasks in `tasks/TASKS.md`
