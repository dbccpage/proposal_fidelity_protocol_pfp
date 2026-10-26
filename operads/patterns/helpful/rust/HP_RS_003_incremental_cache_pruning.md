---
pattern_id: HP_RS_003
name: incremental_cache_pruning
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_RS_003_incremental_cache_disk_exhaustion
language: rust
authority_effect: None
---

# Healthy Pattern: Incremental Build Cache Pruning (`HP_RS_003`)

## Description

Selectively prune `omega_engine/crates_rs/target/debug/incremental/` when disk capacity is low or upon encountering `os error 112`, preserving compiled third-party dependencies in `target/debug/deps/`.

## Remediation & Implementation

```powershell
# PowerShell on Windows
Remove-Item -Recurse -Force "omega_engine\crates_rs\target\debug\incremental"
```

```bash
# Bash on Linux/macOS
rm -rf omega_engine/crates_rs/target/debug/incremental
```

## Operadic Property

Eliminates the `AP_RS_003` disk-exhaustion witness instantly reclaiming 15–20+ GB while maintaining pre-compiled crate dependencies:
$$\|A_{\text{RS-003}}(H_{\text{RS-003}}(c))\| = 0$$
