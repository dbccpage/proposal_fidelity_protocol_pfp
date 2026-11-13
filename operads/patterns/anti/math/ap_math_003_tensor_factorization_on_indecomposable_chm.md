---
pattern_id: AP_MATH_003_tensor_factorization_on_indecomposable_chm
name: ab_tensor_parity_generalization_fallacy
category: anti_pattern
failure_class: math:tensor_parity_generalization_fallacy
language: math
authority_effect: None
dual_pattern: HP_MATH_003_2circulant_odd_monomial_pairing
source_pilot: pilot_031
---

# Anti-Pattern: Anti-Tensor Parity Generalization Fallacy (`AP_MATH_003_tensor_factorization_on_indecomposable_chm`)

## Description
Rejects falsely asserting that indecomposable 2-circulant complex Hadamard matrices (such as Szollosi B_6) factor into a Kronecker tensor product U (x) V to claim Conjecture 2(b) qubit block parity cancellation without evaluating the 2-circulant Laurent monomials.

## Flawed Formulation (Adversarial Specimen)
```text
Claiming: B_6(theta) = U(phi) (x) V implies alpha_2 = 2m - 3 cancels qubit block.
```

## Repaired Invariant
```text
For indecomposable 2-circulant H = [[A, B], [B^dagger, -A^dagger]], odd exponent beta_2 = 3(2m - 3) guarantees (-1)^{beta_2} = -1, causing both G_H and G_{H^*} to vanish independently via column Laurent monomial pairing.
```
