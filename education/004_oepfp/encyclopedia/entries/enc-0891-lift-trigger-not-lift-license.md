---
id: ENC-0891
kind: theorem
name: "Lift Trigger Is Not Lift License"
status: MECHANIZED
conditional_on:
  - "LiftTrigger records missing-structure and residual signals separately from LicensedLift"
  - "LicensedLift still requires next-level indexing, budget drop, and declared structure growth"
layer: symbol-game
tower_level: null
primitive: repair
aliases: ["paper:sn-packets:lift-trigger-not-license"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §9 'Theorem 10: Lift Trigger Is Not Lift License'"
  - ".planning/omega_symbol_game_slevel_product_plan.md §S(n) / MSS-N"
uses: ["ENC-0104", "ENC-0887"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_trigger_not_license.lean"
  - "PaperER007.zero_budget_blocks_every_licensed_lift"
  - "PaperER007.concrete_zero_budget_trigger_is_populated"
  - "PaperER007.concrete_zero_budget_trigger_has_no_licensed_target"
  - "PaperER007.exists_populated_zero_budget_trigger_without_license"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0891 - Lift Trigger Is Not Lift License

## Statement

A trigger that records missing structure or a nonzero residual is not itself a
licensed lift. A same-level target cannot be a licensed lift, and a target with
no budget drop cannot be a licensed lift.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_runtime_limits.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.same_level_target_not_licensed_lift`
- `SnSymbolGameAndPackets.trigger_alone_does_not_license_same_level_lift`
- `SnSymbolGameAndPackets.no_budget_drop_blocks_licensed_lift`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- This entry sharpens [[ENC-0104]] and [[ENC-0887]] for product use: detecting
  an obstruction may justify seeking a lift, but does not itself supply the
  lift license.

- PaperER007 reconciliation (2026-07-19): PaperER007 supplies a genuine finite non-implication witness: a populated trigger on a zero-budget source has no licensed target. This is not a universal authority or GTOC licensing theorem. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization continuation
  pass.

## Changelog

- 2026-06-13: ENC-0891 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
