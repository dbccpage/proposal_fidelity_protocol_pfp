---
id: ENC-0907
kind: theorem
name: "Arbitrary Refinement Preserves Descent"
status: MECHANIZED
conditional_on:
  - "A refined packet maps deterministically to a coarser packet"
  - "The target already descends through the coarsened packet"
  - "Descent is interpreted either as fiber invariance, decoder factorization, or primitive-difference quotient descent"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:arbitrary-refinement-preserves-descent", "paper:sn-packets:coarse-descent-lifts-to-fine"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 25: Arbitrary Refinements Preserve Descent'"
uses: ["ENC-0899", "ENC-0900", "ENC-0904", "ENC-0906"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0907 - Arbitrary Refinement Preserves Descent

## Statement

Let `fine : World -> Fine` be a refined packet and let
`coarsen : Fine -> Coarse` be a deterministic forgetting map. If a target
descends through the coarsened packet `coarsen(fine(world))`, then it also
descends through the refined packet `fine(world)`.

The result holds in three forms: fiber invariance lifts from the coarse packet
to the fine packet, a decoder from coarse packets lifts to a decoder from fine
packets, and primitive-difference quotient descent through the coarse quotient
lifts to quotient descent through the fine quotient.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.coarsened_shadow_invariant_lifts_to_refinement`
- `SnSymbolGameAndPackets.coarsened_factor_lifts_to_refinement`
- `SnSymbolGameAndPackets.coarsened_quotient_descent_lifts_to_refinement`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-invariance
and decoder-factorization lift theorems as axiom-free; the quotient-descent
lift uses the standard quotient soundness axiom.

## Notes

- This theorem generalizes [[ENC-0904]] from pair augmentation to arbitrary
  deterministic refinement.
- Together with [[ENC-0900]], it gives the monotonicity boundary: coarsening
  cannot repair a target collision, while refinement cannot destroy a target
  that already descended through a coarser observable.
- This is a descent-preservation theorem, not an authority theorem. The refined
  packet still needs the normal bridge, license, or terminalizer discipline.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the next general EPK monotonicity theorem.

## Changelog

- 2026-06-13: ENC-0907 created with Lean mechanization.
