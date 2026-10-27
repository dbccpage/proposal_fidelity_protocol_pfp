---
id: ENC-0916
kind: theorem
name: "Target-Image Encodings Preserve Downstream Descent"
status: MECHANIZED
conditional_on:
  - "The encoding is target-image injective for the source target"
  - "Downstream descent is measured by shadow-fiber invariance or the induced primitive-difference quotient"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:target-image-downstream-descent", "paper:sn-packets:encoded-target-observable-equivalence"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 33: Target-Image Encodings Preserve Downstream Descent'"
uses: ["ENC-0899", "ENC-0909", "ENC-0914", "ENC-0915"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0916 - Target-Image Encodings Preserve Downstream Descent

## Statement

If an encoding is target-image injective for `value`, then the encoded target
observable `encode(value(world))` has the same fibers as the original target
observable `value(world)`. Therefore every downstream target has the same
descent status through the encoded observable as it has through the original
target observable.

At the primitive-difference quotient level, downstream descent through the
encoded-target quotient is equivalent to downstream descent through the
original-target quotient.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.target_image_injective_preserves_downstream_shadow_invariant`
- `SnSymbolGameAndPackets.target_image_injective_preserves_downstream_quotient_descent`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry applies the representation-equivalence discipline of [[ENC-0909]]
  to target encodings. A target-image injective encoding is a safe
  representation of the target partition for every downstream descent query.
- It depends on the fiber-equivalence characterization in [[ENC-0915]]. If the
  encoding merges target fibers, the observable is no longer equivalent.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing EPK from a single target to downstream consumers.

## Changelog

- 2026-06-13: ENC-0916 created with Lean mechanization.
