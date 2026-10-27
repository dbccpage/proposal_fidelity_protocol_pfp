---
id: ENC-0898
kind: theorem
name: "Target-Augmented Shadow Repair"
status: MECHANIZED
conditional_on:
  - "The augmented shadow explicitly carries the target value as a second coordinate"
  - "The theorem concerns factorization only, not authority certification"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:target-augmented-shadow-repair", "paper:sn-packets:carry-missing-evaluator"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 17: Target-Augmented Shadows Carry the Target'"
uses: ["ENC-0897", "ENC-0890"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0898 - Target-Augmented Shadow Repair

## Statement

If a finite shadow is augmented with the target value itself,
`shadow_plus(world) = (shadow(world), value(world))`, then the target factors
through the augmented shadow by projection onto the second coordinate.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.target_augmented_shadow_carries_value`

`lake build SnSymbolGameAndPackets` succeeds and reports this theorem as
axiom-free.

## Notes

- This is the positive repair counterpart to [[ENC-0897]]. When a local shadow
  collapses target-distinct worlds, the generic finite repair is to carry the
  missing target datum explicitly.
- The theorem is a factorization theorem, not an authority theorem. The carried
  target still needs the normal packet, bridge, or terminalizer discipline
  before it can count as authority.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass to state the generic repair pattern for finite-shadow collisions.

## Changelog

- 2026-06-13: ENC-0898 created with Lean mechanization.

