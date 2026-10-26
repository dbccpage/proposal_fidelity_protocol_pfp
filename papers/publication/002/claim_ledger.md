# Paper 002 claim ledger

Author-review preprint, version 1.1.0, 2026-09-28. Code baseline cited
by the manuscript: c819bec432446dd3c9b1edf1583384cfe76c6c71.

"Proof" means the argument stated in the manuscript. A pytest node
reference (file, optional class, and function) names an executable check
in `code/tests/`. Whether a check passed for this revision is recorded
by the dated review receipt, not by this ledger.

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim             Evidence and hypotheses                                                                                                                                                                                                                                                      Boundary or
                                                                                                                                                                                                                                                                                                                   falsifier
  ----------------- ----------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------
  PFP002-01         A finite signed   Manuscript Section 2 proof;                                                                                                                                                                                                                                                  Fixed finite
                    graph admits a    [sign_graph.py](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/sign_graph.py);             graph, binary
                    vertex gauge iff  `test_manuscript_examples.py::test_all_positive_triangle_and_odd_self_loop_are_obstructions`; `test_native_sign_graph.py::test_native_or_py_classify_odd_triangle`; `test_sign_graph.py::SignGraphTests::test_odd_triangle_and_gaugeable_matrix_have_distinct_receipts`      parity, declared
                    every closed walk                                                                                                                                                                                                                                                                              vertex gauge
                    has even parity.                                                                                                                                                                                                                                                                               grammar.

  PFP002-02         Exact real        Section 3 entrywise proof; exact matrix adapter; `test_manuscript_examples.py::test_running_matrix_gauge_and_sign_change`; `test_sign_graph.py::SignGraphTests::test_exact_input_and_carrier_checks`                                                                         Does not cover
                    symmetric matrix                                                                                                                                                                                                                                                                               general local or
                    diagonal-sign                                                                                                                                                                                                                                                                                  global unitaries.
                    stoquasticity
                    reduces to that
                    graph.

  PFP002-03         A finite          Shift and power-series proof, Section 3; no executable check                                                                                                                                                                                                                 No sampling-time
                    stoquastic real                                                                                                                                                                                                                                                                                or variance
                    matrix has an                                                                                                                                                                                                                                                                                  guarantee.
                    entrywise
                    nonnegative
                    thermal
                    exponential for
                    nonnegative beta.

  PFP002-04         Enumeration       [frontier_search.py](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/frontier_search.py);   A truncated search
                    preserves an      `test_frontier_search.py::FrontierSearchTests::test_budget_unknown_retains_exact_untested_frontier_for_resume`; `test_frontier_search.py::FrontierSearchTests::test_resume_chain_covers_every_prior_index`;                                                                  is UNKNOWN; a
                    honest untested   `test_frontier_search.py::FrontierSearchTests::test_changed_or_malformed_frontier_is_refused`                                                                                                                                                                                skipped segment or
                    suffix and                                                                                                                                                                                                                                                                                     different graph
                    verifies prior                                                                                                                                                                                                                                                                                 invalidates
                    coverage.                                                                                                                                                                                                                                                                                      continuation.

  PFP002-05         Search order and  Fixed batches of eight and canonical result consumption; `test_frontier_search.py::FrontierSearchTests::test_parallel_schedule_does_not_change_selected_result_or_receipt`                                                                                                   No measured or
                    chosen witness do                                                                                                                                                                                                                                                                              promised multicore
                    not depend on                                                                                                                                                                                                                                                                                  speedup.
                    worker completion
                    order.

  PFP002-06         Retrieval matches PresentationIndex implementation; `test_frontier_search.py::FrontierSearchTests::test_index_separates_presentations_and_does_not_certify`; `test_frontier_search.py::FrontierSearchTests::test_changing_transformation_grammar_cannot_run_or_replay`                         A matching key is
                    the complete                                                                                                                                                                                                                                                                                   not proof of
                    declared                                                                                                                                                                                                                                                                                       physical adapter
                    presentation key.                                                                                                                                                                                                                                                                              correctness;
                                                                                                                                                                                                                                                                                                                   recheck every
                                                                                                                                                                                                                                                                                                                   candidate.

  PFP002-07         The introductory  Exact displayed matrix and endpoint equations; `test_manuscript_examples.py::test_running_matrix_gauge_and_sign_change`; `test_manuscript_examples.py::test_frontier_worked_trace_of_section_4`                                                                              All-positive
                    matrix accepts                                                                                                                                                                                                                                                                                 triangle is an
                    gauge 010; its                                                                                                                                                                                                                                                                                 odd-cycle
                    first two                                                                                                                                                                                                                                                                                      obstruction.
                    candidates fail,
                    so a budget of
                    two ends UNKNOWN
                    with interval
                    \[2, 8) and a
                    resumed budget of
                    one verifies 010
                    at index 2.

  PFP002-08         Equal-weight      Pairwise proof and the +2, −1, −1 counterexample, Section 5; no executable check                                                                                                                                                                                             Nonnegative total
                    cancellation                                                                                                                                                                                                                                                                                   weight alone does
                    requires a closed                                                                                                                                                                                                                                                                              not prove
                    involution,                                                                                                                                                                                                                                                                                    pairability.
                    opposite signs,
                    and equal
                    magnitudes.

  PFP002-09         At the specified  Section 6; [exact checker](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/exact_fock_gap.py);            Excludes
                    triangle Fock     `test_exact_fock_gap.py::test_exact_gap_covers_every_length_class`; `test_exact_fock_gap.py::test_alternating_bounds_nest_without_numeric_exponentials`; finite 192-path enumeration plus bounds for all other lengths                                                       individual rooted
                    parameters, the                                                                                                                                                                                                                                                                                integrated-path
                    target integrated                                                                                                                                                                                                                                                                              pairing only; not
                    path has no                                                                                                                                                                                                                                                                                    time-labelled
                    positive                                                                                                                                                                                                                                                                                       maps, regrouping,
                    equal-weight                                                                                                                                                                                                                                                                                   other
                    partner.                                                                                                                                                                                                                                                                                       representations,
                                                                                                                                                                                                                                                                                                                   or all sign
                                                                                                                                                                                                                                                                                                                   problems.

  PFP002-10         Checking and      2026-09-24 source repair in [provenance](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/PROVENANCE.md);  A hash of a
                    hashing use the   `test_frontier_search.py::FrontierSearchTests::test_one_shot_matrix_is_digested_and_checked_from_one_snapshot`                                                                                                                                                               consumed iterator
                    same snapshotted                                                                                                                                                                                                                                                                               can bind the wrong
                    matrix.                                                                                                                                                                                                                                                                                        object; an
                                                                                                                                                                                                                                                                                                                   immutable snapshot
                                                                                                                                                                                                                                                                                                                   is essential.

