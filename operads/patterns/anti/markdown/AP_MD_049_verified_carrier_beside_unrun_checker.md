---
pattern_id: AP_MD_049
name: verified_carrier_beside_unrun_checker
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_049_carrier_flag_follows_checker
language: markdown
authority_effect: None
---

# Anti-Pattern: Verified Carrier Beside An Unrun Checker (`AP_MD_049`)

## Description

A narrative or receipt sets `certificate_verified` true and `status` `MEASURED` on a carrier block while the same record says the checker was `NOT_MEASURED` and independent compilation was `NOT_RUN`.

## Detection Signature

- `checker_verdict` is `NOT_MEASURED` and `independent_compilation_or_proof` is `NOT_RUN`.
- The nested `carrier_measurement` still says `certificate_verified` true, `defect_count` 0, and `status` `MEASURED`.
- A terminal label such as `COMPOSTED` does not supply the missing check.

## Witness

Historical file `_ic/odni/narratives/uns_foc_006_degree_wise_dsl_verification.md`, run `foc_006_degree_wise_dsl_verification`, 2026-10-03. The prompt asked to verify a degree-wise DSL cochain contract. Act V records `terminal_verdict` `COMPOSTED`, `checker_verdict` `NOT_MEASURED`, and `independent_compilation_or_proof` `NOT_RUN`, while `carrier_measurement.certificate_verified` is true. The sibling narrative `uns_ddc_operad_demo_test.md` uses the same renderer and keeps `certificate_verified` false beside the same `NOT_MEASURED` checker. No checker was rerun.

## Hazard & Failure Mode

- A reader treats the carrier flag as a degree-wise verification.
- A later digest copies `defect_count` 0 into a pass count.

## Dual Healthy Pattern

See [HP_MD_049_carrier_flag_follows_checker](../../helpful/markdown/HP_MD_049_carrier_flag_follows_checker.md).
