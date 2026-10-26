---
pattern_id: HP_PY_010
name: typed_refusal_boundary
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_010_exception_not_typed_refusal
language: python
authority_effect: None
---

# Healthy Pattern: Typed Refusal Boundary (`HP_PY_010`)

## Description

Every input that can fail on a bout boundary is decoded inside the handler that returns a typed refusal. The function's success type is not used for that failure.

## Structural Signature

```python
def run_bout(carrier: object) -> Result:
    try:
        digest = instruction_request_digest(carrier)
    except (TypeError, ValueError) as exc:
        return Err(refusal("CARRIER_NOT_ENCODABLE", str(exc)))
    return proceed(digest)
```

## Remediation Applied

- Move the digest or decode call into the refusal handler.
- Test the unencodable carrier and assert the refusal code, not an exception.
