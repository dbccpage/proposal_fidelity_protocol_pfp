---
id: ENC-0910
kind: theorem
name: "Augmented Repair Is Target-Collision Separation"
status: MECHANIZED
conditional_on:
  - "The augmented packet is the pair of a base shadow and an extra field"
  - "The target has decidable equality for the separation-to-invariance direction"
  - "Descent is interpreted as augmented fiber invariance or primitive-difference quotient descent"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:augmented-repair-target-collision-separation", "paper:sn-packets:repair-iff-separates-target-collisions"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 28: Augmented Repair Is Exactly Target-Collision Separation'"
uses: ["ENC-0901", "ENC-0903", "ENC-0908"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0910 - Augmented Repair Is Target-Collision Separation

## Statement

For an augmented packet `(shadow, extra)`, repair succeeds exactly when the
extra field separates every target-distinct pair that the base shadow
collapses:

```text
shadow(x) = shadow(y) and value(x) != value(y)  =>  extra(x) != extra(y).
```

For targets with decidable equality, this condition is equivalent to augmented
fiber invariance, and therefore equivalent to descent through the augmented
primitive-difference quotient.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.augmented_fiber_invariant_iff_separates_target_collisions`
- `SnSymbolGameAndPackets.augmented_quotient_descent_iff_separates_target_collisions`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-level
criterion as axiom-free; the quotient-descent criterion uses the standard
quotient soundness axiom.

## Notes

- This is the global repair criterion behind [[ENC-0901]] and [[ENC-0903]].
- The extra field does not need to equal the target. It must separate every
  target collision left by the base shadow.
- The theorem is still a factorization theorem, not an authority theorem. A
  repaired packet still needs bridge, license, or terminalizer discipline.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the global target-collision criterion for augmented repair.

## Changelog

- 2026-06-13: ENC-0910 created with Lean mechanization.
