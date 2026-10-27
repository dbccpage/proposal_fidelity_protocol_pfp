# PFP VI: Retained Failure Evidence and Controlled Reuse

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication candidate

This package holds a systems methods paper about keeping rejected proposals as
evidence. It audits the repository's refusal store, a JSON Lines file whose
entries are chained by SHA-256 predecessor digests, and explains what its
count-and-head receipt can and cannot detect. It then describes a bounded
procedure for turning a retained failure into a proposed detector. PFP means
Proposal Fidelity Protocol; Symbol Game is the legacy name.

The source audit is pinned to commit `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
The store is logically append-only through its interface, but it rewrites the
whole file through a temporary path on every append. It does not provide
immutable media, concurrent-writer safety, authenticated provenance, or
power-loss durability. The retained catalog of 61 harvested detector
candidates is described only as a data file; no audited code applies its
fixtures.

## Contents

| Path | Purpose |
| --- | --- |
| [paper.md](paper.md) | Manuscript |
| [paper_claim_ledger.md](paper_claim_ledger.md) | Claims, evidence, and limits |
| [paper_change_log.md](paper_change_log.md) | Versions, changes, and withdrawn claims |
| [docs/completion_supplement.md](docs/completion_supplement.md) | Reproduction scope and evidence boundary |
| [docs/descriptions.md](docs/descriptions.md) | Plain-text description for the deposit record |
| [docs/references.md](docs/references.md) | Bibliography |
| [code/README.md](code/README.md) | What the package tests do and do not show |
| [_lev_examiner_theoretical_minimum_quiz/quiz.md](_lev_examiner_theoretical_minimum_quiz/quiz.md) | 24 graded problems, levels 0-7 |
| [_lev_examiner_theoretical_minimum_quiz/study_guide.md](_lev_examiner_theoretical_minimum_quiz/study_guide.md) | Worked prerequisites and replay instructions |
| [_lev_examiner_theoretical_minimum_quiz/instructor_key.md](_lev_examiner_theoretical_minimum_quiz/instructor_key.md) | Separate answers, proofs, and rubric |
| [code/examiner_worksheet.py](code/examiner_worksheet.py) | Standard-library exact educational replay |
| [docs/first_publication_review_2026_10_02.md](docs/first_publication_review_2026_10_02.md) | Review findings and publication verdict |
| [docs/first_publication_validation_2026_10_02.json](docs/first_publication_validation_2026_10_02.json) | Fresh source-bound execution record |
| `code/tests/` | Package tests |
| `verify_deposit.py`, `tools/`, `scripts/` | Release verification and packaging tools |

## Run the package tests

From this folder, with Python 3.12 (`py -3.12` on Windows):

```powershell
py -3.12 -m pip install "pytest>=9.0.3" "ruff==0.14.13"
py -3.12 -m pytest code/tests/test_006_epistemic_immune.py -q
py -3.12 -m pytest code/tests/test_006_worked_example.py -q
py -3.12 -m pytest code/tests/test_006_catalog_file.py -q
py -3.12 -m ruff check code
py -3.12 code/examiner_worksheet.py
```

`test_006_worked_example.py` runs the paper's Section 6 example and its three
modifications against the repository's failure store.
`test_006_catalog_file.py` recomputes the Section 7.1 catalog counts from the
catalog bytes at the audited commit, read through Git or the identical bound
snapshot in `code/fixtures/`. The catalog checks run from the deposit alone.
The worked storage checks need repository sources and skip with a reason when
those are absent. They also exercise cached receipts, failed replacement,
nested mutation, header metadata, formatting, and valid extension.
`test_006_epistemic_immune.py` tests small toy classes only.

## Run the repository checks the paper cites

From the root of a full repository checkout, choosing the baseline commit
`52cb5457f6c485ba548cfd292f6012a941ed22cf` for historical replay or recording
the actual source hashes for a current-branch run:

```powershell
py -3.12 -m pytest pfp/tests/test_cemetery_sink.py -q
py -3.12 -m pytest pfp/tests/test_immune_defect_regressions.py -q
```

No provider call, model download, or network access is required.

## Verify a release

After the release manifests and the dated archive have been built:

```powershell
py -3.12 verify_deposit.py
py -3.12 tools/rebuild_release.py --check
```

`verify_deposit.py` checks the manifest and the two-way file census.
`tools/rebuild_release.py --check` checks the dated release archive against
both manifests.

## Toolchain

- Python 3.12; the fresh first-publication review used 3.12.14
- pytest 8.3.5 and Ruff 0.14.13, pinned in `pyproject.toml`
- Pandoc and XeLaTeX for the TeX/PDF build; exact versions and commands are
  recorded in the fresh validation receipt

## Verification record

The fresh package-local `docs/first_publication_validation_2026_10_02.json`
lists commands, tool versions, source hashes, outcomes, and tested scope.
The implementation replay uses byte-verified materialized baseline sources;
it is not a full-repository or current-branch integration run. Historical
receipts here and under `_intelligence/core_paper_reviews/` keep their original
bytes, dates, and scope.

## Licenses

The manuscript and documentation are licensed under CC BY 4.0
([LICENSE](LICENSE)). The code is licensed under the PolyForm Noncommercial
License 1.0.0 ([LICENSE-CODE](LICENSE-CODE)).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114681> (DOI: `10.5281/zenodo.23114681`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.1.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

The fresh execution record is
`docs/first_publication_validation_2026_10_02.json`.
`docs/release_validation_2026_10_02.json` and the earlier release receipt are
retained historical records; their tested hashes do not describe the revised
publication assets.

## 2026-10-23 author-review extension

The current manuscript adds the evidence-bound harness study. New PDFs are built in the collection's `publication/author_review_2026_10_23/` directory. Existing package PDFs, archives and deposited metadata retain their historical identities. See Paper 029 for source mapping and campaign reproduction. The live campaign is NOT_RUN.

Working-tree `MANIFEST.sha256` and `SHA256SUMS` describe the current author-review
revision. Historical release ZIPs and their embedded manifests retain their original
bytes and deposited identities; these working manifests do not redeposit them.
