---
pattern_id: AP_RS_003
name: incremental_cache_disk_exhaustion
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_RS_003_incremental_cache_pruning
language: rust
authority_effect: None
---

# Anti-Pattern: Incremental Build Cache Disk Exhaustion (`AP_RS_003`)

## Description

Unbounded accumulation of rustc incremental compilation cache artifacts in `engine/crates_rs/target/debug/incremental/` during repeated iterative testing, leading to developer workstation disk exhaustion.

## Detection Signature

- Process/Environment:
  Cargo build or test commands halting with:
  `error: failed to write to ...: There is not enough space on the disk. (os error 112)`
- Filesystem:
  `engine/crates_rs/target/debug/incremental/` expanding to 15–30+ GB while host drive capacity drops to zero bytes.

## Hazard & Failure Mode

- Abruptly terminates compilation mid-flight.
- Fails `RULE_CARGO_WORKSPACE_ROOT_001`.
- Can leave partially written `.rmeta` or lock files that block subsequent invocations.
- Misleads engineers into executing destructive full `cargo clean`, wiping pre-compiled dependency artifacts in `target/debug/deps/` and forcing long re-compilation cycles.

## Dual Healthy Pattern

See [HP_RS_003_incremental_cache_pruning](../../helpful/rust/HP_RS_003_incremental_cache_pruning.md).
