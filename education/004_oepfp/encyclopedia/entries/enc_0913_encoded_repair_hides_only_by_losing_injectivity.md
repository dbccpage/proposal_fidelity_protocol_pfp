---
id: ENC-0913
kind: theorem
name: "Encoded Repair Hides Only by Losing Injectivity"
status: MECHANIZED
conditional_on:
  - "A finite shadow identifies a pair of worlds"
  - "The original target separates that same pair"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:encoded-repair-noninjective", "paper:sn-packets:target-encoding-loss-boundary"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 30: Encoded Repair Can Hide a Collision Only by Losing Injectivity'"
uses: ["ENC-0897", "ENC-0899", "ENC-0911"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0913 - Encoded Repair Hides Only by Losing Injectivity

## Statement

Suppose a shadow identifies two worlds while the original target separates
them. If the encoded target is invariant on that same shadow fiber, then the
encoding is not injective. The same conclusion holds when the encoded target
descends through the primitive-difference quotient induced by the shadow.

Equivalently: a label, bucket, color, score, or UI status can hide an LGGR
collision only by merging target values that the original evaluator needed to
distinguish.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.encoded_invariant_on_target_collision_forces_noninjective`
- `SnSymbolGameAndPackets.encoded_quotient_descent_on_target_collision_forces_noninjective`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry is the converse boundary to [[ENC-0911]]. Injective encodings
  preserve and reflect descent; non-injective encodings can hide a collision
  only by discarding the target distinction.
- The theorem does not certify a repair. It classifies an apparent repair as a
  target change unless a separate packet field, bridge, or terminalizer carries
  the missing distinction.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while extending the EPK/LGGR target-encoding boundary.

## Changelog

- 2026-06-13: ENC-0913 created with Lean mechanization.