PFP002-11         A found native    [native_sign_graph.py](https://github.com/dbccpage/the_symbol_game/blob/c819bec432446dd3c9b1edf1583384cfe76c6c71/omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/code/native_sign_graph.py);             Package code
                    sign-graph        `test_native_refusals.py::test_native_refusal_is_not_replaced`; `test_native_refusals.py::test_malformed_native_output_is_not_replaced`                                                                                                                                      behavior; the
                    executable                                                                                                                                                                                                                                                                                     paper's statements
                    decides; its                                                                                                                                                                                                                                                                                   rest on the proofs
                    refusals and                                                                                                                                                                                                                                                                                   and the Python
                    malformed outputs                                                                                                                                                                                                                                                                              checkers
                    raise typed
                    errors and are
                    never replaced by
                    a Python answer.
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Evidence levels

The graph and pairing arguments are self-contained mathematical proofs.
The test files are executable checks of the stated finite facts. This
package contains no machine-checked formal proof. Retained historical
counts concern their dated source bytes.

The Fock statement is not pure finite enumeration: it combines a finite
three-hop enumeration with a proved bound for an unbounded family of
longer sequences. The source code's physical_sign_problem_classification
field is false.

## Reference checks

The Crossref records for Troyer and Wiese and for Klassen and Terhal
confirm authors, titles, journals, volumes, article numbers, and DOIs.
The Crossref record for Harary confirms author, title, year 1953,
journal, volume 2, issue 2, and DOI but gives no page numbers; the
publisher's landing page, reached through the DOI, gives pages 143--146.
No quotation or claim requiring the full text of any source is made. The
balance result is proved in full in the manuscript. No source is treated
as proof of this implementation.

## Current validation

The manuscript's Section 7 lists the commands. The dated review receipt
for this revision records each command, tool version, exit status, and
tested scope, including the skipped-frontier and one-shot-iterator
controls and the actual Fock checker. A successful run does not
establish a Hamiltonian-to-presentation adapter or a model-benefit
measurement.
