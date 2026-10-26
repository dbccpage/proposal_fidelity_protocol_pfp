---
pattern_id: AP_MATH_016_atlas_overlap_gauge_trap
name: ab_atlas_overlap_gauge_trap
category: anti_pattern
failure_class: math:atlas_overlap_gauge_trap
language: math
authority_effect: None
dual_pattern: HP_MATH_015_c2_cocycle_overlap_compatibility
source_pilot: pilot_044
---

# Anti-Pattern: Anti-Atlas Overlap Gauge Fallacy (`AP_MATH_016_atlas_overlap_gauge_trap`)

## Description
Rejects chart gluing claims that ignore non-trivial phase cocycles across chart boundary intersections.

## Flawed Formulation (Adversarial Specimen)
```text
The charts C_2 and B_6 intersect trivially so their transition function is the identity matrix.
```

## Repaired Invariant
```text
The cocycle g_{ij} on C_2 intersect B_6 incorporates the non-trivial Karlsson dephasing gauge, satisfying cocycle condition g_ij g_jk g_ki = I.
```
