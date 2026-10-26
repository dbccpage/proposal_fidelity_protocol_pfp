---
id: ENC-0906
kind: theorem
name: "Successful Bridge Separates Target-Distinct Worlds"
status: MECHANIZED
conditional_on:
  - "A bridge packet is modeled as a finite map from worlds to bridge values"
  - "The target is modeled as a function on worlds"
  - "Successful decoding means a function from bridge values recovers the target for every world"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:successful-bridge-separates-targets", "paper:sn-packets:bridge-must-separate-target-collisions"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 24: A Successful Bridge Must Separate Target-Distinct Worlds'"
uses: ["ENC-0897", "ENC-0901", "ENC-0905"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0906 - Successful Bridge Separates Target-Distinct Worlds

## Statement

If a bridge packet successfully decodes a target, then the bridge separates any
two worlds with different target values. Equivalently, if two target-distinct
worlds have the same bridge packet, then no decoder from bridge packets to
target values can be correct for every world.

For the RH-source tower witness, any bridge that decodes whether an RH-named
tower is the `delta = 2` Symbol Game tower must distinguish the RH-named
`delta = 2` world from the RH-named non-`delta = 2` world.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.bridge_factorization_implies_fiber_invariant`
- `SnSymbolGameAndPackets.bridge_factorization_descends_to_bridge_quotient`
- `SnSymbolGameAndPackets.bridge_factorization_separates_target_distinct_worlds`
- `SnSymbolGameAndPackets.nonseparating_bridge_cannot_decode_target`
- `SnSymbolGameAndPackets.rh_delta_bridge_must_separate_delta_worlds`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-invariance,
separation, no-decode, and RH witness theorems as axiom-free; the
bridge-quotient descent theorem uses the standard quotient soundness axiom.

## Notes

- This is the bridge form of the generic shadow-collision obstruction in
  [[ENC-0897]]. A bridge is only useful for a target when its fibers do not
  collapse target-distinct worlds.
- The quotient theorem ties the bridge rule to Primitive Difference: successful
  bridge decoding gives target invariance on bridge fibers, hence descent
  through the bridge-induced quotient.
- This theorem does not construct the RH continuum bridge. It states a necessary
  finite contract condition that any such bridge must satisfy before it can
  certify a tower delta.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the next EPK generalization after the RH-source-name boundary.

## Changelog

- 2026-06-13: ENC-0906 created with Lean mechanization.
