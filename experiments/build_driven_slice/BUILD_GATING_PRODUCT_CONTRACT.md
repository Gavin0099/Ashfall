# Ashfall Build-Gating Product Contract

## Product Direction

Ashfall is moving toward a:

**Build-driven wasteland RPG roguelite**

The core experience is not open-world exploration, not large procedural content, and not resource attrition alone.

The core promise is:

> The world does not ask what you choose.
> It asks who you are.

In v0.1, the game must prove that changing character build creates meaningfully different choices, consequences, and replay desire.

## Platform Strategy

The first public validation target is:

**Steam Demo**

Development should remain PC/Web-first until build reactivity is proven. iOS and iPadOS are valid later targets, but they must not drive early validation or force premature touch UI, App Store, TestFlight, mobile monetization, or short-session compromises.

Recommended order:

1. PC/Web validation prototype.
2. Steam Demo / itch-style external testing.
3. iPad-first mobile adaptation after the core loop proves replay desire.
4. iPhone compatibility only after the event UI, character sheet, and run summary are compact enough.

Platform rule:

> Prove on PC/Web that changing build changes the story; then decide how to package it for iOS.

## Primary Validation Question

Does changing character build create:

1. different available options,
2. different locked-but-visible temptations,
3. different flags and downstream consequences,
4. different endings or ending signatures,
5. a desire to replay with another build?

If this is not proven, no additional content, UI, dashboard, Steam work, or meta progression should be added.

## Product Pillars

### 1. Build Identity First

Each playable build must feel like a distinct identity, not just a stat modifier.

A build is successful if the player can say:

> This happened because I was this kind of character.

v0.1 builds:

- Vault Mechanic
- Wasteland Grifter
- Ex-Raider

Each build must have at least two moments where its identity creates a meaningful option or consequence.

### 2. Qualitative Options Over Numeric Bonuses

Attributes and traits should open different routes, not merely increase success chance.

Preferred:

- intelligence opens repair / terminal / old-tech routes
- charisma opens bluff / trade / negotiation routes
- strength opens force / intimidation routes
- perception opens detection / trap-avoidance routes
- endurance opens infection / injury / survival routes

Avoid in v0.1:

- `+10% success chance`
- `+1 damage`
- pure probability modifiers
- invisible stat bonuses

The player should feel build difference through available actions, not through hidden math.

### 3. Locked Options Create Replay Desire

The player should see some options they cannot currently access.

Locked options must be visible when they are important for replay motivation.

A locked option must explain:

1. what the player lacks,
2. why the current character cannot access it,
3. why another build might.

Example:

```text
[LOCKED] Repair the clinic door control panel
Requires: intelligence >= 7 or mechanic
You can see the door still has power, but the wiring is beyond your skill.
```

The goal is to make the player think:

> Next run, I want to try a build that can do that.

### 4. Early Flags Must Affect Later Events

Build-gated choices must not be isolated one-off flavor.

At least two early choices must set flags that affect later options, outcomes, or ending signatures.

Examples:

- `clinic_entered_safely`
- `guard_scanner_disabled`
- `market_contact_earned`
- `raider_reputation_seen`
- `saved_injured_scavenger`

The final event must read at least two earlier flags.

### 5. Roguelite Structure Supports Replay, Not Random Noise

v0.1 should not use a large random event pool.

The first slice should be deterministic:

- fixed seed
- fixed three builds
- fixed five events
- reproducible run summaries

The goal is not to prove content variety.

The goal is to prove build reactivity.

Randomization can be added only after build identity is proven.

## v0.1 Scope

### Must Include

- 3 character presets
- existing SPECIAL-based `CharacterProfile`
- trait / tag-based build identity
- 5 deterministic events
- build-gated options
- locked-visible options
- flag setting and flag consumption
- at least 3 ending signatures
- CLI playthrough
- machine-readable end summary

### Must Not Include

- open world
- new engine
- complex combat
- free stat allocation
- large procedural event pool
- UI or dashboard expansion
- Steam packaging or store work before the Steam Demo validation slice is ready
- iOS-first or mobile-first design constraints
- meta stat progression
- large worldbuilding expansion
- new analytics unrelated to build reactivity

## v0.1 Event Requirements

Each of the five events must include:

1. at least one common option,
2. at least one build-gated available option,
3. at least one locked-visible option,
4. at least one flag set or flag read,
5. a consequence that can be summarized at the end of the run.

Planned deterministic event sequence:

1. `roadside_trap`
2. `locked_clinic`
3. `infection_checkpoint`
4. `underground_market`
5. `vault_gate`

## Build Presets

### Vault Mechanic

Core fantasy:

> I understand old-world systems better than people.

Expected strengths:

- repair
- terminals
- old-tech access
- scanner manipulation
- technical endings

Suggested tags:

- `mechanic`
- `vault_dweller`

Expected weakness:

- intimidation
- black-market trust
- physical confrontation

### Wasteland Grifter

Core fantasy:

> I survive by reading people and lying better than they do.

Expected strengths:

- bluff
- trade
- fake documents
- negotiation
- social shortcuts

Suggested tags:

- `liar`
- `trader`

Expected weakness:

- direct force
- technical systems
- exposure if lies fail

### Ex-Raider

Core fantasy:

> I know how violent people think because I used to be one of them.

Expected strengths:

- intimidation
- gang recognition
- black-market access
- violent shortcuts
- raider reputation

Suggested tags:

- `ex_raider`
- `intimidator`

Expected weakness:

- civilian distrust
- authority hostility
- violent choices creating downstream consequences

## Gate A - Machine Self-Playtest

Run the same five events with the same seed using three presets:

1. Vault Mechanic
2. Wasteland Grifter
3. Ex-Raider

Passing criteria:

- at least 2 / 5 events have option divergence between builds
- each build sees at least 2 locked temptations
- at least 2 flags affect later event options
- at least 2 ending signatures are produced across the three runs
- each run produces a machine-readable summary
- fixed seed and fixed choices are reproducible

Required summary fields:

```json
{
  "build_id": "vault_mechanic",
  "build_options_taken": [],
  "locked_options_seen": [],
  "flags_triggered": [],
  "flags_consumed": [],
  "ending_id": "",
  "death_or_win_reason": ""
}
```

## Gate B - 3-Player Playtest

Ask only four questions:

1. What did your build feel good at?
2. Do you remember any locked option you could not choose?
3. Which consequence felt caused by your earlier choice?
4. Which build would you want to try next?

Passing criteria:

- at least 2 / 3 players can describe their build identity
- at least 2 / 3 players remember one locked option
- at least 2 / 3 players can attribute one consequence to an earlier choice
- at least 1 / 3 players wants to try another build

## Gate C - Instrumented Validation

The run log and end summary must prove:

- which build-gated options were taken,
- which locked options were shown,
- which flags were triggered,
- which flags were consumed later,
- which ending was reached,
- why that ending happened.

If the ending cannot be explained through build + choices + flags, the slice has failed.

## Stop Conditions

Stop adding content if any of the following are true:

1. all three builds feel similar,
2. locked options are not remembered,
3. endings are not meaningfully different,
4. flags do not affect later events,
5. the player feels punished by randomness rather than shaped by build and choices,
6. the developer does not want to replay with another build.

If these happen, fix build reactivity before adding more content.

## Success Definition

v0.1 succeeds only if this sentence is true:

> Same events, different build, different story.

If that sentence is not true, Ashfall should not proceed to UI, dashboard, Steam, or larger content production.
