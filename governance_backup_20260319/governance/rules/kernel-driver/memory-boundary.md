# Kernel Driver Memory Boundary

Kernel-driver changes must treat user input, DMA buffers, and mapped memory as hostile boundaries rather than ordinary C/C++ data.

- Validate all buffer lengths, structure sizes, and pointer assumptions before dereferencing or copying.
- Do not trust user-mode buffers, IOCTL payloads, or externally supplied lengths without explicit validation.
- Any change touching DMA, MDLs, mapped views, or shared memory must preserve ownership, lifetime, and cleanup symmetry.
- Refactors must not hide or weaken checks that prevent use-after-free, double-free, stale mapping, or memory-corruption risks.
