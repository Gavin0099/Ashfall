# Current Task: PT-1 Playtest Operations and Equipment Prototype Integration

## Progress
- [x] Real equipment acquisition and replacement integrated into core run flow
- [x] EXP-4 rerun with real event acquisition flow
- [x] CLI runner rebuilt into stable Chinese output with equipment visibility
- [x] Run analytics and playability logs extended with equipment state and summaries
- [x] PT-1 operator packet generator added
- [x] PT-1 summary generator upgraded with automatic gate verdicts
- [x] PT-2 comparison output upgraded with mismatch reason breakdowns and equipment-arc notice rate
- [x] PT-1 summary now surfaces PT-2 mismatch reasons directly
- [ ] Run the remaining PT-1 human sessions using `output/playtests/PT1_operator_packet.md`
- [ ] Re-run PT-1 comparison and summary after more human logs are completed

## Context
- **Recent achievements**: `rust_rifle` and `field_pack` are now real event-driven equipment rewards, CLI players can see acquisition and replacement in Chinese, PT-1 now has an operator packet plus automatic PASS/FAIL summary output, and PT-2 readouts now classify mismatch reasons instead of only reporting raw match rates.
- **Remaining issues**: current PT-1 sample size is too small, and the latest machine-vs-human summary shows `regret_match_rate = 0.0` and hesitation density below target.
- **Next steps**: finish P2-P5 human sessions, validate logs, regenerate `output/playtests/comparison_summary.json` and `output/playtests/PT1_summary.md`, then decide whether to proceed to PT-2 or rebalance route pressure / warning clarity. When reviewing mismatch, separate victory-run regret from true death-chain attribution failures.
