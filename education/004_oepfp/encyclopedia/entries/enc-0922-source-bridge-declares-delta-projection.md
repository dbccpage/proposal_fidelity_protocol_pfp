---
id: ENC-0922
kind: theorem
name: "A Source Bridge Must Declare Its Delta Projection"
status: MECHANIZED
conditional_on:
  - "A candidate source bridge is represented by an explicit source-to-delta projection"
  - "Tower-local zeta data are finite evidence indexed by the induced delta tower"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:source-bridge-delta-projection", "paper:sn-packets:rh-source-bridge-deltaof"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.3: A Source Bridge Must Declare Its Delta Projection'"
uses: ["ENC-0895", "ENC-0905", "ENC-0912", "ENC-0921"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0922 - A Source Bridge Must Declare Its Delta Projection

## Statement

A candidate continuum source, including an RH-based source hypothesis, enters
the finite tower system only through explicit bridge data. The mechanized
bridge skeleton takes a source type and requires two finite projections:

```text
deltaOf : source -> natural_delta
zetaAt  : source -> level -> finite_input -> integer_value.
```

The induced tower for a source point is `deltaTower(deltaOf(source))`, and its
first coordinate is exactly `deltaOf(source)`. The induced zeta family remains
evidence-only. If two source points have different declared deltas, their first
tower coordinates are different; if their first tower coordinates are equal,
their declared deltas are equal. The `delta = 2` Symbol Game case is recognized
exactly by first coordinate `2`.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.tower_family_bridge_first_coordinate`
- `SnSymbolGameAndPackets.tower_family_bridge_zeta_no_authority`
- `SnSymbolGameAndPackets.tower_family_bridge_distinct_deltas_have_distinct_first_coordinates`
- `SnSymbolGameAndPackets.tower_family_bridge_same_first_coordinate_forces_same_delta`
- `SnSymbolGameAndPackets.tower_family_bridge_delta_two_iff_first_coordinate_two`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry is the finite interface for the RH-source proposal. It does not
  construct the continuum object, prove RH, or prove that RH generates the tower
  family.
- The entry sharpens [[ENC-0895]] and [[ENC-0905]]: naming RH is not a delta
  projection. A bridge must provide the replayable `deltaOf` map and finite
  zeta-data projection before the contract system can identify a tower carrier.
- The result reuses [[ENC-0921]] because source-derived zeta data still attach
  as evidence-only data on an explicitly declared delta tower.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the RH-as-continuum-source tower conjecture.

## Changelog

- 2026-06-13: ENC-0922 created with Lean mechanization.
