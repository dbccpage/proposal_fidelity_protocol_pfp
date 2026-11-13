---
pattern_id: HP_PY_004
name: atomic_write_with_backup_and_fail_closed
category: helpful_pattern
operad_type: Isomorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "exact"
dual_pattern: AP_PY_004_silent_catalog_reset_on_corruption
language: python
authority_effect: None
---

# Helpful Pattern: Atomic Write with Backup and Fail-Closed (`HP_PY_004`)

## Description

Enforcing fail-closed behavior on corrupted state catalogs by raising explicit exceptions rather than resetting in-memory structures, combined with atomic file writes using temporary staging files and rolling `.bak` backup files.

## Implementation Pattern

```python
# 1. Fail-closed loading:
except json.JSONDecodeError as exc:
    raise ValueError(f"CORRUPT_CATALOG: unreadable catalog at {path}") from exc

# 2. Atomic write with rolling backup:
tmp_path = path.with_suffix(".tmp")
bak_path = path.with_suffix(".bak")
tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
if path.exists():
    shutil.copy2(path, bak_path)
tmp_path.replace(path)
```

## Guarantees Under Declared Assumptions

- Corrupted files are never overwritten with blank state.
- In-flight write crashes cannot corrupt the canonical catalog file.
- The previous valid catalog snapshot is preserved in `.bak`.
