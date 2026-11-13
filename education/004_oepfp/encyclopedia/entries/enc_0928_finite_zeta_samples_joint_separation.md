---
id: ENC-0928
kind: theorem
name: "Finite Zeta Samples Repair Only by Joint Separation"
status: MECHANIZED
conditional_on:
  - "The bridge source is represented by a positive-delta stream index"
  - "A finite zeta sample is explicitly projected into the bridge packet"
  - "Source-level targets are decoded from finite bridge packets only"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:finite-zeta-sample-bridge", "paper:sn-packets:zeta-sample-joint-separation"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.2.3: Finite Zeta Samples Repair Only by Joint Separation'"
uses: ["ENC-0889", "ENC-0926", "ENC-0927"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0928 - Finite Zeta Samples Repair Only by Joint Separation

## Statement

A positive-stream zeta bridge may expose an additional finite sample field:

```text
sampleOf : source -> zeta_sample.
```

The resulting finite bridge packet is `(indexOf(source), sampleOf(source))`.
The induced tower is still `positiveDeltaTower(indexOf(source))`, and the
tower-local zeta family remains evidence-only.

Any decoder from this finite zeta packet is invariant on fibers of the pair.
Therefore, if two source points have the same `indexOf` value and the same
finite zeta sample but different source-level targets, no decoder from
`(index, sample)` can recover those targets for all source points.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_first_coordinate`
- `SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_zeta_no_authority`
- `SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_packet_eq`
- `SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_decode_implies_packet_invariant`
- `SnSymbolGameAndPackets.positive_tower_finite_zeta_bridge_collision_blocks_target_decode`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This entry is the zeta-sample instance of the EPK/LGGR joint-separation
  rule: adding a field repairs a collapsed view only when the combined packet
  separates the target fibers.
- It refines [[ENC-0927]] by distinguishing tower-local `zetaAt` evidence from
  the finite `sampleOf` field a decoder may actually inspect.
- It does not choose the production sample type or prove the runtime checker.
  Those remain implementation obligations for product tower semantics.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, to mechanize the finite zeta-sample compatibility boundary.

## Changelog

- 2026-06-13: ENC-0928 created with Lean mechanization.
