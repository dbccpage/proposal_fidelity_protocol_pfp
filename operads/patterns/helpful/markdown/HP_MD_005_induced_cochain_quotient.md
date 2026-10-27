---
pattern_id: HP_MD_005
name: induced_cochain_quotient
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_005_wrong_degree_cochain_quotient
language: markdown
authority_effect: None
---

# Healthy Pattern: Induced Cochain Quotient (`HP_MD_005`)

## Description

Name the complex before a quotient or cohomology claim. Keep the quotient cochain space, the induced differential, and cohomology as three different objects.

## Construction

For scalar cochains with `d0: C0 -> C1`, `d1: C1 -> C2`, and `d1 ∘ d0 = 0`:

- `im(d0)` is a subspace of `C1`. The quotient cochain space is `C1/im(d0)`, not a quotient of `C2`.
- `d1` descends to `bar(d1): C1/im(d0) -> C2`.
- First cohomology is `H1 = ker(d1)/im(d0) = ker(bar(d1))`.
- `d1(delta)` is an element of `C2` and a coboundary there. It is not, by itself, a nonzero class in `H2`.
- Evaluate a k-cochain only on a k-chain.

If the complex stops at `C1`, say so. Then `H1 = C1/im(d0)` is the cokernel of the only differential. Do not also write `d1` or `H2`.

## Limit

Correct degree does not identify the quotient with a length, angle, deficit, connection, or physical dynamics. A complex with only one differential is the exception above, not a counterexample. The motivating sentences are the historical report in `_ic/inr/core_paper_reviews/po035_2026-10-11/review.md`. This pattern does not assert that the current manuscript still contains them.

## Dual

See [AP_MD_005_wrong_degree_cochain_quotient](../../anti/markdown/AP_MD_005_wrong_degree_cochain_quotient.md).
