---
pattern_id: AP_MATH_012_cusp_smoothness_fallacy
name: ab_cusp_smoothness_fallacy
category: anti_pattern
failure_class: math:cusp_smoothness_fallacy
language: math
authority_effect: None
dual_pattern: HP_MATH_011_stratified_collar_decomposition
source_pilot: pilot_040
---

# Anti-Pattern: Anti-Cusp Smoothness Fallacy (`AP_MATH_012_cusp_smoothness_fallacy`)

## Description
Rejects applying smooth Taylor expansions or standard implicit function theorems across non-smooth deltoid cusps.

## Flawed Formulation (Adversarial Specimen)
```text
The gradient of det(H(theta)) is smooth at theta=0, so linear Taylor expansion gives valid interval bounds.
```

## Repaired Invariant
```text
At the 3 deltoid cusps, d/dtheta det(H(theta)) vanishes; exact fractional Lipschitz collars of radius 1/256 seal the singular locus.
```
