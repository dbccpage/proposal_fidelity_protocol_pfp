---
id: ENC-0909
kind: theorem
name: "Fiber-Equivalent Representations Preserve Descent"
status: MECHANIZED
conditional_on:
  - "Two packet representations identify exactly the same pairs of worlds, or are mutually decodable on all worlds"
  - "The target is a function on worlds"
  - "Descent is interpreted as fiber invariance, decoder factorization, primitive-difference quotient descent, or no-factorization"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:fiber-equivalent-representations", "paper:sn-packets:representation-equivalence-preserves-descent"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 27: Fiber-Equivalent Packet Representations Preserve Descent'"
uses: ["ENC-0899", "ENC-0907", "ENC-0908"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0909 - Fiber-Equivalent Representations Preserve Descent

## Statement

If two packet representations identify exactly the same pairs of worlds, then
target descent through one representation is equivalent to target descent
through the other. This holds for fiber invariance and for the
primitive-difference quotients induced by the two representations.

If the two representations are mutually decodable on all worlds, then ordinary
decoder factorization through one representation is equivalent to decoder
factorization through the other. Consequently, no-factorization also transports
across mutually decodable representations.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.fiber_equivalent_shadow_invariant_iff`
- `SnSymbolGameAndPackets.fiber_equivalent_quotient_descent_iff`
- `SnSymbolGameAndPackets.mutually_decodable_factorization_iff`
- `SnSymbolGameAndPackets.mutually_decodable_no_factorization_iff`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-invariance,
mutual-decoder factorization, and mutual-decoder no-factorization theorems as
axiom-free; the quotient-descent equivalence uses the standard quotient
soundness axiom.

## Notes

- This is the packet representation boundary for the S(n) / Symbol Game paper.
  Serialization or record-shape changes preserve EPK facts only when they
  preserve the same world fibers.
- If a representation change merges or splits fibers, use [[ENC-0907]] and
  [[ENC-0908]] instead of treating the representations as equivalent.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the representation-invariance theorem for finite shadows.

## Changelog

- 2026-06-13: ENC-0909 created with Lean mechanization.
