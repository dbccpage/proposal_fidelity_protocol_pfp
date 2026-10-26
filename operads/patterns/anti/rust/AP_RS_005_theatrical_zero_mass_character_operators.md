---
pattern_id: AP_RS_005
name: theatrical_zero_mass_character_operators
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_RS_005_witness_certified_operator_execution
language: rust
authority_effect: None
---

# Anti-Pattern: Theatrical Zero-Mass Character Operators (`AP_RS_005`)

## Description

Character operators or test evaluation roles returning constant zero residual mass, zero defects, and declaring external compilers passed (e.g. setting `zero_sorry_lake_build = True`) without executing the underlying external verifier or inspecting actual execution output.

## Hazard & Failure Mode

- Emits unearned consensus and creates an illusion of formal verification.
- Code containing unproven sorries or broken proofs passes gates undetected.
- Violates the Landauer/Landau principle of truth verification.

## Detection Signature

```python
# Anti-pattern:
def observe(self, candidate):
    # Returns success flags without calling any verifier
    return Observation(residual_mass=Fraction(0, 1), zero_sorry_lake_build=True)
```

## Dual Healthy Pattern

See [HP_RS_005_witness_certified_operator_execution](../../helpful/rust/HP_RS_005_witness_certified_operator_execution.md).
