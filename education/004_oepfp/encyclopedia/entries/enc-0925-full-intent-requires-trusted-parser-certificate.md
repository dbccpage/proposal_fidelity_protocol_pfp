---
id: ENC-0925
kind: theorem
name: "Full Intent Requires a Trusted Parser Certificate"
status: MECHANIZED
conditional_on:
  - "Typed fidelity is modeled as a finite accepted/refused gate"
  - "A trusted parser certificate records both a normalizer identifier and evidence digest"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:full-intent-trusted-parser", "paper:sn-packets:trusted-parser-oracle-gate"]
sources:
  - "s_n_packets_and_the_symbol_game.md §3 'Theorem 3.1: Full Intent Requires a Trusted Parser Certificate'"
  - "crates/omega_representation/src/fidelity.rs"
uses: ["ENC-0112", "ENC-0888"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0925 - Full Intent Requires a Trusted Parser Certificate

## Statement

The raw-to-typed bridge has a separate admission gate. A trusted parser
certificate is valid only when both its normalizer identifier and evidence
digest are present. Missing either field blocks the trusted-parser certificate.

Full-intent admission has three finite outcomes:

- accepted typed fidelity plus a trusted parser certificate admits full intent;
- accepted typed fidelity without a trusted parser certificate routes to
  `OracleNeeded`;
- refused typed fidelity blocks full intent.

Consequently, if full intent is admitted, both typed fidelity and the trusted
parser certificate were present. Typed-pair fidelity alone is not full
natural-language intent.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.trusted_parser_certificate_requires_normalizer_id`
- `SnSymbolGameAndPackets.trusted_parser_certificate_requires_evidence_digest`
- `SnSymbolGameAndPackets.missing_normalizer_id_blocks_trusted_parser_certificate`
- `SnSymbolGameAndPackets.missing_evidence_digest_blocks_trusted_parser_certificate`
- `SnSymbolGameAndPackets.accepted_fidelity_and_trusted_parser_certifies_full_intent`
- `SnSymbolGameAndPackets.accepted_fidelity_without_trusted_parser_routes_oracle`
- `SnSymbolGameAndPackets.refused_fidelity_blocks_full_intent`
- `SnSymbolGameAndPackets.full_intent_certification_requires_trusted_parser`
- `SnSymbolGameAndPackets.full_intent_certification_requires_typed_fidelity`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry mechanizes the paper's trusted-parser/oracle discipline in the
  same shape as the Rust `TrustedParserCertificate` and `FullIntentCertificate`
  gate in `omega_representation`.
- It refines [[ENC-0888]]: packetization and typed fidelity are evidence, not
  unrestricted intent authority.
- The theorem locates the parser trust base. It does not implement the
  per-family trusted parser registry or evidence-digest audit.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, to discharge the finite theorem part of the trusted parser/oracle
  discipline obligation.

## Changelog

- 2026-06-13: ENC-0925 created with Lean mechanization.
