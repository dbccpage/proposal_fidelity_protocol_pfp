---
id: ENC-0089
kind: theorem
name: "Priority Classifier Totality"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.10"]
sources:
  - "canonical_omega_math_spine.md v1.5.2 §IV.3 'Theorem IV.10'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0089 — Priority Classifier Totality

## Statement

Every declared action receives exactly one label.

## Proof

*Proof.* Ordered finite case split with a universal fallback. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| totality and single-valuedness of the first-match classifier \(\mathcal{O}\) (ordered finite case split with universal fallback) | local | none identified | NOT-STARTED |

## Notes

- The source region between this theorem and §IV.4 carries two further
  non-theorem blocks that are NOT part of this statement and are not extracted
  as separate entries here: the "**Projector policy.**" doctrine (the
  classifier remains the canonical first-match map; declared projectors are
  additional witnesses only under four listed conditions; the \(L^1\)-optimal
  residual operator \(R_T\) remains governed by deterministic TieR) and the
  "**Effect on Obstruction Classes.**" table giving each operator class's
  algebraic effect on \(Q^1\) (\(E_\alpha\) quotient-preserving, \(R_T\)
  class-preserving/representative-selecting, \(I_C\) \(\Phi_1\)-preserving,
  \(C\) diagnostic-only, \(M\) uncertified/potentially class-destroying).

## Provenance

- Extracted 2026-06-09 from `canonical_omega_math_spine.md` v1.5.2, §IV.3
  (statement and proof copied verbatim). Original header line:
  `**Theorem IV.10 (Priority Classifier Totality).** [PROVED] Every declared action receives exactly one label.`

## Changelog

- 2026-06-09: ENC-0089 created (M2 E1 extraction).
