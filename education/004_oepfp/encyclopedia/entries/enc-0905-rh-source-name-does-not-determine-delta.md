---
id: ENC-0905
kind: theorem
name: "RH Source Name Does Not Determine Delta"
status: MECHANIZED
conditional_on:
  - "The continuum source name is represented as a finite shadow"
  - "The tower delta-two status is represented as a separate target"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:rh-source-name-not-delta", "paper:sn-packets:rh-name-does-not-determine-tower-delta"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Corollary 15.1: Naming RH Does Not Determine the Tower Delta'"
uses: ["ENC-0894", "ENC-0895", "ENC-0896"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0905 - RH Source Name Does Not Determine Delta

## Statement

Naming RH as a continuum source does not by itself determine whether a tower is
the Symbol Game `delta = 2` tower. There is a two-world witness in which both
worlds have the same RH-source-name shadow, while one world has `delta = 2`
status and the other does not.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.rh_source_name_forgets_delta_two_status`
- `SnSymbolGameAndPackets.rh_source_name_forgetfulness_is_shadow_collision`

`lake build SnSymbolGameAndPackets` succeeds and reports both theorems as
axiom-free.

## Notes

- This entry sharpens [[ENC-0895]] and [[ENC-0896]]. The RH-source proposal is
  admissible as a research conjecture, but the source name is not a bridge law
  from continuum data to the finite tower delta.
- The second Lean theorem routes the result through the generic shadow-collision
  obstruction of [[ENC-0897]].
- To make RH a contract-system source for the `S(n)` tower, one still needs a
  declared continuum carrier, finite-shadow functor, zeta-data compatibility
  law, and terminalized certified theorem.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in direct response to the RH-as-continuum-source tower conjecture.

## Changelog

- 2026-06-13: ENC-0905 created with Lean mechanization.
