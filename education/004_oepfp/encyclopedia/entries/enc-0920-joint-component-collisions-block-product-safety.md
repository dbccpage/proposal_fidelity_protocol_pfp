---
id: ENC-0920
kind: theorem
name: "Joint Component Collisions Block Product Safety"
status: MECHANIZED
conditional_on:
  - "The paired encoding evaluates two components on the same original target value"
  - "The two worlds have distinct original target values"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:joint-component-collision", "paper:sn-packets:product-encoding-failure"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 37: Joint Component Collisions Block Product Safety'"
uses: ["ENC-0915", "ENC-0919"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0920 - Joint Component Collisions Block Product Safety

## Statement

If two worlds have different target values, but both components of a paired
encoding agree on those worlds, then the paired encoding is not target-image
injective. Conversely, a safe paired encoding forbids any such joint component
collision on target-distinct worlds.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.joint_encoded_collision_on_distinct_targets_blocks_pair_safe`
- `SnSymbolGameAndPackets.pair_safe_blocks_joint_encoded_collision`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry is the operational audit companion to [[ENC-0919]]. A tuple of
  added fields repairs a target collision only if no target-distinct pair
  remains equal in every component.
- It is another finite form of LGGR: locally equal component views do not carry
  the global target when their product still collapses target-distinct worlds.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing EPK from single encodings and serial pipelines to
  parallel field products.

## Changelog

- 2026-06-13: ENC-0920 created with Lean mechanization.
