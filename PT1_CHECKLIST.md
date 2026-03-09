# PT-1 Checklist

## Purpose

This checklist turns `PLAYTEST_PROTOCOL.md` into a concrete operator workflow.

Use this for the first Blind CLI playtest round.

## Before Session

- [ ] Confirm latest repo state is on `main`
- [ ] Confirm these files exist:
  - [PLAYTEST_PROTOCOL.md](e:\BackUp\Git_EE\Ashfall\PLAYTEST_PROTOCOL.md)
  - [play_cli_run.py](e:\BackUp\Git_EE\Ashfall\scripts\play_cli_run.py)
  - [human_playtest_log_schema.json](e:\BackUp\Git_EE\Ashfall\schemas\human_playtest_log_schema.json)
  - [observation_sheet_template.md](e:\BackUp\Git_EE\Ashfall\playtests\observation_sheet_template.md)
- [ ] Prepare one blank observation sheet per player
- [ ] Prepare one JSON log file per player using `playtests/sample_session_log.json` as the template

Recommended naming:

- `playtests/P1_session_log.json`
- `playtests/P2_session_log.json`

## Operator Setup

- [ ] Open one terminal for the player run
- [ ] Open one editor window for the observer log
- [ ] Choose a seed for the session

Recommended fixed seeds for the first round:

1. `101`
2. `103`
3. `104`
4. `105`
5. `1001`

## Start Script

Run:

```bash
python scripts/play_cli_run.py 103
```

Replace `103` with the session seed.

## Intro Script

Say only:

`This is a wasteland survival prototype. You need to choose routes, manage resources, and try to survive to the end.`

Do not explain:

- best strategy
- hidden rules
- exact system math

## During Run

- [ ] Do not coach the player unless blocked by input handling
- [ ] Record hesitation at nodes
- [ ] Record emotional spike quotes
- [ ] Record confusion moments
- [ ] Record the player's exact wording when possible

Observer capture targets:

- `timestamp`
- `node_id`
- `decision_time_ms`
- `selected_option`
- `hesitation_flag`
- `confusion_flag`
- `what_i_thought_happened`
- `why_im_salty`
- `verbal_note`

## Immediate Interview

Ask exactly:

1. Which choice was hardest to make?
2. When you died, or almost died, what do you think caused it?
3. If you ran again, which choice would you change?

Then record:

- `hardest_choice`
- `perceived_death_cause`
- `regret_choice`
- `replay_intent`

## After Each Session

- [ ] Save the human log as `playtests/PX_session_log.json`
- [ ] Confirm `output/cli/latest_seed_<seed>.json` exists
- [ ] Confirm the player log references the correct `run_id`

If needed, use one of these known run ids:

- `north_aggressive`
- `north_cautious`
- `south_aggressive`
- `south_cautious`
- `mixed_pressure`

## After All Sessions

Validate logs:

```bash
python scripts/validate_human_playtest_logs.py
```

Generate comparison summary:

```bash
python scripts/compare_playtest_vs_machine.py
```

Expected artifact:

- [comparison_summary.json](e:\BackUp\Git_EE\Ashfall\output\playtests\comparison_summary.json)

## Success Readout

Look at:

- `hesitation_match_rate`
- `regret_match_rate`
- `replay_intent_rate`
- `avg_decision_time_ms`

Interpretation target for PT-1:

- hesitation match rate `>= 0.7`
- regret match rate `>= 0.7`
- replay intent rate `>= 0.5`

## If PT-1 Fails

- If hesitation is low: pressure signals are not visible enough
- If regret match is low: failure attribution is too machine-centric or too late
- If replay intent is low: route divergence may exist, but felt strategy may still be weak

Do not respond by adding UI first.

Respond by:

1. adjusting route pressure shape
2. adjusting regret distance
3. refining CLI warning clarity
