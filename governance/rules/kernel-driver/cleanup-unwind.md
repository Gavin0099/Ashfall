# Kernel Driver Cleanup And Unwind

Kernel-driver code must preserve symmetric unwind behavior for partial initialization, failure paths, unload, remove, and cancel flows.

- If initialization succeeds only partway, the failure path must release every resource already acquired.
- Unload, device-remove, surprise-remove, and cancel paths must be treated as first-class behaviors, not best-effort cleanup.
- Refactors must preserve rollback order, object ownership, and lock-release symmetry.
- Review evidence should state how halfway failure, cleanup, and teardown remain safe after the change.
