---
id: ENC-0135
kind: lemma
name: "Finite Lexicographic TieR"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §5.2 'Lemma (Finite Lexicographic TieR)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0135 — Finite Lexicographic TieR

## Statement

If the optimal residual set is a
nonempty finite subset of a totally ordered coordinate domain, lexicographic
TieR selects a unique representative.

## Proof

Lexicographic order on finite coordinate tuples over a total order
is itself a total order. Every nonempty finite totally ordered set has a unique
least element. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| lexicographic order on finite tuples over a total order is total; nonempty finite totally ordered set has a unique least element | local | none identified | NOT-STARTED |

## Notes

- The source immediately bounds the lemma's reach, verbatim: "For polyhedral or
  infinite argmin sets, this lemma is insufficient. A deterministic TieR for
  those cases must declare an additional bounded optimization problem or
  canonical solver certificate."
- Distinct from [[ENC-0069]] Lexicographic Polyhedral TieR Determinism
  (canonical III.7): that theorem handles the nonempty *compact polyhedral*
  optimal set with a separating functional list; this lemma is the elementary
  finite-set case with its own proof, kept in the satellite's net-new
  admission-discipline block.

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §5.2 "UnadmittedRelation Lemma"
  (statement and proof copied verbatim). Original header line:
  `**Lemma (Finite Lexicographic TieR).** If the optimal residual set is a`

## Changelog

- 2026-06-09: ENC-0135 created (M2 E2 satellite extraction).
