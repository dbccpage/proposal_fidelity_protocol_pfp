---
id: ENC-0930
kind: theorem
name: "Public Prompt Memory Append Preserves Raw-Free Ledgers"
status: MECHANIZED
conditional_on:
  - "Public memory events expose only rawPromptPresent, promptHashPresent, familyIdPresent, and boundedMetadata flags"
  - "The public ledger is modeled by event count and raw prompt event count"
  - "Public appends are checked against PublicMemorySafe or redacted before append"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:public-memory-append-raw-free", "paper:sn-packets:redacted-public-memory-ledger"]
sources:
  - "s_n_packets_and_the_symbol_game.md §9 'Theorem 11.1: Public Prompt Memory Append Preserves Raw-Free Ledgers'"
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean"
uses: ["ENC-0892"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0930 - Public Prompt Memory Append Preserves Raw-Free Ledgers

## Statement

A finite public prompt-memory ledger has two counters:

```text
publicEvents
rawPromptEvents
```

Appending any public memory event increments `publicEvents`. If the ledger is
raw-free and the event satisfies `PublicMemorySafe`, then the appended ledger is
still raw-free. Redacting an event before append produces a `PublicMemorySafe`
event, so redaction also preserves the raw-free invariant.

Conversely, if an event with `rawPromptPresent = true` is appended to a raw-free
ledger, then the resulting `rawPromptEvents` count is positive. Such an append
cannot be treated as preserving the public raw-free invariant.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.append_public_memory_event_increments_count`
- `SnSymbolGameAndPackets.append_safe_prompt_memory_preserves_raw_free`
- `SnSymbolGameAndPackets.append_redacted_prompt_memory_preserves_raw_free`
- `SnSymbolGameAndPackets.append_raw_prompt_memory_raw_count_positive`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry strengthens [[ENC-0892]] by moving from event shape to append
  behavior.
- It is a finite contract model, not a proof about a concrete database,
  serializer, queue, or deployment.
- A production public prompt-memory writer must still be wired to enforce the
  redaction or `PublicMemorySafe` gate before append.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, to close the finite prompt-memory append invariant without claiming a
  production storage proof.

## Changelog

- 2026-06-13: ENC-0930 created with Lean mechanization.
