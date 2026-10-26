---
id: ENC-0929
kind: theorem
name: "Routed Seed Schema Readiness Is Closed and Field-Complete"
status: MECHANIZED
conditional_on:
  - "RoutedSeed is treated as the current product-level prompt packet anchor"
  - "Schema readiness means all declared fields are present and no unknown fields are present"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:routed-seed-schema-readiness", "paper:sn-packets:closed-routed-seed-schema"]
sources:
  - "s_n_packets_and_the_symbol_game.md §3 'Theorem 3.2: Routed Seed Schema Readiness Is Closed and Field-Complete'"
  - "crates/omega_representation/src/types.rs"
  - "crates/omega_representation/src/packet.rs"
uses: ["ENC-0112", "ENC-0888", "ENC-0925"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0929 - Routed Seed Schema Readiness Is Closed and Field-Complete

## Statement

A product prompt packet is ready as a `RoutedSeed` only when all nine declared
schema fields are present:

```text
family
instance
carrier
constraints
protected_boundaries
terminal_target
evidence_ceiling
oracle_policy
allowed_transforms
```

and the unknown-field count is zero. Readiness therefore implies that every
named field is present and no shadow field remains. If any named field is
missing, or if any unknown field is present, schema readiness is blocked.

This is a closed finite schema gate. It does not certify unrestricted natural
language intent, and it does not create authority.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.routed_seed_schema_ready_requires_field`
- `SnSymbolGameAndPackets.routed_seed_schema_ready_has_no_unknown_fields`
- `SnSymbolGameAndPackets.routed_seed_schema_missing_field_blocks_ready`
- `SnSymbolGameAndPackets.routed_seed_schema_unknown_fields_block_ready`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- The theorem mirrors the Rust `RoutedSeed` schema in
  `crates/omega_representation/src/types.rs` and its
  `serde(deny_unknown_fields)` discipline.
- It refines [[ENC-0888]] by separating packet-shape evidence from closed
  schema readiness.
- It is compatible with [[ENC-0925]]: even a closed typed packet still needs a
  trusted parser certificate before full natural-language intent can be
  admitted.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, to discharge the finite `RoutedSeed` part of the general prompt packet
  schema obligation.

## Changelog

- 2026-06-13: ENC-0929 created with Lean mechanization.
