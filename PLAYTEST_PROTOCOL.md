# Ashfall Playtest Protocol (v0.1)

## Goal

This playtest validates only the core decision loop in the CLI prototype.

Questions under test:

1. Decision Tension: does the player genuinely hesitate at route choices?
2. Consequences Visibility: can the player feel earlier choices shaping later states?
3. Replay Signal: does the player want to run again?

Not in scope:

- UI quality
- story quality
- visuals
- full onboarding polish

## Test Group

Recommended first round:

- 5 to 8 players
- at least half should not be familiar with game development
- at least 2 should have played roguelites

Instruction given to the player:

`Your goal is to survive to the end.`

Do not explain:

- optimal strategy
- hidden rules
- system details unless the player is fully blocked

## Session Flow

Each player session should take about 20 to 30 minutes.

### Step 1: Brief Intro (1 min)

Say only:

`This is a wasteland survival prototype. You need to choose routes, manage resources, and try to survive to the end.`

Reason:

- the test is measuring natural system comprehension, not guided mastery

### Step 2: First Run (10 to 15 min)

Let the player complete one full run.

Observer duties:

1. Watch player behavior
2. Record three moment types

Behavior signals to watch:

- long pauses at nodes
- repeated reading of event text
- visible resource calculation
- route comparison before committing

Record these moment types:

- decision hesitation
- emotional spike
- confusion

Example notes:

- `node 4 hesitation 9s`
- `node 6 "I'm dead"`
- `node 7 confused about medkit timing`

### Step 3: Immediate Interview (3 to 5 min)

Ask only these three questions:

1. Which choice was hardest to make?
2. When you died, or almost died, what do you think caused it?
3. If you ran again, which choice would you change?

Desired signal quality:

- Q1 should identify a route or event choice
- Q2 should point to a previous decision, not only randomness
- Q3 should show decision memory and route learning

### Step 4: Optional Second Run

If the player wants to run again, allow it.

Do not push for a second run.

Reason:

- voluntary replay is the strongest replay signal

## Observation Sheet

Use one sheet per player.

```text
Player ID:
Roguelite experience: yes / no
Game-dev background: yes / no

Run 1
------
Decision hesitation nodes:
- node __ : __s
- node __ : __s
- node __ : __s

Emotional spikes:
- node __ : "________"
- node __ : "________"

Confusion:
- node __ : "________"

Death cause perception:
"________________"

Replay:
yes / no

If replay yes:
What would change?
"________________"
```

## Success Criteria

The first round is successful if these four conditions are met:

1. Decision hesitation
   - average at least 3 hesitation nodes per player
   - average hesitation time above 5 seconds
2. Consequence attribution
   - at least 70% of players can explain which decision led to failure
3. Route diversity
   - different players choose different routes
4. Replay signal
   - at least 50% of players voluntarily start a second run or explicitly say they want to

## Data to Review After the Test

Combine player observation with run analytics.

Suggested combined fields:

- `avg_decision_time`
- `hesitation_nodes_per_player`
- `distinct_outcome_signatures`
- `rerun_signal_runs`
- `death_causes`
- `route_family_summary`

What to look for:

- whether human hesitation matches analytics pressure points
- whether perceived failure causes match logged death chains
- whether replay desire appears alongside route divergence

## Interview Guidance

Do not ask:

- `Was it fun?`

Ask instead:

- `Which moment was the most tense?`
- `Which moment do you regret most?`

Reason:

- generic enjoyment questions produce weak data
- regret and tension questions expose whether the decision loop is working

## First-Round Objective

The purpose of the first playtest is not to improve the game broadly.

It is to answer one question:

`Does route choice actually create tension?`

If yes:

- the prototype is proving the core loop

If no:

- the core loop needs to change before more content or polish work

## How This Connects to the Repo

Use this protocol together with:

- [PROTOTYPE_SUCCESS_CRITERIA.md](PROTOTYPE_SUCCESS_CRITERIA.md)
- [PLAN.md](PLAN.md)
- [tasks/TASKS.md](tasks/TASKS.md)
- `output/playability/run_*.json`
- `output/analytics/summary.json`
- `output/analytics/balance_summary.json`

This protocol is the human-validation counterpart to the machine-validation gates already in the repo.
