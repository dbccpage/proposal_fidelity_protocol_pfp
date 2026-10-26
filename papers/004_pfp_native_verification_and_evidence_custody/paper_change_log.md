# PFP IV change log

## 2026-10-03 — Zenodo deposit upload (v0.1.0 Preprint)

Recorded canonical Zenodo upload <https://zenodo.org/uploads/23114538> (DOI: `10.5281/zenodo.23114538`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — Review repairs before the v0.1 deposit

Current identity remains version 0.1.0, dated 2026-10-02. Version 2.8.0 remains
the internal revision of 2026-09-28.

- The native counts 12, 11, 32, and 9 are attributed to the author-run report
  of 2026-09-28 EDT (2026-09-29 UTC). This repair did not run Cargo. The report,
  the two pipeline receipts from that window, and a pax archive of the audited
  source at `52cb5457f6c485ba548cfd292f6012a941ed22cf` are included in the
  package. Raw Cargo standard output was not retained.
- The README now states the implemented governor rule: an unset
  `OMEGA_FUNCTIONAL_GRAPH_BIN` uses Python enumeration, and a configured native
  error or refusal propagates. `verify_deposit.py` checks the manifest and
  census. `tools/rebuild_release.py --check` checks the archive.
- The deposit description and claim-ledger title use 0.1.0 / 2026-10-02.
  Version 2.8.0 stays in the historical entries.
- The Landau companion is a student guide, an 18-question quiz, and a separate
  instructor key. It is a teaching draft, not a measured learning study.
- The unused pytest `asyncio_default_fixture_loop_scope` setting was removed.
  pytest-asyncio is not a dependency.
- The manuscript no longer links to the PFP I package path. The four-vertex
  calculation is restated in Section 6 and the study guide.

The current execution record is
`docs/release_validation_2026_10_02_review_repairs.json`. Earlier receipts keep
their dates.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-28 — Version 2.8.0: source check and package completion

Checked against the pinned sources:

- Checked the worked-example table (Section 6) and the resource limits
  (Section 7) against `tests/host_contract.rs`, `src/host.rs`, `src/protocol.rs`,
  `src/main.rs`, and `src/invoke.rs` at `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
  Every listed value agrees with the source. On the executed path the host emits
  exactly the two listed admission codes.
- Added a hand derivation of the intermediate values: the fixture's face
  circulations are 7 and 5, so Gamma2 = 12, and the unit-weight distance to
  vertex-potential differences is Phi1 = 7.

Manuscript changes:

- Section 6: narrowed the outcome-rehash sentence to what the named test checks.
- Section 7: stated the four dense-matrix fences and the timeout range; limited
  the "no silently substituted Python estimate" sentence to the engine paths.
- Section 8: described this package's six Lean modules and their axiom census
  in place of a reference to Lean sources elsewhere in the repository.
- Sections 9 and 10: added package-local commands and disclosed that the
  companion governor falls back to exact Python enumeration; added the standard
  nonclaim sentence.
- Replaced the verification section with a pointer to the dated review receipt.
  Both references now carry DOIs; the proof-carrying-code link now resolves to
  the paper instead of an author page.
- Adopted the series title block with version and date.

Package changes:

- Moved `completion_supplement.md` to `docs/` and corrected its statement that
  both legacy wrappers reach only the native calculator.
- Added `LICENSE` (CC BY 4.0), `LICENSE-CODE` (PolyForm Noncommercial 1.0.0),
  `zenodo_metadata.json`, `docs/descriptions.md`, `docs/references.md`,
  `verify_deposit.py`, `tools/rebuild_release.py`,
  `tools/replay_lean_axiom_census.py`, `scripts/regen_sha256sums.py`,
  `scripts/build_deposit_zip.py`, `code/deposit_paths.py`,
  `lean4/axiom_report.txt`, and the generated `lean4/Census.lean`.
- `pyproject.toml`: version 2.8.0, pinned ruff and pytest settings, optional
  `attention` dependencies, and no repository root on the test path. The Lean
  package version is also 2.8.0.
- Code: removed unused imports and variables and sorted imports; replaced one
  assigned lambda; added explicit `check=False` to two subprocess calls. The
  governor's repository-root bootstrap now adds only a directory that contains
  the provider package; its previous fallback raised `IndexError` on shallow
  extraction paths and could add an unrelated ancestor to the import path.
- The historical attention benchmark now imports `transformers` and `httpx`
  only when it runs, reads an API key only from the process environment instead
  of a fixed `.env` path outside the package, writes a re-run to a new file
  instead of over its retained receipt, and names the hosted model it actually
  queries. Its test skips with a stated reason when PyTorch or NumPy is absent,
  and its random case is seeded.
- Added `code/tests/test_weighted_cycle_supplement.py` for the supplement's
  table and the governor's no-pin path, and removed apparatus names from a few
  code comments.
- Ran the four native `omega_symbol_game` test targets on 2026-09-28 EDT
  (2026-09-29 UTC) against the crate, which is unchanged since the pinned base:
  12, 11, 32 and 9 tests passed. The report is copied under
  `docs/historical_native_run/`. The package
  folder was renamed from `004_pfp_three_layer_sovereignty_and_discrete_l1_projection`
  so that its dated release archive fits the Windows path limit.
- Removed the governor's blanket native fallback in `compute_phi1`. It called the
  native calculator and, if that call raised for any reason, substituted an exact
  Python enumeration, including for native input and search-bound refusals. It
  now calls the native calculator only when `OMEGA_FUNCTIONAL_GRAPH_BIN` is set
  and lets every native refusal or error propagate; otherwise it uses the exact
  enumeration. Both paths refuse floating-point or Boolean edge weights. New tests:
  `code/tests/test_native_refusal_propagation.py`.
- Fixed review finding R008-04 in `code/l1_symbol_game_governor.py`:
  `step_cut(proposed_claims=...)` scored omitted edges as zero claims, so an
  empty or partial proposal could reach Phi1 = 0 and be labelled `ExactRepair`.
  A relational CUT must now supply exactly one exact integer or fraction for
  every declared edge; otherwise it is refused with the new status
  `IncompleteProposal` and the governor state is unchanged. A complete proposal
  is scored as before. Added `code/tests/test_cut_completeness.py`; the same fix
  is applied to the copy vendored by Paper 005.

Withdrawn or narrowed:

- "A locally rehashed outcome does not become a fresh native replay" now states
  what the test checks: an edited outcome fails its root check, and a
  recomputed unkeyed root would show only internal consistency.
- The supplement's "delegate to the same native graph owner" is replaced by an
  account of the current fallback.
- The archived change log of the former manuscript is condensed into the table
  below. Its claims were already withdrawn; the verbatim text remains in the
  repository history.

## 2026-09-27 — Native verification and finite evidence

- Replaced the former broad theory manuscript with a standalone systems paper pinned to source base `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
- Separated the restricted native replay host, runtime dispatch, the graph-functional adapter, and the two packet codecs.
- Added a four-vertex schema-to-replay-to-refusal example. Its native outcomes are source-derived expectations, not newly executed results.
- Rewrote the claim ledger, README, and supplement. The supplement retains a complete bounded weighted-cycle argument rather than a claim of general sheaf gluing or host correctness.
- Corrected the Cargo workspace path to `omega_engine/crates_rs/Cargo.toml`. No new native build or test result is claimed.

