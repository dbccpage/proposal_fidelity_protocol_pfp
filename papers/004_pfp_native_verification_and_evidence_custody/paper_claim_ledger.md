# PFP IV claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Author-review preprint

Baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`. Repository paths are
relative to a checkout of that commit; the main paper links each one at the
pinned revision. The named native fixture values are source-derived assertions.
A historical author-run report records the September native tests. It is
distinct from the October 2 package-local validation. No fresh October native
run is claimed. The public evidence record in this deposit includes that
report and the audited source tar. Package paths (`code/`, `lean4/`, `docs/`)
are relative to this package.

| ID | Claim | Exact evidence | Status and limit |
| --- | --- | --- | --- |
| P4-01 | Default host, runtime dispatcher, and foundation library are distinct interfaces. | `omega_engine/crates_rs/omega_symbol_game/src/main.rs`, `lib.rs`, `invoke.rs`, `foundation.rs` | Source inventory; no global parity theorem |
| P4-02 | The restricted host binds a finite carrier and minimally encoded i128 wire inputs before exact rational solve and replay. | `src/host.rs`, `src/protocol.rs` in that crate | Source-inspected path |
| P4-03 | The four-vertex fixture expects gauge Phi1 = 7 and Gamma2 = 12, then final 0 and 0. | `tests/host_contract.rs::face_aware_coda_crosses_exact_host_but_global_admission_stays_refused`; hand check in paper Section 6 | Source-derived fixture assertion, hand-checked. The 2026-09-28 EDT report records a historical run of the native target that contains this test. The 2026-10-02 package receipt does not record a fresh native run. |
| P4-04 | The same expected outcome refuses admission for partial conformance and unsigned attestation. | Same test; `src/host.rs` emits exactly these two admission codes on the executed path | Source-inspected explicit refusal; no promotion |
| P4-05 | Rehashed carrier and candidate mutations do not bypass manifest or replay checks in named tests; an edited outcome fails its root check. | `tests/host_contract.rs` hostile-mutation cases and `a_locally_rehashed_outcome_is_not_a_fresh_replay` | Source-inspected finite cases; the unkeyed root authenticates nothing |
| P4-06 | The host has input and preallocation bounds; the timeout is validated metadata, not an internal watchdog. | `src/main.rs`, `src/protocol.rs`, `src/host.rs` | Interface-specific resource contract |
| P4-07 | Python uses the operating-system native seam and preserves the complete outcome. | `omega_engine_pfp/ffi.py` | Source-inspected adapter; authentication is separate |
| P4-08 | The graph tutorial adapter requires its own executable path and SHA-256 pin. | `omega_engine_providers/adapters/native_functional.py` | The adapter itself has no Python numerical fallback; see P4-15 for this package's governor |
| P4-09 | PacketCodec uses NFC plus tagged encoding and checks only payload digest and authority in `verify`. | `omega_engine_pfp/domain/packet_codec.py` | Source-inspected limitation; no RFC 8785 or full-envelope claim |
| P4-10 | PacketEnvelopeV2 binds a richer identity and freezes payload representation. | `omega_engine_pfp/domain/entities/packet_envelope.py` | Transport identity; deserialization is not a solver certificate |
| P4-11 | Legacy `run-turn`, `run-bout`, and `run` refuse before writing functionals. | `omega_engine_pfp/tests/test_functional_boundary.py` | Source-inspected retirement assertions |
| P4-12 | On a directed cycle the weighted minimum is the minimum penalty times the absolute cycle sum; claims (1,1,1) with penalties (1,2,2) project uniquely to (-2,1,1). | Proof in `docs/completion_supplement.md`; `test_weighted_cycle_supplement.py::test_cycle_minimum_matches_closed_form`, `test_weighted_cycle_supplement.py::test_first_row_projection_is_unique` | Rational cycle theorem and three table rows; not a general solver performance theorem |
| P4-13 | Digests and source stamps do not authenticate a producer or a build. | Protocol inputs and trust analysis in paper Sections 2 and 8 | Explicit security limitation |
| P4-14 | Foundation tests include shared packet vectors and finite extension and composition refusals. | `tests/foundation_contract.rs` | Example-level contract evidence; not arbitrary cross-language equivalence |
| P4-15 | Without a configured native executable, this package's governor computes the graph minimum by exact Python enumeration; with one, every native refusal or error propagates, and floating-point or Boolean edge weights are refused on both paths. | `code/l1_symbol_game_governor.py::compute_phi1`; `test_weighted_cycle_supplement.py::test_missing_native_pins_fall_back_to_python_enumeration`; `test_native_refusal_propagation.py::test_configured_native_failure_is_not_replaced`; `test_native_refusal_propagation.py::test_float_or_bool_weight_is_refused` | Describes current companion code, which differs from the baseline copy; enumeration results are not native evidence |
| P4-16 | The six package Lean modules build under the pinned toolchain, and the census lists the axioms of all 86 theorems. | `lean4/lakefile.lean`, `lean4/lean-toolchain`, `lean4/axiom_report.txt`, `tools/replay_lean_axiom_census.py --replay` | Legacy finite statements; none formalizes the native host or a receipt field |
| P4-17 | This package's governor refuses a relational CUT that omits a declared edge or gives a non-exact value (status `IncompleteProposal`, state unchanged); an omitted edge is not read as a zero claim. | `code/l1_symbol_game_governor.py::L1SymbolGameGovernor.step_cut`; `test_cut_completeness.py::test_cut_omitting_a_declared_edge_is_refused`, `test_cut_completeness.py::test_cut_with_a_non_exact_value_is_refused`, `test_cut_completeness.py::test_complete_explicit_proposal_is_still_scored` | Fix for review finding R008-04 in the companion code; accepting replaced claims still does not make them factually correct |
| P4-18 | A reader of this deposit can obtain the audited source and the retained native report without repository permissions. | `audited_source/pfp-iv-native-source-52cb5457.tar.gz`; `audited_source/SOURCE_MEMBERS.sha256`; `audited_source/REVISION.json`; `docs/historical_native_run/report_second_revision_2026-09-28.md` | The tar is commit `52cb5457f6c485ba548cfd292f6012a941ed22cf`, crate tree `75d77aa5e1f30dfc102f00c8f7cb6159418dec63`, 7875 files. The report is the native record: 12, 11, 32, and 9 passing tests, Rust 1.98.0, 2026-09-28 EDT. The two JSON files beside the report are the package pipeline and do not name the four Cargo targets. Raw Cargo stdout was not retained. This October repair did not execute Cargo. |

## Formal and empirical ceiling

No full matrix-level total-unimodularity Lean theorem, end-to-end
Python/Rust/Lean refinement, neural or model-internal result, general speedup,
authenticated deployment, or source-to-binary reproducibility result is claimed.
The historical benchmark receipts in `code/` and aggregate test counts from the
former manuscript are not results of this systems paper.

## 2026-10-23 harness extension

| Claim | Evidence | Limit |
| --- | --- | --- |
| New research mechanism | Paper 029 source manifest and focused checks | Implemented adaptation; historical evidence remains separately pinned |
| New model effects | Replayed campaign report | NOT_MEASURED; live campaign NOT_RUN |
| External AIDE2 findings | Versioned PDF and page-level source map | Attribution, not replication |
| Formal results above | Existing proofs and finite examples | No additional formal theorem or Lean claim |
