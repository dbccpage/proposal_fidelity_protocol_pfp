---
id: ENC-0921
kind: theorem
name: "Delta Towers Carry Tower-Local Zeta Families Without Identifying Deltas"
status: MECHANIZED
conditional_on:
  - "TowerProfile records an outcome coordinate separate from the LicensedLift S(n)->S(n+1) index"
  - "TowerZetaFamily is finite evidence indexed by a declared TowerProfile"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:delta-tower-zeta-carriers", "paper:sn-packets:one-zeta-family-per-delta-tower"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.2: Delta Towers Carry Tower-Local Zeta Families Without Identifying Deltas'"
uses: ["ENC-0894", "ENC-0895", "ENC-0912"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0921 - Delta Towers Carry Tower-Local Zeta Families Without Identifying Deltas

## Statement

For every natural-number delta `d`, there exists an evidence-only finite zeta
family indexed by the carrier `deltaTower(d)`. More generally, any finite zeta
table can be attached to `deltaTower(d)` as a `TowerZetaFamily(deltaTower(d))`,
and the resulting zeta family has authority effect `none`.

Attaching zeta data does not identify distinct delta carriers. If `d1 != d2`,
then the first coordinates of `deltaTower(d1)` and `deltaTower(d2)` remain
different even after arbitrary tower-local zeta families are attached. The
`delta = 2` Symbol Game tower is still recognized by first coordinate `2`;
zeta attachment is evidence on that carrier, not a replacement for the carrier
law.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.delta_tower_zeta_family_no_authority`
- `SnSymbolGameAndPackets.every_delta_has_evidence_only_zeta_family`
- `SnSymbolGameAndPackets.delta_tower_zeta_family_carrier_first_coordinate`
- `SnSymbolGameAndPackets.distinct_delta_zeta_family_carriers_have_distinct_first_coordinates`
- `SnSymbolGameAndPackets.delta_tower_zeta_family_delta_two_iff_first_coordinate_two`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry formalizes the finite contract-system content of "there are
  infinitely many towers, each with its own zeta family": natural-number deltas
  index distinct tower carriers, and each carrier may hold finite zeta data.
- It does not assert that the analytic Riemann zeta function, RH, or any
  continuum carrier generates those towers. That remains the bridge conjecture
  bounded by [[ENC-0895]] and [[ENC-0905]].
- The result refines [[ENC-0912]] by showing that zeta attachment is typed over
  the carrier and cannot collapse the delta distinction.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the delta-tower/zeta-family/RH-source refinement.

## Changelog

- 2026-06-13: ENC-0921 created with Lean mechanization.
