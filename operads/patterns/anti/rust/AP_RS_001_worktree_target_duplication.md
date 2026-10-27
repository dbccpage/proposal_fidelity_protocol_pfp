---
pattern_id: AP_RS_001
name: worktree_target_duplication
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_RS_001_shared_cargo_target_cache
language: rust
authority_effect: None
---

# Anti-Pattern: Git Worktree Target Duplication (`AP_RS_001`)

## Description

Executing `cargo build` or `cargo test` inside an isolated git worktree without pointing `CARGO_TARGET_DIR` to the primary workspace target cache.

## Detection Signature

- Process/Environment:
  Invoking cargo commands in `.worktrees/<name>/engine/crates_rs` with unset `CARGO_TARGET_DIR`.
- Filesystem:
  Presence of a redundant local `target/` directory inside a worktree path.

## Hazard & Failure Mode

- Forces full rebuild of 59-crate workspace dependencies.
- Consumes ~30 GB of redundant disk space.
- Triggers MSVC linker failures (`LNK1140`, `LNK1201`) due to disk exhaustion.
- Fails `RULE_CARGO_WORKSPACE_ROOT_001`.

## Dual Healthy Pattern

See [HP_RS_001_shared_cargo_target_cache](../../helpful/rust/HP_RS_001_shared_cargo_target_cache.md).
