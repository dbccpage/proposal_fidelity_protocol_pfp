---
id: ENC-0927
kind: theorem
name: "Positive-Stream Source Bridges Need an Index Projection"
status: MECHANIZED
conditional_on:
  - "The proposed source is meant to generate the positive-delta stream positiveDeltaTower(i)=deltaTower(i+1)"
  - "The finite bridge exposes indexOf and tower-local zeta data"
  - "Source-level targets are decoded from finite bridge fields only"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:positive-stream-source-bridge", "paper:sn-packets:rh-source-index-projection"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.2.2: Positive-Stream Source Bridges Need an Index Projection'"
uses: ["ENC-0895", "ENC-0905", "ENC-0922", "ENC-0926"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0927 - Positive-Stream Source Bridges Need an Index Projection

## Statement

If a proposed continuum source is meant to generate the positive-delta tower
stream, the finite bridge must expose at least

```text
indexOf : source -> natural_index
zetaAt  : source -> level -> finite_input -> integer_value.
```

The induced tower is `positiveDeltaTower(indexOf(source))`. Its first
coordinate is `indexOf(source) + 1`, and its induced zeta family has authority
effect `none`. Distinct source indices give distinct first tower coordinates;
equal first tower coordinates force equal source indices. The `delta = 2`
Symbol Game tower is exactly the source points whose `indexOf` value is `1`.

If two source points have the same `indexOf` value but different source-level
targets, no decoder from the index alone can recover those targets for all
source points. Such collisions require additional certified bridge fields.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.positive_tower_family_bridge_first_coordinate`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_zeta_no_authority`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_distinct_indices_have_distinct_first_coordinates`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_same_first_coordinate_forces_same_index`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_delta_two_iff_index_one`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_same_index_has_same_first_coordinate`
- `SnSymbolGameAndPackets.positive_tower_family_bridge_index_collision_blocks_target_decode`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry is the positive-stream specialization of [[ENC-0922]].
- It refines [[ENC-0926]] by adding the source-to-index projection needed when
  a continuum source is proposed for the whole stream.
- The RH-source proposal remains non-authority unless it supplies this finite
  bridge data, a zeta compatibility law, collision separation for the intended
  target, and a terminalized certified theorem.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, to bound the "RH as continuum source of the tower stream" hypothesis.

## Changelog

- 2026-06-13: ENC-0927 created with Lean mechanization.
