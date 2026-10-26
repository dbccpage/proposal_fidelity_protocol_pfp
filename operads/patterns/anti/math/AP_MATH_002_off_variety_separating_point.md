---
pattern_id: AP_MATH_002_off_variety_separating_point
name: ab_off_variety_sampling_leak
category: anti_pattern
failure_class: math:off_variety_sampling_leak
language: math
authority_effect: None
dual_pattern: HP_MATH_002_sos_variety_grid_exhaustion
source_pilot: pilot_032
---

# Anti-Pattern: Anti-Off-Variety Sampling Leak (`AP_MATH_002_off_variety_separating_point`)

## Description
Rejects evaluating a candidate separating polynomial g_sep on arbitrary ambient sample points (a, b, c, d) in Q^4 and claiming emptiness of {V, g_sep >= 0} without verifying that the point satisfies all defining generators of variety V.

## Flawed Formulation (Adversarial Specimen)
```text
Evaluating g_sep at sample point (1/2, 3/4, 5/6, 7/8) yields g_sep = -1/100, proving emptiness.
```

## Repaired Invariant
```text
Evaluating g_sep on genuine variety points in {-1, 1}^4 where f_segre = 0 and k^2 - 1 = 0 yields g_sep = -1/1000 < 0; verified algebraically across Q[a,b,c,d] via Stengle Positivstellensatz identity on 5^4 grid.
```
