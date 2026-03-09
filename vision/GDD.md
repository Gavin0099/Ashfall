# Ashfall GDD

## Product Goal

Ashfall is a CLI-first roguelite survival prototype.

The current product question is:

> Can route choice reliably create repeatable high-stakes tension?

The repository also serves as a testbed for spec-driven AI-assisted development, but gameplay validation remains the primary product goal.

## Release Direction

Primary release direction:

- prove the loop in CLI first

Secondary release direction:

- if the loop proves replayable, prepare a future Steam-facing build

## v0.1 Focus

v0.1 exists to validate:

- route pressure
- event risk
- resource pressure
- death explainability
- replay signal

v0.1 does not attempt to prove:

- progression fantasy
- large content scale
- polished presentation

## v0.2 Design Goal

v0.2 should increase decision identity without bloating the prototype.

Core target:

> Players should feel that who they are changes how they navigate the map.

This means:

- keep route choice as the main tension source
- add one layer of player identity
- add one layer of travel-level risk management
- add one small equipment layer

This does not mean:

- add levels
- add a skill tree
- add meta progression as a crutch

## v0.2 Target Loop

Current loop:

- route
- event
- resource change

v0.2 target loop:

- character
- route
- travel mode
- event
- equipment effect

## Design Guardrail

Every new system must strengthen route tension, not replace it.

If a new layer makes the player think about power scaling instead of navigation pressure, it is out of scope for the current prototype track.
