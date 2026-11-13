---
name: config-migration
description: Migrate versioned JSON/YAML configuration documents to a new schema version safely.
---
# Config migration

Use this skill when a task asks you to convert configuration documents from one schema
version to another.

## Procedure

1. Write the migration as a pure function `migrate(old: dict) -> dict`. Do not mutate the input.
2. Build the new document key by key from the target schema; do not copy the old dict and patch it,
   because stale keys leak through.
3. Map every renamed key explicitly. Keep a small table of `old_key -> new_key` at the top of the module.
4. Convert units at the boundary (for example seconds to milliseconds) using exact arithmetic
   (`decimal.Decimal`) and an explicit rounding mode, then convert to `int`.
5. Optional fields: if the old value is missing or `null`, follow the target schema's rule exactly
   (omit the key, or use the documented default). Never emit `null` for a field the schema calls optional.
6. Validate cross-references (ids, state names) and raise `ValueError` with a stable code when one is unknown.
7. Produce deterministic output: sort lists whose order is not meaningful by a documented key.

## Checklist

- [ ] Pure function, no I/O
- [ ] Every target key produced by explicit code
- [ ] Units converted with exact rounding
- [ ] Optional/null handling matches the schema
- [ ] Unknown references rejected
- [ ] Output ordering deterministic
