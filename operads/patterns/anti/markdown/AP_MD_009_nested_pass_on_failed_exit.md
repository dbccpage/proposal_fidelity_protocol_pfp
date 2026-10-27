---
pattern_id: AP_MD_009
name: nested_pass_on_failed_exit
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_009_stage_status_follows_exit
language: markdown
authority_effect: None
---

# Anti-Pattern: Nested Pass On A Failed Exit (`AP_MD_009`)

## Description

A review stage is blocked and the recorded process exit is nonzero, but a nested verdict field in that same stage says PASSED. Quoting the nested word drops the failed exit.

## Detection Signature

- The stage `status` is `BLOCKED` or `FAIL`, and that stage lists errors.
- A nested field such as `preflight_verdict` is `PASSED`.
- The same review folder records that command's exit as `1`.
- A typed-rule summary in the same stage object has `overall_status` `FAIL`.

## Witness

Historical receipt, not a fresh preflight. This digest did not rerun gates. Source folder `_ic/inr/core_paper_reviews/2026-10-06_po_r2/`.

`exits.txt`:

> preflight exit=1

`run_all.json` stage `preflight_and_envelope_purity` has `status` `BLOCKED`. Its `typed_gate_rules` say `overall_status` `FAIL`, 19 passed, 7 failed, and 5 blockers. The nested verdict in that object is:

> "preflight_verdict": "PASSED"

`gates.md` records the same score as **FAIL**, 19 / 26 rules passed, 5 blockers. `run_all_exit.txt` records `run-all exit=1`.

## Hazard & Failure Mode

- A later note cites `preflight_verdict: PASSED` and treats the blocked stage as clean.
- The nonzero exit and the typed-rule failures stay in the folder but drop out of the summary.
- Deposit defects listed on that stage are then handled as if preflight had accepted them.

## Dual Healthy Pattern

See [HP_MD_009_stage_status_follows_exit](../../helpful/markdown/HP_MD_009_stage_status_follows_exit.md).
