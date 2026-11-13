---
id: ENC-0088
kind: definition
name: 'Operator Classification Functor $\mathcal{O}$'
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.9"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.3 'Definition IV.9'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0088 — Operator Classification Functor $\mathcal{O}$

## Statement

The first-match priority classifier over declared actions:

$$
\mathcal{O} : \mathsf{DeclaredAction} \to \{M, C, E, R, I, M_{\mathsf{fallback}}\}
$$

with priority order $M \prec C \prec E \prec R \prec I \prec M_{\mathsf{fallback}}$.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| definition of the first-match priority classifier \(\mathcal{O}\) with order \(M \prec C \prec E \prec R \prec I \prec M_{\mathsf{fallback}}\) | local | none identified | NOT-STARTED |

## Notes

- §IV.3 is titled "The Operator-Discovery Functor and Effect on Obstruction
  Classes". The section's later "**Projector policy.**" block (after Theorem
  IV.10) reaffirms that "The classifier remains the canonical first-match map"
  and that projectors do not replace it — see [[ENC-0089]] Notes.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.3
  (statement copied verbatim; definition carries no status bracket).
  Original header line:
  `**Definition IV.9 (Operator Classification Functor $\mathcal{O}$).** The first-match priority classifier over declared actions:`

## Changelog

- 2026-06-09: ENC-0088 created (M2 E1 extraction).
