# Paper 002 claim ledger

Initial author-review preprint, version 0.1.0, 2026-10-02. Repository snapshot
inspected for this review: e11c07ce90318309f058c8097ffd1c440a8ffb84.
The package manifests and
[current execution receipt](docs/preprint_review_validation_2026_10_02.json)
bind the revised sources. Earlier revision 1.1.0 remains historical.

"Proof" means the argument stated in the manuscript. A pytest node reference
(file, optional class, and function) names an executable check in
`code/tests/`. Whether a check passed for this revision is recorded by the
dated review receipt, not by this ledger.

| ID | Claim | Evidence and hypotheses | Boundary or falsifier |
| --- | --- | --- | --- |
| PFP002-01 | A finite signed graph admits a vertex gauge iff every closed walk has even parity. | Manuscript Section 2 proof; [sign_graph.py](code/genesis_alpha/sign_graph.py); `test_manuscript_examples.py::test_all_positive_triangle_and_odd_self_loop_are_obstructions`; `test_native_sign_graph.py::test_native_or_py_classify_odd_triangle`; `test_sign_graph.py::SignGraphTests::test_odd_triangle_and_gaugeable_matrix_have_distinct_receipts` | Fixed finite graph, binary parity, declared vertex gauge grammar. |
| PFP002-02 | Exact real symmetric matrix diagonal-sign stoquasticity reduces to that graph. | Section 3 entrywise proof; exact matrix adapter; `test_manuscript_examples.py::test_running_matrix_gauge_and_sign_change`; `test_sign_graph.py::SignGraphTests::test_exact_input_and_carrier_checks` | Does not cover general local or global unitaries. |
| PFP002-03 | A finite stoquastic real matrix has an entrywise nonnegative thermal exponential for nonnegative beta. | Shift and power-series proof, Section 3; no executable check | No sampling-time or variance guarantee. |
| PFP002-04 | Enumeration preserves an honest untested suffix and verifies prior coverage. | [frontier_search.py](code/genesis_alpha/frontier_search.py); `test_frontier_search.py::FrontierSearchTests::test_budget_unknown_retains_exact_untested_frontier_for_resume`; `test_frontier_search.py::FrontierSearchTests::test_resume_chain_covers_every_prior_index`; `test_frontier_search.py::FrontierSearchTests::test_changed_or_malformed_frontier_is_refused` | A truncated search is UNKNOWN; a skipped segment or different graph invalidates continuation. |
| PFP002-05 | Search order and chosen witness do not depend on worker completion order. | Fixed batches of eight and canonical result consumption; `test_frontier_search.py::FrontierSearchTests::test_parallel_schedule_does_not_change_selected_result_or_receipt` | No measured or promised multicore speedup. |
| PFP002-06 | Retrieval matches the complete declared presentation key. | PresentationIndex implementation; `test_frontier_search.py::FrontierSearchTests::test_index_separates_presentations_and_does_not_certify`; `test_frontier_search.py::FrontierSearchTests::test_changing_transformation_grammar_cannot_run_or_replay` | A matching key is not proof of physical adapter correctness; recheck every candidate. |
| PFP002-07 | The introductory matrix accepts gauge 010; its first two candidates fail, so a budget of two ends UNKNOWN with interval [2, 8) and a resumed budget of one verifies 010 at index 2. | Exact displayed matrix and endpoint equations; `test_manuscript_examples.py::test_running_matrix_gauge_and_sign_change`; `test_manuscript_examples.py::test_frontier_worked_trace_of_section_4` | All-positive triangle is an odd-cycle obstruction. |
| PFP002-08 | Equal-weight cancellation requires a closed involution, opposite signs, and equal magnitudes. | Pairwise proof and the +2, −1, −1 counterexample, Section 5; no executable check | Nonnegative total weight alone does not prove pairability. |
| PFP002-09 | At the specified triangle Fock parameters, the target integrated path has no positive equal-weight partner. | Section 6; [exact checker](code/exact_fock_gap.py); `test_exact_fock_gap.py::test_exact_gap_covers_every_length_class`; `test_exact_fock_gap.py::test_alternating_bounds_nest_without_numeric_exponentials`; finite 192-path enumeration plus bounds for all other lengths | Excludes individual rooted integrated-path pairing only; not time-labelled maps, regrouping, other representations, or all sign problems. |
| PFP002-10 | Checking and hashing use the same snapshotted matrix. | 2026-09-24 source repair in [provenance](code/PROVENANCE.md); `test_frontier_search.py::FrontierSearchTests::test_one_shot_matrix_is_digested_and_checked_from_one_snapshot` | A hash of a consumed iterator can bind the wrong object; an immutable snapshot is essential. |
| PFP002-11 | A found native sign-graph executable decides; its refusals and malformed outputs raise typed errors and are never replaced by a Python answer. | [native_sign_graph.py](code/native_sign_graph.py); `test_native_refusals.py::test_native_refusal_is_not_replaced`; `test_native_refusals.py::test_malformed_native_output_is_not_replaced` | Package code behavior; the paper's statements rest on the proofs and the Python checkers |
| PFP002-12 | The specified integrated rooted-path expansion converges absolutely. | Section 6: at most four outgoing hops per occupation state; at most \(64\cdot4^n\) sequences at length \(n\); each weight at most \(\beta^n/n!\); sum bounded by \(64e^{4\beta}\). | Applies to the specified finite triangle carrier and nonnegative beta; neither a total-tail bound of \(1/6144\) nor a sampling-efficiency claim. |

## Evidence levels

The graph and pairing arguments are self-contained mathematical proofs. The
test files are executable checks of the stated finite facts. This package
contains no machine-checked formal proof. Retained historical counts concern
their dated source bytes.

The Fock statement is not pure finite enumeration: it combines a finite
three-hop enumeration with a proved bound for an unbounded family of longer
sequences. The source code's physical_sign_problem_classification field is false.

The native transport also checks the shape and scalar types of gauge and walk
payloads before constructing witness objects. The parameterized regression
`test_native_refusals.py::test_malformed_native_witness_is_typed_and_not_replaced`
covers missing/null data, incorrect bit types, and malformed walk steps using
fixture executables. This verifies transport refusal behavior, not a build of
the optional Rust crate.

## Retained reference checks

The Crossref records for Troyer and Wiese and for Klassen and Terhal confirm
authors, titles, journals, volumes, article numbers, and DOIs. The Crossref
record for Harary confirms author, title, year 1953, journal, volume 2, issue
2, and DOI but gives no page numbers; the publisher's landing page, reached
through the DOI, gives pages 143–146. No quotation or claim requiring the full
text of any source is made. The balance result is proved in full in the
manuscript. No source is treated as proof of this implementation.

These bibliographic checks were recorded in the earlier author review. The
current preprint review distinguishes its accessible primary-source checks
from that retained evidence.

## Current validation

The manuscript's Section 7 lists the commands. The dated review receipt for
this revision records each command, tool version, exit status, and tested
scope, including the skipped-frontier and one-shot-iterator controls and the
actual Fock checker. A successful run does not establish a
Hamiltonian-to-presentation adapter or a model-benefit measurement.
