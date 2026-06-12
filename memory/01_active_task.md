# Current Task: Build-Driven Validation Slice

## Progress

- [x] Refresh Ashfall AI Governance adoption against the latest local `ai-governance-framework` checkout.
- [x] Add product contract for the build-driven wasteland RPG roguelite direction.
- [x] Lock first public validation target as Steam Demo, with PC/Web validation before iOS/iPad adaptation.
- [x] Add implementation contract for build-gating over the existing runtime.
- [x] Add P3 event specs for the deterministic five-event sequence.
- [x] Add P3 experiment event payloads under `experiments/build_driven_slice/events/`.
- [x] Add runtime support for compact requirements, visible locked options, locked text, flag setting, and flag consumption.
- [x] Update CLI path to pass run flags into option visibility and choice resolution.
- [x] Add build-driven contract and P3 payload tests.
- [x] Add P4 UI contract defining the build reactivity viewer.
- [x] Add static React prototype for the build reactivity viewer.
- [x] Make the build-driven viewer the default UI entry.
- [x] Translate the build-driven UI to Traditional Chinese.
- [x] Add local scene assets for clinic, checkpoint, and underground market states.
- [x] Connect the build-driven UI to P3 payloads through a `ChoiceView` adapter.
- [x] Add focused tests for the UI payload adapter.
- [x] Verify focused Python tests, Phase A validator, UI production build, browser desktop, and browser 390px checks.
- [x] Produce instrumented player/debug summaries for comparing the three builds.
- [x] Package the build-driven viewer into a Steam-demo-facing web prototype flow.
- [ ] Next: decide whether to add runtime-backed save/export logs or broaden the demo with one more build-reactive branch.

## Context

- Current product direction is **build-driven wasteland RPG roguelite**.
- The first public validation target is **Steam Demo**, but current development remains PC/Web-first.
- The validation sentence is: same events, different build, different story.
- P3 currently uses five deterministic events: `roadside_trap`, `locked_clinic`, `infection_checkpoint`, `underground_market`, and `vault_gate`.
- P4 UI is not a generic RPG dashboard. It is a build reactivity viewer that must show current build, opened options, locked temptations, consequences, flags, and ending attribution.

## Verification Notes

- `python -m pytest tests/test_build_driven_p3_payloads.py tests/test_build_driven_slice_contract.py tests/test_trait_flow.py`: 7 passed.
- `python scripts/validate_phase_a.py`: passed.
- `npm run build` in `ui/`: passed.
- Browser desktop check at `http://127.0.0.1:5174/`: Chinese build-driven viewer rendered with scene image and no old Base first screen.
- Browser 390px check: Chinese UI and scene image rendered without horizontal overflow.
- `python -m pytest tests/test_build_driven_ui_payload_adapter.py tests/test_build_driven_p3_payloads.py tests/test_build_driven_slice_contract.py tests/test_trait_flow.py`: 10 passed after P4-UI-C.
- P4-UI-D adds active-build `Machine Summary` plus a three-build `Instrumented Summary` comparison for `build_id`, opened options, locked options, triggered/consumed flags, and ending attribution.
- Steam demo-facing web prototype flow now lets a player choose a build, start the five-event run, click available choices, see locked temptations, reach an ending, and inspect the machine summary.
- Memory workflow check must be run from the framework path until Ashfall imports `governance_tools.memory_workflow` locally:
  `PYTHONPATH=E:\BackUp\Git_EE\ai-governance-framework python -X utf8 -m governance_tools.memory_workflow --check --repo . --run-guard --format json`
