---
pattern_id: HP_RS_001
name: shared_cargo_target_cache
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_RS_001_worktree_target_duplication
language: rust
authority_effect: None
---

# Healthy Pattern: Shared Cargo Target Cache (`HP_RS_001`)

## Description

Explicitly bind `$env:CARGO_TARGET_DIR` (or `--target-dir`) to the primary repository's pre-compiled target cache (`<repo_root>/omega_engine/crates_rs/target`) when operating within worktrees.

## Remediation & Implementation

```powershell
# PowerShell on Windows
$env:CARGO_TARGET_DIR = "c:\Users\a343o\source\repos\the_symbol_game\omega_engine\crates_rs\target"
cargo test -p <target_crate> -j 1
```

```bash
# Bash on Linux/macOS
export CARGO_TARGET_DIR="/path/to/the_symbol_game/omega_engine/crates_rs/target"
cargo test -p <target_crate> -j 1
```

## Operadic Property

Eliminates the `AP_RS_001` disk-exhaustion witness and accelerates worktree compilation to $\approx 2.5\text{s}$:
$$\|A_{\text{RS-001}}(H_{\text{RS-001}}(c))\| = 0$$
