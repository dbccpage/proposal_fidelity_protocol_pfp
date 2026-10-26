---
id: ENC-0892
kind: theorem
name: "Public Prompt Memory Requires Redaction"
status: MECHANIZED
conditional_on:
  - "Public prompt memory events expose raw-prompt, hash, family-id, and bounded-metadata flags"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:public-prompt-memory-redaction"]
sources:
  - "s_n_packets_and_the_symbol_game.md §9 'Theorem 11: Public Prompt Memory Requires Redaction'"
  - ".planning/2026-06-12-omega-engine-immune-review.md §24 'Privacy and Abuse Model'"
uses: ["ENC-0888"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0892 - Public Prompt Memory Requires Redaction

## Statement

In the finite public-memory model, a public prompt memory event is safe only
when raw prompt text is absent and the prompt hash, family id, and bounded
metadata fields are present. Redaction produces a public-safe memory event.
Raw prompt presence or a missing hash blocks public-safe status.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.redacted_prompt_memory_is_public_safe`
- `SnSymbolGameAndPackets.raw_prompt_blocks_public_memory`
- `SnSymbolGameAndPackets.missing_hash_blocks_public_memory`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This is a memory-shape theorem, not a storage-layer implementation proof.
- It records the public-ledger side of prompt memory; private product stores
  still need their own consent, retention, and access-control policy.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass.

## Changelog

- 2026-06-13: ENC-0892 created with Lean mechanization.

