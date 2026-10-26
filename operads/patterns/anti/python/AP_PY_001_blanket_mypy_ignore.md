---
pattern_id: AP_PY_001
name: blanket_mypy_ignore
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_001_scoped_mypy_overrides
language: python
authority_effect: None
---

# Anti-Pattern: Blanket Mypy Import Ignoring (`AP_PY_001`)

## Description

Setting `ignore_missing_imports = true` globally under `[tool.mypy]` in `pyproject.toml` or `mypy.ini` silences type errors across the entire codebase, obscuring missing internal modules, broken relative imports, and type signature regressions.

## Detection Signature

- AST / TOML Pattern:
  `[tool.mypy]` section containing `ignore_missing_imports = true` without scoping.
- Regex: `^\s*ignore_missing_imports\s*=\s*true\b` under un-scoped `[tool.mypy]`.

## Hazard & Failure Mode

- Disables static type checks on internal package modules.
- Hides broken imports and circular dependency regressions.
- Fails Stage $\Omega$ republication check `E06`.

## Dual Healthy Pattern

See [HP_PY_001_scoped_mypy_overrides](../../helpful/python/HP_PY_001_scoped_mypy_overrides.md).
