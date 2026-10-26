---
id: ENC-0908
kind: theorem
name: "Coarsening Cannot Recover a Failed Refinement"
status: MECHANIZED
conditional_on:
  - "A refined packet maps deterministically to a coarser packet"
  - "The target does not descend through the refined packet"
  - "Descent is interpreted either as fiber invariance, decoder factorization, or primitive-difference quotient descent"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:coarsening-cannot-recover-failed-refinement", "paper:sn-packets:no-coarse-recovery-after-fine-failure"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 26: Coarsening Cannot Recover a Failed Refinement'"
uses: ["ENC-0899", "ENC-0900", "ENC-0907"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0908 - Coarsening Cannot Recover a Failed Refinement

## Statement

Let `fine : World -> Fine` be a refined packet and let
`coarsen : Fine -> Coarse` be a deterministic forgetting map. If a target does
not descend through the refined packet, then it cannot descend through the
coarsened packet `coarsen(fine(world))`.

The result holds in three forms: if fine-packet fiber invariance fails then
coarse-packet fiber invariance fails, if no fine decoder exists then no coarse
decoder exists, and if fine primitive-difference quotient descent fails then
coarse quotient descent fails.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.no_coarsened_invariant_if_no_refinement_invariant`
- `SnSymbolGameAndPackets.no_coarsened_factor_if_no_refinement_factor`
- `SnSymbolGameAndPackets.no_coarsened_quotient_descent_if_no_refinement_quotient_descent`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-invariance
and decoder-factorization contrapositive theorems as axiom-free; the quotient
contrapositive uses the standard quotient soundness axiom.

## Notes

- This is the contrapositive of [[ENC-0907]] and the general form of
  [[ENC-0900]]. If a richer packet cannot recover the target, then forgetting
  information cannot recover it.
- Any apparent recovery after coarsening must have introduced new structure
  outside the deterministic coarsening map: a bridge, oracle, license, or
  terminalizer.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the non-recovery half of the refinement/coarsening monotonicity law.

## Changelog

- 2026-06-13: ENC-0908 created with Lean mechanization.
