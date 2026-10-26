---
pattern_id: AP_MD_028
name: runner_outage_scored_as_package_fail
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_028_stage_fail_names_the_runner
language: markdown
authority_effect: None
---

# Anti-Pattern: Runner Outage Scored As A Package Fail (`AP_MD_028`)

## Description

A formal Lean stage and a test stage are `FAIL`, and the package is `NEEDS_REVISION`, because the runner could not reach GitHub and because the selected interpreter has no pytest module. The stderr names the network and the missing module. Quoting the stage status drops that cause.

## Detection Signature

- Stage `formal_lean4_mechanization` has `status` `FAIL`. The error says `lake build failed (exit 1)`, `Failed to connect to github.com port 443`, and `external command 'git' exited with code 128`.
- That error does not say `failed to create file` for an `.olean`, and it does not print `does not depend on any axioms`.
- Stage `techne_code_swarm_and_tests` has `status` `FAIL`. The error names `Python39_64\python.exe` and `No module named pytest`. It does not name a failed test.
- `overall_status` is `NEEDS_REVISION`. Stage `packaging_and_release_bundle` is `BLOCKED` by those two stages.
- A separate historical review of the same commit records `lake build` exit 0 and pytest exit 0. That review is not this receipt.

## Witness

Historical receipts and reviews. This digest did not rerun gates, pytest, lake, or the network check. Source folder `_ic/inr/omega_paper_reviews/`.

`008_so_k_invariant_gauge_classification_swarm_receipt.json` (`SWARM_REV_20260927_223121`) has `overall_status` `NEEDS_REVISION`. Stage `formal_lean4_mechanization` is `FAIL`. Its error includes:

> fatal: unable to access '<https://github.com/leanprover-community/mathlib4/>': Failed to connect to github.com port 443 after 35 ms: Could not connect to server

> error: external command 'git' exited with code 128

Stage `techne_code_swarm_and_tests` is `FAIL`. Its error is:

> pytest failed (exit 1): C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe: No module named pytest

Stage `packaging_and_release_bundle` is `BLOCKED` because of stage 2 and stage 3. The same file's `summary.stages_blocked` is 3.

`009_coordinate_wise_additivity_swarm_receipt.json` uses the same `review_id` and the same pytest line. Its clone error says `after 55 ms` and names the Paper 009 `lean4\p\mathlib` path. It is the same runner pair, not a second defect.

`so_k_invariant_gauge_classification_v2.0.0_republication_review.md`, same commit `e4a1214bb3e47570b0f74ecc9117c98f27a26b5e`, records `lake build` exit 0 (1,678 jobs) and pytest exit 0 (102 tests) under CPython 3.14.2. `coordinate_wise_additivity_v1.0.0_republication_review.md` records `lake build` exit 0 (921 jobs) and pytest exit 0 (32 tests) under the same interpreter. Those exits do not rewrite the swarm receipts. Both reviews remain `NOT READY FOR ZENODO REPUBLICATION` for other findings.

## Hazard & Failure Mode

- A later note treats `formal_lean4_mechanization: FAIL` as a Lean proof defect.
- A later note treats `pytest failed (exit 1)` as a failing suite. The named interpreter never imported pytest.
- Packaging `BLOCKED` is then cited as a release defect of the candidate rather than a block on a runner outage.
- The separate exit-0 rows are merged into the swarm receipt, or the swarm `FAIL` is cited as if that later run had failed.

## Dual Healthy Pattern

See [HP_MD_028_stage_fail_names_the_runner](../../helpful/markdown/HP_MD_028_stage_fail_names_the_runner.md).
