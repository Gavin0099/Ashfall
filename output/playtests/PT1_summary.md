# PT-1 Summary

Date: TBD
Operator: TBD
Sessions completed: 1

## Sample

- Player count: 1
- Seeds used / run ids: south_aggressive
- Players with roguelite experience: 1
- Players without game-dev background: 1

## Quantitative Readout

From `output/playtests/comparison_summary.json`:

- hesitation match rate: 1.0
- regret match rate: 1.0
- replay intent rate: 1.0
- avg decision time ms: 6200.0
- avg hesitation nodes per player: 2.0
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
- Manual callout: review sessions where `hesitation_match` or `regret_match` is false.

## Radiation Read

- Perceived death causes:
- I stacked too much radiation on the south route.

## Decision

Choose one:

- Keep current route-pressure shape for next round
- Adjust south-route pressure
- Reduce radiation dominance
- Improve warning clarity before any balance change

## Next Action

1. TBD
2. TBD
3. TBD
