# Playtests

## Purpose

This directory stores human playtest observation material for PT-1 and later rounds.

## Files

- `observation_sheet_template.md`: paper/markdown observer sheet
- `PT1_session_template.json`: blank JSON log template for a real player session
- `P1_session_log.json`: ready-to-edit first player session file
- `sample_session_log.json`: filled example log for validator and comparison smoke tests

## Naming

Use one JSON file per player session.

Recommended pattern:

- `P1_session_log.json`
- `P2_session_log.json`
- `P3_session_log.json`

## Workflow

1. Optional: run `python scripts/bootstrap_pt1_sessions.py`
2. Or copy `PT1_session_template.json`
3. Rename it to `PX_session_log.json`
4. Fill it during or immediately after the session
5. Run:

```bash
python scripts/validate_human_playtest_logs.py
python scripts/compare_playtest_vs_machine.py
```
