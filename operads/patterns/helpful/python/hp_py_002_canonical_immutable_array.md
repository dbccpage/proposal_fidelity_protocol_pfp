---
pattern_id: HP_PY_002
name: canonical_immutable_array
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_002_array_hash_equality_asymmetry
language: python
authority_effect: None
---

# Healthy Pattern: Canonical Immutable Array (`HP_PY_002`)

## Description

Ensure strict hash/equality symmetry by canonicalizing numeric arrays in `__post_init__` to a fixed dtype, C-contiguous layout, normalized zero representations (`-0.0` to `+0.0`), and explicit write-protection (`flags.writeable = False`).

## Remediation & Implementation

```python
import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class NormalizedVector:
    data: np.ndarray

    def __post_init__(self) -> None:
        arr = np.ascontiguousarray(self.data, dtype=np.float64)
        # Gauge fixing or sign reflections (e.g. arr = -arr) must precede zero canonicalization.
        arr[arr == 0.0] = 0.0  # Canonicalize -0.0 after any sign reflections
        arr.flags.writeable = False
        object.__setattr__(self, "data", arr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NormalizedVector):
            return NotImplemented
        return bool(np.array_equal(self.data, other.data))

    def __hash__(self) -> int:
        return hash((self.data.shape, self.data.tobytes()))
```

## Operadic Property

Eliminates `AP_PY_002` witness, ensuring deterministic hash table invariants:
$$\|A_{\text{PY-002}}(H_{\text{PY-002}}(c))\| = 0$$
