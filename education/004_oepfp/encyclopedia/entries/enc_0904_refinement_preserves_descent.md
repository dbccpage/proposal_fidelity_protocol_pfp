---
id: ENC-0904
kind: theorem
name: "Refinement Preserves Descent"
status: MECHANIZED
conditional_on:
  - "The augmented packet is the pair of a base shadow and an extra field"
  - "The target already factors through or descends through the base shadow"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:refinement-preserves-descent", "paper:sn-packets:extra-fields-do-not-break-descent"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 23: Refinement Preserves Descent'"
uses: ["ENC-0899", "ENC-0900", "ENC-0903"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0904 - Refinement Preserves Descent

## Statement

If a target already descends through a base shadow, then it also descends
through any augmented packet `(shadow, extra)`. Equivalently, base-shadow fiber
invariance lifts to augmented-packet fiber invariance, and any decoder from the
base shadow lifts to a decoder from the augmented packet by ignoring the extra
field.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.shadow_fiber_invariant_lifts_to_augmented`
- `SnSymbolGameAndPackets.shadow_factor_lifts_to_augmented_shadow`
- `SnSymbolGameAndPackets.shadow_quotient_descent_lifts_to_augmented_quotient`

`lake build SnSymbolGameAndPackets` succeeds. The fiber and decoder lift
theorems are axiom-free. The quotient-descent lift uses the standard quotient
soundness axiom, matching the surrounding primitive-difference quotient
machinery.

## Notes

- This entry is the monotonicity complement to [[ENC-0900]] and [[ENC-0903]].
  A refinement cannot repair a collision unless it separates the target values,
  but it also cannot break a target that already descended through the base
  shadow.
- The theorem is a preservation result, not an authority result. The refined
  packet still needs the usual bridge, license, or terminalizer before it can
  act as a contract witness.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the positive refinement counterpart to the LGGR no-repair results.

## Changelog

- 2026-06-13: ENC-0904 created with Lean mechanization.
