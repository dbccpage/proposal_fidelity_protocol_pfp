---
id: ENC-0081
kind: theorem
name: "Boundary Decidability"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.2"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.1 'Theorem IV.2'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0081 — Boundary Decidability

## Statement

If $\mathrm{Parse}_\Gamma$, $L_\Gamma$, and $V_\Gamma$ are total deterministic polynomial-time procedures, then $\mathcal{V}$ is total and polynomial-time.

## Proof

*Proof.* Each step terminates in polynomial time by assumption. A finite composition of polynomial-time procedures is polynomial-time. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| totality (and, if a cost model is formalized, polynomial-time bound) of \(\mathcal{V}\) from totality of its three stages | local | none identified | NOT-STARTED |

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.1
  (statement and proof copied verbatim). Original header line:
  `**Theorem IV.2 (Boundary Decidability).** [PROVED] If $\mathrm{Parse}_\Gamma$, $L_\Gamma$, and $V_\Gamma$ are total deterministic polynomial-time procedures, then $\mathcal{V}$ is total and polynomial-time.`

## Changelog

- 2026-06-09: ENC-0081 created (M2 E1 extraction).
