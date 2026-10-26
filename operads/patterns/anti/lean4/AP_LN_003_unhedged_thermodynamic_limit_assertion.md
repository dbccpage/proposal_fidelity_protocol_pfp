---
pattern_id: AP_LN_003
name: unhedged_thermodynamic_limit_assertion
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Proof"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_LN_003_finite_difference_envelope
language: lean4
authority_effect: None
---

# Anti-Pattern: Unhedged Thermodynamic Limit Assertion (`AP_LN_003`)

## Description

Asserting an unhedged thermodynamic limit ($N \to \infty$, $V \to \infty$) or asymptotic convergence theorem in Lean 4 without a companion discrete finite-difference envelope and typed non-zero residual recording.

## Detection Signature

- AST / Theorem Pattern:
  Theorems asserting asymptotic equality or infinite convergence without bounding assumptions or discrete cost budgets.
- Regex: `theorem\s+.*thermodynamic_limit\b` without finite difference witnesses.

## Hazard & Failure Mode

- Violates Natural Science Gate `limit_honesty: FAIL` (OMC report blocker).
- Conceals discrete deformation calculus (DDC) truncation errors.
- Disconnects mechanized proof terms from physical computational costs ($\mu_1 \ge 2$).

## Dual Healthy Pattern

See [HP_LN_003_finite_difference_envelope](../../helpful/lean4/HP_LN_003_finite_difference_envelope.md).
