---
pattern_id: AP_PY_002
name: array_hash_equality_asymmetry
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_002_canonical_immutable_array
language: python
authority_effect: None
---

# Anti-Pattern: Array Hash & Equality Asymmetry (`AP_PY_002`)

## Description

Defining `__hash__` and `__eq__` over numeric NumPy arrays without byte-level dtype canonicalization, contiguous layout enforcement, and immutability protection.

## Detection Signature

- AST Pattern:
  Class defining `__hash__` and `__eq__` where an attribute is a raw mutable `np.ndarray` without freezing `flags.writeable = False`.
- Hash/Equality Divergence:
  `a == b` evaluates to `True`, but `hash(a) != hash(b)` due to differing dtypes (`int64` vs `float64`) or memory layouts (C-order vs Fortran-order).

## Hazard & Failure Mode

- Dict lookup and `set` deduplication failures.
- Post-insertion hash mutation corrupting hash-table buckets.
- Fails `RULE_PYTHON_HASH_EQUALITY_NORMALIZATION_001`.

## Dual Healthy Pattern

See [HP_PY_002_canonical_immutable_array](../../helpful/python/HP_PY_002_canonical_immutable_array.md).
