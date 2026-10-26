---
pattern_id: AP_PY_006
name: host_absolute_path_injection
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_006_dynamic_repository_relative_resolution
language: python
authority_effect: None
---

# Anti-Pattern: Host-Absolute Path Injection (`AP_PY_006`)

## Description

Hardcoding host-machine absolute filesystem paths (such as `C:\Users\<user>\...` or `file:///C:/Users/...`) into repository Python scripts, constants, test fixtures, or generated documentation files instead of dynamically deriving paths relative to `Path(__file__)` or repository roots.

## Detection Signature

- AST Pattern: `Constant(value)` containing string patterns matching `file:///[a-zA-Z]:` or `[a-zA-Z]:[/\\]Users[/\\]` in module-level constants or default parameters.
- Regex: `(file:///[a-zA-Z]:|[a-zA-Z]:[\\/]Users)` in non-test source files and linters.

## Hazard & Failure Mode

- Non-portability across machines, operating systems, and developer accounts.
- Broken links and unresolvable dependencies in git worktrees and CI/CD pipelines.
- Accidental leakage of local username and directory structure into tracked repository manifests.

## Dual Healthy Pattern

See [HP_PY_006_dynamic_repository_relative_resolution](../../helpful/python/HP_PY_006_dynamic_repository_relative_resolution.md).
