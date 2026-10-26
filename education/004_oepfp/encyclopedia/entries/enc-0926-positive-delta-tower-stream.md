---
id: ENC-0926
kind: corollary
name: "Positive Delta Towers Form an Indexed Zeta-Carrying Stream"
status: MECHANIZED
conditional_on:
  - "TowerProfile records an outcome coordinate separate from the LicensedLift S(n)->S(n+1) index"
  - "positiveDeltaTower(i) is defined as deltaTower(i+1)"
  - "TowerZetaFamily is finite evidence indexed by a declared TowerProfile"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:positive-delta-tower-stream", "paper:sn-packets:infinite-zeta-carrying-tower-family"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Corollary 13.2.1: Positive Delta Towers Form an Indexed Zeta-Carrying Stream'"
uses: ["ENC-0894", "ENC-0912", "ENC-0921"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0926 - Positive Delta Towers Form an Indexed Zeta-Carrying Stream

## Statement

Define the positive-delta tower stream by

```text
positiveDeltaTower(i) = deltaTower(i + 1).
```

Every member has positive step and obeys

```text
coord_i(k+1) = coord_i(k) + (i + 1).
```

Every member also admits an evidence-only finite zeta family. The
first-coordinate map `i |-> coord_i(1)` is injective, so different stream
indices give different declared tower outcomes. The Symbol Game tower is the
index `1` member of this stream: it is exactly the member whose first
coordinate is `2`.

This is the finite contract-system content of an indexed infinity of
`S(n)`-tower profiles, each carrying its own tower-local zeta evidence. It
does not assert that the analytic Riemann zeta function or RH is the source of
the stream.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.positive_delta_tower_first_coordinate`
- `SnSymbolGameAndPackets.positive_delta_tower_has_positive_step`
- `SnSymbolGameAndPackets.positive_delta_tower_step_law`
- `SnSymbolGameAndPackets.positive_delta_tower_family_injective_first_coordinate`
- `SnSymbolGameAndPackets.distinct_positive_delta_towers_have_distinct_first_coordinates`
- `SnSymbolGameAndPackets.positive_delta_tower_index_one_is_delta_two`
- `SnSymbolGameAndPackets.positive_delta_tower_symbol_game_index_iff_first_coordinate_two`
- `SnSymbolGameAndPackets.every_positive_delta_tower_has_evidence_only_zeta_family`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry refines [[ENC-0921]] from "each declared delta may carry zeta
  evidence" to an explicit positive-delta stream indexed by natural numbers.
- The RH-source reading remains a bridge conjecture bounded by [[ENC-0895]],
  [[ENC-0905]], [[ENC-0922]], [[ENC-0923]], and [[ENC-0924]].
- The `delta = 2` tower is not privileged by zeta attachment alone. It is
  privileged only after the finite tower law identifies it as the member whose
  first coordinate is `2`.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the tower-family/RH-continuum-source refinement.

## Changelog

- 2026-06-13: ENC-0926 created with Lean mechanization.
