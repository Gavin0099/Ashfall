# Ashfall P3 Event Specifications

## Purpose

This file derives the five deterministic v0.1 events from `BUILD_GATING_PRODUCT_CONTRACT.md`.

It is a specification gate, not gameplay content. Do not implement event payloads until each event below satisfies the product contract:

- same events, different build, different story
- qualitative build routes over numeric bonuses
- locked-visible temptations
- early flags affecting later events
- machine-readable end-summary consequences

## Shared Build Vocabulary

| Build id | Runtime strengths | Tags |
| --- | --- | --- |
| `vault_mechanic` | `intelligence`, `perception` | `mechanic`, `vault_dweller` |
| `wasteland_grifter` | `charisma`, `luck` | `liar`, `trader` |
| `ex_raider` | `strength`, `endurance` | `ex_raider`, `intimidator` |

## Shared Event Option Rules

Every event must have:

- one common option available to all builds,
- at least one available build-gated option,
- at least one locked-visible build temptation,
- either a flag set or a flag read,
- an end-summary consequence.

Locked text must explain what is missing in player-facing terms. Requirements must use the existing runtime contract:

```json
{
  "requirements": {
    "attribute": {"INT": 4},
    "trait": ["mechanic"]
  },
  "visible_if_locked": true,
  "locked_text": "You can see the fix, but you do not know how to make it hold."
}
```

## Event 1: `roadside_trap`

### Product Job

Establish that build identity changes how the player reads danger. This event should set up at least one downstream path for the clinic or market.

### Common Option

`push_through_trap`

- Available to all builds.
- Cost: minor HP or food loss.
- Summary consequence: player chose a brute survival route without gaining special leverage.

### Build-Gated Options

`detect_tripwire`

- Build: Vault Mechanic / perception-leaning technical read.
- Requirement: `PER >= 4` or `mechanic`.
- Sets: `trap_disarmed=true`.
- Summary consequence: player converted perception/technical knowledge into safe passage.

`turn_trap_into_warning`

- Build: Ex-Raider.
- Requirement: `STR >= 4` or `ex_raider`.
- Sets: `raider_reputation_seen=true`.
- Summary consequence: player recognized raider signaling and used it as social leverage.

### Locked-Visible Temptation

`sell_fake_safe_route`

- Build: Wasteland Grifter.
- Requirement: `CHA >= 4` or `liar`.
- Sets: `market_contact_earned=true`.
- Locked text should imply that another character could turn the trap into a scam or bargaining chip.

### Required Flag Behavior

At least one of these must be set by the chosen route:

- `trap_disarmed`
- `raider_reputation_seen`
- `market_contact_earned`

### Product Pillars Proved

- Build Identity First
- Qualitative Options Over Numeric Bonuses
- Early Flags Must Affect Later Events

## Event 2: `locked_clinic`

### Product Job

Make locked-visible temptation explicit. The player should understand why a different build would enter the clinic differently.

### Common Option

`force_clinic_window`

- Available to all builds.
- Cost: HP loss or noise flag.
- Sets: `clinic_forced_entry=true`.
- Summary consequence: player entered without build leverage and created risk.

### Build-Gated Options

`repair_clinic_door`

- Build: Vault Mechanic.
- Requirement: `INT >= 4` or `mechanic`.
- Sets: `clinic_entered_safely=true`.
- Summary consequence: player used old-world repair skill to preserve resources and unlock medical leverage.

`intimidate_squatters`

- Build: Ex-Raider.
- Requirement: `STR >= 4` or `intimidator`.
- Sets: `clinic_squatters_cowed=true`.
- Summary consequence: player gained access through threat, increasing later distrust risk.

### Locked-Visible Temptation

`fake_medical_authorization`

- Build: Wasteland Grifter.
- Requirement: `CHA >= 4` or `liar`.
- Sets: `clinic_fake_credentials=true`.
- Locked text should make the player want to try a grifter route next run.

### Required Flag Behavior

At least one flag from this event must be read by `infection_checkpoint`.

Candidate flags:

- `clinic_entered_safely`
- `clinic_squatters_cowed`
- `clinic_fake_credentials`
- `clinic_forced_entry`

### Product Pillars Proved

- Locked Options Create Replay Desire
- Early Flags Must Affect Later Events

## Event 3: `infection_checkpoint`

### Product Job

Consume earlier clinic/trap flags and show that a previous build choice changed a later event.

### Common Option

`wait_out_screening`

- Available to all builds.
- Cost: food or time pressure.
- Summary consequence: player accepted attrition because no prior leverage applied.

### Build-Gated / Flag-Gated Options

`use_sterile_clinic_supplies`

- Requirement: `clinic_entered_safely=true`.
- Strong fit: Vault Mechanic.
- Sets: `infection_screening_passed=true`.
- Summary consequence: earlier safe clinic access created a later survival shortcut.

`talk_through_checkpoint`

- Build: Wasteland Grifter.
- Requirement: `CHA >= 4` or `trader`.
- Optional flag boost: `clinic_fake_credentials=true`.
- Sets: `checkpoint_story_believed=true`.
- Summary consequence: player used social cover to avoid quarantine.

