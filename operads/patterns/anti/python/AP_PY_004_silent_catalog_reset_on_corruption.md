---
pattern_id: AP_PY_004
name: silent_catalog_reset_on_corruption
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_004_atomic_write_with_backup_and_fail_closed
language: python
authority_effect: None
---

# Anti-Pattern: Silent Catalog Reset on Corruption (`AP_PY_004`)

## Description

Catching `json.JSONDecodeError` or file read errors when loading a persistent state catalog and resetting the in-memory data to an empty dictionary `{}`.

## Hazard & Failure Mode

- When the subsequent write or save operation is triggered, the empty dictionary overwrites the corrupted file on disk.
- Permanently destroys historical admission records, antibody inventories, and audit trails.
- Erases epistemic immune memory and allows previously blocked defects to re-enter.

## Detection Signature

```python
# Anti-pattern:
except (json.JSONDecodeError, OSError):
    self._catalog = {}  # Destroys catalog history on next write!
```

## Dual Healthy Pattern

See [HP_PY_004_atomic_write_with_backup_and_fail_closed](../../helpful/python/HP_PY_004_atomic_write_with_backup_and_fail_closed.md).
