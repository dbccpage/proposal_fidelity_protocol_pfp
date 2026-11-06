# PFP VI change log

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114681> (DOI: `10.5281/zenodo.23114681`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 0.1.0 (2026-10-02): first-publication review

- Separate the historical implementation audit from the current package and
  later encoder changes; preserve internal 1.x history.
- State that tail receipts use memory, successful disk verification must
  precede persisted-snapshot comparison, and failed replacement can leave
  memory ahead of disk. Add six concrete storage-boundary replay cases.
- Clarify header/schema and formatting limits, lossy normalization, legitimate
  prefix extension, and the simple accumulated write-cost model.
- Distinguish returned clonal/regulatory records from applied host action;
  clarify trigger denominators and empty samples; state decay assumptions.
- Include the unchanged, digest-bound historical catalog as data so its census
  can be recomputed from the deposit alone. Loading it executes no detector.
- Expand the Examiner companion to 24 problems across levels 0-7, with worked
  prerequisites, a separate instructor key, a 96-point rubric, and an exact
  standard-library worksheet. Remove the shared external worksheet dependency.
- Pin pytest to the documented 8.3.5, align current documentation headers,
  add the fresh review and validation receipt, and rebuild publication assets.

No current detector efficacy, immutable retention, authenticated provenance,
integrated semantic miner, external publication, or DOI is claimed. The
historical release receipts keep their original bytes and scope.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 1.1.0 (2026-09-28): author-review revision

### Changed

- Section 7.1 is rewritten as a factual description of
  `_intelligence/_antibodies/pharmacy_catalog.json` at commit
  `52cb5457f6c485ba548cfd292f6012a941ed22cf`: 61 entries, 14 distinct
  `failure_class` values with their per-class counts, 56 entries marked
  `candidate` and 5 marked `active`, 15 fields per entry, and 49 entries whose
  two fixtures are placeholder comments. The earlier text grouped the 14
  classes into seven descriptive categories with interpretive labels; the table
  now lists the literal class values.
- `evidence_sha256` is described as a digest that supports comparison only
  against an independently retained anchor. The section names the identifying
  strings hashed by the two harvesting implementations at the audited commit
  and reports that 19 stored values are reproduced from a defect label with run
  and task identifiers found in retained run records.
- Section 3 describes the sink's fixed marker field in plain terms, and the
  `TailReceipt` sentence lists the four values its digest covers.
- Section 6 names the typed errors raised by the first two modifications and
  states that the consistent shorter file reopens without error.
- Section 8 states the toxicity denominator (the number of supplied trigger
  records), the 0-or-1 score of the unlabelled-corpus mode, the decay factor,
  and the expiry rule.
- Section 9 names the package tests and the full-repository requirement of the
  worked-example and catalog tests.
- The verification section names the package verifier, the release-archive
  check, and the dated review receipt. References gain volume, issue, and DOI
  details. The header gains a version number, and the abstract mentions the
  catalog as a data file.
- The claim ledger keeps identifiers P6-01 to P6-15, corrects P6-15, adds
  P6-16 to P6-18, and cites package tests as `file::function`.

### Added

- `code/tests/test_006_worked_example.py`: executes the Section 6 block as
  printed, its three modifications, and the number-versus-string reason case
  against the repository sink. It skips, stating why, when the repository
  checkout is absent.
- `code/tests/test_006_catalog_file.py`: recomputes the Section 7.1 counts,
  fields, placeholder fixtures, and digest reconstructions from the catalog
  bytes read through Git at the audited commit. It skips, stating why, when the
  repository, that commit, or `git` is unavailable.
- `paper_change_log.md`, `docs/descriptions.md`, `docs/references.md`,
  `zenodo_metadata.json`, `LICENSE` (CC BY 4.0), `LICENSE-CODE` (PolyForm
  Noncommercial 1.0.0), `verify_deposit.py`, `tools/rebuild_release.py`,
  `scripts/regen_sha256sums.py`, `scripts/build_deposit_zip.py`, and
  `code/deposit_paths.py`.
- `pyproject.toml` pins the package version, the pytest test path, and the ruff
  and mypy configuration.

### Moved

- `completion_supplement.md` to `docs/completion_supplement.md`.
- `code/test_006_epistemic_immune.py` to
  `code/tests/test_006_epistemic_immune.py`. Imports are sorted, an unused
  import is removed, docstrings describe the toy classes plainly, and the test
  formerly named `test_cemetery_dag_append_only_zero_loss` is renamed
  `test_toy_chain_links_predecessor_digests`. Test logic is unchanged.

### Withdrawn

- “61 active antibodies”: the file marks 5 entries `active` and 56
  `candidate`.
- “107 multi-round AST cochain transitions and 134 empirical artifacts”: no
  file retained at the audited commit supports either count, and the cited
  findings document was added after that commit.
- `negative_fixture` as “the exact minimal reproduction case” and
  `positive_fixture` as “the verified repaired state that passes the host
  oracle”: 49 of 61 fixture pairs are placeholder comments, and no fixture is
  bound to a checker.
- `evidence_sha256` as “an immutable cryptographic commitment binding the
  reproduction receipt”.
- The statement that a host filter matches incoming proposals against negative
  fixtures and provides a repair differential derived from the positive
  fixture: no code at the audited commit implements it.
- The ledger's citation of `challenges_findings_and_updates.md` as evidence for
  the catalog.

## 2026-09-27: author-review revision

Unversioned revision without a change log. Version 1.1.0 supersedes its text;
the statements listed under “Withdrawn” above come from it.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.1.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.

## 2026-10-23 — author-review harness extension

Added a focused research extension linked to Paper 029. Separated implemented mechanisms, externally reported findings and unmeasured model effects. Preserved historical source pins, proofs, release archives and deposited identities. New renderings live in the dated author-review collection.

## Author-review package custody repair — 2026-10-23

Refreshed current draft manifests after manuscript revisions. Historical release
archives and deposited metadata were preserved. Author-review copies now carry
their own manifests and the ledger filename required by the existing verifier.