`recognize_raider_scar_protocol`

- Build: Ex-Raider.
- Requirement: `raider_reputation_seen=true` or `ex_raider`.
- Sets: `checkpoint_guard_spooked=true`.
- Summary consequence: violent past opened a shortcut but made authority hostility plausible.

### Locked-Visible Temptation

If the current build lacks the relevant flag, show one tempting locked route from another build:

- Mechanic sees grifter paperwork route locked.
- Grifter sees raider intimidation route locked.
- Raider sees technical clinic-supply route locked.

### Required Flag Behavior

This event must consume at least one earlier flag and set at least one later flag for `vault_gate`.

Candidate consumed flags:

- `clinic_entered_safely`
- `clinic_fake_credentials`
- `raider_reputation_seen`

Candidate set flags:

- `infection_screening_passed`
- `checkpoint_story_believed`
- `checkpoint_guard_spooked`

### Product Pillars Proved

- Early Flags Must Affect Later Events
- Same Events, Different Build, Different Story

## Event 4: `underground_market`

### Product Job

Let social, technical, and violent builds each create a distinct kind of leverage before the finale.

### Common Option

`buy_overpriced_pass`

- Available to all builds.
- Cost: scrap, ammo, or food.
- Summary consequence: player bought access without special leverage.

### Build-Gated Options

`forge_market_contact`

- Build: Wasteland Grifter.
- Requirement: `CHA >= 4` or `trader`.
- Stronger if `market_contact_earned=true`.
- Sets: `market_contact_earned=true`.
- Summary consequence: player converted social skill into finale access.

`repair_vendor_scanner`

- Build: Vault Mechanic.
- Requirement: `INT >= 4` or `mechanic`.
- Sets: `guard_scanner_disabled=true`.
- Summary consequence: player disabled a finale obstacle through technical favor.

`call_in_raider_debt`

- Build: Ex-Raider.
- Requirement: `ex_raider` or `raider_reputation_seen=true`.
- Sets: `raider_debt_called=true`.
- Summary consequence: player used violent reputation, with possible ending cost.

### Locked-Visible Temptation

Each non-matching build should see one market route they cannot access, with text that makes the alternate build fantasy concrete.

### Required Flag Behavior

At least one flag from this event must be read by `vault_gate`.

Candidate flags:

- `market_contact_earned`
- `guard_scanner_disabled`
- `raider_debt_called`

### Product Pillars Proved

- Build Identity First
- Qualitative Options Over Numeric Bonuses
- Locked Options Create Replay Desire

## Event 5: `vault_gate`

### Product Job

Pay off build identity and earlier flags. The finale must produce at least three ending signatures across the three builds.

### Common Option

`force_vault_wait`

- Available to all builds.
- Outcome: partial or costly access.
- Ending signature: `vault_entry_costly_survival`.

### Build / Flag Payoff Options

`technical_override`

- Build: Vault Mechanic.
- Requirements: `INT >= 4` or `mechanic`; benefits from `guard_scanner_disabled` or `clinic_entered_safely`.
- Ending signature: `vault_entry_technical_success`.
- Summary consequence: old-world systems opened because the player understood them.

`social_bypass`

- Build: Wasteland Grifter.
- Requirements: `CHA >= 4` or `liar`; benefits from `market_contact_earned` or `checkpoint_story_believed`.
- Ending signature: `vault_entry_social_fraud`.
- Summary consequence: the player lied their way into a system built on trust.

`raider_pressure`

- Build: Ex-Raider.
- Requirements: `STR >= 4` or `intimidator`; benefits from `raider_debt_called` or `checkpoint_guard_spooked`.
- Ending signature: `vault_entry_intimidation`.
- Summary consequence: violent credibility opened the gate but changed how survivors remember the player.

### Locked-Visible Temptation

The finale should show at least two locked ending routes to each build if requirements are unmet. These are the strongest replay prompts in the slice.

### Required Flag Behavior

The finale must read at least two earlier flags across each run evaluation matrix.

Candidate read flags:

- `clinic_entered_safely`
- `guard_scanner_disabled`
- `market_contact_earned`
- `checkpoint_story_believed`
- `raider_debt_called`
- `checkpoint_guard_spooked`

### Product Pillars Proved

- Early Flags Must Affect Later Events
- Build Identity First
- Same Events, Different Build, Different Story

## P3 Acceptance Checklist

Before implementing event payloads, confirm this spec still satisfies:

- [ ] All five events have at least one common option.
- [ ] All five events have at least one build-gated option.
- [ ] All five events have at least one locked-visible temptation.
- [ ] At least two early flags affect later options.
- [ ] `vault_gate` reads at least two earlier flags.
- [ ] Three distinct ending signatures are possible.
- [ ] Each build has at least two high moments.
- [ ] Each build sees at least two locked temptations.
- [ ] The spec does not rely on numeric success chances.
- [ ] The spec does not require new engine, UI, Steam, or iOS work.
