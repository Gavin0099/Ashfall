# Refactor Behavior Lock Rule Pack

- Refactoring is allowed only when observable behavior remains unchanged.
- Tests must lock expected behavior, not just implementation details.
- Green tests after refactoring are evidence only when they include regression, boundary, and failure-path coverage.
- If behavior is intentionally changed, the task is no longer pure refactor and must be treated as a feature or behavior change.
- Do not justify risky refactors with readability alone when behavior has not been locked first.
