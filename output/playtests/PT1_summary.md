# PT-1 External Playtest Summary Report

Date: 2026-03-17
Participants: 4 (Gavin, Mei, Leo, diashi)
Seeds Tested: 101 (Fixed)

## 📊 Core Metrics

- **Average Decision Time**: 3,917 ms
- **Max Hesitation**: 11,694 ms (Player: Mei, Node: `node_approach`)
- **Victory Rate**: 50% (2/4)
- **Machine Pressure Alignment**: 50% (Hesitation matched machine pressure nodes in 2/4 runs)
- **Equipment Awareness**: 50% (Players noticed equipment utility/arcs)

## 🔍 Key Findings

### 1. Pressure Point Validation
The machine simulation successfully predicted **50% of the observed human hesitation points**, specifically around the `node_approach` and `node_mid` locations where resource scarcity meets path ambiguity.

### 2. Radiation Sensitivity Gap
Players (e.g., `diashi]`) tended to underestimate the long-term impact of radiation compared to the machine's cautious projections. This suggests that the current UI warning for radiation might need to be more "visceral" or "alarming" to match the actual mathematical threat.

### 3. Starvation vs. Caution
`Gavin`'s death by starvation highlights a common human strategy: choosing "Safe" but "Long" routes without auditing the food supply. This confirms that the food-to-distance ratio is a primary "Regret Node" source.

## 🛠 Action Items for Next Phase

1. **[UI/UX]** Enhance Radiation Warning visual feedback.
    - *Idea*: Screen tint or heartbeat sound when entering high-rad areas without protection.
2. **[Balance]** Audit `node_north_1/2` food consumption rates.
    - *Goal*: Ensure "Safety" has a clearer food cost trade-off.
3. **[Systems]** Implement Equipment Scarcity visibility.
    - Players need to "feel" the absence of a Gas Mask earlier in the run.

## 📁 Artifacts Generated
- **Final JSON Logs**: `playtests/*_session_log.json`
- **Comparison Summary**: `output/playtests/comparison_summary.json`
- **Observation Notes**: `playtests/sessions/*/observation_*.md`
