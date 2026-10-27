---
id: ENC-0888
kind: theorem
name: "Packetization Is Evidence-Only and Forgets Unencoded Semantic Truth"
status: MECHANIZED
conditional_on:
  - "PacketizationContract exposes a compile function whose soundness obligation includes typed field fidelity and AuthorityEffect.none"
  - "The forgetfulness witness uses a finite two-world model with identical packet shape and different semantic truth"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:packetization-forgetfulness", "paper:sn-packets:evidence-only-packetization"]
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §3 'Packetization'"
  - "crates/core_representation/src/packet.rs"
  - "crates/core_representation/src/fidelity.rs"
uses: ["ENC-0087", "ENC-0112"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean"
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_typed_packet_shadow.lean"
  - "PaperER007.no_typed_packet_decoder_of_collision"
  - "PaperER007.finite_typed_packet_projection_collides"
  - "PaperER007.finite_typed_packet_targets_differ"
  - "PaperER007.finite_typed_packet_collision_blocks_total_decoder"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0888 - Packetization Is Evidence-Only and Forgets Unencoded Semantic Truth

## Statement

If a packetization contract compiles a seed to a packet, then the packet
preserves the declared fidelity fields and has no authority effect.

Separately, packet shape alone cannot reconstruct unencoded semantic truth in
general: there is a finite two-world witness where the same packet shape
corresponds to opposite semantic truth values.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.packetization_contract_preserves_fidelity`
- `SnSymbolGameAndPackets.packetization_contract_no_authority`
- `SnSymbolGameAndPackets.packet_shape_forgets_semantic_truth`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry separates typed-pair packet fidelity from unrestricted
  natural-language intent fidelity.
- It is compatible with `core_representation`: `TypedCorePacket` is sealed
  proposal evidence, and `FullIntentCertificate` requires the additional
  trusted-parser/oracle bridge.

- PaperER007 reconciliation (2026-07-19): PaperER007 replaces the earlier Unit-shaped illustration at this scope with one actual TypedPacket projection and a generic collision lemma. The result remains a finite countermodel, not a theorem that all packets forget semantic truth. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization pass.

## Changelog

- 2026-06-13: ENC-0888 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
