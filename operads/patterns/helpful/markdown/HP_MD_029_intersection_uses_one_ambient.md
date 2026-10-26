---
pattern_id: HP_MD_029
name: intersection_uses_one_ambient
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_029_intersection_without_ambient
language: markdown
authority_effect: None
---

# Healthy Pattern: An Intersection Uses One Ambient Set (`HP_MD_029`)

## Description

Write an intersection only after both operands are subsets of one named set. If they are not, write the class or image statement that is actually defined.

## Construction

- Before writing $X\cap Y$, name a set that contains both as subsets, or do not write the intersection.
- For the historical cochain display, write $[d_0f]=0$ in $H^1$. Do not intersect $\operatorname{im}d_0$ with the quotient $H^1$.
- A harmonic alternative is allowed only after the text declares an inner product and the representative subspace. Intersect that subspace, not the quotient.
- For a coproduct $T$, write $\operatorname{im}(\operatorname{inl})\cap\operatorname{im}(\operatorname{inr})=\varnothing$ inside $T$. Do not intersect the bare summand types.

## Limit

The witnesses in [AP_MD_029_intersection_without_ambient](../../anti/markdown/AP_MD_029_intersection_without_ambient.md) are historical reviews dated 2026-10-08. No manuscript was reopened and no check was rerun. This pattern does not claim those sentences are still in the current files.

`AP_MD_005` still owns a quotient at the wrong degree, a cochain evaluated on a chain of another dimension, and naming $C^1/\operatorname{im}d_0$ as first cohomology when $d_1$ exists. This pattern does not replace that repair.

`/woland-proof-scope-rule` still owns a stronger negative sentence beside a proved bound, including a non-recovery claim labeled proved next to a cycle bound, and an unqualified infinite-time persistence exclusion beside an all-time zero certificate. `/woland-proof-premise-rule` still owns a transferred bound that drops a hypothesis the argument uses. `AP_MD_004` still owns acceptance by an unfixed family. `AP_MD_002` still owns spaced identifiers in a printed Lean listing. `AP_MD_003` still owns the ambient traceless space called the product tangent space. `AP_MD_001` still owns a stated command, version, or test count the package does not match.

Images of the two injections inside $T$ may be intersected. A declared harmonic subspace may be intersected. Those are not this defect.

## Dual Anti-Pattern

See [AP_MD_029_intersection_without_ambient](../../anti/markdown/AP_MD_029_intersection_without_ambient.md).
