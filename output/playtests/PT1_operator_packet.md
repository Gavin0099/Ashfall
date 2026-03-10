# PT-1 Operator Packet

Use this packet during live sessions so the observer does not need to cross-check seed tables and machine logs by hand.

## Session Commands

```bash
python scripts/bootstrap_pt1_sessions.py
python scripts/play_cli_run.py <seed>
python scripts/validate_human_playtest_logs.py
python scripts/compare_playtest_vs_machine.py
python scripts/generate_pt1_summary.py
```

## Seed Coverage

### P1 / seed 101

- expected run family: `north_aggressive`
- operator note: strong early pressure
- machine reference: `north_aggressive`
- pressure nodes: node_north_1, node_north_2, node_mid, node_final
- primary risk read: survived reference run
- final state snapshot: hp=2 food=4 ammo=3 rad=2 weapon=rust_rifle tool=None
- equipment arc:
- node_north_1: weapon -> makeshift_blade (replaced empty)
- node_mid: weapon -> rust_rifle (replaced makeshift_blade)

### P2 / seed 103

- expected run family: `south_aggressive`
- operator note: food relief + radiation tension
- machine reference: `south_aggressive`
- pressure nodes: node_south_1, node_south_2, node_mid, node_final
- primary risk read: survived reference run
- final state snapshot: hp=4 food=6 ammo=2 rad=3 weapon=rust_rifle tool=field_pack
- equipment arc:
- node_south_2: tool -> field_pack (replaced empty)
- node_mid: weapon -> rust_rifle (replaced empty)

### P3 / seed 104

- expected run family: `south_cautious`
- operator note: lower explicit pressure, good for contrast
- machine reference: `south_cautious`
- pressure nodes: node_south_1, node_south_2, node_mid, node_final
- primary risk read: survived reference run
- final state snapshot: hp=10 food=3 ammo=1 rad=0 weapon=None tool=scavenger_kit
- equipment arc:
- node_south_1: tool -> scavenger_kit (replaced empty)

### P4 / seed 105

- expected run family: `mixed_pressure`
- operator note: mixed route pressure
- machine reference: `mixed_pressure`
- pressure nodes: node_north_1, node_north_2, node_mid, node_final
- primary risk read: survived reference run
- final state snapshot: hp=2 food=3 ammo=1 rad=1 weapon=rust_rifle tool=None
- equipment arc:
- node_north_1: weapon -> makeshift_blade (replaced empty)
- node_mid: weapon -> rust_rifle (replaced makeshift_blade)

### P5 / seed 1001

- expected run family: `exploratory`
- operator note: check whether non-baseline seed still reads clearly
- machine reference: unavailable

## Observer Focus

- Mark hesitation when the player compares routes, re-reads warnings, or counts food/ammo before committing.
- Copy exact wording for confusion and regret statements. Do not paraphrase if avoidable.
- After the run, make sure `run_id` in the human log matches the closest machine family, not just the seed.
