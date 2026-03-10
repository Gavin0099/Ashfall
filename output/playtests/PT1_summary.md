# PT-1 Summary

Date: TBD
Operator: TBD
Sessions completed: 1

## Verdict

- PT-1 verdict: FAIL
- gate hesitation match (>= 0.7): 1.0 [PASS]
- gate regret match (>= 0.7): 0.0 [FAIL]
- gate replay intent (>= 0.5): 1.0 [PASS]
- gate hesitation nodes/player (>= 3): 2.0 [FAIL]
- gate hesitation time ms (>= 5000): 7250.0 [PASS]

## Sample

- Player count: 1
- Seeds used / run ids: south_aggressive
- Players with roguelite experience: 1
- Players without game-dev background: 1

## Quantitative Readout

From `output/playtests/comparison_summary.json`:

- hesitation match rate: 1.0
- regret match rate: 0.0
- replay intent rate: 1.0
- avg decision time ms: 6200.0
- avg hesitation nodes per player: 2.0
- avg hesitation time ms: 7250.0
- equipment arc notice rate: 1.0
- sessions with confusion flagged: 0

## Qualitative Readout

### Judgment Regret

- Common "my mistake" pattern:
- Taking the greedy village option was my own mistake.

### Frustration Regret

- Common "this felt unfair" pattern:
- I understood the warning, so this did not feel unfair.

### Replay Signal

- Why players wanted another run:
- I want to try the same seed with a safer south route.

## Machine vs Human Alignment

- See `output/playtests/comparison_summary.json`
- hesitation breakdown:
- aligned_pressure_hesitation: 1
- regret breakdown:
- victory_run_has_no_machine_regret_nodes: 1
- machine blame breakdown:
- none: 1

## PT-2 Read

- If `victory_run_has_no_machine_regret_nodes` dominates, treat regret mismatch separately from death attribution failure.
- If `machine_pressure_but_no_human_hesitation` appears, route pressure is not reading strongly enough in the CLI.
- If `human_hesitation_on_confusion_only` appears, the issue is clarity, not tension.

## Radiation Read

- Perceived death causes:
- I stacked too much radiation on the south route.

## Decision

- Recommended call: run another PT-1 iteration

## Next Action

1. Increase visible route pressure earlier; current hesitation density is below PT-1 target.
2. Separate victory-run regret from death-chain regret in PT-2 readouts; the current mismatch is coming from a win with no machine regret nodes.
3. Update tasks/TASKS.md with the PT-1 verdict once operator fields are filled.
