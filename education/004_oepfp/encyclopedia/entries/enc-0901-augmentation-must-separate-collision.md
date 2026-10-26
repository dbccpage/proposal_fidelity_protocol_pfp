---
id: ENC-0901
kind: theorem
name: "Augmentation Must Separate Collision"
status: MECHANIZED
conditional_on:
  - "A local shadow identifies two worlds"
  - "The target value separates those two worlds"
  - "The augmented packet is the pair of the local shadow and an extra field"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:augmentation-must-separate-collision", "paper:sn-packets:metadata-only-not-repair"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 20: Augmentation Must Separate the Collision'"
uses: ["ENC-0897", "ENC-0898", "ENC-0900"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_factorization.lean"
  - "PaperER007.shadow_augmentation_must_separate_collision"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0901 - Augmentation Must Separate Collision

## Statement

If a local shadow identifies two worlds with different target values, then any
successful augmented packet `(shadow, extra)` must separate those two worlds in
the extra coordinate. If both the shadow and extra field agree on a
target-distinct pair, no decoder from the augmented packet can recover the
target for every world.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.augmentation_must_separate_target_collision`
- `SnSymbolGameAndPackets.nonseparating_augmentation_cannot_repair_collision`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry refines [[ENC-0898]]: carrying the target itself repairs the
  collision because it separates the worlds the target separates.
- It also refines [[ENC-0900]]: neither coarser summaries nor irrelevant metadata
  repair a local/global collision. The added field must distinguish the
  target-distinct worlds.

- PaperER007 reconciliation (2026-07-19): The PaperER007 theorem is an imported wrapper: a successful augmentation must separate the specific target-distinct collision. It does not construct a repair. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the finite packet-design criterion for repairing a shadow collision.

## Changelog

- 2026-06-13: ENC-0901 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
