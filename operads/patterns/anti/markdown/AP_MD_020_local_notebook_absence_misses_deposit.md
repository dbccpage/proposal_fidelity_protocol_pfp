---
pattern_id: AP_MD_020
name: local_notebook_absence_misses_deposit
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_020_pedagogy_follows_deposit_notebooks
language: markdown
authority_effect: None
---

# Anti-Pattern: Local Notebook Absence Misses The Deposit (`AP_MD_020`)

## Description

A pedagogy stage records that no local notebooks were found and marks itself not applicable. The same review folder's republication snapshot lists notebooks, and a static check counts them. The absence note is then read as "this package has no notebooks."

## Detection Signature

- `interactive_pedagogy_and_replay` is `NOT_APPLICABLE`, and its note says no local notebooks were found.
- The same folder's republication file list contains `.ipynb` paths.
- A static notebook check in that gate reports a nonzero notebook count as `PASS`.
- Fresh-replay checks in that gate stay `NOT_VERIFIED`, and the gate status is `BLOCKED`.
- The local summary can still say `PASS`.

## Witness

Historical receipts. This digest did not rerun gates, open the notebooks, or open the worktree. Source folder `_ic/inr/core_paper_reviews/pfp_mssn_batch_20260929_061529/`.

`003/run_all_receipt.json` (`SWARM_REV_20260929_061529`) has `overall_status` `PASS`. Stage `interactive_pedagogy_and_replay` is `NOT_APPLICABLE`. Its note is:

> No local notebooks found.

The summary verdict is `LOCAL PIPELINE PASSED; INDEPENDENT REPUBLICATION REVIEW REQUIRED`, with `stages_passed` 7.

`003/republication_gate_receipt.json` in that folder lists these snapshot paths:

> demos/demo_3/demo_3_live_protocol.ipynb
> demos/demo_antimorphic_reversal/demo_antimorphic_reversal.ipynb
> demos/demo_token_frontier/demo_token_frontier.ipynb

Check `F01` is `PASS`:

> Validated stored JSON structure for 3 notebooks.

Check `F02` is `PASS` and says fresh execution remains unverified. Checks `F03` and `F05` are `NOT_VERIFIED`. The gate `status` is `BLOCKED` and the verdict is `NOT READY FOR ZENODO REPUBLICATION`.

## Hazard & Failure Mode

- Pedagogy is skipped for a deposit snapshot that contains notebooks.
- A static JSON or stored-cell `PASS` is cited as fresh replay.
- The local `PASS` is cited as if the notebook obligation did not exist. This folder's republication gate is `BLOCKED`.

## Dual Healthy Pattern

See [HP_MD_020_pedagogy_follows_deposit_notebooks](../../helpful/markdown/HP_MD_020_pedagogy_follows_deposit_notebooks.md).
