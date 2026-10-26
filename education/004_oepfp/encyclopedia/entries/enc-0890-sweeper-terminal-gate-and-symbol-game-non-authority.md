---
id: ENC-0890
kind: theorem
name: "Sweeper Terminal Gate and Symbol Game Non-Authority"
status: MECHANIZED
conditional_on:
  - "The finite gate model records strict validation, survivor verdict, witness presence, and author-blind host gate as Booleans"
  - "The Symbol Game operation signature omits Authority as an output color"
layer: symbol-game
tower_level: null
primitive: null
aliases: ["paper:sn-packets:sweeper-gate", "paper:sn-packets:no-authority-output"]
sources:
  - "omega_engine/research/published/008_engine_runtime/007_the_symbol_game/007_the_symbol_game_monograph.md"
  - "s_n_packets_and_the_symbol_game.md §6-§7"
  - "crates/omega_sweep_kernel/src/terminalize.rs"
  - "crates/omega_symbol_game/src/refusal.rs"
uses: ["ENC-0805", "ENC-0813", "ENC-0845"]
lean_status: MECHANIZED
lean_refs:
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_sweeper.lean"
  - "omega_engine/lean4/research_programs/008_engine_runtime/007_er007_operation_tree_fold.lean"
  - "PaperER007.recursive_fold_retains_child_outputs"
  - "PaperER007.recursive_fold_composes_child_effect"
  - "PaperER007.admitted_operation_effect_none"
  - "PaperER007.internal_operation_tree_effect_closure"
  - "PaperER007.internal_operation_tree_outputs_not_authority"
extracted: 2026-06-13
migration: VERIFIED
---

# ENC-0890 - Sweeper Terminal Gate and Symbol Game Non-Authority

## Statement

In the finite host-gate model, a certificate terminal requires all gate fields:
strict validation, survivor verdict, witness presence, and author-blind host
separation. Without witness content or without the author-blind gate, the
terminalizer cannot return certificate status.

Separately, the Symbol Game operation signature has no Authority output color.
No primitive operation, and no operation tree rooted in a Symbol Game operation,
outputs authority.

## Proof Pointer

Mechanized in `omega_engine/lean4/research_programs/008_engine_runtime/007_er007_sweeper.lean`.

The Lean theorem names are:

- `SnSymbolGameAndPackets.certificate_requires_all_gates`
- `SnSymbolGameAndPackets.no_certificate_without_witness`
- `SnSymbolGameAndPackets.no_certificate_without_author_blind_gate`
- `SnSymbolGameAndPackets.append_survived_monotone`
- `SnSymbolGameAndPackets.append_killed_monotone`
- `SnSymbolGameAndPackets.append_obligation_monotone`
- `SnSymbolGameAndPackets.operation_output_not_authority`
- `SnSymbolGameAndPackets.operation_tree_output_not_authority`
- `SnSymbolGameAndPackets.formal_replay_remains_non_authority`

`lake build SnSymbolGameAndPackets` succeeds. The gate proofs are finite Boolean
case analyses; the formal replay theorem imports the existing OmegaCore
non-promotion kernel.

## Notes

- The mechanized gate is a finite model of the runtime condition in
  `omega_sweep_kernel/src/terminalize.rs`; it is not a full formalization of
  the YAML validator.
- The operation-color theorem captures the product-level authority firewall:
  the Symbol Game may emit terminal/evidence material, but authority remains
  outside its operation signature.

- PaperER007 reconciliation (2026-07-19): PaperER007 adds genuine recursive child folding, but the primitive operation-effect table is admitted as none by definition. The result is internal closure under that declared table, not a derived universal authority firewall. AuthorityEffect remains None.

## Provenance

- Added 2026-06-13 during the S(n) / Symbol Game / packetization pass.

## Changelog

- 2026-06-13: ENC-0890 created with Lean mechanization.
- 2026-07-19: Reconciled the exact PaperER007 theorem binding and preserved the stated scope and AuthorityEffect None boundary.
