---
pattern_id: HP_MD_050
name: pass_row_names_a_content_digest
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_050_zero_digest_governance_pass
language: markdown
authority_effect: None
---

# Healthy Pattern: A Pass Row Names A Content Digest (`HP_MD_050`)

## Description

A `PASS` governance row names a digest that is not sixty-four zeros. An all-zero digest stays `N_A` or `NOT_MEASURED` in the same sentence as `checker_verdict`.

## Construction

- Quote `skill_id`, `result`, and `digest` together.
- If `digest` is sixty-four `0` characters, do not write `PASS` for that row. Keep it with `checker_verdict` `NOT_MEASURED`, or mark the row `N_A`.
- Do not promote `certificate_verified` false, `defect_count` 0, or `terminal_verdict` `COMPOSTED` into a governance measurement. Those fields can stay honest and still sit beside the zero row.
- Leave a sibling nonzero digest on its own row. Do not recompute it in order to clear the zero row.

## Limit

The witness in [AP_MD_050_zero_digest_governance_pass](../../anti/markdown/AP_MD_050_zero_digest_governance_pass.md) is the historical pair of inventory summaries dated 2026-10-11. No renderer, null checker, or governance skill was rerun. The pattern does not claim the zero row has been removed from those files.

`AP_MD_049` still owns `certificate_verified` true beside `NOT_MEASURED` and `NOT_RUN`. These summaries keep that flag false. That honesty is not this repair. `AP_MD_014` still owns `PASS_TO_MASTER` with a zero demo count. `AP_PY_005` still owns treating any 64-hex shape as fitness evidence without hashing a payload. This pattern only binds a summary `PASS` whose digest is the zero sentinel.

`/woland-check-sensitivity-pattern` still owns an empty counterexample search. A `NON_BLOCKING` critique that says no search was run is not this pattern. `governance-ddc` `PASS` with a nonzero digest, and the `N_A` rows, are not this defect.
