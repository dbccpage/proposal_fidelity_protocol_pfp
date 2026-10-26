---
pattern_id: HP_MD_033
name: full_product_rule_before_onset_order
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_033_isolated_leibniz_term_as_derivative
language: markdown
authority_effect: None
---

# Healthy Pattern: The Full Product Rule Before The Onset Order (`HP_MD_033`)

## Description

Differentiate every factor in the product. Keep every Leibniz summand. Read the first nonzero order from that sum, after cancellation, not from one displayed term.

## Construction

- For a residual `F = rho_e - rho_a tensor rho_b`, differentiate both moving marginals.
- A single summand such as `-2 rho'_a tensor rho'_b` is not `F''`.
- If the sum is zero, do not stop. The next derivative may be the first nonzero order.
- Check a decoupling input. Independent local fields, historically `J=0`, must leave a zero residual. A nonzero isolated term at that input is the defect.
- The historical repair records `F'(0)=F''(0)=0` and `||F'''(0)||_1=16|J|h^2` for the two-qubit Ising example. Quote that record as historical. Do not present it as a new computation.

## Limit

The witness is the 2026-10-06 brief `_ic/darpa/research/briefs/projection_obstruction_jets`. No proposal bytes were decoded, no pytest or Lean command was rerun, and `paper_candidate.md` was not opened. Controller status `Verified` does not extend these arithmetic notes to the analytic limit.

`AP_MD_003` still owns the sentence that calls the ambient traceless space the product tangent space. It does not state this product-rule summand. `AP_MD_005` still owns a quotient, evaluation, or cohomology name at the wrong degree. `AP_MD_029` still owns an intersection with no common ambient set. `AP_MD_051` still owns a printed rational that is not the value of the formula beside it. `AP_MD_022` still owns axiom-free lines quoted in place of a failed `.olean` create.

`/woland-proof-scope-rule` still owns a finite check or kernel sentence promoted past its scope, including arithmetic Lean lemmas presented as the analytic theorem and a controller disposition presented as semantic verification. `/woland-proof-premise-rule` still owns a changed hypothesis, such as interaction support larger than two sites, advertised as no new premise.

A derivative that equals one summand because the other summands are proved zero is not this defect. A raw commutator written in place of `(I-P)` of that commutator is not this defect. Cancellation between a Hamiltonian normal and a dissipative normal is not this defect. Cross-order cancellation inside an already complete Taylor polynomial is the bound's own warning, not this defect.

## Dual Anti-Pattern

See [AP_MD_033_isolated_leibniz_term_as_derivative](../../anti/markdown/AP_MD_033_isolated_leibniz_term_as_derivative.md).
