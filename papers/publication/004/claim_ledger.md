# PFP IV claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Author-review preprint

Baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`. Repository paths
are relative to a checkout of that commit; the main paper links each one
at the pinned revision. The named native fixture values are
source-derived assertions. A historical author-run report records the
September native tests. It is distinct from the October 2 package-local
validation. No fresh October native run is claimed. The public evidence
record in this deposit includes that report and the audited source tar.
Package paths (`code/`, `lean4/`, `docs/`) are relative to this package.

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                   Exact evidence                                                                                     Status and limit
  ----------------- ----------------------- -------------------------------------------------------------------------------------------------- ---------------------------------------------
  P4-01             Default host, runtime   `omega_engine/crates_rs/omega_symbol_game/src/main.rs`, `lib.rs`, `invoke.rs`, `foundation.rs`     Source inventory; no global parity theorem
                    dispatcher, and
                    foundation library are
                    distinct interfaces.

  P4-02             The restricted host     `src/host.rs`, `src/protocol.rs` in that crate                                                     Source-inspected path
                    binds a finite carrier
                    and minimally encoded
                    i128 wire inputs before
                    exact rational solve
                    and replay.

  P4-03             The four-vertex fixture `tests/host_contract.rs::face_aware_coda_crosses_exact_host_but_global_admission_stays_refused`;   Source-derived fixture assertion,
                    expects gauge Phi1 = 7  hand check in paper Section 6                                                                      hand-checked. The 2026-09-28 EDT report
                    and Gamma2 = 12, then                                                                                                      records a historical run of the native target
                    final 0 and 0.                                                                                                             that contains this test. The 2026-10-02
                                                                                                                                               package receipt does not record a fresh
                                                                                                                                               native run.

  P4-04             The same expected       Same test; `src/host.rs` emits exactly these two admission codes on the executed path              Source-inspected explicit refusal; no
                    outcome refuses                                                                                                            promotion
                    admission for partial
                    conformance and
                    unsigned attestation.

  P4-05             Rehashed carrier and    `tests/host_contract.rs` hostile-mutation cases and                                                Source-inspected finite cases; the unkeyed
                    candidate mutations do  `a_locally_rehashed_outcome_is_not_a_fresh_replay`                                                 root authenticates nothing
                    not bypass manifest or
                    replay checks in named
                    tests; an edited
                    outcome fails its root
                    check.

  P4-06             The host has input and  `src/main.rs`, `src/protocol.rs`, `src/host.rs`                                                    Interface-specific resource contract
                    preallocation bounds;
                    the timeout is
                    validated metadata, not
                    an internal watchdog.

  P4-07             Python uses the         `omega_engine_pfp/ffi.py`                                                                  Source-inspected adapter; authentication is
                    operating-system native                                                                                                    separate
                    seam and preserves the
                    complete outcome.

  P4-08             The graph tutorial      `omega_engine_providers/adapters/native_functional.py`                                             The adapter itself has no Python numerical
                    adapter requires its                                                                                                       fallback; see P4-15 for this package's
                    own executable path and                                                                                                    governor
                    SHA-256 pin.

  P4-09             PacketCodec uses NFC    `omega_engine_pfp/domain/packet_codec.py`                                                  Source-inspected limitation; no RFC 8785 or
                    plus tagged encoding                                                                                                       full-envelope claim
                    and checks only payload
                    digest and authority in
                    `verify`.

  P4-10             PacketEnvelopeV2 binds  `omega_engine_pfp/domain/entities/packet_envelope.py`                                      Transport identity; deserialization is not a
                    a richer identity and                                                                                                      solver certificate
                    freezes payload
                    representation.

  P4-11             Legacy `run-turn`,      `omega_engine_pfp/tests/test_functional_boundary.py`                                       Source-inspected retirement assertions
                    `run-bout`, and `run`
                    refuse before writing
                    functionals.

  P4-12             On a directed cycle the Proof in `docs/completion_supplement.md`;                                                          Rational cycle theorem and three table rows;
                    weighted minimum is the `test_weighted_cycle_supplement.py::test_cycle_minimum_matches_closed_form`,                       not a general solver performance theorem
                    minimum penalty times   `test_weighted_cycle_supplement.py::test_first_row_projection_is_unique`
                    the absolute cycle sum;
                    claims (1,1,1) with
                    penalties (1,2,2)
                    project uniquely to
                    (-2,1,1).

  P4-13             Digests and source      Protocol inputs and trust analysis in paper Sections 2 and 8                                       Explicit security limitation
                    stamps do not
                    authenticate a producer
                    or a build.

  P4-14             Foundation tests        `tests/foundation_contract.rs`                                                                     Example-level contract evidence; not
                    include shared packet                                                                                                      arbitrary cross-language equivalence
                    vectors and finite
                    extension and
                    composition refusals.

  P4-15             Without a configured    `code/l1_symbol_game_governor.py::compute_phi1`;                                                   Describes current companion code, which
                    native executable, this `test_weighted_cycle_supplement.py::test_missing_native_pins_fall_back_to_python_enumeration`;     differs from the baseline copy; enumeration
                    package's governor      `test_native_refusal_propagation.py::test_configured_native_failure_is_not_replaced`;              results are not native evidence
                    computes the graph      `test_native_refusal_propagation.py::test_float_or_bool_weight_is_refused`
                    minimum by exact Python
                    enumeration; with one,
                    every native refusal or
                    error propagates, and
                    floating-point or
                    Boolean edge weights
                    are refused on both
                    paths.

  P4-16             The six package Lean    `lean4/lakefile.lean`, `lean4/lean-toolchain`, `lean4/axiom_report.txt`,                           Legacy finite statements; none formalizes the
                    modules build under the `tools/replay_lean_axiom_census.py --replay`                                                       native host or a receipt field
                    pinned toolchain, and
                    the census lists the
                    axioms of all 86
                    theorems.

  P4-17             This package's governor `code/l1_symbol_game_governor.py::L1SymbolGameGovernor.step_cut`;                                  Fix for review finding R008-04 in the
                    refuses a relational    `test_cut_completeness.py::test_cut_omitting_a_declared_edge_is_refused`,                          companion code; accepting replaced claims
                    CUT that omits a        `test_cut_completeness.py::test_cut_with_a_non_exact_value_is_refused`,                            still does not make them factually correct
                    declared edge or gives  `test_cut_completeness.py::test_complete_explicit_proposal_is_still_scored`
                    a non-exact value
                    (status
                    `IncompleteProposal`,
                    state unchanged); an
                    omitted edge is not
                    read as a zero claim.

P4-18             A reader of this        `audited_source/pfp-iv-native-source-52cb5457.tar`; `audited_source/SOURCE_MEMBERS.sha256`;        The tar is commit
                    deposit can obtain the  `audited_source/REVISION.json`; `docs/historical_native_run/report_second_revision_2026-09-28.md`  `52cb5457f6c485ba548cfd292f6012a941ed22cf`,
                    audited source and the                                                                                                     crate tree
                    retained native report                                                                                                     `75d77aa5e1f30dfc102f00c8f7cb6159418dec63`,
                    without repository                                                                                                         7875 files. The report is the native record:
                    permissions.                                                                                                               12, 11, 32, and 9 passing tests, Rust 1.98.0,
                                                                                                                                               2026-09-28 EDT. The two JSON files beside the
                                                                                                                                               report are the package pipeline and do not
                                                                                                                                               name the four Cargo targets. Raw Cargo stdout
                                                                                                                                               was not retained. This October repair did not
                                                                                                                                               execute Cargo.
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Formal and empirical ceiling

No full matrix-level total-unimodularity Lean theorem, end-to-end
Python/Rust/Lean refinement, neural or model-internal result, general
speedup, authenticated deployment, or source-to-binary reproducibility
result is claimed. The historical benchmark receipts in `code/` and
aggregate test counts from the former manuscript are not results of this
systems paper.
