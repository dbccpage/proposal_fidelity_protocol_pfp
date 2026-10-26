---
id: ENC-0899
kind: theorem
name: "Shadow Quotient Descent Criterion"
status: MECHANIZED
conditional_on:
  - "A shadow map induces the primitive-difference relation shadow(x) = shadow(y)"
  - "The target is evaluated as a function on worlds"
layer: symbol-game
tower_level: null
primitive: difference
aliases: ["paper:sn-packets:shadow-quotient-descent", "paper:sn-packets:fiber-invariance-criterion"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 18: Shadow Quotient Descent Is Exactly Fiber Invariance'"
uses: ["ENC-0897", "ENC-0898", "ENC-0889"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_factorization.lean"
  - "PaperER007.shadow_quotient_descent_iff_fiber_invariance"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0899 - Shadow Quotient Descent Criterion

## Statement

A shadow map induces a primitive-difference quotient by zero-relating worlds
with the same shadow. A target descends to that quotient exactly when it is
invariant on shadow fibers: whenever `shadow(x) = shadow(y)`, then
`value(x) = value(y)`.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.shadow_value_descends_iff_fiber_invariant`

`lake build SnSymbolGameAndPackets` succeeds. The theorem uses the standard
quotient soundness axiom, matching the existing primitive-difference quotient
machinery.

## Notes

- This entry gives the exact quotient criterion behind [[ENC-0897]]. A target
  can factor through a local shadow quotient if and only if the target is
  constant on every shadow fiber.
- The criterion explains LGGR as a failed descent condition: the local dashboard
  quotient identifies states that the global evaluator separates.

- PaperER007 reconciliation (2026-07-19): The PaperER007 theorem is an imported wrapper of the existing quotient-descent result. It adds paper ownership, not a new quotient proof. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass to connect the shadow-collision theorem directly to Primitive Difference.

## Changelog

- 2026-06-13: ENC-0899 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
