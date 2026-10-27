---
id: ENC-0915
kind: theorem
name: "Target-Image Injectivity Is Fiber Equivalence"
status: MECHANIZED
conditional_on:
  - "The target is a function from worlds to values"
  - "The encoding is evaluated on target values through encodedTarget"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:target-image-fiber-equivalence", "paper:sn-packets:encoded-target-fibers"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 32: Target-Image Injectivity Is Fiber Equivalence'"
uses: ["ENC-0909", "ENC-0913", "ENC-0914"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0915 - Target-Image Injectivity Is Fiber Equivalence

## Statement

For a target `value : World -> Value` and encoding
`encode : Value -> Encoded`, target-image injectivity is equivalent to equality
of encoded target values having exactly the same world fibers as equality of
original target values:

```text
encode(value(x)) = encode(value(y))  <=>  value(x) = value(y).
```

Consequently, target-image injective encodings preserve target distinctions:
if two worlds have different target values, their encoded target values are
different. Conversely, an encoded collision between target-distinct worlds
blocks target-image injectivity.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.target_image_injective_encoded_target_fibers`
- `SnSymbolGameAndPackets.encoded_target_fiber_equivalence_implies_target_image_injective`
- `SnSymbolGameAndPackets.target_image_injective_iff_encoded_target_fiber_equivalence`
- `SnSymbolGameAndPackets.target_image_injective_preserves_target_distinction`
- `SnSymbolGameAndPackets.encoded_collision_on_distinct_targets_blocks_target_image_injective`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry is the fiber-level EPK form of [[ENC-0914]]. It says a valid
  encoding may rename target values but may not change the target partition of
  the world space under certification.
- It complements [[ENC-0913]]: an encoded apparent repair that merges two
  target-distinct worlds is a target change, not a packet repair.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing the target-encoding/EPK boundary.

## Changelog

- 2026-06-13: ENC-0915 created with Lean mechanization.
