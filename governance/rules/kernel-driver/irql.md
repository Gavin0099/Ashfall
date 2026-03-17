# Kernel Driver IRQL Boundary

Kernel-driver changes must declare and preserve the callable IRQL assumptions of every dispatch, callback, and cleanup path they modify.

- Do not perform pageable, blocking, or wait-based operations from contexts that may execute above `PASSIVE_LEVEL`.
- Do not assume a callback always runs at `PASSIVE_LEVEL`; the contract must state the required IRQL or explicitly defer work.
- Any refactor touching ISR, DPC, completion, work-item, or dispatch code must preserve the handoff between high-IRQL and passive-level work.
- If the task changes locking or callback flow, the review evidence must state why the resulting IRQL behavior remains safe.
