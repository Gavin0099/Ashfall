# Refactor Boundary Safety Rule Pack

- Refactoring must not introduce new boundary crossings without explicit architectural approval.
- Do not move logic across Domain / Application / Adapter / Infrastructure boundaries under the label of refactor.
- Interface or dependency changes must preserve existing ownership, lifecycle, and responsibility boundaries unless an ADR or explicit approval says otherwise.
- If a refactor reduces coupling, the resulting boundary should become clearer, not more implicit.
- When uncertain whether a change is structural or behavioral, escalate instead of silently widening scope.
