---
pattern_id: HP_PY_014
name: complete_interface_annotation_parity
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_014_incomplete_interface_forward_ref_defect
language: python
authority_effect: None
---

# Healthy Pattern: Complete Interface and Annotation Parity (`HP_PY_014`)

## Description

Value objects and domain interfaces declare `from __future__ import annotations` at the top of the module to resolve forward self-references cleanly, and explicitly implement all contractual methods declared in the specification before proposing the candidate to the review oracle.

## Structural Signature

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ExactRational:
    numerator: int
    denominator: int

    @classmethod
    def from_string(cls, val: str) -> ExactRational:
        # Full parsing and exact rational reduction
        ...

    def __sub__(self, other: ExactRational) -> ExactRational:
        ...

    def __truediv__(self, other: ExactRational) -> ExactRational:
        if other.numerator == 0:
            raise ZeroDivisionError("division by zero in exact rational arithmetic")
        ...
```

## Remediation Applied

- Always place `from __future__ import annotations` as the first statement in Python source files containing recursive or self-referential class type annotations.
- Verify every specified method and constructor (`from_string`, `__sub__`, `__truediv__`) is defined and tested prior to candidate diff generation.
- Execute a hermetic import smoke test (`python -c "import <module>"`) before emitting candidate diffs.
