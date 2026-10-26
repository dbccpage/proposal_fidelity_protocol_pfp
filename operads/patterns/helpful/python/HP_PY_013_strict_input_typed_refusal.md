---
pattern_id: HP_PY_013
name: strict_input_typed_refusal
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_013_silent_input_schema_coercion
language: python
authority_effect: None
---

# Healthy Pattern: Strict Input Typed Refusal (`HP_PY_013`)

## Description

Parsers and boundary ingress validators strictly validate input types and structures against declared schemas. Any malformed structure (such as unexpected scalars, malformed step dictionaries, or unrecognized elements) triggers an immediate, typed refusal record without silent transformation or data dropping.

## Structural Signature

```python
def parse_workflow_step(raw_step: object) -> Result[WorkflowStep, RefusalRecord]:
    if not isinstance(raw_step, dict):
        return Err(RefusalRecord(
            code="BAD_STEP",
            reason=f"Step must be a mapping, got {type(raw_step).__name__}: {raw_step!r}",
            severity="P0",
        ))
    if "op" not in raw_step or not isinstance(raw_step["op"], str):
        return Err(RefusalRecord(
            code="INVALID_OPERATION_NAME",
            reason="Step mapping missing non-empty string 'op' field",
            severity="P0",
        ))
    return Ok(WorkflowStep.from_dict(raw_step))
```

## Remediation Applied

- Reject non-dict steps with `BAD_STEP` typed refusal.
- Refuse mixed lists immediately if any item violates schema rather than silently filtering valid items.
- Write unit tests covering malformed scalars, non-string operation keys, and mixed collections, asserting explicit refusal outputs.
