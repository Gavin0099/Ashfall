# Ashfall v0.1 Balancing Notes

Date: 2026-03-09
Source artifacts:

- `output/analytics/balance_summary.json`
- `output/analytics/balance/run_*.json`
- `output/analytics/run_*.json`

## Purpose

These notes summarize the first machine-driven balance pass after adding:

- deterministic event templates
- weighted regret/failure analysis
- `radiation` as the first irreversible-state signal

This document is not a content wishlist.
It is a prototype-balance readout for deciding the next controlled changes.

## Snapshot

- runs sampled: `20`
- victory rate: `0.20`
- avg pressure count: `3.35`
- distinct outcome signatures: `15`
- avg final radiation: `0.9`
- death attribution rate: `1.0`
- trash-time deaths: `0 / 20`

Death reasons:

- `radiation_death`: `9`
- `starvation`: `4`
- `event_or_resource_death`: `3`
- `reached_final_node`: `4`

## What Is Working

### 1. Route divergence is real

- `pairwise_average resource divergence = 11.27`
- `distinct_outcome_signatures = 15`

Interpretation:

- route choice is materially changing final state
- runs are not collapsing into one dominant outcome pattern

### 2. Radiation is creating long-term stakes

- `radiation_death` is the most common failure mode
- `failure_analysis.primary_blame_factor = radiation` in `9` balance runs

Interpretation:

- irreversible-state pressure is now visible in the data
- players can plausibly be told a coherent failure chain instead of only "you ran out of hp"

### 3. Current radiation implementation is not obviously producing garbage time

- `failure_analysis.is_trash_time_death = false` in all `20` sampled runs

Interpretation:

- the current fixed attrition model is harsh, but the sampled runs do not show long doomed tails under the current heuristic
- this does not prove human perception is good; it only means the machine-side garbage-time detector is currently clean

### 4. Death attribution is strong

- decision trace coverage: `1.0`
- death cause attribution rate: `1.0`
- weighted `regret_nodes` now exist for each losing run

Interpretation:

- post-run explanation quality is now good enough for Blind CLI testing

## What Is Not Balanced Yet

### 1. South route pressure is still too low

Route family summary:

- `north avg_pressure_count = 3.75`
- `south avg_pressure_count = 2.75`
- `mixed avg_pressure_count = 3.75`

Interpretation:

- south path is still less tense than north/mixed
- this weakens the "every route is a gamble" claim

Likely cause:

- south-side choices provide food relief more often than immediate survival crisis
- south path accumulates radiation, but does not force as many moment-to-moment hard decisions

### 2. Victory rate is slightly on the harsh side

- current victory rate: `0.20`

Interpretation:

- this is not automatically wrong for a prototype
- but it is low enough that human testing may read the game as punishing before it reads as strategic

Decision:

- do not soften globally yet
- first verify human regret quality and replay intent in Blind CLI tests

### 3. Radiation is dominating the failure landscape

- `9 / 16` losses are `radiation_death`

Interpretation:

- this is good for proving irreversible-state pressure
- but it risks flattening failure variety if left untouched

Decision:

- keep `radiation` in place for the next human test round
- avoid adding a second irreversible system before gathering human evidence

## Regret Analysis Read

Current weighted failure analysis is more useful than a single regret anchor.

Why:

- losses are often multi-step chains
- weighted `regret_nodes` preserve both early setup mistakes and late confirmation errors

Observed value:

- radiation runs usually show regret split across multiple nodes rather than a fake single culprit
- this is closer to the actual design question: was the player squeezed by one bad bet, or by a chain of bets?

## Decisions

### Keep

- deterministic event template system
- radiation as the only active irreversible-state signal
- weighted regret/blame analysis
- pre-choice warning signals in analytics

### Do Not Add Yet

- UI-first visual prototype
- a second irreversible-state system
- large content expansion
- volatility-based radiation damage
- explicit `max_hp` sacrifice trade in the main route pool

Reason:

- human evidence is still missing
- adding more moving parts now will weaken attribution

## Next Actions

1. Run `PT-1` Blind CLI tests using `PLAYTEST_PROTOCOL.md`
2. Compare human hesitation/regret with machine `failure_analysis`
3. If humans still fail to feel tension on south route, increase explicit trade intensity on south templates
4. Only after human comparison, evaluate one controlled experiment:
   - `EXP-1`: explicit irreversible trade (`max_hp` sacrifice)
   - or volatility-based `radiation`

## Recommended South-Route Adjustment Candidate

If the next adjustment is needed, start here:

- add one south-route option that trades immediate relief for explicit long-term cost
- example shape:
  - gain `food` or `medkit`
  - take `radiation`
  - add moderate combat chance or resource loss

Do not:

- simply increase random damage
- add more text without changing stakes

## Release Readiness Note

These notes improve prototype confidence only.

They do not justify:

- Steam release planning changes
- visual prototype prioritization
- broader content production

The gating question is still:

`Do humans in pure CLI mode feel regret, tension, and replay desire?`
