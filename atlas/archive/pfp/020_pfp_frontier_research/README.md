# PFP XX: Identity prefixes share the braid action and the mean defect 23/1200

Jeremy H. Carroll · 2026-10-03 · Version 0.1.0 · Initial public preprint candidate.

This folder is shelf 022. The collection index relocates catalog id 020 here. Historical self-scores and model-labelled tables do not establish new live model performance. The “96% coverage” figure below is a local pytest coverage claim for `code/tests/test_adaptive_braid_tournament_demo.py`. It is not a model-performance result.

The manuscript asks whether language models (OpenRouter candidates LLaMA 3.1 8B, LLaMA 3.3 70B, and GLM 5.3 alongside deterministic baselines) can discover adaptive noise-mitigation braid schedules that protect multi-qubit Majorana zero mode (MZM) carriers against local skew-symmetric noise perturbations under fixed rational budgets. That question is the manuscript’s question. This README does not record a new live trial.

## Contents

- [paper.md](paper.md): synchronized manuscript.
- [paper_claim_ledger.md](paper_claim_ledger.md): evidence and scope for each claim.
- [paper_change_log.md](paper_change_log.md): version history.
- `code/adaptive_braid_tournament_demo.py`: complete runnable tournament demo.
- `code/tests/test_adaptive_braid_tournament_demo.py`: test suite with 96% coverage.
- `scripts/run_tournament.py`: CLI tournament execution tool.
- `verify_deposit.py`: fail-closed two-way deposit verifier.
- `zenodo_metadata.json`: preprint record metadata.

## Run the offline checks

From this folder with Python 3.12 (use `py -3.12` on Windows):

```text
python -m pytest code/tests
python code/adaptive_braid_tournament_demo.py
python scripts/run_tournament.py --qubits 2
python verify_deposit.py
```

## What each check establishes

- `code/adaptive_braid_tournament_demo.py` runs an end-to-end multi-round tournament evaluating proposers across noise sweeps under exact rational arithmetic (`fractions.Fraction`) and emits a signed `TournamentRunReceipt`.
- `code/tests/test_adaptive_braid_tournament_demo.py` verifies all schedule synthesis modes, fallback behavior, referee gates, and claim hygiene formatting.
- `verify_deposit.py` checks two-way hash parity, manifest completeness, and required artifacts.

## Licences

- Manuscript and documentation: CC BY 4.0 ([LICENSE](LICENSE)).
- Code and tooling: PolyForm Noncommercial 1.0.0 ([LICENSE-CODE](LICENSE-CODE)).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23120020> (DOI: `10.5281/zenodo.23120020`, v0.1.0 Preprint).
Published October 3, 2026. AuthorityEffect: None.
