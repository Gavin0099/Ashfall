# Task: Steam Release Preparation

## Goal

Prepare Ashfall for first Steam release (store-ready + build-ready + compliance-ready).

## Scope

- Steamworks setup
- Store page assets and metadata
- Build packaging and depot upload pipeline
- Release checklist and QA gate

## Task List

### SR-1 Steamworks Foundation
- [ ] Create Steam App and configure base app settings
- [ ] Configure branch strategy (`default`, `playtest`, `internal`)
- [ ] Define depots and platform targets

### SR-2 Store Presence
- [ ] Draft short description and full description
- [ ] Define tags, capsule art requirements, and screenshots plan
- [ ] Prepare trailer plan and launch announcement copy
- [ ] Add age rating/compliance review items

### SR-3 Build and Delivery
- [ ] Choose shipping runtime target and packaging format
- [ ] Add automated build output folder contract
- [ ] Add SteamCMD upload script template (dry-run first)
- [ ] Define versioning and changelog format for releases

### SR-4 QA and Release Gate
- [ ] Add release smoke test checklist
- [ ] Validate save/load compatibility for release candidate
- [ ] Validate crash reporting/log collection path
- [ ] Run go/no-go checklist before first public build

## Deliverables

- Steam release checklist document (v1)
- Initial Steam store draft content
- First internal Steam build uploaded to test branch

## Dependencies

- Phase B core loop playable
- Phase C combat-resource integration stable
- Minimal content set for screenshots/trailer capture
