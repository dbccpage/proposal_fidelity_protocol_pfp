# PFP V claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Publication-review candidate

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

This ledger replaces the earlier PO033 result taxonomy for the current guide.
Historical receipts and previous text remain attributable to their original
bytes through Git history. No old pass count is promoted to a fresh run. Test
references name files under `code/tests/`.

| ID | Claim | Evidence kind and source | Scope |
| --- | --- | --- | --- |
| G005-01 | Potential differences sum to zero on the directed triangle | Algebraic argument in guide Section 2; the printed worksheet run by `test_offline_worksheet.py::test_printed_worksheet_runs_and_matches_section_2` | Declared three-edge additive model |
| G005-02 | For claims (1,1,1) and weights (1,2,3), the weighted minimum is 3 | Explicit feasible potential and matching lower bound in Section 2; `test_offline_worksheet.py::test_lower_bound_is_attained_and_replacement_is_consistent` | This finite instance; no model measurement |
| G005-03 | Replacing claims by (-2,1,1) gives zero discrepancy | Direct equality with the displayed potential differences; same test as G005-02 | The claims have changed |
| G005-04 | The session refuses (5,0,0), admits (-2,1,1), and restores the prior snapshot | [Session](code/play_demo.py); `test_play_demo.py::test_worked_session_offline_enumeration` (Python enumeration path); `test_play_demo.py::test_worked_session_matches_manual` (native path, skips without pins) | Enumeration-path result in this package; native result needs a configured run |
| G005-05 | The package quickstart delegates the named minimum to the native adapter and rejects missing pins and non-exact inputs | [Quickstart](code/quickstart.py), [adapter copy](code/native_functional.py); `test_quickstart_native.py::test_quickstart_requires_native_pin`, `test_quickstart_native.py::test_approximate_or_boolean_input_is_rejected`, `test_quickstart_native.py::test_candidate_enumeration_is_retired`, `test_quickstart_native.py::test_projection_replays_native_and_is_idempotent` (native, skips without pins) | Native graph path, not every runtime surface |
| G005-06 | CUT permits non-increase, including stationary outcomes | [Governor copy](code/l1_symbol_game_governor.py), `step_cut` | Source-inspected; no arbitrary-search termination guarantee |
| G005-07 | Hashes bind declared bytes; current replay needs matching sources and inputs | Guide Section 6; [functional-boundary notes](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/FUNCTIONAL_BOUNDARY.md) at the baseline | No unsigned producer authentication or semantic proof |
| G005-08 | Domain labels and hypothetical chat costs are illustrative | [Scenario implementation](code/multi_domain_symbol_game_bouts.py) | No domain theorem or measured LLM comparison |
| G005-09 | The native-test fixture consumes caller pins and skips only its dependent tests, with a stated reason, when configuration is absent | [Fixture](code/tests/conftest.py) and tests explicitly requesting `native_functional` | No build, automatic pin, or source-to-binary attestation |
| G005-10 | The Python companion runs without the repository and records provenance for its copied adapter and governor | Vendored headers; `test_vendored_sources.py`; direct recorded-source comparisons in the fresh review | Unpatched AST structure compared; documented `compute_phi1`, `step_assert`, `step_cut`, and `step_verify` patches excluded and tested behaviorally; native binary separately required |
| G005-11 | The governor copy uses a configured native calculator and propagates its refusals; without one it computes the value by exact Python enumeration; floating-point or Boolean edge weights are refused | `code/l1_symbol_game_governor.py::compute_phi1`; `test_native_refusal_propagation.py::test_configured_native_failure_is_not_replaced`; `test_native_refusal_propagation.py::test_enumeration_path_without_native_configuration`; `test_vendored_sources.py::test_vendored_compute_phi1_has_no_exception_handler` | Describes the patched copy; enumeration results are not native results |
| G005-12 | A relational CUT that omits a declared edge or gives a non-exact value is refused with `IncompleteProposal` and leaves the state unchanged; a complete exact proposal is scored as before | Documented local change in `code/l1_symbol_game_governor.py` (`step_cut`); `test_cut_completeness.py::test_cut_omitting_a_declared_edge_is_refused`, `test_cut_completeness.py::test_cut_with_a_non_exact_value_is_refused`, `test_cut_completeness.py::test_complete_explicit_proposal_is_still_scored`, `test_vendored_sources.py::test_vendored_step_cut_carries_the_completeness_check` | Fix for review finding R008-04; acceptance still does not make replaced claims factually correct |
| G005-13 | The streaming harness refuses float and Boolean claim values and scores integers and exact rational strings | [Harness](code/llm_streaming_harness.py); `test_harness_exact_inputs.py::test_float_or_bool_claim_value_is_refused`; `test_harness_exact_inputs.py::test_exact_values_are_scored` | Governor Python path; no live provider run |
| G005-14 | Offline scoring refuses undeclared claim edges and duplicate carrier entries; supported Edge keys are normalized before scoring | `test_manual_contracts.py::test_offline_scoring_refuses_undeclared_claims`, `test_edge_object_keys_are_scored_after_normalization`, `test_scoring_refuses_duplicate_carrier_entries` | Patched `compute_phi1`; no claim silently discarded |
| G005-15 | ASSERT and section CUT refuse non-exact values; section CUT refuses unknown vertices and a CUT cannot silently choose one of two supplied payloads | `test_manual_contracts.py::test_non_exact_assertion_is_refused_without_state_change`, `test_section_cut_validates_values_and_carrier`, `test_cut_cannot_silently_ignore_a_second_payload` | Active claims, section, and admitted history preserved; attempt counter may advance |
| G005-16 | EDGE_MATCH requires a declared edge, and local equality does not discharge a global obstruction | `test_manual_contracts.py::test_edge_verification_refuses_undeclared_or_malformed_edge`, `test_matching_one_declared_edge_does_not_discharge_global_obstruction`, `test_zero_obstruction_and_zero_current_defect_are_distinct` | Specific governor obligations; no semantic or whole-domain verification |
| G005-17 | A projection error after candidate scoring restores pre-CUT claims and propagates instead of partially committing a replacement | `test_manual_contracts.py::test_native_projection_error_preserves_pre_cut_state` | Mocked configured adapter failure; not a Rust execution |
| G005-18 | Stationary score need not mean unchanged claims; the capstone refuses invalid replacements, descends 3 to 2 to 0, and restores the saved minimum 3 | `test_manual_contracts.py::test_stationary_score_can_accompany_changed_claims`, `test_capstone_refusals_repairs_and_snapshot_restore`; `code/study_capstone.py` | Exact Python session in current review; path disclosed in transcript |
| G005-19 | The educational companion has 32 questions in eight levels, worked answers, and a local grading rubric | Quiz and study guide; capstone implementation and test | Instructional design only; no validated learner-performance measure; UNKNOWN budget policy explicitly separate from governor implementation |

