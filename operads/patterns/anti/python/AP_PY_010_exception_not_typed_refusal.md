---
pattern_id: AP_PY_010
name: exception_not_typed_refusal
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_010_typed_refusal_boundary
language: python
authority_effect: None
---

# Anti-Pattern: Exception Not Typed Refusal (`AP_PY_010`)

## Description

A bout or gate boundary lets a precondition failure escape as an uncaught exception. Callers that only handle a typed refusal then crash or record a success path.

## Detection Signature

- A digest or decode call sits outside the `try` that maps failures to a refusal record.
- Seen in code-review records for PRs 580 and 584 (`exception-not-refusal`).
- The Rust twin is `AP_RS_006`.

## Hazard & Failure Mode

- An unencodable carrier or a missing field aborts the process instead of returning `Err` or a refusal code.
- The receipt ledger never records the refusal.

## Dual Healthy Pattern

See [HP_PY_010_typed_refusal_boundary](../../helpful/python/HP_PY_010_typed_refusal_boundary.md).
