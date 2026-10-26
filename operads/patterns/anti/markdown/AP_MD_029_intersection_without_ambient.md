---
pattern_id: AP_MD_029
name: intersection_without_ambient
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_029_intersection_uses_one_ambient
language: markdown
authority_effect: None
---

# Anti-Pattern: Intersection Without An Ambient Set (`AP_MD_029`)

## Description

A markdown sentence writes an intersection of two objects that the same text has not placed in one set. The formula is not defined. It is not a theorem waiting on an extra premise.

## Detection Signature

- A displayed formula intersects `im(d_0)` with `H^1`, while that text introduces `H^1` as the quotient `C^1/im(d_0)` and `im(d_0)` as a subspace of `C^1`.
- A displayed formula intersects the bare summand types, while the disjointness that was proved is the intersection of the two injection images inside the coproduct.
- The same review already states a typed replacement and does not treat the missing ambient set as a hypothesis.

## Witness

Historical review text. This digest did not reopen either manuscript and did not rerun the recorded checks.

`_ic/darpa/research/reviews/representation_abundance_publication_review_20261008/review.md`, reviewed 2026-10-08 at `c33fb25be7f7bb340eb7345d90134dc116bac244`:

> The displayed consequence
> $$\operatorname{im}d_0\cap H^1(G,\mathbb Q)=\{0\}$$
> is not properly defined in this presentation.
>
> For a graph, $H^1(G,\mathbb Q)=C^1/\operatorname{im}d_0$ is a quotient space, whereas $\operatorname{im}d_0$ is a subspace of $C^1$. There is no specified common ambient space in which to take this intersection.

That review's typed replacement is: every exact cochain represents the zero class, $[d_0f]=0$ in $H^1(G,\mathbb Q)$. It also allows an intersection with a harmonic representative subspace after a declared inner product. That alternative is not the displayed formula.

`_ic/darpa/research/reviews/paper027_publication_review_20261008/review.md`, same date and commit:

> §3.1, line 183: write the disjointness of the injection images inside $T$:
> $$\operatorname{im}(\operatorname{inl})\cap\operatorname{im}(\operatorname{inr})=\varnothing.$$
> Bare types $A$ and $R$ do not have the stated intersection without a common ambient interpretation.

Those line numbers are the reviewer's historical loci. The same review's pointwise coproduct argument at its stated zero-guard scope was not this defect.

## Hazard & Failure Mode

- The undefined intersection is cited later as a proved vanishing or as constructor disjointness.
- A degree correction is treated as if it had named the ambient set. Wrong-degree quotients remain `AP_MD_005`.
- The coproduct lemma can stay valid while the bare-type intersection is not a statement.

## Dual Healthy Pattern

See [HP_MD_029_intersection_uses_one_ambient](../../helpful/markdown/HP_MD_029_intersection_uses_one_ambient.md).
