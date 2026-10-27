# PFP V editorial history

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114578> (DOI: `10.5281/zenodo.23114578`, Concept DOI: `10.5281/zenodo.23114577`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — v0.1 publication review and expanded examination

Reviewed the package at repository snapshot `e11c07ce90318309f058c8097ffd1c440a8ffb84`.
Version 0.1.0 remains the initial preprint candidate designation.

- Corrected the README, deposit description, metadata description, and claim ledger's stale internal revision and native-fallback wording.
- Added an abstract, explicit rational and cell declarations, a current-score versus minimum table, and explanations of gauge freedom, stationary replacements, scoped verification, and rollback evidence.
- Aligned play_demo with weights (1,2,3); the worked session and new study capstone print and return their selected calculator path.
- Fixed offline `compute_phi1` silently dropping undeclared claims or supported Edge object keys; added carrier uniqueness checks and used normalized claims on both routes.
- Fixed Boolean and floating-point ASSERT/section-CUT admission, undeclared section keys, and ambiguous two-payload CUTs.
- Fixed EDGE_MATCH verification of absent or malformed edges against default zeros.
- Fixed partial state mutation when configured native projection raises after replacement scoring; the old claims are restored before the exception propagates.
- Recorded these local patches in the vendored header and custody-test exclusions; added behavioral regression tests rather than asserting unchanged vendored bytes.
- Expanded the Examiner quiz from five to 32 questions in Levels 0-7, with worked solutions, an exact lower-bound witness, refusal cases, a local rubric, and an executable capstone. The budget/UNKNOWN exercise is explicitly a policy example, not an implemented governor state.
- Removed an unused pytest-asyncio setting that warned in this synchronous suite without the undeclared plugin.
- Preserved earlier execution records; added a fresh review and scoped execution record. Historical Windows native passes are not current evidence. This review records native execution as unavailable.
- Regenerated the LaTeX, inspected PDF, checksums, and deterministic ZIP after source corrections.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-28 — Version 1.2.0: self-contained package

Version 1.1.0 was last used by the former PO-033 manual (2026-09-19); the
2026-09-27 rewrite carried no version, so this revision is 1.2.0.

Manuscript and documents:

- Retitled as "PFP V: A Practitioner's Guide to Checked Proposals" in the series
  title block, with version and date. The manuscript and its companions were
  renamed to `paper.md`, `paper_claim_ledger.md`, and `paper_change_log.md`.
- Section 3: replaced "The companion imports repository provider modules and the
  sibling 004 governor; copying only this paper directory is insufficient" with a
  description of the two vendored modules and their provenance headers.
- Section 3: removed the link to an internal agent instruction file and the
  platform policy sentence built on it; the build note now gives the
  `cargo build --locked -j 1` command for any platform.
- Sections 3 and 6: commands now run from the package directory; the repository
  setup notes are linked at the pinned baseline, and the transport link points
  to the package's adapter copy.
- Section 4: disclosed that the governor copy computes a Python enumeration
  value when the native call raises and does not report which path ran; the
  session table is now checked by a package test on that path.
- Section 7: noted that the streaming harness accepts JSON floats and Booleans
  as exact rationals instead of refusing them.
- Added Section 9 (Limitations) with the standard nonclaim sentence, replaced the
  verification section with a pointer to the dated review receipt, and gave the
  references DOIs.
- Claim ledger: bound each executable claim to a named test, added rows for the
  vendored copies and the fallback, and corrected the statement that four
  adversarial cases call a "retired" `evaluate_defect` helper: the helper is a
  working function in `code/quickstart.py`.

Package:

- Added `code/native_functional.py` (vendored from
  `providers/adapters/native_functional.py` at the baseline) and
  `code/l1_symbol_game_governor.py` (vendored from the Paper 004 package at
  commit `691a01ec3e0ee4f06b4d13b1b8f751edb67c5cee`, later than the baseline),
  each with its source path, commit, SHA-256, and local changes in a header.
- Removed every repository import and `sys.path` insertion from the code and
  tests; the package now runs from any directory.
- Re-running `llm_streaming_harness.py` or `multi_domain_symbol_game_bouts.py`
  now writes a new file in the working directory instead of overwriting the
  retained historical receipts.
- Added `code/tests/test_offline_worksheet.py`,
  `code/tests/test_vendored_sources.py`, and an offline session test in
  `code/tests/test_play_demo.py`; the native-skip reason now says how to
  configure the pins.
- Ran the native-requesting tests against a pinned `solve_graph_phi1` built from
  the unchanged `core_functional` source: 75 passed, none skipped (previously
  all 30 native-requesting tests had been skipped).
- The streaming harness now refuses float and Boolean claim values instead of
  converting them with `Fraction(value)`. New tests:
  `code/tests/test_harness_exact_inputs.py`.
- Removed the governor's blanket native fallback in `compute_phi1`. It called the
  native calculator and, if that call raised for any reason, substituted an exact
  Python enumeration, including for native input and search-bound refusals. It
  now calls the native calculator only when `CORE_FUNCTIONAL_GRAPH_BIN` is set
  and lets every native refusal or error propagate; otherwise it uses the exact
  enumeration. Both paths refuse floating-point or Boolean edge weights. New tests:
  `code/tests/test_native_refusal_propagation.py`.
- Fixed review finding R008-04 in the vendored governor: `step_cut` scored
  omitted edges of a relational CUT as zero claims, so an empty or partial
  proposal could reach a zero minimum and be labelled `ExactRepair`. A CUT must
  now supply exactly one exact integer or fraction for every declared edge;
  otherwise it is refused with the new status `IncompleteProposal` and the state
  is unchanged. The same fix is applied to the Paper 004 package copy. The
  vendored header lists it as a local change, the refusal table in Section 5 has
  a new row, and `code/tests/test_cut_completeness.py` covers it. Accepting
  complete replaced claims still does not make them factually correct.
- Lint fixes: unused imports and one unused variable removed, imports sorted,
  f-strings without placeholders made plain strings.
- Added `LICENSE` (CC BY 4.0), `LICENSE-CODE` (PolyForm Noncommercial 1.0.0),
  `zenodo_metadata.json`, `docs/descriptions.md`, `docs/references.md`,
  `verify_deposit.py`, `tools/rebuild_release.py`,
  `scripts/regen_sha256sums.py`, `scripts/build_deposit_zip.py`, and
  `code/deposit_paths.py`; pinned ruff and pytest settings in `pyproject.toml`.

Withdrawn or narrowed:

- "copying only this paper directory is insufficient" is withdrawn; the package
  is now self-contained.
- The session table's status changes from "source-described expectations" to a
  result checked on the Python enumeration path; native results still need a
  configured run.

## 2026-09-27: Practitioner companion revision

The canonical PO-033 manuscript filename is retained. The current document is
an operator guide accompanying the research papers.

- Replaced broad performance and domain claims with one fully explained finite
  triangle and its source-described session.
- Distinguished fixed-claim residual minimization from replacement of the
  claims, and documented stationary CUT acceptance.
- Chose the package's pinned native quickstart and added an arithmetic-only
  offline route that emits no native receipt.
- Replaced the current claim ledger and marked old execution receipts as
  historical until replayed under reconciled source bindings.
- Preserved historical receipt bytes without regenerating them.
- Replaced the test fixture's automatic native discovery, build, and self-pin
  with caller-supplied executable and digest validation. Only two native tests
  request the fixture; missing configuration skips them, while invalid supplied
  configuration fails. Runtime modules remain at the inspected baseline.
- Made the full-checkout dependency and explicit pytest configuration visible.

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

## Earlier source history

Earlier revisions introduced the field manual, scripted session, streaming
harness, and four labeled graph scenarios. Their detailed prose and old
PO033 claim rows are available in Git history. Statements about whole-domain
results, universal invariant coverage, measured chat savings, or model-internal
attention are not conclusions of the current guide.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.2.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.

## 2026-10-23 — author-review harness extension

Added a focused research extension linked to Paper 029. Separated implemented mechanisms, externally reported findings and unmeasured model effects. Preserved historical source pins, proofs, release archives and deposited identities. New renderings live in the dated author-review collection.

## Author-review package custody repair — 2026-10-23

Refreshed current draft manifests after manuscript revisions. Historical release
archives and deposited metadata were preserved. Author-review copies now carry
their own manifests and the ledger filename required by the existing verifier.
