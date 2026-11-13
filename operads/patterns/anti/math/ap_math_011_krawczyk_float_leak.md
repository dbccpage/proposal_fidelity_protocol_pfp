---
pattern_id: AP_MATH_011_krawczyk_float_leak
name: ab_krawczyk_float_leak
category: anti_pattern
failure_class: math:krawczyk_float_leak
language: math
authority_effect: None
dual_pattern: HP_MATH_010_rational_interval_smale_sentry
source_pilot: pilot_039
---

# Anti-Pattern: Anti-Krawczyk Float Leak Fallacy (`AP_MATH_011_krawczyk_float_leak`)

## Description
Rejects using floating-point evaluations in interval Newton or Krawczyk operators without exact rational rounding guards.

## Flawed Formulation (Adversarial Specimen)
```text
Running float64 Newton-Raphson converges to 1e-16 so the box contains an exact zero.
```

## Repaired Invariant
```text
Exact rational interval arithmetic over Q proves K(X) intersect X = empty across all 56 cells at depth 64.
```
