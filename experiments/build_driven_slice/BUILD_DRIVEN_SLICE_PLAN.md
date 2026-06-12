# Ashfall Build-Gating Thin Slice Plan

## Contract Layer

This is the implementation contract for the product direction defined in:

`experiments/build_driven_slice/BUILD_GATING_PRODUCT_CONTRACT.md`

The product contract answers why this slice exists and what must not be built yet. This file answers how the slice attaches to the existing runtime, schema, CLI, and tests.

Do not add the five gameplay events until the event specs are explicitly derived from the product contract. The P3 event specification lives at:

`experiments/build_driven_slice/P3_EVENT_SPECS.md`

That file is the gate between product contract and gameplay content. Event payload implementation can start only after its acceptance checklist is satisfied.

The first public validation target is a Steam Demo, but this implementation slice remains PC/Web-first. Do not introduce Steam packaging, iOS export, mobile UI constraints, or store workflow until the build-reactivity gates pass.

## Scope

Build a thin, deterministic slice over the existing Ashfall runtime:

`CharacterProfile -> option requirements -> locked option display -> flags -> end summary -> deterministic self-playtest`

This slice proves that character build changes available choices and later consequences. It must reuse the current `src/` runtime instead of introducing a parallel engine under `experiments/build_driven_slice/`.

## Non-goals

- No UI or dashboard work.
- No Steam, store, or packaging work before the validation slice is ready.
- No iOS-first or mobile-first work.
- No meta-progression expansion.
- No 20-event or 30-perk content push.
- No replacement of `CharacterProfile`, `RunEngine`, or the main event resolver.
- No generic wasteland events that do not prove build reactivity.
- No P3 gameplay event implementation before the event specs satisfy the product contract.

## Attribute Strategy

The slice keeps Ashfall's existing Fallout-like SPECIAL keys in `CharacterProfile.special`:

| Slice shorthand | Runtime SPECIAL key |
| --- | --- |
| `STR` | `strength` |
| `PER` | `perception` |
| `INT` | `intelligence` |
| `CHA` | `charisma` |
| `SUR` | `endurance` |

`SUR` is a slice shorthand only. Runtime code should store it as `endurance` so the existing character model remains authoritative.

## Trait/Tag Strategy

Build-gated options use `CharacterProfile.tags` through `character_filters.require_any_tag`.

Initial presets:

| Build id | High stat | Tags |
| --- | --- | --- |
| `vault_mechanic` | `intelligence` | `mechanic`, `vault_dweller` |
| `wasteland_grifter` | `charisma` | `liar`, `trader` |
| `ex_raider` | `strength` | `ex_raider`, `intimidator` |

Free allocation is out of scope for the thin slice. Presets are enough to prove option divergence.

## Event Option Schema Mapping

Authoring may use this compact shape:

```json
{
  "requirements": {
    "attribute": {"INT": 4},
    "trait": ["mechanic"]
  }
}
```

Runtime must treat it as equivalent to:

```json
{
  "character_filters": {
    "require_special": {
      "intelligence": {"min": 4}
    },
    "require_any_tag": ["mechanic"]
  }
}
```

`character_filters` remains the canonical runtime representation. Compact `requirements` exists only to make slice content easier to author and review.

## Locked Option Behavior

An unmet option is still shown when `visible_if_locked` is omitted or true. It must be marked as locked and include any provided `locked_text`.

An unmet option is hidden only when:

```json
{"visible_if_locked": false}
```

Locked options cannot be selected. The CLI should display the requirement reason and the `locked_text` so the player understands which build would have opened the route.

## Flag Propagation Requirement

The CLI path and `RunEngine` path must use the same flag behavior:

- `get_available_options(..., run_flags=run.flags)` evaluates current flags.
- `resolve_event_choice(..., run_flags=run.flags)` applies selected option flags.
- A later option with `required_flags` can consume the earlier choice as a gate.

This prevents a build-driven slice from passing in engine tests while failing in manual CLI play.

## End Summary Fields

The slice end summary should be machine-readable and include:

```json
{
  "build_id": "vault_mechanic",
  "build_options_taken": ["clinic_repair_door"],
  "locked_options_seen": ["grifter_fake_documents"],
  "flags_triggered": ["clinic_entered_safely"],
  "flags_consumed": ["clinic_entered_safely"],
  "resource_pressure_turns": ["event_3_infection_checkpoint"],
  "ending_id": "vault_entry_technical_success",
  "death_or_win_reason": "Opened vault gate through technical override."
}
```

## Deterministic Self-playtest Matrix

Run the same seed and five-event sequence for:

- `vault_mechanic`
- `wasteland_grifter`
- `ex_raider`

Required events:

1. `roadside_trap`
2. `locked_clinic`
3. `infection_checkpoint`
4. `underground_market`
5. `vault_gate`

P3 event specs are defined in `P3_EVENT_SPECS.md`. Each event spec must state:

- the common option,
- the build-gated available option,
- the locked-visible temptation,
- the flag set or consumed,
- the end-summary consequence,
- which product pillar it proves.

Do not implement event payloads if a proposed event only adds wasteland flavor without proving one of the product pillars.

Expected output path:

`output/build_driven_slice/self_playtest_summary.json`

## Success Criteria

- At least 2 of 5 events expose different available choices across the three builds.
- Each build sees at least one locked option.
- Every locked option includes explanation text.
- At least two flags affect later event options.
- End summary includes `build_options_taken`, `locked_options_seen`, and `flags_triggered`.
- Same seed and same build produce reproducible results.
