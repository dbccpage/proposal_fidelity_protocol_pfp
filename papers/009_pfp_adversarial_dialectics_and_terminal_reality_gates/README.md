# Paper 009: Reviewing claims against code and evidence

Jeremy H. Carroll. Author-review revision, 2026-10-02. Version 0.1.0.

This v0.1 Zenodo preprint presents a review protocol with exact
triangle arithmetic, LP and packet probes, a ten-trial historical recount,
and a terminal-gate audit. The historical directory name is retained for
stable links.

## Read and study

- [Manuscript](paper.md), [PDF](paper.pdf), and [claim ledger](paper_claim_ledger.md).
- [Change log](paper_change_log.md), [implementation scope](docs/completion_supplement.md),
  [description](docs/descriptions.md), and [references](docs/references.md).
- [Examiner quiz](_lev_examiner_theoretical_minimum_quiz/quiz.md): 24 questions in eight levels.
- [Study guide](_lev_examiner_theoretical_minimum_quiz/study_guide.md) and
  [separate instructor key](_lev_examiner_theoretical_minimum_quiz/answer_key.md).
- [Historical evidence](docs/historical_evidence/README.md): three byte-identical
  records, with provenance; standalone recount tests require no sibling package.
- `code/`: exact triangle arithmetic, recount module, and focused tests.
- `jupyter_notebooks/009_triangle_cycle_sum.ipynb`: five ordinary Python cells
  with assertions and retained display outputs.
- `lean4/`: four source modules plus retained named and full axiom reports.

Related [practitioner guide](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/paper.md)
and [curriculum guide](https://github.com/dbccpage/the_symbol_game/blob/593230f7daba7aa04d7c41dd456dfbd00a39bcbd/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/paper.md).

## Reproduce the package checks

From this folder with Python 3.12 or later (on Windows, substitute `py -3.12`):

```sh
python -m pip install -e '.[dev,notebooks]'
python -m pytest -q
python -m ruff check code tools/review_capstone.py tools/replay_notebook.py tools/render_paper.py
python -m mypy
python tools/review_capstone.py
python tools/replay_notebook.py
python verify_deposit.py
python tools/rebuild_release.py --check
```

The notebook replay defaults to a fresh CPython process and compares every code
cell's source, position, output, and execution count without rewriting it. For
a separate Jupyter kernel check, use `python tools/replay_notebook.py --engine jupyter`.
The default does not test IPython rendering. The capstone and tests recount
retained data; they make no model call and do not replay the original gate or
native physics checker. Undefined fractions are reported as `None`.

Lean reproduction requires the pinned `leanprover/lean4:v4.34.0` toolchain:

```sh
cd lean4
lake build
lake env lean Census.lean
cd ..
python tools/replay_full_axiom_census.py .
```

These are reproduction instructions, not claims that every dependency ran in
this review. The 32 named theorems and 516 environment declarations are two
different retained report scopes.

## Rebuild the publication

Pandoc and XeLaTeX are required for the PDF. The deposited preamble is used:

```sh
python tools/render_paper.py
python tools/rebuild_release.py
python verify_deposit.py
python tools/rebuild_release.py --check
```

The release tool refreshes the manifests and deterministic ZIP. Hash identity
supports custody, not the correctness of manuscript claims.

## Validation and scope

[docs/v01_review_2026_10_02.json](docs/v01_review_2026_10_02.json) records fresh
commands, actual versions, hashes, and unexecuted dependencies. The earlier
`docs/release_validation_2026_10_01.json` and `docs/release_validation_2026_10_02.json`
remain unchanged historical records. The current review does not freshly
compile Lean 4.34.0 or replay the model, native checker, or Adversary gate.
Development dependency ranges are specified in `pyproject.toml`; they are not
exact lock pins. Notebook imports use only the package's own triangle module.

## Licenses and provenance

Text, figures, and documentation: [CC BY 4.0](LICENSE). Code, notebooks, Lean
sources, and tooling: [PolyForm Noncommercial 1.0.0](LICENSE-CODE). Retained
evidence keeps its original scope. Internal revisions 1.2.0 and 1.2.1 remain
documented in the change log; the first-publication designation is 0.1.0.

Conceptual source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`. Review retrieval: `593230f7daba7aa04d7c41dd456dfbd00a39bcbd`.

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23115634> (DOI: `10.5281/zenodo.23115634`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revisions 1.2.0 and 1.2.1 and their corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

## 2026-10-23 author-review extension

The current manuscript adds the evidence-bound harness study. New PDFs are built in the collection's `publication/author_review_2026_10_23/` directory. Existing package PDFs, archives and deposited metadata retain their historical identities. See Paper 029 for source mapping and campaign reproduction. The live campaign is NOT_RUN.

Working-tree `MANIFEST.sha256` and `SHA256SUMS` describe the current author-review
revision. Historical release ZIPs and their embedded manifests retain their original
bytes and deposited identities; these working manifests do not redeposit them.
