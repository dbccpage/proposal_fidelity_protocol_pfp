---
id: ENC-0918
kind: theorem
name: "Any Unsafe Encoding Stage Makes the Pipeline Unsafe"
status: MECHANIZED
conditional_on:
  - "The pipeline has two target-encoding stages"
  - "Safety is target-image injectivity on the observed image at each stage"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:unsafe-encoding-stage", "paper:sn-packets:pipeline-encoding-failure"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 35: Any Unsafe Encoding Stage Makes the Pipeline Unsafe'"
uses: ["ENC-0915", "ENC-0917"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0918 - Any Unsafe Encoding Stage Makes the Pipeline Unsafe

## Statement

For a two-stage encoding pipeline

```text
value |-> encode2(encode1(value)),
```

the composed encoding is not target-image injective if either `encode1` is not
target-image injective for the original target, or `encode2` is not
target-image injective on the observed first-stage image
`encode1(value(world))`.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.unsafe_first_stage_blocks_composed_target_image_injective`
- `SnSymbolGameAndPackets.unsafe_second_stage_blocks_composed_target_image_injective`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry is the operational contrapositive of [[ENC-0917]]. A final encoded
  display value cannot certify the original target unless each observed stage
  preserves the partition presented to that stage.
- The theorem applies to serializers, labels, hashes, colors, badges, display
  strings, or transport encodings whenever they are used as target
  representations.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while turning EPK target-encoding composition into an audit rule.

## Changelog

- 2026-06-13: ENC-0918 created with Lean mechanization.
