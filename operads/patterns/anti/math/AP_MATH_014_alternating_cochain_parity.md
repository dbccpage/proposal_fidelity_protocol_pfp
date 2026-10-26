---
pattern_id: AP_MATH_014_alternating_cochain_parity
name: ab_alternating_cochain_parity
category: anti_pattern
failure_class: math:alternating_cochain_parity
language: math
authority_effect: None
dual_pattern: HP_MATH_013_simplicial_filtration_exactness
source_pilot: pilot_042
---

# Anti-Pattern: Anti-Alternating Cochain Parity Fallacy (`AP_MATH_014_alternating_cochain_parity`)

## Description
Rejects simplicial cochain evaluations where 1-cochains are treated as symmetric rather than alternating under edge reversal.

## Flawed Formulation (Adversarial Specimen)
```text
The 1-cochain is symmetric so omega(u, v) = omega(v, u), making the 3-cycle circulation vanish.
```

## Repaired Invariant
```text
Alternating parity omega(v, u) = -omega(u, v) establishes cycle circulation Gamma = 12133/5000 > 0.
```
