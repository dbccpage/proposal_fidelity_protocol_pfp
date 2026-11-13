# PFP III: Admitting Failure Detectors and Testing Their Effects

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication candidate

This deposit accompanies the manuscript [paper.md](paper.md), its
[claim ledger](paper_claim_ledger.md), and its [change log](paper_change_log.md).
PFP, the Proposal Fidelity Protocol, was previously called the Symbol Game. The
paper specifies how a failure detector should be admitted, describes what the
repository's Demo 3 host enforces at commit
`52cb5457f6c485ba548cfd292f6012a941ed22cf`, and proposes a study design for
detector effectiveness and false suppression. Its Appendix A establishes three small lemmas about two-signal gates, Hill-type quorums and
negative selection, checks them exhaustively in `code/tests/`, and audits the
repository against them. It reports no new model trial.

## Contents

- `code/`: a small standalone re-implementation of the host
  (`host_engine.py`), the two-signal decision table (`danger_gate.py`), the four
  candidate phrase detectors (`canaries.py`), and a synthetic self panel
  (`self_panel.py`); the exact lemma checks of Appendix A (`detector_lemmas.py`);
  demonstration scripts; tests in `code/tests/`; and a Rust
  port in `code/rust/`. Section 4.1 of the paper lists how this
  re-implementation differs from the repository host.
- `demos/`: historical traces, receipts, notebooks, and notes, kept with their
  original bytes. They are not current execution evidence, and the notebooks
  import modules that are not part of this deposit.
- `docs/`: the deposit description, references, reproduction boundary, review
  response, and historical validation records.
- `_lev_examiner_theoretical_minimum_quiz/`: 24 problems over levels 0-7,
  a prerequisite study guide, a separate instructor key with exact numerical
  answers, and the fictional Apartment 50 preface.
- `verify_deposit.py`, `scripts/`, `tools/`: release tooling from the series
  template.

## Running the checks

From the package root, with Python 3.12, install the pinned tools and run:

```powershell
py -3.12 -m pip install "pytest>=9.0.3" ruff==0.14.13
py -3.12 -m pytest -o addopts= code/tests -q -p no:cacheprovider
py -3.12 -m ruff check code
py -3.12 verify_deposit.py
```

The Rust port has its own tests:

```powershell
cargo test -j 1 --manifest-path code/rust/Cargo.toml
cargo build --release -j 1 --manifest-path code/rust/Cargo.toml
```

After the release build, `code/tests/test_danger_gate.py` also compares the Rust
binary with the Python reference; without a binary that test is skipped with the
reason printed. A binary built elsewhere can be named with the environment
variable `PFP003_HOST_DETECTOR_BIN`. Build output in `code/rust/target/` is not
part of the deposit.

## Demonstrations

```powershell
py -3.12 code/run_demos.py
```

This runs the three package demonstration scripts (host transactions, the
two-signal table, the phrase detectors) and the candidate-response audit, all
offline. The package scripts are numbered 1 to 3; they are not the repository's
Demo 3. The candidate-response audit makes one network request only when asked:

```powershell
py -3.12 code/live_proposer_demo.py --live
```

with `OPENROUTER_API_KEY` set in the environment, or in a file named with
`--env-file` (see `.env.example`). No `.env` file is read otherwise. A live
response is a demonstration, not a study result.

## Toolchain

Python 3.12, pytest 8.3.5, and ruff 0.14.13, with lint, test, and type-check
settings in `pyproject.toml`. The historical native toolchain was Rust
1.98.0 with cargo 1.98.0; fresh tool versions and unavailable checks are recorded
in the current validation receipt. The PDF is
built from `paper.md` by the series build with pandoc and XeLaTeX.

## Verification

`verify_deposit.py` checks the manifest, the two-way file census, and the
required files. Fresh replay outcomes and their input hashes are in
`docs/first_publication_validation_2026_10_02.json`; the publication review is
`docs/first_publication_review_2026_10_02.md`. Native checks not executed in that
receipt remain explicitly unassessed. Historical receipts in `demos/` and `docs/` keep their original dates
and scope.

## License

Text: Creative Commons Attribution 4.0 International (`LICENSE`). Code:
PolyForm Noncommercial 1.0.0 (`LICENSE-CODE`).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114331> (DOI: `10.5281/zenodo.23114331`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.2.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

The current package-local execution record is
`docs/first_publication_validation_2026_10_02.json`.
`docs/release_validation_2026_10_02.json` retains an earlier selected-check replay;
historical review receipts keep their original dates.

## 2026-10-23 author-review extension

The current manuscript adds the evidence-bound harness study. New PDFs are built in the collection's `publication/author_review_2026_10_23/` directory. Existing package PDFs, archives and deposited metadata retain their historical identities. See Paper 029 for source mapping and campaign reproduction. The live campaign is NOT_RUN.

Working-tree `MANIFEST.sha256` and `SHA256SUMS` describe the current author-review
revision. Historical release ZIPs and their embedded manifests retain their original
bytes and deposited identities; these working manifests do not redeposit them.
