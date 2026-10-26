---
pattern_id: AP_PY_013
name: silent_input_schema_coercion
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_013_strict_input_typed_refusal
language: python
authority_effect: None
---

# Anti-Pattern: Silent Input Schema Coercion (`AP_PY_013`)

## Description

A parser, workflow runner, or ingress boundary silently accepts malformed input structures (e.g. converting a bare scalar into a nullary operation, discarding non-matching items from a mixed list, or defaulting invalid JSON/YAML keys) without emitting a typed refusal.

## Detection Signature

- Parser logic wrapping unexpected scalars in default containers without refusal:
  ```python
  if not isinstance(raw_step, dict):
      raw_step = {"op": str(raw_step), "args": []}  # Silent repair!
  ```
- Filtering or dropping unrecognized elements from an input collection:
  ```python
  clean_steps = [s for s in raw_steps if is_valid_step(s)]  # Silent item dropping!
  ```
- Observed in `woland_epic_implementation_20261010_launch` (Scene 2): "Hella exposes silent schema repair. The untouched parser accepted scalar operation inputs as a nullary operation... dropping non-matching elements from mixed lists without a typed refusal."

## Hazard & Failure Mode

- Violates fail-closed engineering discipline and hides caller specification errors.
- Allows corrupted or truncated workflow manifests to execute partially, leading to unpredictable downstream side effects.
- Masks API boundary mismatches behind silent semantic degradation.

## Dual Healthy Pattern

See [HP_PY_013_strict_input_typed_refusal](../../helpful/python/HP_PY_013_strict_input_typed_refusal.md).
