---
pattern_id: AP_SQL_002
name: unbounded_transaction_leak
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_SQL_002_unit_of_work_transaction_fence
language: sql
authority_effect: None
---

# Anti-Pattern: Unbounded Transaction Leak (`AP_SQL_002`)

## Description

Opening database transactions without RAII context managers (`with conn:` or unit-of-work scopes), leaving uncommitted locks or failing to rollback on unhandled exceptions.

## Detection Signature

- AST pattern:
  `conn.cursor()` or `conn.execute()` without an enclosing `with` statement, or `try ... finally` block lacking `conn.rollback()` or `conn.close()`.
- Runtime symptom:
  `sqlite3.OperationalError: database is locked` or thread connection exhaustion under concurrent execution.

## Hazard & Failure Mode

- Holds table locks indefinitely across asynchronous turns.
- Causes cascading timeouts in concurrent agent tasks.
- Leaves repository state in partially committed or corrupted states.

## Dual Healthy Pattern

See [HP_SQL_002_unit_of_work_transaction_fence](../../helpful/sql/HP_SQL_002_unit_of_work_transaction_fence.md).
