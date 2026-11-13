---
id: ENC-0136
kind: lemma
name: "Positive Weights Give Bounded Residual Ties"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §5.3 'Lemma (Positive Weights Give Bounded Residual Ties)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0136 — Positive Weights Give Bounded Residual Ties

## Statement

In finite dimension,
if every weight \(w_i>0\) and \(\Phi_1([x])<\infty\), then
\(\mathcal{A}_x\) is bounded in the declared coordinates.

## Hypotheses

Verbatim definition of the residual projection domain from the source section:

> Let the residual projection domain for \(x\in C^1\) be:
>
> \[
> \mathcal{A}_x
> =
> \{h\in C^1\mid h=x-d_0\alpha\text{ for some }\alpha\in C^0,\;
> \|h\|_{1,w}=\Phi_1([x])\}.
> \]

## Proof

For every \(h\in\mathcal{A}_x\):

\[
\sum_i w_i|h_i|=\Phi_1([x]).
\]

Since \(w_i>0\), each coordinate satisfies:

\[
|h_i|\le \Phi_1([x])/w_i.
\]

Thus \(\mathcal{A}_x\) lies in the finite coordinate box
\(\prod_i[-\Phi_1([x])/w_i,\Phi_1([x])/w_i]\). \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| positive-weight \(\ell_1\) level set lies in the coordinate box \(\prod_i[-\Phi_1([x])/w_i,\Phi_1([x])/w_i]\) | local | none identified | NOT-STARTED |

## Notes

- The source adds, verbatim: "If the residual constraints are closed in the
  declared exact or topological semantics, this boundedness plus closedness
  gives compactness. If the system does not declare a topology/compactness
  semantics, compactness must be replaced by explicit finite replay
  certificates for every tie minimum."
- The section's canonical-home note keeps this lemma net-new: "The
  admissible-TieR-domain conditions, the positive-weight boundedness lemma, and
  the solver-independent certificate format above are the realization-instance
  admission discipline and are kept net-new." It supplies the
  boundedness/compactness hypothesis consumed by [[ENC-0069]] Lexicographic
  Polyhedral TieR Determinism (canonical III.7).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §5.3 "R Determinism / TieR
  Certificate Rule" (statement and proof copied verbatim). Original header line:
  `**Lemma (Positive Weights Give Bounded Residual Ties).** In finite dimension,`

## Changelog

- 2026-06-09: ENC-0136 created (M2 E2 satellite extraction).
