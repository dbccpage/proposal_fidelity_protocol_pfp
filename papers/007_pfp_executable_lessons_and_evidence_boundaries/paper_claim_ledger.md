# Companion 007 claim ledger

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · First-publication review

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The guide concerns curriculum design and finite instructional artifacts.
It supersedes the former learning-effect and cognitive-ceiling claims. Package
tests are named as `file::function`. Fresh execution results belong to [the first-publication receipt](docs/first_publication_validation_2026_10_02.json); historical receipts retain their original scope. Identifiers G007-01 to G007-08 keep their earlier
meaning; G007-09 to G007-11 retain their scoped artifact meaning; G007-12 to G007-14 record first-publication additions.

| ID | Claim | Evidence | Limit |
| --- | --- | --- | --- |
| G007-01 | The deep route at the audit baseline contains 20 named notebooks in five groups | [Route README](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/README.md) and the 20 paths in guide Section 4 | File presence and route declaration; no fresh execution inference |
| G007-02 | The triangle residual changes from (1/3,1/3,1/3) to (0,0,1) under the displayed potential adjustment | `test_007_worked_triangle.py::test_potential_adjustment_moves_the_residual`; `test_007_worked_triangle.py::test_section3_code_blocks_run_as_printed`; [notebook](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/100_novices/04_cycle_repair.ipynb) | Declared finite example and telescoping identity; the printed-block check needs the full repository |
| G007-03 | A constant potential shift leaves edge differences unchanged | `test_007_worked_triangle.py::test_constant_shift_leaves_differences_unchanged`; Section 3 derivation | No cognitive or physical inference |
| G007-04 | The verifier audits structure, selected arithmetic restrictions, source bindings, and ordinary Python execution | [Verifier](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/scripts/verify_system_integration.py) | No IPython rendering, semantic teaching-quality check, or learner assessment |
| G007-05 | The saved 20/20 receipt is historical; aggregate paths are stale and the cycle notebook calls a retired norm API | [Receipt](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/headless_receipt.json), [manifest](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/the_symbol_game/lessons/system_integration/lesson_manifest.json), [cochain refusal](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/domain/ddc/cochains.py) | Dated 2026-09-25; explicit child replay is expected to fail; the guide's arithmetic core omits that call |
| G007-06 | Worked-example and reduced-guidance designs have relevant primary research precedent | Sweller and Cooper (1985); Renkl et al. (2002), linked in the guide | Design motivation, not evaluation of this course |
| G007-07 | The cited Lean files establish bounded algebraic/declaration statements | Vendored copies [GrammarCeiling](lean4/GrammarCeiling.lean) and [GrammarDepthCeiling](lean4/GrammarDepthCeiling.lean), with [Expressivity](lean4/Expressivity.lean) | No general expression-depth or human cognitive bound |
| G007-08 | No learner-effect estimate is supplied | [Pedagogy audit](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_education/pedagogy/teaching_and_learning_findings.md), especially its learner-corpus and prediction-record observations | Classroom effectiveness, attention timing, and transfer remain unmeasured |
| G007-09 | The companion notebook repeats the Section 3 lesson with Python fractions only; its stored outputs show the Section 3 values | [Notebook](jupyter_notebooks/007_moving_a_discrepancy.ipynb); `test_007_worked_triangle.py::test_companion_notebook_stores_the_section3_values` | Stored outputs from one execution under Python 3.12; replay compares a fresh execution; no learner data |
| G007-10 | Retained source-bound evidence records a Lean 4.34.0 build, a 21-name selected report, and a 64-declaration full package-local census | [Named report](lean4/axiom_report.txt), [full report](lean4/full_axiom_report.txt), historical `docs/release_validation_2026_10_02.json` | Formal source/report hashes were verified in this review; Lean/Lake unavailable for fresh kernel replay. Generated/private declarations belong to the full census; imported library declarations do not. Whitelist membership is not usage. |
| G007-11 | The legacy test module checks chosen thresholds on supplied values and counts supplied status fields | `test_007_pedagogical_transmission.py::test_learning_metrics_threshold`; `test_007_pedagogical_transmission.py::test_headless_notebook_automated_grading` | Not a measurement of attention or learning, and no notebook execution |
| G007-12 | A source-minus-target mutant passes the cycle-sum checks but fails the predicted coordinate check | Section 3 derivation, notebook sixth code cell, `test_007_evidence_boundaries.py::test_wrong_sign_passes_sum_checks_but_fails_coordinate_prediction` | Sensitivity to this particular sign fault, not all faults |
| G007-13 | The guide includes an exact executable worksheet and the quiz has 24 four-point problems across eight instructional levels | Companion files; `test_007_evidence_boundaries.py::test_study_guide_worksheet_runs_exactly_as_printed` | Proposed rubric and sequence; no measured learning or calibrated readiness cutoff |
| G007-14 | The fresh CPython replay reproduces six ordinary Python code cells without changing the deposited notebook | `tools/replay_companion_notebook.py` and the first-publication receipt | Process and byte-bound finite reproducibility; Jupyter sockets unavailable, so no fresh kernel/rendering check. No learner assessment or full-route integration. |

## Claim hygiene

**Supports:** a source-linked method for authoring executable finite lessons,
a map of the 20-notebook route at the source audit baseline, and one worked lesson checked
with exact fractions.

**Does not support:** universal age suitability, measured attention half-life,
guaranteed mastery, transfer-effect estimates, or a fresh full-route pass.

**Narrowest defensible claim:** the package provides finite worked examples and
named checks whose instructional purpose and evidence limits can be inspected.

**Next check:** record the full cycle notebook's observed diagnostic failure. A
maintained education update must replace retired API calls and reconcile paths
before a new aggregate receipt. Any learning-effect claim additionally needs a
separate learner study.
