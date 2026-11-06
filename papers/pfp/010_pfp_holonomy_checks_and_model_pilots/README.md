# PFP X: Exact Host Checking of Model Verdicts on Small Finite Algebraic Challenges

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Initial public preprint candidate.

Paper 010 of the Proposal Fidelity Protocol (PFP), historically called the Symbol
Game, supplies a finite-group lattice flatness checker, replays five retained C017
cases and 15 model solution records, and audits historical formal-mathematics pilot counts.
The host checks certificates rather than trusting explanations. Different prompts,
small authored panels, answer-bearing identifiers and permissive original checker
rules prevent claims about unaided performance or causal prompt effects.

Earlier 1.x/2.x numbers refer to internal drafts. The
[change log](paper_change_log.md) preserves their corrections and withdrawn claims.
Version 0.1.0 is the initial public preprint release.

## Contents

- [paper.md](paper.md), [paper.pdf](paper.pdf), [paper.tex](paper.tex): synchronized manuscript.
- [paper_claim_ledger.md](paper_claim_ledger.md): evidence and scope for each claim.
- `code/holonomy.py`: validated group tables, lattices, verdicts and certificate checks.
- `code/replay_c017.py`: fresh host verdicts and checks of 15 retained solution records;
  ten other historical responses have no retained payload.
- `code/recount_pilots.py`: hashes, 25 extraction comparisons, and historical Table 3/4 recount.
- `code/data/c017/`: original LF case bytes, provenance and extracted model records.
- [historical evidence](docs/historical_evidence/README.md): 15 original report/record
  files pinned by source commit, Git blob SHA and SHA-256.
- [Examiner study guide](_lev_examiner_theoretical_minimum_quiz/study_guide.md),
  [24-question quiz](_lev_examiner_theoretical_minimum_quiz/quiz.md) and separate
  [instructor key](_lev_examiner_theoretical_minimum_quiz/answer_key.md).
- `tools/study_capstone.py`: executable offline exercises using the host and reports.
- `lean4/`: one identity-link lemma, with historical named and full-module reports.
- `tools/render_paper.py`, `tools/paper_preamble.tex`: deposited Pandoc/XeLaTeX build.
- `verify_deposit.py`, `tools/rebuild_release.py`: file custody and deterministic ZIP checks.

## Run the offline checks

From this folder with Python 3.12 or later (use `py -3.12` on Windows):

```text
python -m pip install -e '.[dev]'
python -m pytest code/tests
python -m ruff check code tools/study_capstone.py tools/render_paper.py
python -m mypy code
python code/replay_c017.py
python code/recount_pilots.py
python tools/study_capstone.py --output /tmp/paper010-capstone.json
python tools/render_paper.py
python verify_deposit.py
python tools/rebuild_release.py --check
```

Choose a writable capstone output path on Windows. Development dependencies are
listed in `pyproject.toml`; runtime algebra, replay and recount use the standard
library and packaged data. PDF rendering additionally needs Pandoc and XeLaTeX.
No script calls a model or provider. Run `python tools/rebuild_release.py` after
intentional edits, then verify custody again.

## What each check establishes

The C017 replay freshly checks local cases and retained certificates. The pilot
recount reproduces original acceptance flags and checks the author's identifier
categories and an earlier checker-baseline record. It does not execute the
C045–C050 checkers or independently classify leakage. For historical checker
execution, use the collection-level `tools/replay_formal_math_baselines.py` with
the Git commits cited in manuscript Section 4.4.

The Lean pin remains `leanprover/lean4:v4.34.0-rc1`, with no external Lean libraries.
With that exact toolchain, run `lake build` in `lean4/` and
`python tools/replay_lean_axiom_census.py --replay .` at the package root.
`--check .` performs only a static generated-source check. The named census
contains one axiom-free theorem; the full historical census includes 26 module
declarations, 25 axiom-free and one generated declaration using `propext`.
The current review did not execute the pin. Lean does not verify the full host.

## Current review record

[docs/v01_review_2026_10_02.json](docs/v01_review_2026_10_02.json) records current
commands, tool versions, tested scopes and limitations. Earlier
`docs/release_validation_*.json` and Lean reports retain their historical dates.
The pinned Lean build and fresh C045–C050 checker executions remain unexecuted
in this review. No new model trial or learner measurement was made.
Digest agreement establishes custody, not the truth of every claim.

## Licences

Manuscript and documentation: CC BY 4.0 ([LICENSE](LICENSE)).
Code, Lean files, fixtures and tools: PolyForm Noncommercial 1.0.0
([LICENSE-CODE](LICENSE-CODE)).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23115720> (DOI: `10.5281/zenodo.23115720`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revisions 1.x/2.x and their corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.
