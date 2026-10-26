---
pattern_id: HP_RS_006
name: result_err_on_refusal_path
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_RS_006_expect_on_refusal_path
language: rust
authority_effect: None
---

# Healthy Pattern: Result Err On A Refusal Path (`HP_RS_006`)

## Description

Seat-turn serialization returns `Result`. A encode failure becomes `Err` and the caller writes the refusal. The path does not call `.expect()` or `.unwrap()`.

## Structural Signature

```rust
fn prompt_block(value: &Value) -> Result<Vec<u8>, Refusal> {
    serde_json::to_vec(value).map_err(|err| Refusal::encode(err.to_string()))
}
```

## Remediation Applied

- Replace `.expect()` on the seat-turn serializer with `map_err`.
- Test a non-serializable value and assert `Err`.
