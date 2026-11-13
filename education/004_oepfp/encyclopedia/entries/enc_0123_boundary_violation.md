---
id: ENC-0123
kind: theorem
name: "Boundary Violation"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: []
sources:
  - "symbol_game_math_spine.md math_spines_v002 §2.2 'Theorem (unnamed)'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0123 — Boundary Violation

## Statement

\[
LocalGreen(x,P)\land \neg GlobalGreen(x,P)\Rightarrow BoundaryViolation(x,P).
\]

## Hypotheses

The source fixes the predicates at the head of §2, verbatim:

Let:

```text
LocalGreen(x,P)  := LΓ(x,P)=1
GlobalGreen(x,P) := VΓ(x,P)=1
```

## Proof

A local-valid/global-invalid packet is exactly a boundary violation:
the local rule replays, but the whole packet fails to preserve the declared
problem, protected skeleton, terminal target, evidence ceiling, or family
invariants. \(\square\)

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| LocalGreen ∧ ¬GlobalGreen ⇒ BoundaryViolation as definitional case split | local | none identified | NOT-STARTED |

## Notes

- The theorem is unnamed in the source; the entry name is the §2.2 section
  title ("Boundary Violation").
- The source follows the proof with a scope sentence, verbatim:
  "BoundaryViolation includes any local-valid packet that fails the
  family-level global invariant, protected boundary, terminal consistency, or
  evidence ceiling."
- The source then gives constructive witnesses, verbatim:
  "**Constructive witnesses.**
  - LP: a valid dual bound with terminal `subopt` while gap is zero.
  - Code rewrite: parseable Rust rewrite that mutates protected signature without
    license.
  - Operator packet: well-formed residual projection missing deterministic TieR.
  - Cochain packet: locally typed maps with \(d_1d_0\ne 0\)."
- The §2 KEEP note flags the section UNCERTAIN (definitional theorems +
  constructive witnesses not reproduced in canonical; cf. canonical §IV.6
  CT-7 = [[ENC-0092]] for the quantified local-green/global-red gap, and
  [[ENC-0081]] for the four-status boundary decidability that names
  `LocalValidGlobalInvalid`).

## Provenance

- Extracted 2026-06-09 from `symbol_game_math_spine.md` (math_spines_v002,
  unversioned; status header "DEPENDENT REALIZATION SPINE"), §2.2 "Boundary
  Violation" under §2 "Local/Global Boundary" (statement, hypotheses context,
  proof, and witnesses copied verbatim). Original header line:
  `**Theorem.**` (§2.2)

## Changelog

- 2026-06-09: ENC-0123 created (M2 E2 satellite extraction).
