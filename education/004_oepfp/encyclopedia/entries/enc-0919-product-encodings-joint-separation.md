---
id: ENC-0919
kind: theorem
name: "Product Encodings Are Safe Exactly When Jointly Separating"
status: MECHANIZED
conditional_on:
  - "The two encodings are evaluated in parallel on the same original target value"
  - "Safety is target-image injectivity for the paired encoding"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:product-encoding-joint-separation", "paper:sn-packets:parallel-target-encoding"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 36: Product Encodings Are Safe Exactly When Jointly Separating'"
uses: ["ENC-0914", "ENC-0915", "ENC-0917", "ENC-0918"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0919 - Product Encodings Are Safe Exactly When Jointly Separating

## Statement

For two target encodings `encode1` and `encode2`, the paired observable

```text
value |-> (encode1(value), encode2(value))
```

is target-image injective exactly when the two components jointly separate
target fibers:

```text
encode1(value(x)) = encode1(value(y))
and
encode2(value(x)) = encode2(value(y))
  => value(x) = value(y).
```

If either component is already target-image injective, then the pair is safe.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.pair_target_image_injective_iff_joint`
- `SnSymbolGameAndPackets.left_target_image_injective_implies_joint`
- `SnSymbolGameAndPackets.right_target_image_injective_implies_joint`
- `SnSymbolGameAndPackets.left_target_image_injective_implies_pair_safe`
- `SnSymbolGameAndPackets.right_target_image_injective_implies_pair_safe`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry is the parallel-packet counterpart to the serial composition law
  [[ENC-0917]] and its failure rule [[ENC-0918]].
- It gives the exact EPK criterion for adding fields: a tuple of fields repairs
  a collapsed target view only when the tuple jointly separates the target
  fibers under certification.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing EPK from serial encoding pipelines to parallel field
  products.

## Changelog

- 2026-06-13: ENC-0919 created with Lean mechanization.
