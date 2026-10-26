---
pattern_id: AP_SQL_001
name: unparameterized_string_query
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_SQL_001_parameterized_query_binding
language: sql
authority_effect: None
---

# Anti-Pattern: Unparameterized String Query Concatenation (`AP_SQL_001`)

## Description

Constructing SQL queries via Python/Rust format strings (`f"SELECT ... WHERE id = '{user_id}'"` or `format!("SELECT ...")`) rather than parameterized positional or named bindings.

## Detection Signature

- AST / Grep pattern:
  `cursor.execute(f"..."` or `f"""SELECT .* WHERE .* = {.*}"""` or `format!("SELECT ...")`.
- Static Analysis:
  Bandit `B608` (hardcoded SQL expression) or SQLFluff parsing defect.

## Hazard & Failure Mode

- Introduces SQL injection vulnerabilities.
- Defeats query plan caching and prepared statement compilation in SQLite / PostgreSQL.
- Fails clean architecture port fences by leaking dynamic query construction into callers.

## Dual Healthy Pattern

See [HP_SQL_001_parameterized_query_binding](../../helpful/sql/HP_SQL_001_parameterized_query_binding.md).
