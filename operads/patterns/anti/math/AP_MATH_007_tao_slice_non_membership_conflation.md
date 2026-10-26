---
pattern_id: AP_MATH_007_tao_slice_non_membership_conflation
name: ab_tao_slice_non_membership
category: anti_pattern
failure_class: math:tao_slice_non_membership
language: math
authority_effect: None
dual_pattern: HP_MATH_006_hadamard_cube_fourier_uncertainty_dual_check
source_pilot: pilot_035
---

# Anti-Pattern: Anti-Tao Slice Non-Membership Conflation Fallacy (`AP_MATH_007_tao_slice_non_membership_conflation`)

## Description
Rejects candidate claims that fail-closed refusal of Conjecture 2 membership implies MUB-4 extendability, or conflating Fourier transform factors with general Hadamard cube vanishing.

## Flawed Formulation (Adversarial Specimen)
```text
S_6 fails Conjecture 2 vanishing, which implies it can be extended to 4 MUBs.
```

## Repaired Invariant
```text
S_6 fails Conjecture 2 vanishing with norm 9 != 0, and Jaming et al. (2009) Fourier uncertainty independently bounds MUB cardinality to 3.
```
