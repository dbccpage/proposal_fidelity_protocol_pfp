---
pattern_id: HP_MD_026
name: ceiling_stop_keeps_unscored_rows
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_026_ceiling_stop_scored_as_completed_gate
language: markdown
authority_effect: None
---

# Healthy Pattern: A Ceiling Stop Keeps Unscored Rows (`HP_MD_026`)

## Description

When a republication receipt stops on a snapshot byte limit, the summary quotes that detail and the receipt counts. Predicates left `NOT_VERIFIED` stay unscored. A later compression sentence is not a new gate result.

## Construction

- Put the ceiling detail and `counts` in the same sentence as any PASS or FAIL total.
- If the counts are `FAIL` 1 and `NOT_VERIFIED` 51, do not assign `PASS` or `FAIL` to the `NOT_VERIFIED` ids.
- Name `A01` as the recorded failure when its detail is the byte limit. Do not replace it with `A04`, `A05`, `A07`, `F01`, or `H05` unless those ids are `FAIL` in that receipt.
- Keep an open tar question when the same report still asks it. A `.tar.gz` size in prose is a proposal until a receipt records a new snapshot and new counts.
- An empty `snapshot_sha256` and an empty `files` list mean this receipt did not score a snapshot.

## Limit

The witness in [AP_MD_026_ceiling_stop_scored_as_completed_gate](../../anti/markdown/AP_MD_026_ceiling_stop_scored_as_completed_gate.md) is the historical folder `symbol_game_swarm_2026-10-02`, paper 004, dated 2026-10-02. No republication gate, rebuild, pytest, notebook, or Lean command was rerun. Papers 002 and 003 in that folder have Stage Ω counts that match the report. Those matching bullets are not this pattern.

`/adversary-check-sensitivity-pattern` still owns a local stage `PASS` beside a `BLOCKED` republication gate. `AP_MD_016` still owns the canned mathematical-research sentence on the packaging errors. `AP_MD_017` still owns a path-depth error called mathematical research. `AP_MD_020` still owns a local "no notebooks" note when the snapshot lists notebooks and `F01` is `PASS`. This 004 receipt has an empty file list, so that witness shape is not shown here. `AP_MD_022` still owns axiom-free lines beside a failed olean. This folder's historical `lake_build` for 004 is `PASS`, and it was not rerun. `AP_MD_009` still owns a nested `PASSED` inside a failed exit. `/declared-vs-actual-gate` still separates `NOT_APPLICABLE` from `PASS`. `/adversarial-receipt-audit` still owns `visual_inspection` `NOT_VERIFIED` on a documentation `PASS`. `/adversary-proof-scope-rule` still refuses a mechanized-proof sentence when the Lean stage is `NOT_APPLICABLE`.

A receipt that actually records `PASS` and `FAIL` counts may be summarized with those counts. This pattern only refuses scores the ceiling stop did not record.

## Dual Anti-Pattern

See [AP_MD_026_ceiling_stop_scored_as_completed_gate](../../anti/markdown/AP_MD_026_ceiling_stop_scored_as_completed_gate.md).
