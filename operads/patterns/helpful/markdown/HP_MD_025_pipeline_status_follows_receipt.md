---
pattern_id: HP_MD_025
name: pipeline_status_follows_receipt
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_025_rollup_pipeline_lags_receipt
language: markdown
authority_effect: None
---

# Healthy Pattern: Pipeline Status Follows The Receipt (`HP_MD_025`)

## Description

A pipeline sentence names the co-located `run_all_receipt.json`: its `review_id`, `timestamp_utc`, and `overall_status`. A series rollup that disagrees is quoted as the rollup, not as that review.

## Construction

- Bind each pipeline stage to the receipt field that records it. Do not copy `swarm_review_summary.json` when that row's status or error is absent from the receipt.
- If the rollup does not cite the receipt `review_id`, keep both bytes. Label the rollup line as not that review.
- Do not restore `MISSING_DUAL_WITNESS` unless that string is in the receipt's `errors`.
- Do not replace a receipt stage `PASS` and its `pytest_summary` with the rollup's `NOT_APPLICABLE`.
- Leave the republication receipt's own `status` and `verdict` on that artifact. A run-all `PASS` does not edit them.

## Limit

The witness in [AP_MD_025_rollup_pipeline_lags_receipt](../../anti/markdown/AP_MD_025_rollup_pipeline_lags_receipt.md) is the historical folder `symbol_game_swarm_2026-09-28`. No gate, pytest, or Lean command was rerun. Package 002's receipt is `SWARM_REV_20260928_164851` at `2026-09-28T16:48:51.241355+00:00` with `overall_status` `PASS`. Package 003's receipt is `SWARM_REV_20260928_170140` at `2026-09-28T17:01:40.412074+00:00`. Packages 004 through 009 still match the rollup. Those matches are not cleared by this pattern.

Package 002's `republication_gate_receipt.json` has `status` `BLOCKED` and `verdict` `NOT READY FOR ZENODO REPUBLICATION`. Check `A03` is `FAIL` for missing `LICENSE`, `MANIFEST.sha256`, `SHA256SUMS`, and `zenodo_metadata.json`. The snapshot lists `tests/test_frontier_search.py`. Package 003's gate receipt is also `BLOCKED` with that same verdict, and its snapshot lists `demos/demo_3/` and `validation/ownership_guard.json`. The report's layout words match those snapshot paths. They are not `run_all` errors. A local `PASS` beside that blocked gate stays with `/adversary-check-sensitivity-pattern`. The receipt sentence `READY FOR ZENODO REPUBLICATION` does not discharge the gate.

`/core-red-team` still owns a missing dual certificate when the receipt records it. Package 009 in this folder is `NO_GO` with `MISSING_DUAL_WITNESS` and dual `PRIMAL_ONLY`. That blocker is in the receipt. This pattern does not remove it. `/adversary-proof-scope-rule` still refuses a mechanized-proof sentence when Lean is `NOT_APPLICABLE`. `/declared-vs-actual-gate` still separates `NOT_APPLICABLE` from `PASS`, including a `stages_passed` count that includes `NOT_APPLICABLE`. `AP_MD_009` still owns package 004's preflight `status` `BLOCKED` with nested `preflight_verdict` `PASSED`. `AP_MD_016` and `AP_MD_017` still own the canned mathematical-research sentence. On 004 that sentence follows a Win32 path-depth count and a pytest exit whose quoted body is `PytestDeprecationWarning`. On 008 it follows the raw repo path `engine/crates_rs/`. On 009 it follows the dual-witness error and does not name that error. `AP_MD_022` does not apply: no receipt here fails `lake build` while printing axiom-free lines. `AP_MD_026` still owns a byte-limit stop scored as a finished gate. This folder's disagreement is an earlier pipeline row, not that scoreboard.

The later `PASS` is historical. It does not prove the paper text is free of an exactness claim, and it does not prove the rollup row was never true.

## Dual Anti-Pattern

See [AP_MD_025_rollup_pipeline_lags_receipt](../../anti/markdown/AP_MD_025_rollup_pipeline_lags_receipt.md).
