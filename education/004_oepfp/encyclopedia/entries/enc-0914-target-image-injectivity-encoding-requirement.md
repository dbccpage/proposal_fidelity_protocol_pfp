---
id: ENC-0914
kind: theorem
name: "Target-Image Injectivity Is the Encoding Requirement"
status: MECHANIZED
conditional_on:
  - "The target is a function from worlds to values"
  - "The encoding is evaluated only on target values that occur in the modeled world space"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:target-image-injectivity", "paper:sn-packets:encoding-requirement"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 31: Target-Image Injectivity Is the Exact Encoding Requirement'"
uses: ["ENC-0899", "ENC-0911", "ENC-0913"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0914 - Target-Image Injectivity Is the Encoding Requirement

## Statement

For a target `value : World -> Value` and an encoding
`encode : Value -> Encoded`, global injectivity of `encode` is sufficient but
not necessary for reflection of descent. The exact requirement is injectivity
on the target image:

```text
encode(value(x)) = encode(value(y))  =>  value(x) = value(y).
```

Under this condition, encoded shadow-fiber invariance is equivalent to original
target shadow-fiber invariance, and encoded primitive-difference quotient
descent is equivalent to original target quotient descent. A globally injective
encoding automatically satisfies the target-image condition.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.injective_encoding_implies_target_image_injective`
- `SnSymbolGameAndPackets.target_image_injective_reflects_shadow_invariant`
- `SnSymbolGameAndPackets.target_image_injective_shadow_invariant_iff`
- `SnSymbolGameAndPackets.target_image_injective_reflects_quotient_descent`
- `SnSymbolGameAndPackets.target_image_injective_quotient_descent_iff`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry sharpens [[ENC-0911]]: global injectivity is a convenient sufficient
  condition, while target-image injectivity is the exact model-relative
  condition.
- It also complements [[ENC-0913]]: an encoded apparent repair fails this
  condition exactly when it merges two target values that occur in the worlds
  under certification.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass while generalizing the EPK target-encoding boundary.

## Changelog

- 2026-06-13: ENC-0914 created with Lean mechanization.
