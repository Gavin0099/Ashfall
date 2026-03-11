# PT-2 Action Report

## Snapshot

- log_count: 1
- hesitation_match_rate: 1.0
- regret_match_rate: 0.0
- replay_intent_rate: 1.0
- avg_decision_time_ms: 6200.0
- equipment_arc_notice_rate: 1.0

## Hesitation Breakdown

- aligned_pressure_hesitation: 1

## Regret Breakdown

- victory_run_has_no_machine_regret_nodes: 1

## Machine Blame Breakdown

- none: 1

## Action Read

1. Complete the remaining PT-1 human sessions before making balance calls; current sample size is below the intended first-round threshold.
2. Split victory-run regret from death-chain regret in PT-2 interpretation; this mismatch does not imply failure-analysis misattribution.
3. Keep comparison output under review as PT-1 sample size grows.
4. Update tasks/TASKS.md once PT-2 evidence is strong enough to mark ready/done.

## Session Notes

- `P1` / `south_aggressive`: hesitation=aligned_pressure_hesitation, regret=victory_run_has_no_machine_regret_nodes, equipment_arc_noticed=True
