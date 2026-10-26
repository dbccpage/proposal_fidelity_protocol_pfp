---
id: ENC-0917
kind: theorem
name: "Safe Target Encodings Compose Exactly"
status: MECHANIZED
conditional_on:
  - "The first encoding is evaluated on original target values"
  - "The second encoding is evaluated on the first encoded target image"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:safe-target-encoding-composition", "paper:sn-packets:target-image-composition-iff"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 34: Safe Target Encodings Compose Exactly'"
uses: ["ENC-0914", "ENC-0915", "ENC-0916"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0917 - Safe Target Encodings Compose Exactly

## Statement

Let `encode1 : Value -> Encoded1` and
`encode2 : Encoded1 -> Encoded2`. The composed encoding
`value |-> encode2(encode1(value))` is target-image injective for `value`
exactly when both stages are safe on the images they actually see:

```text
encode1 is target-image injective for value
and
encode2 is target-image injective for encode1(value(world)).
```

Equivalently, a safe composed encoding cannot hide a collision in either stage,
and safe representation changes compose.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.target_image_injective_composition`
- `SnSymbolGameAndPackets.composed_target_image_injective_implies_first`
- `SnSymbolGameAndPackets.composed_target_image_injective_implies_second_on_first_image`
- `SnSymbolGameAndPackets.target_image_injective_composition_iff`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry modularizes [[ENC-0914]] and [[ENC-0915]]. A pipeline of encodings
  is safe for an EPK target exactly when each stage preserves the partition
  presented to that stage.
- It supports [[ENC-0916]] by showing that representation-invariant downstream
  descent remains stable under safe encoding pipelines.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing EPK target encodings from single maps to pipelines.

## Changelog

- 2026-06-13: ENC-0917 created with Lean mechanization.
