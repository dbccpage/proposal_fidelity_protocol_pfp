> **Historical validation record.** This document reports the 2026-09-24
> recovery and its own pinned implementation, not execution of the 2026-09-27
> PFP paper series. Its aggregate counts and binary hashes have not been
> re-established by this manuscript rewrite. Use the current paper claim
> ledger and separately retained execution receipts for current evidence.


# Recovery validation

**Date:** 2026-09-24.

## Custody

The interrupted task was recovered from the [shared conversation](https://chatgpt.com/s/cx_6ab5540129448191bb7f3b0ccf293bab)
and its local task record. Its three requirements were the seven-question reviewer
response, Paper 003, and exclusive functional calculation in
`omega_engine/crates_rs/omega_functional/src`.

The draft and preceding repairs were preserved in
`07e9f187f4e3e19cb0bb0634f046555c52a9486d` on `codex/mub6-0924094100`.
Recovery uses the isolated `codex/complete-paper-003` branch. The shared checkout
was on another agent's MUB branch, with untracked Demo 6; it was not switched,
reset, or swept into this recovery. Historical traces, receipts, and stored
notebook outputs were not rewritten.

Validated implementation commit: `4c63d7765c05aed03f4946b5c15d7ae59d857058`.

The final source binding and executable hashes are in [validation.json](validation.json).
A binary digest binds the executed bytes, not an independent reproducible-build
attestation. These are local checks, not hosted CI or study results.

## Focused checks

| Check | Result |
| --- | --- |
| Canonical Rust functional library | 305 passed |
| Native wall-functional verifier | 6 passed |
| Education transport/boundary tests | 19 passed, including native smoke |
| Three-cycle education tests | 4 passed |
| Notebook governor tests | 5 passed; 8 unrelated tests deselected |
| Changed beginner/practitioner notebook cells | 3 replayed successfully; saved outputs untouched |
| Notebook 12 fixed-section scorer | Explicit native-adapter refusal observed |
| Python Symbol Game ownership | 9 passed |
| Python operations ownership | 5 passed |
| Python MUB ownership | 4 passed |
| Demo 3 historical replay | 16 passed |
| Demo 2 R1 | 10 passed |
| Demo 1 runner | 6 passed, including its nine scripted rounds and historical replay |
| Recovery refusal/transport/guard/trace regressions | 8 passed |
| Source-pattern ownership guard | PASS; no recognized off-owner producer pattern; exclusions reported |
| Clean architecture skill check | PASS for its implemented single-root check |
| Rust DDA / homology / lifts / runtime | 244 / 329 / 27 / 442 passed |
| Rust pharmacy | 25 passed |
| Rust L1 subgradient fracture regression | 1 passed; 128 unrelated tests filtered |
| Demo EIS-3 (12 mechanical failure classes) | 7 passed; 12/12 positive detected, 0/12 negative false alarms |

**Total:** 1,472 passing test cases across the focused checks above.

The R1 reviewer example was replayed with the corrected `run_demo2` import:
`TermAsserted`, one of sixteen entries, then `RefusedDuplicateAssertion`.
Native graph checks returned 3 on the unit triangle, 0 on an empty cycle, 3 for
a one-claim cycle, 6 for [1,2,3], and 0 for [1,-1,0].

Commands were scoped to individual files or Rust packages and run in small
sequential batches. The machine initially ran out of disk during a fresh Rust
build. Only this recovery's new target output was removed; the successful retry
used disabled debug information and incremental compilation. Python tests used
an installed repository virtual environment where pytest was required and the
bundled Python for standard-library tests. No model provider calls were made.

## Availability limits

The graph adapter requires a trusted locally built executable and its SHA-256
pin. See the education setup, `omega_engine_education/FUNCTIONAL_BOUNDARY.md` in the repository.
The generic Python DDC, Paper 001 primal-dual certificate, fixed-section
educational scorer, old LP speedup benchmark, AST functional proxies, and Woland
functional routes are explicitly unavailable until supported native adapters exist.
The old benchmark refuses because comparing two aliases of the same native solver
would manufacture an independent speedup comparison.

The full `omega_certifiers` library test target cannot compile because
`meron_certificate.rs:488` includes a missing Meron JSON fixture under
`research/published`. The include reference is identical in the recovered base.
This unrelated fixture was not fabricated or repinned. The separate native
functional verifier tests passed.

Some legacy Woland/Woland/operations imports depend on the already absent
`omega_engine.kernel` package. Their changed refusal paths were source-checked;
no end-to-end execution coverage is claimed for those imports. Existing tests
that require retired Python calculators are no longer valid availability checks.
A repository-wide test sweep was not run.

The ownership guard detects named assignments/returns and copied canonical types;
it does not prove arbitrary aliasing or whole-program semantics. Static expected
values and historical records remain distinct from live measurements.

## Study status

Paper III is a completed protocol and reviewer-response package. The controlled
Demo 3 live runner, learned detector bank, model-B held-out trial, and effect/safety
intervals remain future study work. The manifest remains `proposed_not_executed`.
No measured transfer result, publication, DOI, deposit, or fermion-sign conclusion
is asserted.
