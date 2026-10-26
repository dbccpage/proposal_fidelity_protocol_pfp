---
id: ENC-0122
kind: theorem
name: "Admissible Step"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §2.1 'Theorem (unnamed)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0122 — Admissible Step

## Statement

\[
LocalGreen(x,P)\land GlobalGreen(x,P)\Rightarrow AdmissibleStep(x,P).
\]

## Hypotheses

The source fixes the predicates at the head of §2, verbatim:

Let:

```text
LocalGreen(x,P)  := LΓ(x,P)=1
GlobalGreen(x,P) := VΓ(x,P)=1
```

## Proof

`AdmissibleStep` is defined as a step that passes both local replay
and global boundary verification. The implication is definitional. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| definitional implication LocalGreen ∧ GlobalGreen ⇒ AdmissibleStep | local | none identified | NOT-STARTED |

## Notes

- The theorem is unnamed in the source; the entry name is the §2.1 section
  title ("Admissible Step").
- The source follows the proof with a scope caveat, verbatim: "AdmissibleStep
  here means admissible relative to the declared verifier and packet family,
  not policy-safe or externally true."
- The §2 KEEP note flags the section UNCERTAIN: "Canonical §IV.6 (CT-7)
  quantifies the local-green/global-red gap (the NGD bound) but does not state
  `AdmissibleStep` / `BoundaryViolation` definitionally; the definitional
  theorems + constructive witnesses below are not reproduced in canonical.
  Kept. Flagged." See-also [[ENC-0092]] (CT-7).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §2.1 "Admissible
  Step" under §2 "Local/Global Boundary" (statement, hypotheses context, and
  proof copied verbatim). Original header line:
  `**Theorem.**` (§2.1)

## Changelog

- 2026-06-09: ENC-0122 created (M2 E2 satellite extraction).
