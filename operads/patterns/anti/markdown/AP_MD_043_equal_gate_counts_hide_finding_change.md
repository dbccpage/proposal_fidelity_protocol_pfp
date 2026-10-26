---
pattern_id: AP_MD_043
name: equal_gate_counts_hide_finding_change
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_043_gate_summary_names_dated_findings.md
language: markdown
authority_effect: None
---

# Anti-Pattern: Equal Gate Counts Hide a Finding Change (`AP_MD_043`)

## Description

Two publication receipts share the count tuple 34 rules, 26 passed, and 8 failed, and a later summary treats that tuple as one unchanged failure set.

## Detection Signature

- `receipts/baseline_gates.json` at `2026-10-08T21:07:23.726327+00:00` records `overall_status` `FAIL`, `passed_rules_count` 26, and `failed_rules_count` 8. In the read prefix, `R_MANIFEST_BIJECTION` lists `.pytest_cache/.gitignore` among unmanifested paths and `indexed_count` 1646. `R_RESTRICTED_DIR_STRUCTURE` lists `.pytest_cache/` and `__pycache__/` as well as `evidence/`.
- `receipts/r5_policy_gates.json` at `2026-10-09T00:40:45.669963+00:00` records the same 26 and 8. In the read prefix, `R_MANIFEST_BIJECTION` lists only `manifests/coverage.json`, with `indexed_count` 1682. `R_RESTRICTED_DIR_STRUCTURE` names `evidence/` and does not name `.pytest_cache/`.
- The README sentence "26 passing rules and eight failures" does not by itself say which receipt's findings those eight are.

## Hazard & Failure Mode

- A reader treats the earlier pytest-cache paths as the later eight failures, or imports `manifests/coverage.json` back into the 2026-10-08 manifest finding.
- Adding 8 and 8, or calling the two count tuples one result, misstates both historical runs.

## Dual Healthy Pattern

See [HP_MD_043_gate_summary_names_dated_findings.md](../../helpful/markdown/HP_MD_043_gate_summary_names_dated_findings.md).
