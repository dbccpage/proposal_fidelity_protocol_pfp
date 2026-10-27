---
pattern_id: AP_MD_004
name: unfixed_comparison_class
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_004_declared_family_acceptance
language: markdown
authority_effect: None
---

# Anti-Pattern: Unfixed Comparison Class (`AP_MD_004`)

## Description

Prose states unique acceptance or authority for one candidate while the comparison class is missing from the classifier, or while an existential quantifier lets the writer choose that class. The candidate's singleton makes the existential sentence true without new evidence.

## Detection Signature

- The displayed verifier returns one candidate's discrepancy vector, and a terminalizer or taxonomy still requires unique survival in a family that is not in its domain.
- Acceptance, uniqueness, or authority of one object holds whenever some family, context, or subset makes that object the sole survivor.
- With evidence and per-candidate discrepancies held fixed, changing only the declared family changes the verdict: a singleton is accepted and two matching survivors are not.

## Witness

Historical review text only. This pattern does not claim the formula is still in the current manuscript. The publication review of the representation-abundance v2.1.0 text, read on 2026-10-08 at main commit `c33fb25be7f7bb340eb7345d90134dc116bac244`, says:

> A candidate's discrepancy vector does not tell the terminalizer how many other candidates survive. Nevertheless the taxonomy requires unique survival in a declared family and later writes $\tau(\mathcal S)$, outside its declared domain.

The same review records an exact replay against the implementation then current:

> Family $\{A\}$ returns ACCEPTED.
> Family $\{A,B\}$ returns UNDERDETERMINED.
> Family $\{B\}$ returns ACCEPTED.
>
> A's evidence and discrepancies have not changed. Unique acceptance is a property of the evidence and the declared family, not of the single-candidate discrepancy vector.

and:

> The larger problem is the unqualified existential formula for $\mathsf{Authority}(s)$ in Section 4.3. If the family can be chosen freely, each of two indistinguishable survivors can be made uniquely accepted by declaring its singleton family. The stated rule then cannot establish exclusive physical authority between them. Deleting competitors has supplied no new empirical information.

Source: `_ic/inr/core_paper_reviews/2026-10-08_representation_abundance_publication_review/review.md`.

## Hazard & Failure Mode

- Two candidates that agree on the evidence can each receive a unique-acceptance label by shrinking the family, so the label does not separate them.
- A reader treats that label as exclusive empirical or physical authority.
- The displayed terminalizer domain omits the family and evidence the verdict uses.

## Dual Healthy Pattern

See [HP_MD_004_declared_family_acceptance](../../helpful/markdown/HP_MD_004_declared_family_acceptance.md).
