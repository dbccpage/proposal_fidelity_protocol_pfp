---
pattern_id: HP_LN_002
name: scoped_target_cache_build
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_LN_002_unconstrained_lake_mathlib_rebuild
language: lean4
authority_effect: None
---

# Healthy Pattern: Scoped Target Cache Build (`HP_LN_002`)

## Description

Fetch precompiled Mathlib build cache using `lake exe cache get` prior to compiling local proof targets, and scope Lake builds strictly to the active theorem target rather than building the entire estate.

## Remediation & Implementation

```powershell
# 1. Fetch precompiled cloud olean cache (completes in ~30s instead of 2 hours)
lake exe cache get

# 2. Build strictly the target module
lake build MyProject.SpecificTheorem
```

## Operadic Property

Eliminates the `AP_LN_002` build-stall witness:
$$\|A_{\text{LN-002}}(H_{\text{LN-002}}(c))\| = 0$$
