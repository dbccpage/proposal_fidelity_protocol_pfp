---
pattern_id: AP_PY_014
name: incomplete_interface_forward_ref_defect
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_014_complete_interface_annotation_parity
language: python
authority_effect: None
---

# Anti-Pattern: Incomplete Interface and Forward Reference Defect (`AP_PY_014`)

## Description

A value object or interface implementation is emitted with missing specification methods (causing `AttributeError` on required API calls) or with unquoted self-referencing type annotations without `from __future__ import annotations` (causing runtime `NameError` during class evaluation).

## Detection Signature

- Proposer generating a value object (e.g. `ExactRational`) that omits requested constructor or arithmetic methods such as `from_string`, `__sub__`, or `__truediv__`.
- Type hints referencing the enclosing class (e.g. `def add(self, other: ExactRational) -> ExactRational:`) in Python modules lacking `from __future__ import annotations`.
- Observed in `critique_rational_1791553907` headstones:
  - `cand_1`: `AttributeError: type object 'ExactRational' has no attribute 'from_string'`
  - `cand_2`: `NameError: name 'ExactRational' is not defined`

## Hazard & Failure Mode

- Premature submission of patches that fail basic import or attribute lookup.
- Wastes dialectic rounds and evaluation budget on syntax-level or contract-omission defects.
- Breaks contract compatibility with consumers expecting the full specification interface.

## Dual Healthy Pattern

See [HP_PY_014_complete_interface_annotation_parity](../../helpful/python/HP_PY_014_complete_interface_annotation_parity.md).
