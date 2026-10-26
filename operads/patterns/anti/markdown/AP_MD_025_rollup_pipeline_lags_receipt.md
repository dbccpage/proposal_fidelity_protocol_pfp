---
pattern_id: AP_MD_025
name: rollup_pipeline_lags_receipt
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_025_pipeline_status_follows_receipt
language: markdown
authority_effect: None
---

# Anti-Pattern: Rollup Pipeline Lags The Receipt (`AP_MD_025`)

## Description

A series report and `swarm_review_summary.json` state a pipeline status the co-located `run_all_receipt.json` does not record. The receipt has a later `review_id`. Quoting the rollup restores a blocker that receipt's `errors` array does not contain, or it marks a stage `NOT_APPLICABLE` while the receipt marks that stage `PASS`.

## Detection Signature

- The folder has both a series rollup and `<slug>/run_all_receipt.json`.
- The rollup's `run_all.overall_status`, a stage status, or a stage error is not the value in that receipt.
- The receipt has a `review_id` and `timestamp_utc`. The rollup does not cite that `review_id`.
- Packages whose receipts match the rollup are not this defect.

## Witness

Historical receipts. This digest did not rerun gates, pytest, or Lean. Source folder `_ic/inr/omega_paper_reviews/symbol_game_swarm_2026-09-28/`.

`swarm_review_summary.json` for `002_the_symbol_game_signed_presentations_and_search_frontier` sets `run_all.exit_code` to 1 and `overall_status` to `NEEDS_REVISION`. Stage 1 is `FAIL`. Its error is:

> Old Man Red Team Blocker: MISSING_DUAL_WITNESS: Exactness claimed without dual certificate or gap witness.

That rollup row also warns that `proves` occurs twice and `universal` once, and it sets stage `techne_code_swarm_and_tests` to `NOT_APPLICABLE`. `THE_SYMBOL_GAME_SWARM_REVIEW_REPORT.md` puts the same package on `NEEDS_REVISION` and names that dual-witness blocker, tests under `tests/` rather than `code/tests/`, and those hype words.

`002_the_symbol_game_signed_presentations_and_search_frontier/run_all_receipt.json` is `SWARM_REV_20260928_164851`, `timestamp_utc` `2026-09-28T16:48:51.241355+00:00`. `overall_status` is `PASS`. Stage 1 is `PASS`, `old_man_verdict` is `GO`, and `old_man_dual_witness` is `N_A`. Stage 1 `warnings` is empty. `old_man_survived` includes:

> Obstruction persistence admitted honestly; no spurious exactness claim.

Stage 3 is `PASS` and `pytest_summary` ends in `[100%]`. `summary.verdict` is `READY FOR ZENODO REPUBLICATION`. `total_errors` is 0. That receipt does not contain `MISSING_DUAL_WITNESS`.

The same rollup sets package 003 stage `techne_code_swarm_and_tests` to `NOT_APPLICABLE`. `003_the_symbol_game_host_admitted_failure_detectors/run_all_receipt.json` is `SWARM_REV_20260928_170140`, `timestamp_utc` `2026-09-28T17:01:40.412074+00:00`. That stage is `PASS` with `pytest_summary` ending in `[100%]`.

Receipts 004 through 009 in this folder are timestamped from `2026-09-28T15:27:59` through `2026-09-28T15:31:52`, and their `run_all` errors match the rollup. That agreement is not this pattern. No generation log was read. The supported reading is that the rollup row was not updated to the later 002 and 003 review ids.

## Hazard & Failure Mode

- A later note reopens `MISSING_DUAL_WITNESS` for package 002 after this receipt says there is no spurious exactness claim.
- A later note treats package 003 as having no techne stage because the rollup says `NOT_APPLICABLE`, and drops the recorded pytest line.
- The receipt word `PASS`, or `READY FOR ZENODO REPUBLICATION`, is then read as deposit clearance. The co-located republication receipt is a separate artifact.

## Dual Healthy Pattern

See [HP_MD_025_pipeline_status_follows_receipt](../../helpful/markdown/HP_MD_025_pipeline_status_follows_receipt.md).
