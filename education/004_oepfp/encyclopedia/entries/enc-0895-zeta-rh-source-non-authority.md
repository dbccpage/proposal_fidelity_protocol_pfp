---
id: ENC-0895
kind: theorem
name: "Zeta and RH-Source Data Are Non-Authority Without a Bridge"
status: MECHANIZED
conditional_on:
  - "Tower zeta data are represented as finite tower-local evidence"
  - "A continuum-source claim is admissible only with a finite bridge packet and terminalized certified theorem"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:zeta-rh-source-non-authority", "paper:sn-packets:rh-continuum-source-bridge"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 14: Zeta and RH-Source Data Are Not Authority Without a Bridge'"
  - "encyclopedia/entries/gtla/enc-0643-gtla-app25-rh-gtfda-gtfoc-application.md"
uses: ["ENC-0643", "ENC-0890", "ENC-0894"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0895 - Zeta and RH-Source Data Are Non-Authority Without a Bridge

## Statement

A tower-local zeta family can be carried as finite evidence, but the evidence
has authority effect `none`. A claim naming the Riemann Hypothesis as a
continuum source is not admissible by itself. Admissibility requires both a
finite bridge packet and a terminalized certified theorem.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.evidence_only_zeta_family_no_authority`
- `SnSymbolGameAndPackets.rh_source_claim_alone_not_admissible`
- `SnSymbolGameAndPackets.continuum_source_admissible_requires_bridge_packet`
- `SnSymbolGameAndPackets.continuum_source_admissible_requires_certified_terminal`

`lake build SnSymbolGameAndPackets` succeeds and reports these bridge-discipline
theorems as axiom-free.

## Notes

- The associated research conjecture is that a continuum zeta/RH object may
  source a family of finite `S(n)` tower profiles, with the Symbol Game tower as
  one `delta = 2` shadow. That conjecture is not a theorem and is not a proof of
  RH.
- This entry agrees with [[ENC-0643]]: RH counts as solved inside the tower only
  as a finite replayable proof packet terminalized as `CertifiedTheorem`.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, in response to the tower/zeta/RH-source conjecture.

## Changelog

- 2026-06-13: ENC-0895 created with Lean mechanization.

