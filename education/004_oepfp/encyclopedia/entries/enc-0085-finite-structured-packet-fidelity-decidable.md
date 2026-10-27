---
id: ENC-0085
kind: theorem
name: "Finite Structured Packet Fidelity Is Decidable"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.6"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.2 'Theorem IV.6'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0085 — Finite Structured Packet Fidelity Is Decidable

## Statement

If all field comparisons and normalizers are total deterministic polynomial-time, then $F(s, P)$ is decidable in polynomial time.

## Proof

*Proof.* $F$ is a finite conjunction of decidable predicates over finite typed schemas. A finite conjunction of decidable predicates is decidable. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| decidability of the seven-clause fidelity predicate \(F(s, P)\) from decidability of its field comparisons and normalizers | local | none identified | NOT-STARTED |

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.2
  (statement and proof copied verbatim). Original header line:
  `**Theorem IV.6 (Finite Structured Packet Fidelity Is Decidable).** [PROVED] If all field comparisons and normalizers are total deterministic polynomial-time, then $F(s, P)$ is decidable in polynomial time.`

## Changelog

- 2026-06-09: ENC-0085 created (M2 E1 extraction).
