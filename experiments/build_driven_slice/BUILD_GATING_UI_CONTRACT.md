# Ashfall Build-Gating UI Contract

## Purpose

This file defines the UI contract for the build-driven validation slice.

The UI must not become a generic wasteland adventure screen, a decorative RPG dashboard, or a Steam-facing vertical slice. Its first job is to prove build reactivity:

> Same events, different build, different visible choices, different locked temptations, different consequences.

This contract sits after:

- `BUILD_GATING_PRODUCT_CONTRACT.md`
- `BUILD_DRIVEN_SLICE_PLAN.md`
- `P3_EVENT_SPECS.md`

It exists because P3 payloads under `experiments/build_driven_slice/events/` are not enough by themselves. The player and developer need to see why a build matters while the run is happening.

## Product Role

The UI is a:

**Build reactivity viewer**

It must answer four questions at all times:

1. What build am I playing?
2. Which options did this build open?
3. Which options are locked, and what build would likely open them?
4. Which consequences and flags happened because of earlier choices?

If a screen does not help answer one of these questions, it is out of scope for this slice.

## Platform Position

The first target remains:

**PC/Web validation for a future Steam Demo**

The UI may be responsive and iPad-safe, but it must not become iOS-first. Do not optimize the slice around App Store flows, TestFlight, touch-first navigation, short mobile sessions, or mobile monetization.

Platform sequence:

1. PC/Web static prototype.
2. PC/Web payload-backed prototype.
3. Instrumented validation view.
4. Steam Demo packaging only after validation gates pass.
5. iPad/iOS adaptation later.

## Visual Direction

Use a restrained terminal-survival interface:

- card-based responsive layout,
- clear build badges,
- readable narrative panels,
- visible locked options,
- consequence log,
- compact character/resource sheet.

The UI may borrow principles from Citizen Sleeper, Roadwarden, Twine/ink, DCSS, and Cataclysm: Dark Days Ahead, but it must not copy their surface style or become a tile roguelike.

Do not clone Fallout Pip-Boy IP. A terminal/Pip-Boy hybrid mood is acceptable only as a general influence:

- muted screen glow,
- compact technical labels,
- status strips,
- hard-edged panels,
- diegetic debug flavor.

Avoid:

- green monochrome-only imitation,
- decorative CRT noise that hurts readability,
- roguelike grid movement,
- open-world map UI,
- large cinematic hero layout,
- lore-heavy menu chrome,
- icon-only mystery controls.

## Core Screens

### 1. Build Select

Purpose:

Show that choosing a build is choosing a route through the same event sequence.

Must show for each build:

- build name,
- one-sentence fantasy,
- strongest SPECIAL attributes,
- traits/tags,
- high-route preview,
- expected weakness.

Initial builds:

| Build | High routes | Weakness preview |
| --- | --- | --- |
| Vault Mechanic | repair, terminal, scanner, old-tech access | intimidation, black-market trust |
| Wasteland Grifter | bluff, trade, fake documents, negotiation | direct force, technical systems |
| Ex-Raider | intimidation, gang recognition, violent shortcuts | civilian distrust, authority hostility |

Must not show:

- free stat allocation,
- perk trees,
- meta progression,
- character portrait customization.

### 2. Run Path Timeline

Purpose:

Show that every build is walking through the same deterministic five-event path.

Required event order:

1. `roadside_trap`
2. `locked_clinic`
3. `infection_checkpoint`
4. `underground_market`
5. `vault_gate`

Each timeline node should show:

- event id or player-facing title,
- current/completed/upcoming state,
- selected option after completion,
- flags created or consumed after completion.

The timeline must make it obvious that the comparison is fair:

> The route changed because the build changed, not because the event order changed.

### 3. Event Screen

Purpose:

Show the current event, the current build, available choices, locked temptations, and immediate consequence context.

Desktop layout should prioritize:

- scene panel,
- choice list,
- character/resources panel,
- locked temptation panel,
- consequence log.

Mobile/iPad-safe layout may stack these regions:

1. build/resource strip,
2. event title and scene text,
3. available choices,
4. locked choices,
5. consequence log,
6. character sheet drawer.

Required choice categories:

- common option,
- build-gated available option,
- flag-gated available option,
- locked-visible option.

Available build-gated options must show a readable requirement badge, such as:

- `[INT]`
- `[PER]`
- `[mechanic]`
- `[liar]`
- `[ex_raider]`

Locked options must show:

- locked state,
- missing requirement label,
- player-facing locked text,
- alternate-build implication.

Locked options must never be selectable.

### 4. Result / Consequence Screen

Purpose:

After a choice, show what changed before moving to the next event.

Must show:

- chosen option,
- player-facing result text,
- resource changes,
- newly set flags in human-readable language,
- consumed flags when relevant,
- short consequence preview if the flag is expected to matter later.

Raw flag ids may be shown only in a debug drawer or developer mode. The normal player view must translate them into readable consequence language.

Example:

```text
Gained:
- Medkit +1
- Safe clinic access

Consequence:
- The checkpoint may accept your sterile supplies later.

Debug:
- set_flags: ["clinic_entered_safely"]
```

### 5. End Summary

Purpose:

Prove that the run ending can be attributed to build, choices, and flags.

Player-facing summary must show:

- selected build,
- build-gated options taken,
- locked temptations seen,
- important flags triggered,
- important flags consumed later,
- ending title,
- why this ending happened,
- one prompt suggesting which build might reveal a different route.

