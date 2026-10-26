---
id: ENC-0894
kind: theorem
name: "Positive-Delta Tower Profile"
status: MECHANIZED
conditional_on:
  - "TowerProfile records an outcome coordinate separate from the LicensedLift S(n)->S(n+1) index"
  - "The tower delta is a natural-number step size on the outcome coordinate"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:positive-delta-tower", "paper:sn-packets:delta-two-tower"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Tower Profiles, Zeta Data, and the RH Source Hypothesis'"
uses: ["ENC-0887"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0894 - Positive-Delta Tower Profile

## Statement

A tower profile has a coordinate `coord(k) = base + delta * k`. The coordinate is
not the `LicensedLift` index; a lift still moves from `S(n)` to `S(n+1)`.

For any profile, `coord(k+1) = coord(k) + delta`. The Symbol Game tower may be
represented by the special profile with `delta = 2`. If `delta > 0`, then every
coordinate has a strictly larger successor coordinate, so the finite-indexed
tower has no terminal coordinate.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.tower_step_law`
- `SnSymbolGameAndPackets.delta_two_tower_step`
- `SnSymbolGameAndPackets.positive_delta_step_strict`
- `SnSymbolGameAndPackets.positive_delta_no_terminal_coordinate`
- `SnSymbolGameAndPackets.same_base_first_coordinate_equal_forces_delta_equal`

`lake build SnSymbolGameAndPackets` succeeds.

## Notes

- This entry formalizes the user's "delta 2 every time" tower idea without
  changing the separate `LicensedLift` rule in [[ENC-0887]].
- Other tower families may use different deltas; the theorem only requires a
  declared positive step to obtain the no-terminal-coordinate fact.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the tower/zeta/RH-source conjecture.

## Changelog

- 2026-06-13: ENC-0894 created with Lean mechanization.

