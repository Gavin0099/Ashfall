# governance_tools - AI Governance Framework Tools

> Status: governance utilities are available; Ashfall Phase D governance checks are active.
> Source of phase truth: root `PLAN.md` and `tasks/TASKS.md`.
> Last reviewed: 2026-03-11
> Runtime: Python 3.9+ (stdlib-first)

## Available Tools

| Tool | Purpose | Typical Use |
|---|---|---|
| [memory_janitor.py](#memory_janitorpy) | manage hot memory and generated runtime artifacts | context cleanup / cache cleanup |
| [contract_validator.py](#contract_validatorpy) | validate governance contract output and regret gate | CI gate |
| [plan_freshness.py](#plan_freshnesspy) | check PLAN freshness and PT-1 recency | CI gate / Git hook |
| [generate_failure_context.py](#generate_failure_contextpy) | write `FAILURE_CONTEXT.md` from failing gates | next-session prompt handoff |
| [state_generator.py](#state_generatorpy) | emit `.governance-state.yaml` | session bootstrap |
| [linear_integrator.py](#linear_integratorpy) | sync PLAN tasks to Linear | backlog sync |
| [notion_integrator.py](#notion_integratorpy) | sync PLAN tasks to Notion | backlog sync |

## CI Integration

GitHub Actions workflow:
- `.github/workflows/governance.yml`

Current CI gates:
- `plan-freshness`: hard fail on `CRITICAL` or `ERROR`
- `governance-unit-tests`: runs governance tool tests only
- `phase-gates`: executes `scripts/verify_phase_gates.sh`
- `memory-pressure`: advisory warning job
- `generated-artifact-pressure`: advisory report for `__pycache__` and render/audio caches
- on `phase-gates` failure, CI emits `FAILURE_CONTEXT.md` as an artifact using `--skip-contract`

---

## memory_janitor.py

Manages `memory/01_active_task.md` pressure and cleans disposable runtime artifacts.

Handled artifacts:
- Python `__pycache__`
- `output/render_cache`
- `output/audio_cache`
- `output/cache`
- `render_cache`

```bash
python governance_tools/memory_janitor.py --check
python governance_tools/memory_janitor.py --plan
python governance_tools/memory_janitor.py --execute
python governance_tools/memory_janitor.py --clean-generated --dry-run
python governance_tools/memory_janitor.py --clean-generated
```

Notes:
- `--execute` archives `memory/01_active_task.md` and also removes generated caches.
- `--clean-generated` only touches disposable artifacts; it does not modify memory files.
- never auto-run cleanup without human confirmation.

---

## contract_validator.py

Validates `[Governance Contract]` blocks and enforces the regret-distance fail gate.

```bash
python governance_tools/contract_validator.py --file response.md
python governance_tools/contract_validator.py --file response.md --balance-summary output/analytics/balance_summary.json
python governance_tools/contract_validator.py --format json < response.md
```

Fail condition:
- `avg_steps_from_regret_to_death < 0.5`

---

## plan_freshness.py

Checks `PLAN.md` freshness and whether completed PT-1 data is newer than the latest balance update.

```bash
python governance_tools/plan_freshness.py --file PLAN.md
python governance_tools/plan_freshness.py --file PLAN.md --pt1-dir playtests --balance-summary output/analytics/balance_summary.json
python governance_tools/plan_freshness.py --format json
```

Fail condition:
- completed PT-1 logs older than latest balance change => `CRITICAL`

---

## generate_failure_context.py

Builds a concise failure summary for the next AI session.

```bash
python governance_tools/generate_failure_context.py --response-file response.md
python governance_tools/generate_failure_context.py --skip-contract --output FAILURE_CONTEXT.md
```

Generated sections:
- overall gate status
- contract findings
- freshness findings
- next-session prompt bullets

---

## state_generator.py

Emits `.governance-state.yaml` from the root `PLAN.md` header.

---

## Integrators

`linear_integrator.py` and `notion_integrator.py` remain optional backlog sync tools. They do not override `PLAN.md` as the source of truth.
