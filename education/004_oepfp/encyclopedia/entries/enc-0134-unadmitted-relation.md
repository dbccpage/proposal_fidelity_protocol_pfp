---
id: ENC-0134
kind: lemma
name: "UnadmittedRelation"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §5.2 'Lemma (UnadmittedRelation)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0134 — UnadmittedRelation

## Statement

Residual projection without TieR is an
unadmitted relation, not class \(M\).

## Hypotheses

Verbatim setup from the source section:

> Let:
>
> \[
> R(x)=\arg\min_{y\in[x]}\|y\|_{1,w}.
> \]
>
> Without a tie policy, \(R\) is relation-valued when multiple minimizers exist.

## Proof

Every minimizer lies in the same quotient class \([x]\) and achieves
\(\Phi_1([x])\). Thus the construction preserves the quotient class and does
not damage \(\Phi_1\). Its defect is non-determinism/replay failure, not
mutation. Adding TieR repairs determinism without changing the mathematical
role. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| tie-policy-free argmin preserves quotient class and \(\Phi_1\); its defect is non-determinism, not mutation | local | none identified | NOT-STARTED |

## Notes

- Part of the satellite §5 admission-discipline content that the source's
  split note explicitly keeps net-new ("has no canonical home and is **kept
  net-new**"); the canonical TieR determinism results are [[ENC-0069]] /
  [[ENC-0070]] (spine III.7 / III.8), which concern the *admitted* deterministic
  \(R_T\), not the unadmitted relation.
- Companion: [[ENC-0133]] AdmissionStatus Is Not OperatorClass.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §5.2 "UnadmittedRelation Lemma"
  (statement and proof copied verbatim). Original header line:
  `**Lemma (UnadmittedRelation).** Residual projection without TieR is an`

## Changelog

- 2026-06-09: ENC-0134 created (M2 E2 satellite extraction).
