---
pattern_id: HP_MD_046
name: same_hash_schema_status_kept
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_046_review_clears_same_hash_counterexample
language: markdown
authority_effect: None
---

# Healthy Pattern: The Same-Hash Schema Status Stays (`HP_MD_046`)

## Description

When a review and a schema file share a runner hash, the note quotes the schema `status` and `residual_id` beside any "no material counterexample" sentence. The residual stays `COUNTEREXAMPLE` until a receipt names that hash and that residual.

## Construction

- Put `COUNTEREXAMPLE`, `UNREACHED_PERMISSION_SCHEMA`, `QUERY_CUSTODY`, and `code_sha256` `9d9343cd3cbc725a54479ab8b637a367dbda79e516d6a824818e41c369cfdd8c` in the same note as the custody sentence.
- Do not replace that residual with the reviewer's probe counts. Those counts are not a rerun of the schema file.
- Do not read a delivery `status` of `PASS` as clearing the residual when that file has no `runner_sha256` and does not name `UNREACHED_PERMISSION_SCHEMA`.
- Leave the unread tail of `schema_counterexample.json` unread. Do not run `reproduce_permission_gap.py` to fill it.

## Limit

The witness in [AP_MD_046_review_clears_same_hash_counterexample](../../anti/markdown/AP_MD_046_review_clears_same_hash_counterexample.md) is the historical Quiz08 pair. The delivery file is timestamped `2026-10-07T11:45:37.0475804Z`. No permission-gap script, pytest, or gate was rerun. `/woland-check-sensitivity-pattern` still owns the meron R6 `bond_locality` check that does not bind K4. `AP_MD_016` still owns a gate failure called mathematical research; this review already says the Windows parameter-name failure was not a mathematical counterexample. `AP_MD_014` still owns a pass with a zero payload. `AP_MD_020` still owns a local notebook note against a snapshot that lists notebooks. `AP_MD_026` still owns a ceiling stop scored as a finished gate. `/woland-proof-scope-rule` still owns finite tests stated as a theorem. This pattern only refuses clearing this same-hash schema residual from the review sentence or the historical delivery `PASS`.

## Dual Anti-Pattern

See [AP_MD_046_review_clears_same_hash_counterexample](../../anti/markdown/AP_MD_046_review_clears_same_hash_counterexample.md).
