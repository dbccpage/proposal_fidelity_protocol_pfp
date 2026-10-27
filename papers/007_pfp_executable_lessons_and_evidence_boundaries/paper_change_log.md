# PFP VII change log

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114712> (DOI: `10.5281/zenodo.23114712`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## First-publication review: 2026-10-02 · Version 0.1.0

- Aligned publication headers, claim ledger, supplement, notebook version, and development pins with the initial preprint designation.
- Pinned external source links and retained a Git-bound inventory rather than presenting the audited route as current-head execution.
- Corrected the 21-name selected Lean report versus 64-declaration full package-local census; separated permitted axioms from observed usage and historical evidence from fresh checks.
- Added a deliberate wrong-sign control that passes cycle-sum checks but fails independently predicted coordinates.
- Added fresh-process ordinary-Python replay, with an optional explicit-kernel backend, that compares code-cell counts/outputs and preserves deposited bytes. Jupyter kernel sockets were unavailable on the review host.
- Expanded the Examiner materials to 24 graded problems, a worked guide with a standard-library worksheet and first-response record, and a separate 96-point instructor key. Levels and scoring remain proposed instructional choices.
- Added fresh source-bound validation and publication review. Original validation receipts and Lean sources/reports remain unchanged.
- Clarified Zenodo mixed-license field scopes and distinguished the combined-deposit metadata draft from a legacy API payload.

## Retained internal history

# Companion 007 change log

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 1.1.0 (2026-09-28): author-review revision

### Changed

- The package folder was renamed from `007_pfp_pedagogical_transmission_and_micro_attention_curricula` to `007_pfp_executable_lessons_and_evidence_boundaries`: the
  old words did not describe the content, and the dated release archive's path
  exceeded the Windows path limit.
- The header gains version 1.1.0 and the date 2026-09-28. The abstract mentions
  the companion notebook and the local Lean build.
- Section 3 gains a “Standalone replay” subsection that names the companion
  notebook and the package test, including the test's full-repository
  requirement for the printed code blocks.
- Section 6 links the vendored copies of `GrammarCeiling.lean` and
  `GrammarDepthCeiling.lean`, describes the local Lean project and its axiom
  report, and links the legacy test module at its new path under `code/tests/`.
- Two phrases are reworded without change of meaning: Section 2 (“without first
  opening a distant module”) and the Section 4 table row for
  `03_edges_and_parallel_cells.ipynb` (“valid syntax alone”).
- The verification section names the package verifier, the release-archive
  check, and the dated review receipt, and no longer links the collection
  verification report. Reference entries gain DOI text.
- Claim ledger: G007-02, G007-03, and G007-07 cite package tests or local files;
  G007-09 to G007-11 are new. Earlier identifiers keep their meaning.

### Added

- `jupyter_notebooks/007_moving_a_discrepancy.ipynb`: the Section 3 lesson with
  Python fractions only and no repository imports, executed once with nbclient
  under Python 3.12 and stored without timing metadata.
- `code/tests/test_007_worked_triangle.py`: fraction-only checks of the Section 3
  arithmetic, a static check of the notebook's stored values, and a run of the
  printed Section 3 blocks that skips when the repository is absent.
- `lean4/`: `Expressivity.lean`, `GrammarCeiling.lean`, and
  `GrammarDepthCeiling.lean`, vendored from commit
  `52cb5457f6c485ba548cfd292f6012a941ed22cf` with a provenance comment and
  otherwise unchanged; `lakefile.lean`; `lean-toolchain` pinned to Lean 4.34.0;
  `lake-manifest.json`; `Census.lean`; and `axiom_report.txt`. The report lists
  all 21 declarations. `tools/replay_lean_axiom_census.py` regenerates and
  replays the census.
- `paper_change_log.md`, `docs/descriptions.md`, `docs/references.md`,
  `zenodo_metadata.json`, `LICENSE` (CC BY 4.0), `LICENSE-CODE` (PolyForm
  Noncommercial 1.0.0), `verify_deposit.py`, `tools/rebuild_release.py`,
  `scripts/regen_sha256sums.py`, `scripts/build_deposit_zip.py`, and
  `code/deposit_paths.py`. `pyproject.toml` pins the package version, the pytest
  test path, and the ruff and mypy configuration.

### Moved

- `completion_supplement.md` to `docs/completion_supplement.md`; its relative
  links are re-based for the new location.
- `code/test_007_pedagogical_transmission.py` to
  `code/tests/test_007_pedagogical_transmission.py`. Imports are sorted, type
  hints use built-in generics, and docstrings state that every value is
  supplied. Test logic is unchanged.

### Withdrawn

- No claim is withdrawn in this revision. The claims withdrawn earlier, namely
  calibrated four-minute attention decay, quantified learning transfer, and
  formal cognitive complexity limits, stay withdrawn.
- The ledger's former note that no new Lean build is claimed is replaced by
  G007-10, which describes the local build of the vendored files.

## 2026-09-27: author-review revision

Unversioned revision without a change log. It replaced the earlier
learning-effect and cognitive-ceiling claims with the current curriculum-design
guide. Version 1.1.0 supersedes its text.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.1.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.
