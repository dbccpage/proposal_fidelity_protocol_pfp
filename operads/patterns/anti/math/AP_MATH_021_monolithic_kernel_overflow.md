---
pattern_id: AP_MATH_021_monolithic_kernel_overflow
name: ab_monolithic_kernel_overflow
category: anti_pattern
failure_class: math:monolithic_kernel_overflow
language: math
authority_effect: None
dual_pattern: HP_MATH_020_chunked_kernel_reflection_scaling
source_pilot: pilot_049
---

# Anti-Pattern: Anti-Monolithic Kernel Overflow Fallacy (`AP_MATH_021_monolithic_kernel_overflow`)

## Description
Rejects submitting unchunked certificates exceeding 10^5 terms directly to Lean 4 kernel 'by rfl'.

## Flawed Formulation (Adversarial Specimen)
```text
Lean 4 kernel can evaluate the 500,000 monomial Positivstellensatz identity in a single 'by rfl' tactic invocation.
```

## Repaired Invariant
```text
Subgap R8 chunking architecture partitions the certificate into binary sub-trees of <= 1024 terms, verified independently and stitched by transitivity.
```
