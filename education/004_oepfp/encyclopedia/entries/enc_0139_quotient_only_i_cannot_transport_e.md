---
id: ENC-0139
kind: theorem
name: "Quotient-Only I Cannot Transport E"
status: CONDITIONAL
conditional_on: ["fixed cochain layer", "exact or declared-tolerance arithmetic", "declared action domain", "replayable witnesses"]
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md trunk Part III §6.5 'Theorem (Quotient-Only I Cannot Transport E)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0139 — Quotient-Only I Cannot Transport E

## Statement

Let \(I_Q:Q^1\to Q^1\) be a quotient-only isometry. Then
\(I_Q\circ E_\alpha\) is not a well-typed representative-level composition.

## Proof

\(E_\alpha\) has type \(C^1\to C^1\). \(I_Q\) has type
\(Q^1\to Q^1\). Their composition is not defined unless a projection
\(\pi:C^1\to Q^1\) is inserted, yielding \(I_Q\circ\pi\circ E_\alpha\), or a
representative lift \(I_C:C^1\to C^1\) is declared. The first expression is a
quotient-level diagnostic and loses representative information; the second
requires the representative-composable witness rule above. Therefore a
quotient-only \(I_Q\) cannot transport \(E_\alpha\). \(\square\)

## Hypotheses

- Section-level blanket from the source (§6 preamble), verbatim: "All results
  in this section are conditional on a fixed cochain layer, exact or
  declared-tolerance arithmetic, a declared action domain, and replayable
  witnesses." (This is the `conditional_on` list.)
- A quotient-only isometry is, per the §6.5 admission split, a map
  \(I_Q:Q^1\to Q^1\) with \(\Phi_1(I_Q([x]))=\Phi_1([x])\), acting on quotient
  classes, not representatives, and not typed as a map \(C^1\to C^1\).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| type-level non-composability of \(I_Q:Q^1\to Q^1\) with \(E_\alpha:C^1\to C^1\) absent a declared lift or projection | local | none identified | NOT-STARTED |

## Notes

- "The representative-composable witness rule above" in the proof refers to the
  §6.5 admission split: a representative-composable isometry \(I_C\) must carry
  or deterministically derive \(T_I(\alpha)\in C^0\) with
  \(I_C(d_0\alpha)=d_0T_I(\alpha)\) — cf. [[ENC-0138]].
- Companion policy corollary: [[ENC-0140]] Safe Compression Policy for I.
- Kept net-new per the source's §6.5 KEEP note (finer than canonical §IV.5).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (trunk; header status
  "DEPENDENT REALIZATION SPINE"), Part III §6.5 "I Admission Split and
  Transport Witness Rule" (statement and proof copied verbatim). Original
  header line:
  `#### Theorem: Quotient-Only I Cannot Transport E`

## Changelog

- 2026-06-09: ENC-0139 created (M2 E2 satellite extraction).
