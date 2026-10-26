---
id: ENC-0923
kind: theorem
name: "Source-to-Delta Collisions Block Source-Level Decoding"
status: MECHANIZED
conditional_on:
  - "A source bridge exposes the finite delta shadow through deltaOf"
  - "The source-level target distinguishes two source points with the same declared delta"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:source-delta-collision", "paper:sn-packets:delta-shadow-cannot-decode-source-target"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.4: Source-to-Delta Collisions Block Source-Level Decoding'"
uses: ["ENC-0897", "ENC-0906", "ENC-0922"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0923 - Source-to-Delta Collisions Block Source-Level Decoding

## Statement

The bridge projection `deltaOf` is itself a finite shadow. If two source points
have the same declared delta, then their induced tower first coordinates are
the same. Therefore any source-level target that separates those two source
points cannot be decoded from the delta shadow alone.

Equivalently, if

```text
deltaOf(sourceA) = deltaOf(sourceB)
target(sourceA) != target(sourceB),
```

then there is no total decoder

```text
decode : natural_delta -> target_value
```

such that `decode(deltaOf(source)) = target(source)` for every source point.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.tower_family_bridge_same_delta_has_same_first_coordinate`
- `SnSymbolGameAndPackets.tower_family_bridge_delta_shadow_collision_blocks_target_decode`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This is the EPK/LGGR shadow-collision warning applied to the continuum-source
  bridge shape from [[ENC-0922]].
- A declared delta projection is enough to select the induced tower carrier. It
  is not enough to recover arbitrary source-level structure.
- If an RH-source bridge needs source details beyond the tower delta, those
  details must be exposed through additional certified bridge fields rather
  than inferred from the delta tower.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, as the next source-bridge EPK generalization after [[ENC-0922]].

## Changelog

- 2026-06-13: ENC-0923 created with Lean mechanization.
