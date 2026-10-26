---
name: silent-failure-hunter
description: "Audit Python and Rust for swallowed exceptions, bare excepts and unhandled error fall-through (ROP Result purity)."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [code, quality, error-handling, rop, falsification]
---

# Silent Failure Hunter

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Inspection tool; emits ROP audit findings)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Silent Failure Hunter** diagnoses and eliminates silent failure modes across Python and Rust implementations. It enforces strict **Railway-Oriented Programming (ROP)** discipline: errors must never be swallowed or silently dropped, but must instead be converted into typed `Refusal` records within `Result[T, Refusal]` or explicit typed error enums.

---

## 2. Core Invariants

1. **Anti-Swallow Exception Discipline:**
   - Bare `except:` clauses that catch `BaseException` are forbidden.
   - Handlers catching exceptions with an empty body, `pass`, or `...` without re-raising or returning a typed `Refusal` are flagged as `ROP_SILENT_DROP`.
2. **ROP Monad Purity (`Result[T, Refusal]`):**
   - Every failure path must return an explicit `Err(Refusal(code=..., message=..., locus=...))`.
   - In Python, unvalidated `.unwrap()` invocations without prior `.is_ok` or match assertions are flagged.
3. **Rust Panic & Fall-Through Discipline:**
   - Production crates in `omega_engine/crates_rs/` must not use un-annotated `.unwrap()` or `.expect()`.
   - Every panic site must carry an explicit `// Invariant:` or `// Safety:` justification explaining why the state is mathematically guaranteed to be inhabited.
4. **Diagnostic Scanner Execution:**
   - Run the diagnostic scanner locally:
     ```bash
     py -3.12 -m omega_engine_operations.domain.cicd.silent_failure_scan <path>
     ```
   - Emits structured `SilentFailureFinding` records reporting the file, line, kind, and remediation guidance.

---

## 3. Claim Hygiene & Remediation

When reporting silent failure findings:
- State what code was scanned and what was not scanned.
- Distinguish between production source files and test doubles/mocks.
- Recommend explicit `Refusal` types matching the bounded context domain protocol.
