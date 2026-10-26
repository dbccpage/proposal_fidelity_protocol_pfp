---
pattern_id: AP_MD_050
name: zero_digest_governance_pass
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_050_pass_row_names_a_content_digest
language: markdown
authority_effect: None
---

# Anti-Pattern: Zero Digest Governance Pass (`AP_MD_050`)

## Description

A bout summary records `result` `PASS` for `governance-symbol-game` while that row's `digest` is sixty-four zero hex digits. The same summary says the checker was not measured. The zero row is not a governance measurement.

## Detection Signature

- `governance_bundle`, or the same rows under `evidence_receipts`, has `skill_id` `governance-symbol-game`, `result` `PASS`, and `digest` equal to sixty-four `0` characters.
- The same summary has `checker_verdict` `NOT_MEASURED`, `checker_id` `null_checker`, and a reason that no challenge checker is bound.
- `certificate_verified` false, `defect_count` 0, `is_authorized` false, or `terminal_verdict` `COMPOSTED` does not turn the zero row into a pass.
- A sibling row with a nonzero digest, or a row whose `result` is `N_A`, is not this defect.

## Witness

Historical summaries. This digest did not rerun the renderer, the null checker, or any governance skill. Neither run folder contained a `README.md`.

`_ic/darpa/woland/runs/oewas007_full_inventory_control/summary.json`, novella timestamp `2026-10-11 03:28:27 UTC`, `receipt_id` `sha256:cbc3a8fc025c47777e045418575afaf1372834949458142ce6648dd23301a792`. The same row is in `_ic/darpa/woland/runs/oewas007_final_full_inventory_control/summary.json`, novella timestamp `2026-10-11 03:50:47 UTC`, `receipt_id` `sha256:92723f79cb4a1354b568b7c1f3aa46e53a287db4d63e18519e659b2a19122c54`.

Both `governance_bundle` and `evidence_receipts` contain:

> "digest": "0000000000000000000000000000000000000000000000000000000000000000",
> "result": "PASS",
> "skill_id": "governance-symbol-game"

`candidate_checks` for each candidate say `checker_id` `null_checker`, `verdict` `NOT_MEASURED`, and:

> No challenge checker is bound to this bout.

`carrier_measurement.certificate_verified` is false. Its `reason` is `NO_CARRIER_DECLARED: the bout declared no carrier to measure`. `terminal_verdict` is `COMPOSTED`. `fixture_seats` is true. `is_authorized` is false.

The sibling `governance-ddc` row is `PASS` with digest `d447b14fb7f5f2b98b07e02c9c7455b4386cc1e2dc4c2ee55402f04ef1a0a493`. That nonzero digest was not recomputed. `governance-coda` and `governance-clean-arch` are `N_A`. The empty-context sha256 in the same file is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, which is not this zero digest.

## Hazard & Failure Mode

- A later note cites `governance-symbol-game` `PASS` as if the symbol-game rule measured a payload.
- The sixty-four zeros are treated as a content hash. They are not the empty-string sha256.
- `COMPOSTED` or `defect_count` 0 is then read as clearing the `NOT_MEASURED` checker.

## Dual Healthy Pattern

See [HP_MD_050_pass_row_names_a_content_digest](../../helpful/markdown/HP_MD_050_pass_row_names_a_content_digest.md).
