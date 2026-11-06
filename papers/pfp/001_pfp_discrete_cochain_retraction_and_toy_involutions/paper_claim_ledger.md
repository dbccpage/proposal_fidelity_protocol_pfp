# Paper 001 claim ledger

Author-review preprint, version 0.1.0, 2026-10-02. Code baseline cited by the
manuscript: c819bec432446dd3c9b1edf1583384cfe76c6c71.

"Prose proof" means the argument stated in the manuscript. A pytest node
reference (file and function) names an executable check in `code/tests/`; Rust
unit tests live in `../../../../../../engine/crates_rs/core_solvers/src/graph_phi1.rs`. Whether a check passed for
this revision is recorded by the dated review receipt, not by this ledger.

| ID | Claim and hypotheses | Evidence | Falsifier or boundary |
| --- | --- | --- | --- |
| PFP001-01 | Positive rational penalties on a finite graph give \(D_c(s)\geq\Phi(c)\), with \(\Phi=0\) exactly for \(c\in\operatorname{im}B\). | Prose proof, Section 2; `test_review_regressions.py::test_small_rational_cycles_against_independent_potential_grid`; `test_manuscript_witnesses.py::test_manuscript_triangle_costs_and_certificate` (exact reports give 0) | Zero penalties can conceal a residual. |
| PFP001-02 | Adding a coboundary to the reports leaves the quotient minimum invariant; a section update leaves it unchanged. | Substitution proof, Section 2; `test_zenodo_regression_suite.py::test_regression_3_cut_invariance_and_defect_descent` checks the section-update case only | Changing reports arbitrarily changes the problem. |
| PFP001-03 | Feasible primal and dual witnesses with equal values certify the optimum. | Direct weak-duality proof, Section 3; `test_review_regressions.py::test_degenerate_multicycle_dual_is_feasible`; `test_manuscript_witnesses.py::test_manuscript_triangle_costs_and_certificate` | Objective equality with an unbalanced or over-capacity dual is insufficient. |
| PFP001-04 | A directed cycle has minimum \(\min_e w_e\,\lvert\sum_e c_e\rvert\); the manuscript triangle costs 6 at zero, 3 at an optimum, and has dual value 3. | Constructive proof, Section 4; `test_manuscript_witnesses.py::test_manuscript_triangle_costs_and_certificate`; `test_manuscript_witnesses.py::test_demo1_replays_every_manuscript_witness`; Rust test `manuscript_triangle_minimum_is_three` | Positive penalties and the declared directed-cycle carrier are required. |
| PFP001-05 | Some optimal residual uses at most \(\lvert E\rvert-\operatorname{rank}B\) edges. | Basic-feasible-solution proof, Section 4; no executable check | This is an existence bound, not a bound on all minimizers or the optimal-face dimension. |
| PFP001-06 | A weighted null-space property on the residual support suffices for uniqueness. | Triangle-inequality proof, Section 4; no executable check | Failure of a sufficient condition is not a nonuniqueness certificate. |
| PFP001-07 | Strict rational descent alone does not imply finite termination. | Single-edge sequence \(D_t=2^{-t}\), Section 5; `test_manuscript_witnesses.py::test_rational_descent_exhausts_fuel_without_reaching_minimum` | Fuel bounds attempts only when each attempt returns or times out. |
| PFP001-08 | The native Rust solver enumerates spanning forests exactly, caps the search at 100,000 forests, refuses with `EnumerationLimit` beyond the cap, and returns `phi1`, `gauge`, and `forests_checked`. | [Rust source](../../../../../../engine/crates_rs/core_solvers/src/graph_phi1.rs); Rust tests `enumeration_limit_refuses_instead_of_returning_partial_minimum`, `rejects_unknown_endpoint_self_edge_and_bad_rational`, `kagome_trimer_multi_cycle_b1_4` | No dual circulation in its response; no polynomial-time claim; the Python adapter does not pin the binary. |
| PFP001-09 | The paper-local Python reference returns a primal potential and dual circulation only after independent verification, caps tree enumeration at 100,000 per component, and its governor admits only strictly decreasing potential updates. | [Reference source](code/symbol_game_governor.py); `test_zenodo_regression_suite.py::test_regression_2_triangle_phi_1_five`; `test_review_regressions.py::test_degenerate_multicycle_dual_is_feasible`; `test_governor.py::test_governor_monotonic_descent_and_rejection` | Exponential in graph size; the per-component cap is established by source inspection, not by a test. |
| PFP001-10 | Local Lean statements concern pair cancellation, a triangle sign gauge, and a policy type with one value. | [InvolutionLaws](lean4/InvolutionLaws.lean), [OddCycleObstruction](lean4/OddCycleObstruction.lean), [NonAuthority](lean4/NonAuthority.lean); `lake build` and the [axiom report](lean4/axiom_report.txt) | No general graph LP, runtime correctness, or physical theorem follows; the policy theorem holds by construction. |

## Current validation

The complete package test suite, code lint, Lean build, notebook execution, and
Rust cargo tests are recorded in
`docs/release_validation_2026_10_02_review_repairs.json`, which binds the
repaired adapter and governor by SHA-256. Follow-on targeted checks (Demo 1
string potentials, BQNF route aliases, and worksheet verification) are recorded
in `docs/release_validation_2026_10_02_continued_review.json`. Each receipt lists
its specific commands, tool versions, exit status, and tested scope. The
baseline commit cited above does not identify the repaired adapter and
governor; those file hashes are in the review-repairs receipt. The Rust unit
tests run with `cargo test -j 1`. The manuscript's Section 7 lists the
commands.

## Historical material

The retained results/ receipts and the earlier change-log entries concern
earlier revisions. The archived adversarial labels are not independent physical
ground truth. No recall, accuracy, speedup, model benefit, publication status,
or general fermion-sign result is asserted by this ledger.