Debug/machine summary must preserve:

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

## Component Contract

If implemented as Web UI, use these components as the initial boundary:

- `BuildSelectPanel`
- `RunPathTimeline`
- `CharacterSheetCard`
- `ResourceBar`
- `EventScenePanel`
- `ChoiceList`
- `ChoiceCard`
- `LockedChoiceCard`
- `ConsequencePanel`
- `EndSummaryPanel`
- `DebugRunLogDrawer`

Do not create a generic RPG dashboard component layer before these exist.

## Choice View Contract

UI choices should normalize runtime/payload data into this shape before rendering:

```ts
type ChoiceView = {
  id: string
  label: string
  kind: "common" | "build_gated" | "flag_gated" | "locked"
  requirementLabel?: string
  lockedText?: string
  consequencePreview?: string
}
```

Rules:

- `common` is available to every build.
- `build_gated` is available because the current build satisfies a stat or trait requirement.
- `flag_gated` is available because earlier run state unlocked it.
- `locked` is visible but unavailable.

The UI must not infer locked state from styling alone. Locked state must be explicit in data and visible in text.

## Data Flow Contract

Future Web UI endpoints may use this shape:

- `GET /experiments/build-driven/builds`
- `POST /experiments/build-driven/start-run`
- `GET /experiments/build-driven/current-event`
- `POST /experiments/build-driven/choose`
- `GET /experiments/build-driven/summary`

For P4-UI-B, no backend is required. Static hardcoded run states are preferred so layout and comprehension can be reviewed before API work.

For P4-UI-C, read from:

`experiments/build_driven_slice/events/`

Do not promote experiment payload schema into the global event schema until build-reactivity validation proves the shape is worth keeping.

## Required Static Prototype States

P4-UI-B must include at least these hardcoded states:

| Build | Event | Purpose |
| --- | --- | --- |
| Vault Mechanic | `locked_clinic` | Show technical route, grifter/raider locked temptations, and safe clinic flag preview. |
| Wasteland Grifter | `infection_checkpoint` | Show social route, earlier-paperwork leverage, and technical/raider locked temptations. |
| Ex-Raider | `underground_market` | Show intimidation/reputation route, violent consequence risk, and technical/social locked temptations. |

The static prototype must show the same UI structure across all three builds. Only build identity, available choices, locked options, and consequences should differ.

## Layout Contract

Desktop:

- left/primary column: event scene and result text,
- right/support column: build sheet, resources, flags, locked temptations,
- bottom or side region: run timeline and consequence log.

Tablet:

- top status strip,
- scene,
- choices,
- locked choices,
- collapsible character/log panels.

Phone-safe later:

- single-column stacked layout,
- short scene text,
- compact choice cards,
- drawer for character sheet and debug log.

Phone-safe does not mean phone-first. It only means the UI should not make later iOS adaptation impossible.

## Information Hierarchy

Every event state must visually prioritize:

1. current build,
2. current event,
3. available choice difference,
4. locked temptation,
5. consequence / flag change.

Resources are important, but they are not the main validation signal. Do not let HP, water, ammo, or inventory dominate the screen over build reactivity.

## Debug Visibility

Normal player view:

- human-readable consequences,
- readable requirement labels,
- readable build identity,
- readable ending attribution.

Developer/debug view:

- raw option ids,
- raw flag ids,
- raw payload event id,
- `build_options_taken`,
- `locked_options_seen`,
- `flags_triggered`,
- `flags_consumed`.

The debug drawer exists to validate implementation without polluting the player-facing UI.

## Non-goals

Do not build:

- Steam store page,
- Steam packaging,
- iOS export,
- TestFlight flow,
- meta progression UI,
- inventory-heavy survival UI,
- tile/grid movement,
- combat screen,
- procedural map,
- large art pipeline,
- character creator,
- build planner,
- analytics dashboard unrelated to build reactivity.

Do not add new gameplay events for the UI prototype. Use the P3 five-event contract.

## P4 Execution Order

### P4-UI-A: UI Contract

Deliver this file.

Acceptance:

- Defines screen jobs.
- Defines choice and locked-option display rules.
- Defines summary requirements.
- Defines desktop and mobile-safe layout.
- Defines non-goals.
- Keeps Steam Demo as target but PC/Web as validation platform.

### P4-UI-B: Static Prototype

Build a static PC/Web prototype with hardcoded states.

Acceptance:

- Includes the three required prototype states.
- Shows current build clearly.
- Separates available choices and locked temptations.
- Shows consequence log.
- Shows run path timeline.
- Does not require backend.

### P4-UI-C: Read P3 Payload

Connect the UI to `experiments/build_driven_slice/events/`.

Acceptance:

- Converts payload options into `ChoiceView`.
- Preserves locked-visible behavior.
- Shows readable requirement labels.
- Does not mutate global event schema.

### P4-UI-D: Instrumented Summary

Display machine-readable and player-readable run summaries.

Acceptance:

- Shows build-gated options taken.
- Shows locked options seen.
- Shows flags triggered and consumed.
- Shows ending id and human explanation.
- Can compare at least three build runs.

## Success Definition

The UI succeeds only if a reviewer can answer this without reading the JSON payloads:

> What did this build unlock, what did it fail to unlock, and what consequence came from that difference?

If the UI only looks like a polished text RPG but does not make build reactivity legible, it fails this contract.
