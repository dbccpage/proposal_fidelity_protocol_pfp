---
pattern_id: AP_MATH_009_gauge_loss_fallacy
name: ab_gauge_loss_fallacy
category: anti_pattern
failure_class: math:gauge_loss_fallacy
language: math
authority_effect: None
dual_pattern: HP_MATH_008_projective_unitary_gauge_fixing
source_pilot: pilot_037
---

# Anti-Pattern: Anti-Gauge Loss Fallacy (`AP_MATH_009_gauge_loss_fallacy`)

## Description
Rejects claims that fixing column phases in additional bases eliminates non-gauge-equivalent MUB solutions.

## Flawed Formulation (Adversarial Specimen)
```text
Setting the first row of bases 3 and 4 to 1 loses solutions because some MUBs have complex first rows.
```

## Repaired Invariant
```text
Column phase transformation U_j -> U_j D_j preserves projective rank-one projectors and mutual unbiasedness exactly.
```
