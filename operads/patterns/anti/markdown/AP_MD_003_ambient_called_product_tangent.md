---
pattern_id: AP_MD_003
name: ambient_called_product_tangent
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_003_separate_ambient_and_tangent
language: markdown
authority_effect: None
---

# Anti-Pattern: Ambient Space Called Product Tangent (`AP_MD_003`)

## Description

Prose names the full ambient space of traceless Hermitian variations as the tangent space of an algebraic product manifold. That ambient space is the larger translation space. The product tangent space is the smaller projector image already fixed by a later theorem.

## Detection Signature

- An early sentence equates the space of traceless Hermitian variations with the tangent space of a product of normalized Hermitian factors.
- A later statement already names a strictly smaller image, such as `im P`, as that tangent space.
- A finite dimension count, or an exhibited traceless Hermitian direction, falls outside the product tangent space.

## Witness

Historical source, not a fresh manuscript inspection or recomputed dimension count: `C:\Users\a343o\source\repos\the_symbol_game\_ic\inr\omega_paper_reviews\2026-10-08_po034_first_publication_review\review.md` (review dated 2026-10-08 at main commit `c33fb25be7f7bb340eb7345d90134dc116bac244`).

> The manuscript says that the full vector space of traceless Hermitian variations is the tangent space of the algebraic product manifold. This is false. That vector space is the ambient translation space $\mathcal B_0$. The product tangent space is the smaller space $\operatorname{im}P$ already correctly specified by Theorem 4.1.
>
> For three qubits the ambient real dimension is $8^2-1=63$, whereas the product tangent dimension is $3(2^2-1)=9$. Counterexample 4.2a also exhibits a traceless Hermitian direction outside the product tangent space.

The review places the sentence in canonical manuscript Section 2.1, lines 68–72. Those coordinates are the reviewer's historical locus.

## Hazard & Failure Mode

- A reader treats ambient directions as product-tangent. That misreads isolation, annihilator, and boundary-velocity claims even when Theorem 4.1 already names `im P`.
- The same review says the boundary qualification needs this sentence correction, and that the repair does not change Theorem 4.1 or the code. The false sentence is not a failed principal theorem.

## Dual Healthy Pattern

See [HP_MD_003_separate_ambient_and_tangent](../../helpful/markdown/HP_MD_003_separate_ambient_and_tangent.md).
