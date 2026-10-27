---
id: ENC-0911
kind: theorem
name: "Injective Target Encodings Cannot Hide LGGR"
status: MECHANIZED
conditional_on:
  - "The encoded target is obtained by post-processing the original target"
  - "Reflection from encoded descent to original descent requires injectivity of the encoding"
  - "Descent is interpreted as fiber invariance or primitive-difference quotient descent"
layer: symbol-game
tower_level: null
primitive: quotient
aliases: ["paper:sn-packets:injective-target-encoding-lggr", "paper:sn-packets:target-relabeling-cannot-repair-shadow"]
sources:
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 29: Injective Target Encodings Cannot Hide LGGR'"
uses: ["ENC-0889", "ENC-0899", "ENC-0909", "ENC-0910"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0911 - Injective Target Encodings Cannot Hide LGGR

## Statement

Post-processing a target preserves descent: if `value` descends through a
shadow, then `encode(value)` also descends through that shadow. If `encode` is
injective, the converse holds: descent of the encoded target implies descent of
the original target.

The same preservation and reflection laws hold for primitive-difference
quotient descent.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.target_encoding_preserves_shadow_invariant`
- `SnSymbolGameAndPackets.injective_target_encoding_reflects_shadow_invariant`
- `SnSymbolGameAndPackets.injective_target_encoding_shadow_invariant_iff`
- `SnSymbolGameAndPackets.target_encoding_preserves_quotient_descent`
- `SnSymbolGameAndPackets.injective_target_encoding_reflects_quotient_descent`
- `SnSymbolGameAndPackets.injective_target_encoding_quotient_descent_iff`

`lake build SnSymbolGameAndPackets` succeeds. Lean reports the fiber-level
theorems and the forward quotient theorem as axiom-free; the quotient reflection
and quotient equivalence use the standard quotient soundness axiom.

## Notes

- This theorem prevents a dashboard-level evasion of LGGR. Encoding a global
  target as a label, hash, color, badge, or UI status cannot make an
  insufficient local shadow sufficient when the encoding is injective.
- A non-injective encoding can hide a failure only by discarding target
  distinctions. That is not a repair of the original target.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the target-representation counterpart to packet-representation
  invariance.

## Changelog

- 2026-06-13: ENC-0911 created with Lean mechanization.
