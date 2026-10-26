---
id: ENC-0897
kind: theorem
name: "Shadow Collision Blocks Factorization"
status: MECHANIZED
conditional_on:
  - "A finite shadow map identifies two worlds"
  - "The target value separates those two worlds"
layer: symbol-game
tower_level: null
primitive: difference
aliases: ["paper:sn-packets:shadow-collision-nonfactorization", "paper:sn-packets:generic-lggr-shadow-boundary"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 16: Shadow Collision Blocks Factorization'"
uses: ["ENC-0888", "ENC-0889", "ENC-0896"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_factorization.lean"
  - "PaperER007.shadow_collision_blocks_total_decoder"
  - "PaperER007.shadow_factorization_implies_fiber_invariance"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_typed_packet_shadow.lean"
  - "PaperER007.no_typed_packet_decoder_of_collision"
  - "PaperER007.finite_typed_packet_projection_collides"
  - "PaperER007.finite_typed_packet_targets_differ"
  - "PaperER007.finite_typed_packet_collision_blocks_total_decoder"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0897 - Shadow Collision Blocks Factorization

## Statement

Let `shadow : World -> Shadow` be a finite observation map and
`value : World -> Value` be the target to recover. If two worlds `a` and `b`
have the same shadow but different target values, then no decoder
`F : Shadow -> Value` can satisfy `F (shadow world) = value world` for every
world.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.no_factor_through_shadow_of_collision`
- `SnSymbolGameAndPackets.packet_shape_forgetfulness_is_shadow_collision`
- `SnSymbolGameAndPackets.local_pass_shadow_forgets_global_green`
- `SnSymbolGameAndPackets.finite_zeta_source_forgetfulness_is_shadow_collision`
- `SnSymbolGameAndPackets.finite_zeta_delta_forgetfulness_is_shadow_collision`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry is the generic finite form of the EPK/LGGR warning. A local shadow
  can be useful evidence, but if it collapses target-distinct worlds, the target
  cannot factor through that shadow.
- The theorem unifies [[ENC-0888]] packet-shape forgetfulness, [[ENC-0889]]
  local-dashboard quotient failure, and [[ENC-0896]] finite zeta-shadow
  forgetfulness.

- PaperER007 reconciliation (2026-07-19): PaperER007 binds this owner both to the imported generic collision facade and to the actual TypedPacket finite countermodel. The latter is existential and finite; it does not say every packet projection loses every target. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass to factor the common finite-shadow obstruction.

## Changelog

- 2026-06-13: ENC-0897 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
