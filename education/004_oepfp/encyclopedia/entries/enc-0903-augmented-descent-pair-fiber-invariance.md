---
id: ENC-0903
kind: theorem
name: "Augmented Descent Pair-Fiber Criterion"
status: MECHANIZED
conditional_on:
  - "The augmented packet is the pair of a local shadow and an extra field"
  - "The target is evaluated as a function on worlds"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:augmented-descent-pair-fiber", "paper:sn-packets:packet-repair-fiber-criterion"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 22: Augmented Descent Is Exactly Pair-Fiber Invariance'"
uses: ["ENC-0899", "ENC-0901", "ENC-0902"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0903 - Augmented Descent Pair-Fiber Criterion

## Statement

For an augmented packet `(shadow, extra)`, a target descends through the
augmented packet quotient exactly when the target is invariant on augmented
fibers: if `shadow(x) = shadow(y)` and `extra(x) = extra(y)`, then
`value(x) = value(y)`.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.augmented_value_descends_iff_pair_fiber_invariant`

`lake build SnSymbolGameAndPackets` succeeds. The theorem uses the standard
quotient soundness axiom, matching the existing primitive-difference quotient
machinery.

## Notes

- This entry is the exact positive criterion behind [[ENC-0901]] and
  [[ENC-0902]]. An extra field repairs a local/global collision precisely when
  the augmented packet fibers are fine enough for the target.
- The theorem is a factorization criterion, not an authority theorem. The
  resulting target still needs the normal packet, bridge, or terminalizer
  discipline.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the augmented-packet quotient criterion.

## Changelog

- 2026-06-13: ENC-0903 created with Lean mechanization.

