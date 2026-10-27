# WDP rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [DDC operations](Rewriting-WDP-DDC.md) · [Examples](Rewriting-WDP-Examples.md)

The **Witnessed Difference Programme** (WDP) is the mathematics underneath the
other layers. It asks how much structure can be made explicit if you start from
one exhibited difference and refuse to smuggle in an observer, a clock, a
probability space, a quantum state or an authority. WDP has no separate rewriting
folder. Its rewrites are the **repair, retention and refusal operations** of its
levels and of the Discrete Deformation Calculus (DDC).

## The admitted cut

Everything starts from an **admitted cut**: a tuple `(X, E, τ, K)` of finite
tokens `X`, comparisons `E`, role assignments `τ` and a declared family `K` of
admissible comparisons. The tuple is data. None of it is chosen from equality on
`X` alone, because on a bare finite set every permutation is a symmetry, so no
point, direction or edge can be picked out without extra structure.

Three facts about a pointed relation `(X, R, a, b)`:

- `R(a,b)` does not imply `a ≠ b`.
- `a ≠ b` does not imply `R(a,b)`.
- `R(a,b)` together with irreflexivity does imply `a ≠ b`.

## Every step has a price

| To get… | You must also declare… |
| --- | --- |
| Residuals from a cut | A comparison family and a repair map |
| Retained residuals | Memory structure (retention is not free) |
| Residuals measured on a complex | A degree-1 window, a norm and a repair map |
| Succession | An immediate-successor relation |
| Duration | An additive valuation (positivity and units are extra) |
| Finite probability | A matching, an additive weight and a normalisation |
| An observer | Presentation, memory, evaluator and policy layers |
| A recorded observation | Interaction, registration, witness, re-access and an accepting evaluator |
| A measurement | Measurand, value carrier, value map, calibration, uncertainty, provenance |
| Aggregated histories | A semiring and a finite path family |

Nothing arrives because it would be convenient. For rewriting this means a
repair is only meaningful relative to a declared comparison family and norm.

## The numbers that judge a repair

On a finite complex, a defect `x` (an edge cochain) has:

- **Φ₁**, the smallest residual cost after subtracting any potential `d0*φ`;
- **Γ₂**, the size of its face (closure) defect `d1*x`.

The monograph's full signature is `(Φ₁, Γ₂, R_cl)`, and its dual certificates
bound Φ₁ from below. These numbers decide whether exact repair is possible. The
other operations have their own gates:

| Operation | Gate |
| --- | --- |
| Exact repair (**E**) | Φ₁ = 0, Γ₂ = 0 and an adequate detector |
| Residual projection (**R**) | Records the residual; must leave the carrier, Φ₁ and Γ₂ unchanged |
| Context exposure (**C**) | Scope may grow but not be laundered |
| Structural lift (**Λ**) | A licence from the lift gate |
| Scale descent (**D**) | A declared loss ledger |
| Typed refusal (**M**) | A recognised reason code; state unchanged |

When Γ₂ = 0 and Φ₁ > 0 the defect is a closed residual. It cannot be repaired
away on this carrier, so **E** is refused and **R** records it.

## What a WDP rewrite must keep separate

Four things are never merged: the **diagnostic class** of the defect, the
**routing terminal** where a run stops, the **extension status** of the carrier,
and **authority**, which is always None.

## Sources

- [WDP education folder](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/education/witnessed_difference_programme)
- [WDP levels](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/education/witnessed_difference_programme/levels)
  and [DDC levels](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/education/witnessed_difference_programme/levels/ddc)
- [Reading guide](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/witnessed_difference_programme/reading_guide.md)
