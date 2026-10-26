# Companion 007: Replay scope and historical records

First-publication companion, 2026-10-02 · Version 0.1.0\
Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The [main guide](../paper.md) integrates the current interpretation. This
supplement is a compact execution-scope index; it does not claim completion of a
learning study or current full-route replay.

## Existing artifacts

| Artifact | What it records | Current reading |
| --- | --- | --- |
| [Integration notebooks](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/README.md) | Twenty worked instructional notebooks | Reading route at the source audit baseline |
| [Headless receipt](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/headless_receipt.json) | Twenty passes dated 2026-09-25 under former paths | Historical execution evidence |
| [Lesson manifest](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/lesson_manifest.json) | Twenty source/scope records using former notebook paths | Needs path reconciliation before aggregate replay |
| [Companion notebook](../jupyter_notebooks/007_moving_a_discrepancy.ipynb) | The Section 3 lesson with Python fractions only | Package replay compares a fresh execution with the stored outputs |
| [Worked-triangle tests](../code/tests/test_007_worked_triangle.py) | Section 3 arithmetic, the notebook's stored values, and the printed Section 3 blocks | The printed-block check needs the full repository and skips otherwise |
| [Legacy threshold examples](../code/tests/test_007_pedagogical_transmission.py) | Supplied durations, supplied metrics, and supplied execution-status strings | Small software fixtures, not human measurements or notebook execution |

## Selected replay diagnostic

The cycle notebook still calls `residual.l1_norm()`. The pinned
[cochain implementation](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/domain/ddc/cochains.py)
unconditionally raises `FunctionalBoundaryUnavailable` there. The main guide's
adapted arithmetic core omits that retired call. The unchanged notebook command
below is expected to fail at the call if its earlier checks succeed.

From the repository root, with the route's Python dependencies installed:

```powershell
python -B omega_engine_education/scripts/verify_system_integration.py --child omega_engine_education/the_symbol_game/lessons/system_integration/100_novices/04_cycle_repair.ipynb --output "$env:TEMP/pfp-cycle-lesson.json"
```

Record the actual failure and its location. A new full-route receipt needs
maintained API calls and reconciled source/manifest paths. The aggregate verifier
writes education receipts; a full refresh is a separate maintained source
operation. This companion reports no fresh execution of the 20-notebook route.

## Formal-source limits

[GrammarCeiling.lean](../lean4/GrammarCeiling.lean) assumes an integer list
length bound and a per-entry magnitude bound.
[GrammarDepthCeiling.lean](../lean4/GrammarDepthCeiling.lean) preserves declared
symbols/operators under unary nesting. Neither establishes a cognitive attention
model, and the latter does not bound tree depth. Both files, with the one
module the first imports, are vendored into this package's local Lean project;
its
[axiom report](../lean4/axiom_report.txt) selects 21 named declarations. The retained full package-local census lists 64, including generated/private names and excluding imported Lean library declarations. Its observed dependencies are subsets of `propext` and `Quot.sound`; `Classical.choice` is permitted, but not listed as used. Historical receipts record successful builds and census runs. This first-publication review verifies matching source/report hashes but does not repeat Lean/Lake execution on a host where those tools are absent.

The former claims of calibrated four-minute attention decay, quantified learning
transfer, and formal cognitive complexity limits are withdrawn from the current
companion. Its positive contribution is the worked design method and source map
in the main guide.

## First-publication checks

The [fresh receipt](first_publication_validation_2026_10_02.json) records standalone package tests, an isolated seven-module DDC check of the printed blocks, the guide's exact worksheet, and six-cell ordinary-Python notebook replay. Parent-package initialization, full route execution, and learner assessment are outside that fresh scope. The [Landau companion](../_lev_landau_theoretical_minimum_quiz/study_guide.md) retains first predictions separately from feedback and defines a proposed assessment record; no participant outcomes are supplied.
