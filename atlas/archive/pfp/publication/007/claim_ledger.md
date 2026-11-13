# Companion 007 claim ledger

Jeremy H. Carroll · 2026-09-28 · Version 1.1.0 · Author-review revision

Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The current guide concerns curriculum design and finite instructional
artifacts. It supersedes the former learning-effect and
cognitive-ceiling claims. Package tests are named as `file::function`.
Current execution results belong to the dated review receipt.
Identifiers G007-01 to G007-08 keep their earlier meaning; G007-09 to
G007-11 are new in this revision.

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                   Evidence                                                                                                                                                                                                                                                                        Limit
  ----------------- ----------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------
  G007-01           The current deep route  [Route README](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/the_symbol_game/lessons/system_integration/README.md) and the 20 paths in guide Section 4                                                       File presence and
                    contains 20 named                                                                                                                                                                                                                                                                                       route declaration;
                    notebooks in five                                                                                                                                                                                                                                                                                       no fresh execution
                    groups                                                                                                                                                                                                                                                                                                  inference

  G007-02           The triangle residual   `test_007_worked_triangle.py::test_potential_adjustment_moves_the_residual`; `test_007_worked_triangle.py::test_section3_code_blocks_run_as_printed`;                                                                                                                           Declared finite
                    changes from            [notebook](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/the_symbol_game/lessons/system_integration/100_novices/04_cycle_repair.ipynb)                                                                       example and
                    (1/3,1/3,1/3) to                                                                                                                                                                                                                                                                                        telescoping
                    (0,0,1) under the                                                                                                                                                                                                                                                                                       identity; the
                    displayed potential                                                                                                                                                                                                                                                                                     printed-block
                    adjustment                                                                                                                                                                                                                                                                                              check needs the
                                                                                                                                                                                                                                                                                                                            full repository

  G007-03           A constant potential    `test_007_worked_triangle.py::test_constant_shift_leaves_differences_unchanged`; Section 3 derivation                                                                                                                                                                           No cognitive or
                    shift leaves edge                                                                                                                                                                                                                                                                                       physical inference
                    differences unchanged

  G007-04           The verifier audits     [Verifier](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/scripts/verify_system_integration.py)                                                                                                               No IPython
                    structure, selected                                                                                                                                                                                                                                                                                     rendering,
                    arithmetic                                                                                                                                                                                                                                                                                              semantic
                    restrictions, source                                                                                                                                                                                                                                                                                    teaching-quality
                    bindings, and ordinary                                                                                                                                                                                                                                                                                  check, or learner
                    Python execution                                                                                                                                                                                                                                                                                        assessment

  G007-05           The saved 20/20 receipt [Receipt](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/the_symbol_game/lessons/system_integration/headless_receipt.json),                                                                                   Dated 2026-09-25;
                    is historical;          [manifest](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/the_symbol_game/lessons/system_integration/lesson_manifest.json), [cochain                                                                          explicit child
                    aggregate paths are     refusal](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/pfp/domain/ddc/cochains.py)                                                                                                                             replay is expected
                    stale and the cycle                                                                                                                                                                                                                                                                                     to fail; the
                    notebook calls a                                                                                                                                                                                                                                                                                        guide's arithmetic
                    retired norm API                                                                                                                                                                                                                                                                                        core omits that
                                                                                                                                                                                                                                                                                                                            call

  G007-06           Worked-example and      Sweller and Cooper (1985); Renkl et al. (2002), linked in the guide                                                                                                                                                                                                             Design motivation,
                    reduced-guidance                                                                                                                                                                                                                                                                                        not evaluation of
                    designs have relevant                                                                                                                                                                                                                                                                                   this course
                    primary research
                    precedent

  G007-07           The cited Lean files    Vendored copies [GrammarCeiling](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/lean4/GrammarCeiling.lean) and No general
                    establish bounded       [GrammarDepthCeiling](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/lean4/GrammarDepthCeiling.lean), with     expression-depth
                    algebraic/declaration   [Expressivity](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/lean4/Expressivity.lean)                         or human cognitive
                    statements                                                                                                                                                                                                                                                                                              bound

  G007-08           No learner-effect       [Pedagogy audit](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/pedagogy/teaching_and_learning_findings.md), especially its learner-corpus and prediction-record observations                                 Classroom
                    estimate is supplied                                                                                                                                                                                                                                                                                    effectiveness,
                                                                                                                                                                                                                                                                                                                            attention timing,
                                                                                                                                                                                                                                                                                                                            and transfer
                                                                                                                                                                                                                                                                                                                            remain unmeasured

  G007-09           The companion notebook  [Notebook](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/jupyter_notebooks/007_moving_a_discrepancy.ipynb);   Stored outputs
                    repeats the Section 3   `test_007_worked_triangle.py::test_companion_notebook_stores_the_section3_values`                                                                                                                                                                                               from one execution
                    lesson with Python                                                                                                                                                                                                                                                                                      under Python 3.12;
                    fractions only; its                                                                                                                                                                                                                                                                                     replay compares a
                    stored outputs show the                                                                                                                                                                                                                                                                                 fresh execution;
                    Section 3 values                                                                                                                                                                                                                                                                                        no learner data

  G007-10           The vendored Lean       [Axiom report](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/lean4/axiom_report.txt),                         Covers the three
                    project builds with     [census](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/lean4/Census.lean),                                    vendored files
                    Lean 4.34.0 and no      `tools/replay_lean_axiom_census.py`                                                                                                                                                                                                                                             only; each differs
                    external library; its                                                                                                                                                                                                                                                                                   from its source
                    21 declarations use no                                                                                                                                                                                                                                                                                  only by a
                    axioms except `propext`                                                                                                                                                                                                                                                                                 provenance comment
                    and `Quot.sound` in two
                    list bounds

G007-11           The legacy test module  `test_007_pedagogical_transmission.py::test_learning_metrics_threshold`; `test_007_pedagogical_transmission.py::test_headless_notebook_automated_grading`                                                                                                                       Not a measurement
                    checks chosen                                                                                                                                                                                                                                                                                           of attention or
                    thresholds on supplied                                                                                                                                                                                                                                                                                  learning, and no
                    values and counts                                                                                                                                                                                                                                                                                       notebook execution
                    supplied status fields
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Claim hygiene

**Supports:** a source-linked method for authoring executable finite
lessons, a complete map of the current 20-notebook route, and one worked
lesson checked with exact fractions.

**Does not support:** universal age suitability, measured attention
half-life, guaranteed mastery, transfer-effect estimates, or a fresh
full-route pass.

**Narrowest defensible claim:** the package provides finite worked
examples and named checks whose instructional purpose and evidence
limits can be inspected.

**Next check:** record the full cycle notebook's observed diagnostic
failure. A maintained education update must replace retired API calls
and reconcile paths before a new aggregate receipt. Any learning-effect
claim additionally needs a separate learner study.
