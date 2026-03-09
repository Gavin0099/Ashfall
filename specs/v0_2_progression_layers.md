# v0.2 Progression Layers

## Purpose

This document defines the minimal system expansion for Ashfall v0.2.

It is not a content expansion plan.
It is a decision-depth plan.

## Core Principle

Keep:

- route choice as the primary tension source

Increase:

- decision identity
- risk management
- long-term consequence

## v0.2 Loop

Current v0.1 loop:

- route
- event
- resource change

Target v0.2 loop:

- character
- route
- travel mode
- event
- equipment effect

The goal is to move from roughly `1.5` decision layers to `3` lightweight layers without making the prototype system-heavy.

## System 1: Character Background

### Intent

Give the player a run identity before the first route choice.

The background is:

- chosen once at run start
- passive only
- no leveling
- no branching tree

### Candidate backgrounds

- `Scavenger`: salvage rewards `+1` resource
- `Soldier`: combat damage taken `-1`
- `Pathfinder`: first travel each node costs `0` food
- `Medic`: medkit heals `+1`

### Desired effect

The player should immediately ask:

- which route fits this background?

That strengthens route tension instead of replacing it.

## System 2: Travel Mode

Reference:

- `specs/travel_mode_experiment.md`

### Intent

Add a small tactical layer before travel.

### Candidate modes

- `Normal`
- `Rush`
- `Careful`

### Example shape

- `Normal`: baseline move
- `Rush`: higher short-term tempo, higher next-node danger
- `Careful`: higher short-term cost, lower next-node danger or better information

### Desired effect

The player should think:

- do I move faster, or do I move safer?

This increases decision depth without requiring more event branches.

## System 3: Equipment Slot

### Intent

Add lightweight run-shaping equipment without creating a full inventory system.

### Slot model

Only three slots:

- `weapon`
- `armor`
- `tool`

### Acquisition model

- equipment comes from event rewards
- a new item replaces the current one in that slot

### Candidate items

- `Rust Rifle`: combat damage `+1`
- `Gas Mask`: radiation damage `-1`
- `Scavenger Kit`: salvage reward `+1`
- `Field Pack`: food capacity `+2`

### Desired effect

Equipment should change route evaluation:

- not by creating build complexity
- but by changing what kinds of nodes or risks feel acceptable

## Analytics Compatibility

Current analytics should remain useful:

- regret nodes
- failure chains
- route divergence

v0.2 may add:

- background survival rate
- equipment survival rate
- travel-mode selection rate

## Explicitly Excluded from v0.2

Do not add:

- level systems
- skill trees
- meta progression
- power scaling between runs

Reason:

These systems would blur the current gameplay research question by letting progression cover for weak route tension.

## Design Target

Ashfall v0.2 should feel closer to:

- route risk
- gear survival
- resource management

It should not become:

- a progression treadmill

## Implementation Order

Recommended order:

1. `EXP-2` Travel Mode if PT-1 confirms low consequence depth
2. `EXP-3` Character Background prototype
3. `EXP-4` Minimal equipment slots

Do not implement all three at once without validating each layer's effect on route tension.
