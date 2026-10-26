---
pattern_id: AP_MATH_020_fourth_root_fourier_confabulation
name: ab_fourth_root_fourier_confabulation
category: anti_pattern
failure_class: math:fourth_root_fourier_confabulation
language: math
authority_effect: None
dual_pattern: HP_MATH_019_rational_fourier_support_bounds
source_pilot: pilot_048
---

# Anti-Pattern: Anti-Fourth Root Fourier Confabulation (`AP_MATH_020_fourth_root_fourier_confabulation`)

## Description
Rejects asserting that having matrix entries in {+/-1, +/-i} proves membership in the Fourier family.

## Flawed Formulation (Adversarial Specimen)
```text
Every matrix whose entries are fourth roots of unity is unitarily equivalent to the Fourier matrix F_6.
```

## Repaired Invariant
```text
Fourier membership requires evaluating the phase-independent conjugate cross-ratio CR(a,b,c,d) = 1, which distinguishes F_6 from Butson Hadamard matrices.
```
