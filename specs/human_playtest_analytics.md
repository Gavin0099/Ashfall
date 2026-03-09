# Human Playtest Analytics

## Purpose

Machine metrics are not enough to prove replay desire or perceived tension.

This spec defines the human-observation layer that must be compared against machine-generated analytics.

## Why This Exists

Machine pressure signals measure:

- resource trade-offs
- combat risk
- irreversible-state accumulation

Human playtests measure:

- hesitation
- confusion
- regret
- replay desire

The prototype is only convincing if these two layers roughly agree.

## Core Comparison Questions

1. Do machine-marked pressure nodes match human hesitation?
2. Do machine failure chains match player regret reports?
3. Does replay intent correlate with meaningful divergence rather than novelty alone?

## Required Inputs

- `output/playability/run_*.json`
- `output/analytics/run_*.json`
- `output/analytics/balance_summary.json`
- `schemas/human_playtest_log_schema.json`
- `playtests/observation_sheet_template.md`

## Human Metrics

- `avg_decision_time_ms`
- `hesitation_nodes_per_run`
- `confusion_nodes_per_run`
- `regret_anchor_rate`
- `replay_intent_rate`

## Machine Metrics To Compare Against

- `pressure_count`
- `failure_analysis.primary_blame_factor`
- `failure_analysis.regret_nodes`
- `failure_analysis.is_trash_time_death`
- `distinct_outcome_signatures`

## Interpretation Rules

### Good Alignment

- human hesitation occurs at nodes already marked as pressure by analytics
- player identifies a regret node also present in `failure_analysis.regret_nodes`
- player replay intent remains high when route divergence is high

### Mismatch Red Flags

- machine marks high pressure, but humans show no hesitation
- humans report confusion instead of tension at pressure nodes
- humans cannot name a regret choice even when machine failure analysis is clear
- replay intent is low despite high divergence and clean death attribution

## Immediate Use

This spec is intended for Blind CLI tests before any meaningful UI layer is introduced.
