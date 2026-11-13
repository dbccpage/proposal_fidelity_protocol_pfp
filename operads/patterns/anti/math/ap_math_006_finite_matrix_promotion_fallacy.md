---
pattern_id: AP_MATH_006_finite_matrix_promotion_fallacy
name: ab_finite_matrix_leak
category: anti_pattern
failure_class: math:finite_matrix_leak
language: math
authority_effect: None
dual_pattern: HP_MATH_005_sporadic_cyclotomic_invariant_obstruction
source_pilot: pilot_034
---

# Anti-Pattern: Anti-Finite Matrix Leak (`AP_MATH_006_finite_matrix_promotion_fallacy`)

## Description
Rejects the Finite-to-Matrix Promotion Fallacy where checking a small row-count table or a single column is asserted to prove non-existence of a fourth MUB without evaluating all 36 vector unbiasing constraints.

## Flawed Formulation (Adversarial Specimen)
```text
The 4-element row-count table for F_6 has no compatible row, proving MUB(6)=3.
```

## Repaired Invariant
```text
Evaluating exact Jaming (2009) bound and Tao Eisenstein norm N(3) = 9 != 0 excludes fourth MUB extension.
```
