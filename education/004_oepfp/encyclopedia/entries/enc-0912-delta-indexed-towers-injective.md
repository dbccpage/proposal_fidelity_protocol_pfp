---
id: ENC-0912
kind: corollary
name: "Delta-Indexed Towers Are Injective at the First Coordinate"
status: MECHANIZED
conditional_on:
  - "TowerProfile records an outcome coordinate separate from the LicensedLift S(n)->S(n+1) index"
  - "Delta-indexed towers are fixed at base zero"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:delta-indexed-towers", "paper:sn-packets:infinite-delta-tower-family"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Corollary 13.1: Delta-Indexed Towers Form an Infinite Finite-Shadow Family'"
uses: ["ENC-0894"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0912 - Delta-Indexed Towers Are Injective at the First Coordinate

## Statement

For each natural-number delta `d`, define the fixed-base tower `deltaTower(d)`
with coordinate `coord_d(k) = d * k`. The first coordinate is exactly `d`, so
the map `d |-> coord_d(1)` is injective. Distinct declared deltas therefore
give distinct first tower outcomes, and the Symbol Game `delta = 2` tower is
the member whose first coordinate is `2`.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.delta_tower_first_coordinate`
- `SnSymbolGameAndPackets.delta_tower_first_coordinate_injective`
- `SnSymbolGameAndPackets.distinct_delta_towers_have_distinct_first_coordinates`
- `SnSymbolGameAndPackets.delta_tower_is_delta_two_iff_first_coordinate_two`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry formalizes the finite contract-system reading of "infinitely many
  towers": natural-number deltas inject into first tower coordinates.
- It does not assert that RH or the analytic Riemann zeta function generates
  those towers. That remains the continuum-source bridge conjecture tracked by
  [[ENC-0895]] and bounded by [[ENC-0905]].
- A `TowerZetaFamily` is indexed by a `TowerProfile`, so each delta-indexed
  tower may carry its own finite zeta family as typed evidence. The zeta family
  still has no authority without an admitted bridge packet.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the delta-tower/RH-source refinement.

## Changelog

- 2026-06-13: ENC-0912 created with Lean mechanization.