## Native execution scope

Tests that request the `native_functional` fixture need configured pins; without
them they skip and state that reason. No skipped case counts as a successful
native execution. The current publication review runs offline and records its
actual checks in `docs/publication_review_2026_10_02.json`; a configured adapter
error is mocked only to check propagation and rollback. Earlier author-review
history reports a Windows `solve_graph_phi1` run with SHA-256
`2b0379557993246cacb1ed8964f9f096964019ecc1c2fb781e6b18f2ca6c8a65` and 75 passes.
That concerns earlier bytes, not this patched package. The executable is not
deposited; a current native claim requires a fresh pinned replay.

Four cases in [the adversarial module](code/tests/test_adversarial_challenges.py),
class `TestQuickstartAdversarialMath`, also recompute the projected cochain's
defect with the Python helper `evaluate_defect` after the native projection:

- `test_disconnected_graph_projection_and_idempotence`
- `test_dense_multi_cycle_theta_graph`
- `test_dense_multi_cycle_complete_graph_k4`
- `test_opposing_edges_two_cycle`

That helper is a working Python function in `code/quickstart.py`, not a retired
one, as an earlier version of this ledger said. The recomputation checks that the
returned potential and projection agree; it is not a second native calculation.

## Claim hygiene

**Supports:** an operator route with explicit finite arithmetic, implementation
links, expected refusals, reproducible commands, and a package that runs without
the repository.

**Does not support:** general problem solvability, external truth of repaired
claims, a live-model effect, publication acceptance, fresh native success
inferred from saved receipts, or native provenance for values printed by the
governor copy.

**Narrowest defensible claim:** the stated triangle has the displayed lower
bound and consistent replacement; the package checks the session table on its
Python enumeration path and supplies a native-backed route for a configured run.

**Next check:** run the Section 6 commands with pins for a native executable
built from the reviewed source, preserving the actual outputs and refusals.

## 2026-10-23 harness extension

| Claim | Evidence | Limit |
| --- | --- | --- |
| New research mechanism | Paper 029 source manifest and focused checks | Implemented adaptation; historical evidence remains separately pinned |
| New model effects | Replayed campaign report | NOT_MEASURED; live campaign NOT_RUN |
| External AIDE2 findings | Versioned PDF and page-level source map | Attribution, not replication |
| Formal results above | Existing proofs and finite examples | No additional formal theorem or Lean claim |
