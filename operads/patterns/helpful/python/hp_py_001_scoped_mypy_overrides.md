---
pattern_id: HP_PY_001
name: scoped_mypy_overrides
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_001_blanket_mypy_ignore
language: python
authority_effect: None
---

# Healthy Pattern: Scoped Mypy Overrides (`HP_PY_001`)

## Description

Retain strict type checking across all internal modules by scoping `ignore_missing_imports = true` exclusively to un-typed third-party libraries using explicit `[[tool.mypy.overrides]]`.

## Remediation & Implementation

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = [
    "scipy.*",
    "pytest.*",
    "matplotlib.*",
]
ignore_missing_imports = true
```

## Operadic Property

Eliminates the witness emitted by `AP_PY_001` while maintaining full static verification over internal domain logic:
$$\|A_{\text{PY-001}}(H_{\text{PY-001}}(c))\| = 0$$
