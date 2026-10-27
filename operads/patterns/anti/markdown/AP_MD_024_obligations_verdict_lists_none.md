---
pattern_id: AP_MD_024
name: obligations_verdict_lists_none
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_024_verdict_matches_obligation_list
language: markdown
authority_effect: None
---

# Anti-Pattern: Obligations Verdict Lists None (`AP_MD_024`)

## Description

An Old Man report's verdict is `GO_WITH_OBLIGATIONS`, and the same report's unresolved-obligations line is `None`. The mathematical stage that records that verdict is `PASS` and keeps the word only as a warning.

## Detection Signature

- The report verdict is `GO_WITH_OBLIGATIONS`.
- The same report says unresolved obligations or blockers are `None`.
- The mathematical stage `status` is `PASS`, its `errors` array is empty, and a warning repeats `GO_WITH_OBLIGATIONS`.
- `red_team_dual_witness` may be `EXACT_VERIFIED`. That dual word is not an obligation sentence.

## Witness

Historical receipt and report. This digest did not rerun gates, Red Team, pytest, ruff, notebooks, or Lean. Source folder `_ic/inr/core_paper_reviews/symbol_game_003_010_20260928_232350/`.

`004_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection/red_team/omc_report_004_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection.md`, audit date 2026-09-28, target SHA-256 `d831fe1f3cc361e05c6238a3c1ebd47356756ad217697051d43ab9048d1ea54e`:

> - **Verdict:** GO_WITH_OBLIGATIONS
> - **Unresolved Obligations / Blockers:** None

`004_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection/run_all_receipt.json` (`SWARM_REV_20260928_232355`) has `overall_status` `NEEDS_REVISION`. Stage `mathematical_foundations_and_dialect_firewall` is `PASS`. Its details record `red_team_verdict` `GO_WITH_OBLIGATIONS` and `red_team_dual_witness` `EXACT_VERIFIED`. The stage warning is:

> Red Team Red Team: GO_WITH_OBLIGATIONS (Dual: EXACT_VERIFIED)

That stage's `errors` array is empty. Seven other reports in this folder do not pair `GO_WITH_OBLIGATIONS` with `None`. Paper 008 records `EXACT_VERIFIED` with verdict `GO`.

## Hazard & Failure Mode

- A later note treats `GO_WITH_OBLIGATIONS` as an open mathematical obligation that the report never wrote.
- The same note treats `Blockers: None` and stage `PASS` as Old Man clearance.
- Those two readings cannot both be this report.

## Dual Healthy Pattern

See [HP_MD_024_verdict_matches_obligation_list](../../helpful/markdown/HP_MD_024_verdict_matches_obligation_list.md).
