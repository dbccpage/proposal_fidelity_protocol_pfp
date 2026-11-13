---
pattern_id: AP_MATH_004_tao_universal_conflation
name: ab_tao_universal_conflation
category: anti_pattern
failure_class: math:tao_universal_conflation
language: math
authority_effect: None
dual_pattern: HP_MATH_004_isolated_negative_control_discrimination
source_pilot: pilot_031
---

# Anti-Pattern: Anti-Tao Universal Conflation (`AP_MATH_004_tao_universal_conflation`)

## Description
Rejects asserting that Conjecture 2 holds universally across all Complex Hadamard Matrices. The isolated Tao matrix S_6 = F_3 (x) F_2 fails both clause (a) and clause (b) on 20/20 permutations and serves as a fail-closed negative control.

## Flawed Formulation (Adversarial Specimen)
```text
Conjecture 2 is a universal property of all 6x6 complex Hadamard matrices.
```

## Repaired Invariant
```text
Tao S_6 contains 0 entries equal to -1 and fails Conjecture 2 on 20/20 permutations as a strict negative control.
```
