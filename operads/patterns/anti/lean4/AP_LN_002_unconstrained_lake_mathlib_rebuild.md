---
pattern_id: AP_LN_002
name: unconstrained_lake_mathlib_rebuild
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_LN_002_scoped_target_cache_build
language: lean4
authority_effect: None
---

# Anti-Pattern: Unconstrained Lake Mathlib Rebuild (`AP_LN_002`)

## Description

Running `lake build` or `lake update` within isolated worktrees without pointing to the shared pre-built Mathlib lake cache, triggering a 2-hour Mathlib recompilation from source and exhausting CPU/RAM.

## Detection Signature

- Process monitor:
  `lake build` running `lean` processes consuming >90% CPU compiling Mathlib modules from scratch (`Mathlib.Algebra...`).
- Terminal output:
  Lake downloading and compiling thousands of olean files without cache hit.

## Hazard & Failure Mode

- Blocks agent task execution indefinitely (timeouts).
- Duplicates tens of gigabytes of olean build artifacts across worktrees.
- Stalls verification loops in local CI.

## Dual Healthy Pattern

See [HP_LN_002_scoped_target_cache_build](../../helpful/lean4/HP_LN_002_scoped_target_cache_build.md).
