---
pattern_id: AP_MATH_015_vector_basis_gap
name: ab_vector_basis_gap
category: anti_pattern
failure_class: math:vector_basis_gap
language: math
authority_effect: None
dual_pattern: HP_MATH_014_psi_bridge_monomial_extension
source_pilot: pilot_043
---

# Anti-Pattern: Anti-Vector Basis Gap Fallacy (`AP_MATH_015_vector_basis_gap`)

## Description
Rejects asserting that a single vector obstruction implies basis non-existence without proving unitary mutual orthogonality.

## Flawed Formulation (Adversarial Specimen)
```text
Because one vector v in C^6 fails mutual unbiasedness, no 4th basis can exist.
```

## Repaired Invariant
```text
The Gluing.lean bridge aggregates all 6 columns under BasisVectorMUContract, proving no orthonormal frame can avoid the curvature wall.
```
