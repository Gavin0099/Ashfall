# Seed 101 Deterministic Run Observation

This note documents a controlled manual exploration of seed `101` to observe how early event decisions affect run outcomes.

All runs used the same route:

`Start -> North Scrapyard -> Tunnel -> Checkpoint -> Final Ridge`

Only event decisions were changed.

## Run A — Conservative Choices (Death)

Key decisions:

- Scrapyard: skip salvage
- Tunnel: camp
- Checkpoint: detour

Outcome:

- Result: Death
- Cause: Food exhaustion

Failure analysis:

- `primary_blame_factor`: `resource_exhaustion`
- `regret_nodes`:
  - `checkpoint`: lost 1 food
  - `tunnel`: lost 1 food
  - `scrapyard`: lost 1 food
- `steps_from_regret_to_death`: `0`

Observation:

The player avoided all combat risks but gradually lost food each node and reached the final travel step with `food = 1`, making the final move lethal.

## Run B — Early Salvage (Victory)

Key difference:

- Scrapyard: salvage wreck (risk option)

Effect:

- `food +1`
- `ammo +2`

Remaining decisions were identical to Run A.

Outcome:

- Result: Victory
- Remaining food: `2`

Observation:

The early salvage created enough resource buffer to complete the route without further risk.

## Run C — Aggressive Path (Victory)

Key decisions:

- Scrapyard: salvage wreck
- Tunnel: force through rubble (combat + radiation)
- Checkpoint: attack checkpoint

Effects:

- combat damage
- radiation gained
- ammo gained

Outcome:

- Result: Victory
- Final state:
  - `HP = 3`
  - `Food = 4`
  - `Radiation = 1`

Observation:

Despite accumulating multiple risks (combat damage and radiation), the run remained survivable due to early resource gains.

## Preliminary Interpretation

These runs surface three early design signals.

### 1. Early Node Resource Swing

The scrapyard event can shift the run economy significantly:

- skip salvage -> `-1 food`
- salvage wreck -> `+1 food +2 ammo`

This creates a `2+ food equivalent` swing early in the run, which strongly influences the player's later margin for error.

This suggests that early-node resource effects may disproportionately influence run survivability.

### 2. Conservative Strategy Viability

The conservative route in Run A produced a deterministic starvation outcome.

This indicates:

- risk avoidance != guaranteed survivability

However, further sampling is required to determine whether conservative play can still produce viable success paths under different seeds.

### 3. Risk Payoff Balance

In Run C, the aggressive choices introduced multiple penalties:

- combat damage
- radiation pressure

However, these penalties did not outweigh the early resource gains.

This raises a balance question:

- are high-risk options currently over-performing relative to conservative options?

Further simulation sampling will be required.

## Hypothesis Check Impact

Ashfall's prototype hypothesis:

> Route choice creates repeatable high-stakes tension.

The Seed 101 observations suggest that current tension may arise primarily from:

- event-level resource swings

rather than strictly from macro route divergence.

Additional sampling across route families will be required to confirm whether tension is driven by:

- route structure
- or event-level decision economy

## Follow-up Validation Tasks

Recommended validation steps:

### First-node dominance test

- same seed
- same route
- only change first event choice
- measure win-rate divergence

### Conservative survivability test

- evaluate whether fully conservative play has viable success paths across multiple seeds

### Risk payoff sampling

- compare net expected value of high-risk vs low-risk event options across `>=100` runs

## Why This Note Matters

This note turns a balancing hunch into explicit, testable design hypotheses.

It does not say:

- "balance feels off"

It says:

- there are three concrete balance signals to verify

That makes the repo look like a gameplay research prototype rather than a project passively tweaking numbers.
