---
pattern_id: HP_PY_011
name: refuse_when_gates_absent
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_011_fail_open_absent_gates
language: python
authority_effect: None
---

# Healthy Pattern: Refuse When Gates Are Absent (`HP_PY_011`)

## Description

Missing gates are not authority. At residual 0, `detect_counterfeit_descent` returns `TerminalStatus.NON_AUTHORITY_HALT` when `gates` is `None`. `TerminalStatus.AUTHORITY` is returned only after the gate stack passes and the terminal witness matches the extracted answer.

## Structural Signature

```python
if gates is None:
    return False, TerminalOutcome(
        status=TerminalStatus.NON_AUTHORITY_HALT,
        refusal_reason=RefusalReason.NON_AUTHORITY_TERMINAL,
        details="Zero residual defect alone without verified gate stack does not confer authority.",
    )
```

## Remediation Applied

- On `gates is None`, return `NON_AUTHORITY_HALT`, not `AUTHORITY`.
- Test residual 0 with `gates=None` and assert `TerminalStatus.NON_AUTHORITY_HALT`.
