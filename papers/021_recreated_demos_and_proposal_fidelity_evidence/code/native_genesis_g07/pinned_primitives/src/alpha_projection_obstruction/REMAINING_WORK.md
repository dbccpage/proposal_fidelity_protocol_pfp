# alpha_projection_obstruction — status and remaining work

`AuthorityEffect: None.` Written 2026-09-06 at the moment of the first commit; corrected 2026-09-07 during review of PR #212.

## What is done

PO-000 v6.3 (`coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/`)
replicated in Rust inside the `ooutwire_primitives` crate, using only the crate's
own source — no external dependency, no NumPy, no symbolic engine.

- New derivative-assembly arithmetic, a source JSON cross-check, and a pinned
  receipt conformance CLI, with adversarial integration tests.
- `RECEIPT.txt`: 24 dispositions covering every one of the 51 ledger ids the
  Python package dispositions (A1–H9, `E4-second`, `E4-commutator`, `D8a`), plus
  `Prop-3B` (the §3.4 experiment, which the Python package runs but does not
  receipt) and `so_k_benchmark` (refused).
- Two claims the Python package leaves to Lean are **computed** here by exact
  linear algebra: H8 (Prop. 7.4.7-B coupled carrier: joint kernels nontrivial on
  both edges, All-Green forces `I = 0`, decided on a basis of `ker(O∘D) ⊆ ker D`
  over `C⁰ = R⁶`) and H9 (§7.4.12 quotient witness `Φ([ω]) = 2`, `ω ∉ im d₀`).
- Shared exact witness values in `evidence/000_mechanization_run.json` are
  compared after explicit JSON/text representation conversion (defect `[['2']]`, `raw_I 2`, bound `6`;
  `[['x**2'], ['0']]`, `[['2*x', '0'], ['0', '0']]`, `[['-2'], ['0'], ['0']]`;
  induced `[['2'], ['3']]`, repair `[['2']]`, separator `[['-1'], ['1']]`,
  pairing `1`, quotient distance `1`, dual witness `[['-1'], ['1']]`;
  `checked_points 9`; `D/T/D_hat = 4/2/1`; window `1/64`, floors `3/256`;
  transfer `2, 0, 2, -3`; three-patch `I 6`, `J {C1: 0, C2: 0, C3: 0}`,
  `Lambda 6`; `scaled_I [3, 14, 30]`; `combined_rank {e: 2}`; fragmentation
  `0` and `1`).  The floating-point witnesses agree with the Python values to
  the pinned tolerances (`observed_defect 0.00279503008110974` to 1e-11,
  `0.0201986400280886` to 1e-11, XX `0.957106781186547` to 1e-12, TFIM rates to
  1e-10, `g = 3.5`, `ν_e = 2`, `g = 1 / 101`).
- The L3 census (`census.rs`) now recurses into directory modules, so the new
  folder is inside it; `the_census_recurses_into_directory_modules` pins that.
- `cargo run --bin po000` prints the receipt; `PO000_WRITE_RECEIPT=1 cargo test`
  or `cargo run --bin po000 -- --write` regenerates `RECEIPT.txt`; the test
  `the_receipt_matches_the_committed_text_byte_for_byte` compares.

## Current disposition of the remaining items

1. **Clippy:** the crate is checked with all targets and warnings denied.
2. **Python correspondence:** the test compares all witness fields in 16
   shared rows and checks the 21-row source inventory. Five paper/prose/Lean
   rows are explicitly excluded from value comparison. Additional Rust
   witnesses are covered by their native tests, not this cross-check.
3. **Float determinism:** a second-machine byte replay remains OPEN. Numerical
   tolerances do not establish byte identity across machines.
4. **Appendix B assembly:** the valid-input Python arithmetic is ported in
   `derivative_bound.rs`, with refusal of invalid/overflowing inputs. It is
   floating-point arithmetic over supplied measurements. It proves no analytic
   bound and does not change the receipt's E4-second/E4-commutator refusals.
5. **Lean correspondence:** H8/H9 declaration names and quantifiers were read
   in the existing Lean source. Rust uses rational matrices; Lean ranges over
   real fibers. No new Lean proof or automated cross-language refinement proof
   is supplied by these comments.
6. **Independent verifier:** OPEN. The earlier claim of completion is
   withdrawn. `verify_po000` now explicitly checks conformance to its trusted,
   compiled-in reference. Missing, extra, reordered, and mutated lines fail.
   The producer's replay is a separate computation; neither is an independent
   proof checker for all 24 mathematical dispositions.
7. **Study-centre registration:** corrected [Note 23](../../../23_the_projection_obstruction_reading.md)
   and [README](../../../README.md) links describe the represented/quotient and
   evaluation/authorization distinctions.
8. **Arithmetic bounds:** `Rational` uses checked `i128`; overflow panics rather
   than wrapping. Surd comparison is depth-bounded at 12. Larger instances
   still need a wider arithmetic design.
9. **Census names:** directory-module recursion remains tested; test-only
   helpers still need correct qualified names in the exclusion inventory.
10. **Concurrent-checkout hazard:** active shared work remains vulnerable to
    unrelated cleanup. The historical incident in the original status note
    remains recoverable at commit `839d2dba`; review uses an isolated worktree.

The blanket “completed work” promotion in commit `462c8bbb` is withdrawn.
This update supplies bounded code and correspondence checks; unresolved
analytic, independent-verifier, and second-machine obligations remain open.
