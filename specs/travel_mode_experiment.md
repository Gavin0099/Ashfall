# Travel Mode Experiment

## Purpose

This document defines `EXP-2: Travel Mode` as a controlled prototype experiment.

It is not part of the current v0.1 baseline loop.

The experiment exists to test one design question:

> Can one additional travel decision layer increase decision depth by extending consequence length, without drowning the route-choice hypothesis?

## Problem Statement

Current Ashfall decisions are usually shaped by:

- immediate resource gain/loss
- combat risk
- radiation pressure

This creates usable tension, but many consequences are still short-range.

The current risk is not "too few options".
The current risk is:

- option impact is too short
- decision axes are too narrow
- many choices still feel like local arithmetic

## Hypothesis

Adding a small travel-level choice before movement may increase:

- consequence length
- route planning depth
- felt tension between nodes

without requiring:

- more content volume
- more route branches
- more event options per node

## Scope

`EXP-2` introduces one new decision dimension before travel:

- `normal`
- `rush`
- `careful`

This experiment does not:

- change map topology
- add new route families
- replace event choice
- alter core state contracts without an explicit follow-up decision

## Baseline Assumption

Current baseline:

- move
- pay node/travel cost
- resolve event

Experimental shape:

- choose travel mode
- move
- apply travel-mode consequence
- resolve event

## Proposed Travel Modes

### Normal

Purpose:

- control group
- same behavior as current baseline

Expected effect:

- no additional modifier

### Rush

Purpose:

- convert future safety into present tempo

Expected effect shape:

- lower immediate travel friction
- higher next-node danger

Candidate implementation forms:

- lower food cost this move
- increase next event `combat_chance`
- increase next event radiation exposure risk

### Careful

Purpose:

- buy information or safety at a higher short-term cost

Expected effect shape:

- higher immediate travel cost
- lower next-node uncertainty or danger

Candidate implementation forms:

- extra food cost this move
- reduce next event `combat_chance`
- reveal a danger/reward hint before option choice

## Design Constraint

`EXP-2` must remain a controlled experiment.

It must not turn the prototype question into:

- everything creates tension

The primary hypothesis remains:

- route choice creates tension

Therefore `Travel Mode` is only valid if it helps us answer:

- whether consequence length is too short in the current loop

## Success Criteria

`EXP-2` is useful if it improves at least one of these without collapsing determinism:

- more meaningful hesitation before movement
- longer regret distance
- clearer player explanation of why a route became dangerous
- stronger distinction between tempo/safety/resource tradeoffs

## Failure Criteria

`EXP-2` should be rejected if it causes:

- state complexity to grow faster than insight
- route tension to be overshadowed by tactical spam
- unclear attribution in playtest or analytics
- deterministic validation difficulty

## Measurement Plan

If implemented, evaluate:

- change in `avg_steps_from_regret_to_death`
- change in hesitation moments per run
- change in replay intent
- whether players describe travel mode as meaningful or bookkeeping

Additional human prompt:

- did travel mode change how you planned the next node, or did it feel like routine maintenance?

## Implementation Guardrails

If `EXP-2` moves forward:

- implement behind an experiment flag or separate script path
- do not replace the baseline CLI runner immediately
- preserve deterministic seed behavior
- keep analytics contract backward-compatible when possible

## Recommendation

Do not implement before `PT-1`.

First gather:

- human regret
- human hesitation
- human replay intent

Then decide whether current low-depth feedback is strong enough to justify the experiment.
