---
pattern_id: AP_MD_033
name: isolated_leibniz_term_as_derivative
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_033_full_product_rule_before_onset_order
language: markdown
authority_effect: None
---

# Anti-Pattern: Isolated Leibniz Term As The Derivative (`AP_MD_033`)

## Description

A markdown derivative of a product keeps one summand and drops the rest. The omitted summands can cancel the displayed term. That isolated term is not the derivative, and it does not fix the first nonzero order.

## Detection Signature

- A second residual derivative is written as only `-2 rho'_a tensor rho'_b`, or as another single Leibniz summand.
- The product rule still differentiates each factor. Those terms are absent from the display.
- At a decoupling value the isolated term is nonzero while the full residual derivative is zero.
- An exact expansion gives a higher first nonzero order than the isolated term predicts.

## Witness

Historical review text. This digest did not decode the base64 proposal, did not open `paper_candidate.md`, did not rerun the matrix checks, and did not recompile Lean.

`_ic/darpa/research/briefs/projection_obstruction_jets/stage3_updated.json`, finding `TFIM_SECOND`, run `PO_20261006_SHORT_TIME_JETS`, status `REPAIRED`:

> GLM retained -2 rho'_a tensor rho'_b and omitted cancelling terms.

The same row's repair note, historical and not recomputed here:

> Exact matrix and amplitude expansions give F''=0 and ||F'''||=16|J|h^2.

`assessment.md` in that folder, dated 2026-10-06:

> The proposed second-order coefficient is false. Exact derivatives for two qubits give F'=F''=0 and ||F'''||_1=16|J|h^2.

The repaired draft `onset_examples_section.md` states the cancellation the proposal dropped:

> In particular, the isolated term
> \(-2\dot\rho_a(0)\otimes\dot\rho_b(0)=-2h^2Y\otimes Y\) is canceled
> by the other terms in \(F''(0)\). Keeping it alone would incorrectly
> predict correlation under independent local fields even at \(J=0\).

A PASS label in `stage5_checks.json` is not a fresh execution. The draft states the failure mode. It is not itself the defective display.

## Hazard & Failure Mode

- Independent local fields are reported as producing correlation.
- A cubic onset is cited as quadratic.
- A later norm bound is attached to the cancelled coefficient.

## Dual Healthy Pattern

See [HP_MD_033_full_product_rule_before_onset_order](../../helpful/markdown/HP_MD_033_full_product_rule_before_onset_order.md).
