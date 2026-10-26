---
pattern_id: AP_MATH_019_moment_degree_blowup
name: ab_moment_degree_blowup
category: anti_pattern
failure_class: math:moment_degree_blowup
language: math
authority_effect: None
dual_pattern: HP_MATH_018_commutative_flat_extension_rank_preservation
source_pilot: pilot_047
---

# Anti-Pattern: Anti-Moment Degree Blowup Fallacy (`AP_MATH_019_moment_degree_blowup`)

## Description
Rejects constructing commuting multiplication operators using polynomials of degree > 4 beyond the bounded Lasserre hierarchy.

## Flawed Formulation (Adversarial Specimen)
```text
Extracting a real point requires constructing commuting multiplication operators on polynomials of degree up to 10.
```

## Repaired Invariant
```text
Curto-Fialkow flat extension on quadratic varieties operates strictly within products of degree at most 4, extracting a verified real point.
```
