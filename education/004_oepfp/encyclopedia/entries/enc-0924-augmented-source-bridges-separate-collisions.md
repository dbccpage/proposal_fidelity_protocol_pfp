---
id: ENC-0924
kind: theorem
name: "Augmented Source Bridges Must Separate Remaining Collisions"
status: MECHANIZED
conditional_on:
  - "A source bridge exposes the finite delta shadow through deltaOf"
  - "The bridge is augmented by an additional finite source field"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:augmented-source-bridge-separation", "paper:sn-packets:source-bridge-extra-field-collision"]
sources:
  - "s_n_packets_and_the_symbol_game.md §10 'Theorem 13.5: Augmented Source Bridges Must Separate Remaining Collisions'"
uses: ["ENC-0910", "ENC-0922", "ENC-0923"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0924 - Augmented Source Bridges Must Separate Remaining Collisions

## Statement

Suppose a source bridge augments the delta shadow with an additional finite
field

```text
extra : source -> extra_value.
```

Any decoder from the augmented pair `(deltaOf(source), extra(source))` to a
source-level target is invariant on fibers of that pair. Therefore, if two
source points have the same declared delta and the same extra value but
different target values, no total decoder from `(delta, extra)` can recover the
target for all source points.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_tower_zeta.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.tower_family_bridge_augmented_decode_implies_pair_invariant`
- `SnSymbolGameAndPackets.tower_family_bridge_augmented_collision_blocks_target_decode`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorem names as
axiom-free.

## Notes

- This is the bridge-level repair rule for [[ENC-0923]]: adding a field repairs
  a delta collision only when the added field separates the relevant
  target-distinct source points.
- The result is the source-bridge analogue of [[ENC-0910]], with
  `(deltaOf, extra)` replacing the generic augmented packet.
- For the RH-source hypothesis, this keeps the bridge finite and auditable:
  every added finite field must be justified by the target distinction it is
  meant to preserve.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass, as the augmented-field EPK generalization for source bridges.

## Changelog

- 2026-06-13: ENC-0924 created with Lean mechanization.
