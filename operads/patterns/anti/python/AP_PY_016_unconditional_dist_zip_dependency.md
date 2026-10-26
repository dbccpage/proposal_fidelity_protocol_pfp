---
pattern_id: AP_PY_016
name: unconditional_dist_zip_dependency
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_019_conditional_dist_zip_or_bare_directory_guard
language: python
authority_effect: None
---

# Anti-Pattern: Unconditional Dist ZIP Dependency (`AP_PY_016`)

## Description

Deposit verification entrypoints (e.g., `verify_deposit.py`) unconditionally attempting to open or verify a bundled distribution archive in `dist/<slug>_v<version>.zip` crash with `FileNotFoundError` when invoked on a clean checkout or bare source tree where the zip has not yet been built.

## Detection Signature

- AST / Python Pattern:
  Direct calls to archive verification routines (e.g. `check_selected_archive(...)`) without guarding against file existence:
  ```python
  # BAD: Crashes if dist/ does not exist
  check_selected_archive(archive_path)
  ```
- Good Pattern:
  ```python
  # GOOD: Verifies archive if present or explicitly requested, else verifies bare directory payload
  if archive_path and archive_path.exists():
      check_selected_archive(archive_path)
  ```

## Hazard & Failure Mode

- Breaks automated CI and local preflight checks (`py -3.12 verify_deposit.py`) on source checkouts.
- Fails closed abruptly with an unhandled `FileNotFoundError` instead of performing standalone source integrity checks.

## Prevention & Resolution

Wrap archive-dependent verification checks in a conditional guard (`if archive_path and archive_path.exists():`) and permit bare-directory manifest and integrity validation when no archive is provided.
