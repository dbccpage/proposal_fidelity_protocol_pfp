---
id: ENC-0887
kind: theorem
name: "S(n) Licensed Lift Non-Silence"
status: MECHANIZED
conditional_on:
  - "S(n) is modeled as a finite symbolic context with separate counts for symbols, operators, packet families, witnesses, and lift budget"
  - "LicensedLift records the next-level, budget-drop, and declared-structure-growth obligations"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:licensed-lift", "paper:sn-packets:slevel-lift-boundary"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §2 'Definition of S(n)'"
  - ".planning/omega_symbol_game_slevel_product_plan.md §Key Definitions To Reconcile"
uses: []
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_lift_patch_semantics.lean"
  - "PaperER007.applyLift_advances_level"
  - "PaperER007.applyLift_strictly_decreases_budget"
  - "PaperER007.applyLift_increases_declared_mass"
  - "PaperER007.applyLift_is_licensed"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0887 - S(n) Licensed Lift Non-Silence

## Statement

An `S(n)` level is a finite symbolic context, not a proof status or authority
level. A licensed lift from `source` to `target` must:

- advance the level index by one;
- strictly decrease the remaining lift budget;
- change the declared finite structure.

Thus a silent relabeling is not a licensed lift.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_s_level.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.licensed_lift_forces_next_level`
- `SnSymbolGameAndPackets.licensed_lift_consumes_budget`
- `SnSymbolGameAndPackets.licensed_lift_not_silent_on_declared_structure`

`lake build SnSymbolGameAndPackets` succeeds and reports these theorems as
axiom-free.

## Notes

- The index `n` is kept separate from counts of symbols, operators, packet
  families, and witnesses.
- This entry does not claim that a lift proves the object under study. It only
  records the finite-contract discipline for declaring growth.

- PaperER007 reconciliation (2026-07-19): PaperER007 derives the three count-shadow LicensedLift fields from applicable LiftPatch data rather than projecting them from an already admitted lift. Preservation, obstruction killing, minimality, and full GTOC licensing remain outside scope. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization pass.

## Changelog

- 2026-06-13: ENC-0887 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
