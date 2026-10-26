---
pattern_id: HP_MD_049
name: carrier_flag_follows_checker
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_049_verified_carrier_beside_unrun_checker
language: markdown
authority_effect: None
---

# Healthy Pattern: The Carrier Flag Follows The Checker (`HP_MD_049`)

## Description

When the checker verdict is `NOT_MEASURED` and independent compilation is `NOT_RUN`, the carrier block does not say `certificate_verified` true. A `COMPOSTED` terminal label stays a narrative disposition.

## Construction

- Quote `checker_verdict` and `independent_compilation_or_proof` in the same sentence as any carrier flag.
- If those two fields are `NOT_MEASURED` and `NOT_RUN`, keep `certificate_verified` false or omit the carrier block.
- Do not promote `defect_count` 0 or a dual-witness list into a degree-wise verification.
- A sibling narrative that already keeps the flag false is the control, not a second pass.

## Limit

The witness in [AP_MD_049_verified_carrier_beside_unrun_checker](../../anti/markdown/AP_MD_049_verified_carrier_beside_unrun_checker.md) is the historical narrative pair dated 2026-10-03. No DSL checker, Lean command, or renderer was rerun. `AP_MD_014` still owns a pass verdict with a zero payload count. `AP_MD_026` still owns a ceiling stop scored as a finished gate. This pattern only binds a verified-looking carrier to a checker that the same record says did not run.
