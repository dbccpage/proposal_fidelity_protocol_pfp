# Change log: Reviewing claims against code and evidence

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23115634> (DOI: `10.5281/zenodo.23115634`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

Entries are dated. Earlier entries keep their original scope.

## [1.2.1] - 2026-09-30

### Changed

- Replaced the challenge-harness commit marker in Appendix A.4 and the claim ledger with commit `e6fbc15cf` ("challenges: repair judges, remove leaks, make the harness honest").
- Bumped package version to 1.2.1 across the manuscript, package metadata, and documentation.

## [1.2.0] - 2026-09-29

### Added

- Appendix A, "Where a gate's verdict comes from". It applies the protocol of
  Sections 2, 4 and 7 to the terminal gate of the repository's seven-act Woland
  engine at commit `30609de2c3928238715375a9bac608256fa381d8`, with a table that
  sets each operation's name beside what it does and four falsifiers: input
  replacement (Act IV replaces the cochain by zeros and Act VII then authorizes),
  keyword adjudication (a critique blocks when its text contains "DEFECT" or
  "FLAW"), phantom evidence references (the SHA-256 of the run key used as
  evidence, and receipt fields that are constants), and templated challenge-gate
  receipts (the C012 copy of the gate reports agreement and repair for a refused
  run with no cases). Each falsifier gives a fixed input, the expected status and
  the observed status, and the fix: commit `a054c8ce1` for F1 to F3 (tests
  `omega_engine_woland/tests/test_honest_gate_falsifiers.py` and
  `test_adversarial_m1_it2_1_challenger.py`) and commit `e6fbc15cf` for F4
  (`omega_engine_projects/mssn_sn_symgam/challenges/harness_tests/test_harness_honesty.py`).
- The falsifiers are replayed by the collection's
  `tools/replay_woland_gate_falsifiers.py`, which extracts the audited packages
  with `git archive`, calls single act functions with a stub runtime and calls no
  model; its record is the collection's `verification/woland_gate_falsifiers.json`.
- Claim ledger rows G009-14 to G009-18.

### Changed

- The Purpose and Limitations sections mention Appendix A and its scope.
- Version 1.2.0, dated 2026-09-29, in the manuscript, `README.md`,
  `docs/descriptions.md`, `docs/completion_supplement.md`, `zenodo_metadata.json`
  and `pyproject.toml`.

## [1.1.0] - 2026-09-28

### Changed

- Rewrote Section 4.1. The former text listed an eight-part “cognitive auditing dialogue” with internal role names. This protocol does not use that format, so the list was removed. The section now recounts the retained proposer–adversary run from Paper 001's package as a four-cell table and names where its labels come from.
- Moved the fixture tests to `code/tests/test_009_adversarial_reality_gate.py`. Fixed the import block, removed unused imports, and renamed the stagnation method and its test to plain names (`should_trigger_review`, `test_stagnation_review_trigger`). Behavior is unchanged.
- Moved `completion_supplement.md` into `docs/` and repaired its links.
- Section 5 now cites local copies of `Level15AuthorityCalculus.lean` and `TriggerNotLicense.lean`, with the two modules the second imports (`RuntimeLimits.lean`, `SLevel.lean`). Each copy matches the repository file at the code baseline except for a two-line provenance comment, and the copies build with Lean 4.34.0. `lean4/axiom_report.txt` and `lean4/Census.lean` list all 32 theorems in these modules and their axioms. The terminal-routing source stays in the repository and is still described as not typechecked.
- Section 3 now says what each external example shows and points to the package's companion notebook and tests.
- The example record in Section 7 uses `decision_scope: review-only` in place of an internal field.
- Replaced the Verification section with the current wording.
- The references now give pages and DOIs.
- The header now carries version 1.1.0. The previous revision had no manuscript version; `pyproject.toml` declared a placeholder 0.1.0.

### Added

- `code/triangle_cycle_sum.py`, `code/tests/test_triangle_cycle_sum.py`, and `jupyter_notebooks/009_triangle_cycle_sum.ipynb`, which recompute the Section 3 arithmetic with exact fractions.
- `code/tests/test_recorded_bout_counts.py`, which recounts the Section 4.1 run when the full repository is present and skips otherwise.
- A Limitations section.
- Package files: this change log, `zenodo_metadata.json`, `docs/descriptions.md`, `docs/references.md`, `LICENSE` (CC BY 4.0), `LICENSE-CODE` (PolyForm Noncommercial 1.0.0), `verify_deposit.py`, `tools/rebuild_release.py`, `tools/replay_lean_axiom_census.py`, `scripts/regen_sha256sums.py`, `scripts/build_deposit_zip.py`, `code/deposit_paths.py`, and pinned ruff, pytest, and mypy settings in `pyproject.toml`.

### Withdrawn

- The statement that the proposer attempted 6 unsound claims and the adversary “caught 10/10 (100% catch rate)”. The retained trace has 6 unsound-labeled proposals, all challenged, and 4 sound-labeled proposals, of which 2 were challenged and 2 accepted. The 10/10 figure counted the trace field `adversary_caught_am`, which is true in all 10 records.
- The statement that the run demonstrates that multi-agent adversarial debate catches unsound proposals before they are stored. The checker refused all six unsound proposals itself, and every trial ended in the same terminal state.
- The eight-part dialogue description and its citation of run records under `_intelligence/symbol_game/runs/`. No files under that path are tracked in the repository.
- Ledger row G009-11 of the previous revision (the dialogue and the 10/10 figure). Rows G009-11 to G009-13 replace it.
- The Section 8 paragraph about earlier informal names for search-escape and reframing techniques. It described internal history, and the Purpose section already states that the paper reports no measured psychological effect or search-escape rate.

## Earlier revision - 2026-09-27

- Author-review revision of the protocol as a review companion to the series. It carried no manuscript version number.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.2.1 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.

## 2026-10-02 — v0.1 first-publication review

- Bundled the three cited historical records byte-for-byte with provenance;
  standalone recount tests fail on absent or altered records instead of skipping.
- Distinguished four gate defect families from five probe records, and corrected
  the script's write-scope wording. Pinned corrected-code references by revision.
- Removed the unsupported blanket claim of fresh notebook and Lean execution;
  current checks and retained reports now have distinct scopes and dates.
- Distinguished the 32 named theorems from the full 516-declaration census;
  protected Lean files and all earlier verification records remain unchanged.
- Corrected stale 1.2.1 description and companion headers to the v0.1 designation,
  preserved internal revision history, and aligned Python support with 3.12.
- Expanded the Landau companion to 24 questions, eight study levels, a separate
  instructor key, and a capstone with exact counts and changed-input controls.
- Added notebook assertions, source/output replay, and a reproducible PDF build.
  Updated the manuscript, TeX, PDF, metadata, manifests, and release ZIP together.

This review does not publish to Zenodo, establish a DOI, call providers, or
reexecute the historical Woland audit or its corrected-code tests.

## 2026-10-23 — author-review harness extension

Added a focused research extension linked to Paper 029. Separated implemented mechanisms, externally reported findings and unmeasured model effects. Preserved historical source pins, proofs, release archives and deposited identities. New renderings live in the dated author-review collection.

## Author-review package custody repair — 2026-10-23

Refreshed current draft manifests after manuscript revisions. Historical release
archives and deposited metadata were preserved. Author-review copies now carry
their own manifests and the ledger filename required by the existing verifier.
