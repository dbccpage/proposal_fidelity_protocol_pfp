# PFP V claim ledger

Jeremy H. Carroll · 2026-09-28 · Version 1.2.0 · Author-review preprint

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

This ledger replaces the earlier PO033 result taxonomy for the current
guide. Historical receipts and previous text remain attributable to
their original bytes through Git history. No old pass count is promoted
to a fresh run. Test references name files under `code/tests/`.

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                  Evidence kind and source                                                                                                                                                                                                                                  Scope
  ----------------- ---------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------
  G005-01           Potential differences  Algebraic argument in guide Section 2; the printed worksheet run by `test_offline_worksheet.py::test_printed_worksheet_runs_and_matches_section_2`                                                                                                        Declared three-edge
                    sum to zero on the                                                                                                                                                                                                                                                               additive model
                    directed triangle

  G005-02           For claims (1,1,1) and Explicit feasible potential and matching lower bound in Section 2; `test_offline_worksheet.py::test_lower_bound_is_attained_and_replacement_is_consistent`                                                                                                This finite
                    weights (1,2,3), the                                                                                                                                                                                                                                                             instance; no model
                    weighted minimum is 3                                                                                                                                                                                                                                                            measurement

  G005-03           Replacing claims by    Direct equality with the displayed potential differences; same test as G005-02                                                                                                                                                                            The claims have
                    (-2,1,1) gives zero                                                                                                                                                                                                                                                              changed
                    discrepancy

  G005-04           The session refuses    [Session](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/play_demo.py);                             Enumeration-path
                    (5,0,0), admits        `test_play_demo.py::test_worked_session_offline_enumeration` (Python enumeration path); `test_play_demo.py::test_worked_session_matches_manual` (native path, skips without pins)                                                                         result in this
                    (-2,1,1), and restores                                                                                                                                                                                                                                                           package; native
                    the prior snapshot                                                                                                                                                                                                                                                               result needs a
                                                                                                                                                                                                                                                                                                     configured run

  G005-05           The package quickstart [Quickstart](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/quickstart.py), [adapter                Native graph path,
                    delegates the named    copy](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/native_functional.py);                         not every runtime
                    minimum to the native  `test_quickstart_native.py::test_quickstart_requires_native_pin`, `test_quickstart_native.py::test_approximate_or_boolean_input_is_rejected`, `test_quickstart_native.py::test_candidate_enumeration_is_retired`,                                         surface
                    adapter and rejects    `test_quickstart_native.py::test_projection_replays_native_and_is_idempotent` (native, skips without pins)
                    missing pins and
                    non-exact inputs

  G005-06           CUT permits            [Governor copy](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py),         Source-inspected;
                    non-increase,          `step_cut`                                                                                                                                                                                                                                                no arbitrary-search
                    including stationary                                                                                                                                                                                                                                                             termination
                    outcomes                                                                                                                                                                                                                                                                         guarantee

  G005-07           Hashes bind declared   Guide Section 6; [functional-boundary notes](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/FUNCTIONAL_BOUNDARY.md) at the baseline                                                     No unsigned
                    bytes; current replay                                                                                                                                                                                                                                                            producer
                    needs matching sources                                                                                                                                                                                                                                                           authentication or
                    and inputs                                                                                                                                                                                                                                                                       semantic proof

  G005-08           Domain labels and      [Scenario                                                                                                                                                                                                                                                 No domain theorem
                    hypothetical chat      implementation](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/multi_domain_symbol_game_bouts.py)   or measured LLM
                    costs are illustrative                                                                                                                                                                                                                                                           comparison

  G005-09           The native-test        [Fixture](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/tests/conftest.py) and tests explicitly    No build, automatic
                    fixture consumes       requesting `native_functional`                                                                                                                                                                                                                            pin, or
                    caller pins and skips                                                                                                                                                                                                                                                            source-to-binary
                    only its dependent                                                                                                                                                                                                                                                               attestation
                    tests, with a stated
                    reason, when
                    configuration is
                    absent

  G005-10           The package runs       Vendored file headers; `test_vendored_sources.py::test_vendored_header_is_complete`; `test_vendored_sources.py::test_vendored_copy_matches_recorded_source` (compares with Git objects inside a repository checkout, apart from the documented `step_cut` Custody of copied
                    without the            change; skips elsewhere)                                                                                                                                                                                                                                  bytes; not a native
                    repository: it carries                                                                                                                                                                                                                                                           build attestation
                    copies of the native
                    adapter and the graph
                    governor with source
                    path, commit, SHA-256,
                    and local changes
                    recorded

  G005-11           The governor copy uses `code/l1_symbol_game_governor.py::compute_phi1`; `test_native_refusal_propagation.py::test_configured_native_failure_is_not_replaced`; `test_native_refusal_propagation.py::test_enumeration_path_without_native_configuration`;                          Describes the
                    a configured native    `test_vendored_sources.py::test_vendored_compute_phi1_has_no_exception_handler`                                                                                                                                                                           patched copy;
                    calculator and                                                                                                                                                                                                                                                                   enumeration results
                    propagates its                                                                                                                                                                                                                                                                   are not native
                    refusals; without one                                                                                                                                                                                                                                                            results
                    it computes the value
                    by exact Python
                    enumeration;
                    floating-point or
                    Boolean edge weights
                    are refused

  G005-12           A relational CUT that  Documented local change in `code/l1_symbol_game_governor.py` (`step_cut`); `test_cut_completeness.py::test_cut_omitting_a_declared_edge_is_refused`, `test_cut_completeness.py::test_cut_with_a_non_exact_value_is_refused`,                              Fix for review
                    omits a declared edge  `test_cut_completeness.py::test_complete_explicit_proposal_is_still_scored`, `test_vendored_sources.py::test_vendored_step_cut_carries_the_completeness_check`                                                                                            finding R008-04;
                    or gives a non-exact                                                                                                                                                                                                                                                             acceptance still
                    value is refused with                                                                                                                                                                                                                                                            does not make
                    `IncompleteProposal`                                                                                                                                                                                                                                                             replaced claims
                    and leaves the state                                                                                                                                                                                                                                                             factually correct
                    unchanged; a complete
                    exact proposal is
                    scored as before

