# Parity & Seam Isolation Inspection Patterns

## 1. Anti-Slop Parity Architecture

When verifying parity across multi-language or multi-engine implementations (e.g. Rust vs Python, C# vs TypeScript):

1. **Independent Reference Implementation:**
   - Parity checks must compare the production candidate against an independently implemented reference algorithm or native binary execution.
   - Self-assignment copies and trivial mirrors that re-import the candidate module are strictly prohibited.

2. **Shared Golden Fixture Sets:**
   - Both implementations must execute against the exact same deterministic RFC 8785 JSON / binary golden vector banks.
   - Any float/integer precision deviation beyond declared tolerance ($\epsilon = 10^{-9}$) fails closed.

3. **FFI Seam Isolation:**
   - FFI bindings must reside in dedicated `ffi.py` or `ffi.rs` bridge modules.
   - Never scatter fictional fallback branches across production domain code.

---

## 2. Replay-Execution State Accumulator Parity (`RULE_REPLAY_STATE_PARITY_001`)

When auditing multi-stage evaluation pipelines that produce deterministic audit logs and support exact replay (e.g. `replay_episode`):

1. **Synchronous In-Memory & Storage State Parity:**
   - Intermediate stage outcomes, model responses, and host verification checks must update in-memory state accumulators (`prior`) synchronously with persistent storage commits.
2. **Replay Prompt Invertibility:**
   - Downstream prompt templates that interpolate prior stage outcomes must produce identical byte-level prompt strings whether rendered during live forward execution or during deserialized replay from storage.
   - Any deviation in intermediate dictionary keys between live execution and replay deserialization fails closed with typed hash divergence (`PROMPT_RECONSTRUCTION_CHANGED`).

