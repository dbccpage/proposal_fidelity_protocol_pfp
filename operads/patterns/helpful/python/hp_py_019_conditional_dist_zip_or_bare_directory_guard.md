---
pattern_id: HP_PY_019
name: conditional_dist_zip_or_bare_directory_guard
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_016_unconditional_dist_zip_dependency
language: python
authority_effect: None
---

# Healthy Pattern: Conditional Dist ZIP or Bare Directory Guard (`HP_PY_019`)

## Description

Deposit verification entrypoints (e.g. `verify_deposit.py`) must verify distribution archives only when present or explicitly requested, falling back cleanly to bare directory payload validation so that clean checkouts or pre-build trees pass without `FileNotFoundError`.

## Implementation Pattern

```python
if archive_path and archive_path.exists():
    check_selected_archive(archive_path)
else:
    check_directory_payload(source_dir)
```

## Resolution

Wrap archive-dependent checks with existence guards and allow bare-directory manifest verification.
