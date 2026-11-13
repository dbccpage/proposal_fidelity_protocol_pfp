---
id: ENC-0902
kind: theorem
name: "Shadow-Derived Metadata Cannot Repair Collision"
status: MECHANIZED
conditional_on:
  - "A local shadow identifies two worlds"
  - "The target value separates those two worlds"
  - "The added metadata field is computed only from the local shadow"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:shadow-derived-metadata-no-repair", "paper:sn-packets:postprocessed-dashboard-no-repair"]
sources:
  - "engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 21: Shadow-Derived Metadata Cannot Repair the Collision'"
uses: ["ENC-0897", "ENC-0900", "ENC-0901"]
lean_status: MECHANIZED
lean_refs:
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
  - "engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_factorization.lean"
  - "PaperER007.shadow_derived_augmentation_cannot_repair_collision"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0902 - Shadow-Derived Metadata Cannot Repair Collision

## Statement

If an added metadata field is computed solely from the local shadow, then it
cannot repair a target collision already present in that shadow. Equivalently,
any successful augmentation that repairs a shadow collision cannot be wholly
derived from the original shadow.

## Proof Pointer

Mechanized in `engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.shadow_derived_augmentation_cannot_repair_collision`
- `SnSymbolGameAndPackets.successful_augmentation_not_shadow_derived_on_collision`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry strengthens [[ENC-0901]]. A useful extra field must separate the
  target-distinct worlds, and it cannot do so if it is merely deterministic
  post-processing of the collapsed local dashboard.
- This is a packet-design warning for LGGR systems: verifier labels, scores, or
  summaries derived only from local green status cannot restore global-red
  information.

- PaperER007 reconciliation (2026-07-19): The PaperER007 theorem is an imported wrapper for metadata derived only from the collapsed shadow. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as the derived-metadata no-repair criterion.

## Changelog

- 2026-06-13: ENC-0902 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
