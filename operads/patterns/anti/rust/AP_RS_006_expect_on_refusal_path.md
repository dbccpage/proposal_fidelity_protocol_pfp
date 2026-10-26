---
pattern_id: AP_RS_006
name: expect_on_refusal_path
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_RS_006_result_err_on_refusal_path
language: rust
authority_effect: None
---

# Anti-Pattern: Expect On A Refusal Path (`AP_RS_006`)

## Description

Serialization or seat-turn code uses `.expect()` or `.unwrap()` where the function can already return `Result`. A bad payload panics the host instead of producing a refusal.

## Detection Signature

- `.expect(` or `.unwrap(` on `serde_json::to_vec`, `to_string`, or a prompt-block builder inside a seat-turn path.
- Seen in the PR 580 review (`panic-not-refusal`).

## Hazard & Failure Mode

- One malformed candidate aborts the process.
- No refusal record is written for that turn.

## Dual Healthy Pattern

See [HP_RS_006_result_err_on_refusal_path](../../helpful/rust/HP_RS_006_result_err_on_refusal_path.md).
