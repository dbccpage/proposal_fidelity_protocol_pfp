---
pattern_id: AP_MD_046
name: review_clears_same_hash_counterexample
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_046_same_hash_schema_status_kept
language: markdown
authority_effect: None
---

# Anti-Pattern: A Review Clears A Same-Hash Counterexample (`AP_MD_046`)

## Description

A pre-freeze note says a custody review found no material counterexample. A schema file for that same runner hash still has status `COUNTEREXAMPLE` and residual `UNREACHED_PERMISSION_SCHEMA`.

## Detection Signature

- `quiz08_research/pre_freeze_review.md` names runner SHA256 `9d9343cd3cbc725a54479ab8b637a367dbda79e516d6a824818e41c369cfdd8c`.
- The custody bullet says `no material counterexample` and that the reviewer did not rerun the full suite.
- `quiz08_research/schema_counterexample.json` records the same `code_sha256`, `status` `COUNTEREXAMPLE`, `claim_id` `QUERY_CUSTODY`, and `residual_id` `UNREACHED_PERMISSION_SCHEMA`.
- `quiz08_delivery_20261007/verification.json` says `status` `PASS` and does not record that residual or that runner hash.

## Witness

Historical files under `_ic/darpa/research/briefs/pfp_migration/`. This digest did not run `reproduce_permission_gap.py`. Only the first 60 lines of the schema file were read.

> Runner SHA256: 9d9343cd3cbc725a54479ab8b637a367dbda79e516d6a824818e41c369cfdd8c.

> It reported512 transition truth-table combinations (one executes),3672 chain cases,16 stale permissions,2 replay variants,7 proposal corruptions and2 snapshot attacks; no material counterexample. It did not rerun the full suite.

> "status": "COUNTEREXAMPLE",
> "claim_id": "QUERY_CUSTODY",
> "residual_id": "UNREACHED_PERMISSION_SCHEMA",
> "code_sha256": "9d9343cd3cbc725a54479ab8b637a367dbda79e516d6a824818e41c369cfdd8c",

## Hazard & Failure Mode

- A later note treats the review sentence as closing `UNREACHED_PERMISSION_SCHEMA`.
- A historical delivery `PASS` is cited as a fresh permission-schema result.

## Dual Healthy Pattern

See [HP_MD_046_same_hash_schema_status_kept](../../helpful/markdown/HP_MD_046_same_hash_schema_status_kept.md).
