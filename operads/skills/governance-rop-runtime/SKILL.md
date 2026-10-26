---
name: governance-rop-runtime
description: "Gate for Railway-Oriented Programming Result strictness, probe/defect firewall and atomic trace ledgers."
operad_source_colours: ["State", "Code"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, rop-runtime]
---

# governance-rop-runtime

AuthorityEffect: None.

## The single rule

> Runtime domain operations must propagate typed Result monad containers rather than throwing naked exceptions or silencing errors, and probe errors must be strictly firewalled from computational object defects.

## Consolidated Invariants

1. **ROP Result Monad Strictness**: Eliminate naked exceptions, silent `pass`, or `sys.exit` in domain logic in favor of explicit `Result.ok(...)` and `Result.err(...)` ledgers (`goo-operad-rop-result-monad-gate`, `goo-woland-rop-monad-strictness`).
2. **Apparatus Probe vs Defect Firewall**: A malformed apparatus probe must raise an apparatus exception rather than corrupting semantic state trichotomies as computational STUCK states (`goo-probe-defect-firewall`, `goo-simulation-probe-error-defect-firewall`).
3. **Atomic Trace Ledger Concurrency**: Evidence traces must use thread lock synchronization and atomic file staging (`.tmp` + `os.replace`) to prevent trace corruption during multi-agent execution (`goo-atomic-trace-ledger-concurrency-guard`).
4. **Receipt Replayability & Value Object Equality**: Receipts must match producer hashes recorded at generation, and value objects must implement symmetric `__eq__` and `__hash__` across primitive types and Enums (`goo-receipt-replayability-gate`, `goo-polymorphic-value-object-equality-guard`).
5. **Create-Only Ledger Persistence (`open("xb")`)**: Content-addressed event stores and ledgers must persist via exclusive file creation (`open(target, "xb")`) rather than existence checks followed by truncating writes. A `FileExistsError` must verify byte-level identity: identical payloads succeed idempotently; divergent payloads under an existing identifier must return a typed `LEDGER_CONFLICT` refusal without modifying the file.
6. **Fail-Closed Probe Selection Before I/O**: When an examination or audit apparatus resolves an empty probe tuple (by default or via caller specification `probes=()`), it must immediately return a typed refusal (`NO_APPLICABLE_PROBES`) before reading subject contents from disk or appending events to any ledger.

## Verification Requirements

Run the ROP monad and runtime defect firewall check:

```bash
python omega_engine_operads/skills/governance-rop-runtime/scripts/check_rop_runtime.py
```