## Earlier versions of the former manuscript

Before 2026-09-27 this package held a broader manuscript, then numbered Paper 032.
The verbatim change log of those versions is preserved in the repository at
commit `0a25c582fe347dca1aa9f79a6b34a109b8f15db9`, file
`omega_engine_atlas/coda_atlas/omega_engine_pfp/004_pfp_three_layer_sovereignty_and_discrete_l1_projection/paper_change_log.md`.
It records claims as they were made; retaining it does not certify them. The
manuscript claims listed there are withdrawn.

| Version | Date | What it added | Status now |
| --- | --- | --- | --- |
| 1.0.0 | 2026-09-04 | First manuscript: a three-layer host-verification proposal, a total-unimodularity argument for the discrete L1 problem, and a 50-row claim ledger | Replaced by the 2026-09-27 systems paper |
| 2.0.0 | 2026-09-11 | Merged earlier Paper 015 material; added the governor, identity-path, arity-rewrite, packet-firewall, and scaling modules, `TotalUnimodularity.lean`, and `IdentityTypes.lean` | Code and Lean retained as companion material; manuscript claims withdrawn |
| 2.1.0 | 2026-09-11 | `Topology50.lean` and an interactive proof governor with a benchmark receipt | Historical code and receipt; its rates are not results of this paper |
| 2.2.0 | 2026-09-11 | A token-sparsity benchmark on 50 tasks with a receipt | Historical; its figures are not results of this paper |
| 2.3.0 | 2026-09-11 | The attention-entropy and key-value-norm benchmark with a receipt | Historical and unrelated to this paper; see below |
| 2.4.0 | 2026-09-17 | A content-addressed repair log and a 100-trial chordal repair benchmark with a receipt | Historical code and receipt |
| 2.5.0 | 2026-09-17 | The weighted null-space and unique-landing module and `SparseLanding.lean` | Retained; its 3-cycle facts support the weighted-cycle note |
| 2.6.0 | 2026-09-17 | `SnTower.lean` and `SparseLandingGeneral.lean`; an 82-row ledger | Lean retained and now in the axiom census; ledger rows withdrawn |
| 2.7.0 | 2026-09-19 | Further sections on cellular sheaves, projection algebra, and a host transition automaton; an 85-row ledger | Withdrawn with the manuscript |

The 2.3.0 entry described a carrier-attention concentration gain and entropy and
memory reductions. The retained receipt (`code/attention_entropy_kv_norm_receipt.json`:
one prompt pair of different lengths on Qwen/Qwen2.5-0.5B-Instruct and one
hosted comparison on meta-llama/llama-3.1-8b-instruct, without an independent
check) records a larger carrier-attention mass under the structured prompt, but
higher, not lower, normalized attention entropy, key-value energy, and hosted
transition entropy. The reduction claims are withdrawn, and the single
concentration comparison supports no general conclusion.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 2.8.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.

## 2026-10-23 — author-review harness extension

Added a focused research extension linked to Paper 029. Separated implemented mechanisms, externally reported findings and unmeasured model effects. Preserved historical source pins, proofs, release archives and deposited identities. New renderings live in the dated author-review collection.

## Author-review package custody repair — 2026-10-23

Refreshed current draft manifests after manuscript revisions. Historical release
archives and deposited metadata were preserved. Author-review copies now carry
their own manifests and the ledger filename required by the existing verifier.