G005-13           The streaming harness  [Harness](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/llm_streaming_harness.py);                 Governor Python
                    refuses float and      `test_harness_exact_inputs.py::test_float_or_bool_claim_value_is_refused`; `test_harness_exact_inputs.py::test_exact_values_are_scored`                                                                                                                   path; no live
                    Boolean claim values                                                                                                                                                                                                                                                             provider run
                    and scores integers
                    and exact rational
                    strings
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Native execution scope

Tests that request the `native_functional` fixture need configured pins;
without them they skip and state that reason. No skipped case counts as
a successful native execution. For this revision the package tests were
run once with a pinned `solve_graph_phi1` built from the unchanged
`core_functional` source (SHA-256
`2b0379557993246cacb1ed8964f9f096964019ecc1c2fb781e6b18f2ca6c8a65`, a
Windows build): 75 passed, none skipped. The executable is not
deposited; another reader must build and pin their own.

Four cases in [the adversarial
module](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/code/tests/test_adversarial_challenges.py),
class `TestQuickstartAdversarialMath`, also recompute the projected
cochain's defect with the Python helper `evaluate_defect` after the
native projection:

- `test_disconnected_graph_projection_and_idempotence`
- `test_dense_multi_cycle_theta_graph`
- `test_dense_multi_cycle_complete_graph_k4`
- `test_opposing_edges_two_cycle`

That helper is a working Python function in `code/quickstart.py`, not a
retired one, as an earlier version of this ledger said. The
recomputation checks that the returned potential and projection agree;
it is not a second native calculation.

## Claim hygiene

**Supports:** an operator route with explicit finite arithmetic,
implementation links, expected refusals, reproducible commands, and a
package that runs without the repository.

**Does not support:** general problem solvability, external truth of
repaired claims, a live-model effect, publication acceptance, fresh
native success inferred from saved receipts, or native provenance for
values printed by the governor copy.

**Narrowest defensible claim:** the stated triangle has the displayed
lower bound and consistent replacement; the package checks the session
table on its Python enumeration path and supplies a native-backed route
for a configured run.

**Next check:** run the Section 6 commands with pins for a native
executable built from the reviewed source, preserving the actual outputs
and refusals.
