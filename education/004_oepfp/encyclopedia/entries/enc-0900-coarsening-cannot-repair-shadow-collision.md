---
id: ENC-0900
kind: theorem
name: "Coarsening Cannot Repair Shadow Collision"
status: MECHANIZED
conditional_on:
  - "A fine shadow identifies two worlds"
  - "The target value separates those two worlds"
  - "The coarse shadow is obtained by post-processing the fine shadow"
layer: symbol-game
tower_level: null
primitive: difference
aliases: ["paper:sn-packets:coarsening-cannot-repair-shadow-collision", "paper:sn-packets:lossier-dashboard-no-repair"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §11 'Theorem 19: Coarsening Cannot Repair a Shadow Collision'"
uses: ["ENC-0897", "ENC-0898", "ENC-0899"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_factorization.lean"
  - "PaperER007.shadow_coarsening_cannot_repair_collision"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0900 - Coarsening Cannot Repair Shadow Collision

## Statement

If a fine shadow already identifies two worlds with different target values,
then any post-processing or coarsening of that fine shadow also fails to recover
the target. A lossier dashboard cannot restore information that the fine
dashboard already collapsed.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_shadow_boundary.lean`.

The Lean theorem name is:

- `SnSymbolGameAndPackets.coarsening_cannot_repair_shadow_collision`

`lake build SnSymbolGameAndPackets` succeeds and reports this theorem as
axiom-free.

## Notes

- This entry rules out a common LGGR false repair: summarizing the same local
  dashboard more aggressively cannot recover a global target that was already
  lost.
- The constructive repair remains [[ENC-0898]]: carry the missing target datum
  explicitly, then subject it to the normal packet/bridge/terminalizer
  discipline.

- PaperER007 reconciliation (2026-07-19): The PaperER007 theorem is an imported wrapper at the displayed collision pair. No universal representation-loss claim is added. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass as a corollary of the generic shadow-collision theorem.

## Changelog

- 2026-06-13: ENC-0900 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
