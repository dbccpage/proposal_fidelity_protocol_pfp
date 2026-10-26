---
pattern_id: HP_MD_003
name: separate_ambient_and_tangent
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_003_ambient_called_product_tangent
language: markdown
authority_effect: None
---

# Healthy Pattern: Separate Ambient And Tangent (`HP_MD_003`)

## Description

Name the ambient variation space and the product tangent space as different objects. At a product reference, the tangent space of the smooth algebraic product manifold of normalized Hermitian factors is `im P`. The ambient space of traceless Hermitian variations is `B_0`.

## Construction

- When a later theorem already specifies the tangent space as `im P`, replace only the sentence that calls the ambient space that tangent space.
- Keep the next distinction: physically feasible two-sided velocities at a boundary density are not the whole algebraic tangent space.
- If the source already gives a finite comparison, state both dimensions. The historical witness is three qubits: ambient real dimension `8^2-1=63`, product tangent dimension `3(2^2-1)=9`.
- Point to an exhibited traceless Hermitian direction outside the product tangent space when the source already has one. The historical witness is Counterexample 4.2a.
- Do not rewrite the theorem or the code for this prose repair, and do not add an optional corollary only because a review noticed a sharper wording.

## Limit

This construction records the 2026-10-08 publication review. It does not assert that the false sentence remains in the current manuscript, notebook, code, or Lean sources; those files were not opened for this digest. Theorem assessments in that review are historical and were not rechecked. The three-qubit dimensions are the review's reported count, not a fresh calculation. Correctly naming `im P` does not classify boundary feasible velocities, and it does not discharge missing supplementary exercises, release identity, or byte-identity findings from the same review.

## Dual Anti-Pattern

See [AP_MD_003_ambient_called_product_tangent](../../anti/markdown/AP_MD_003_ambient_called_product_tangent.md).
