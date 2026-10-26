---
pattern_id: AP_MATH_013_discrete_bianchi_violation
name: ab_discrete_bianchi_violation
category: anti_pattern
failure_class: math:discrete_bianchi_violation
language: math
authority_effect: None
dual_pattern: HP_MATH_012_nilpotent_coboundary_nilpotency
source_pilot: pilot_041
---

# Anti-Pattern: Anti-Discrete Bianchi Violation Fallacy (`AP_MATH_013_discrete_bianchi_violation`)

## Description
Rejects cochain configurations where d3 circ d2 does not vanish identically or spectral floor is negative.

## Flawed Formulation (Adversarial Specimen)
```text
On discrete lattices, d3 circ d2 = 0.04 != 0 due to discretization error.
```

## Repaired Invariant
```text
Discrete cochain algebra over Q satisfies d3 circ d2 = 0 exactly with spectral floor sigma >= 31/800.
```
