---
name: techne-code-sql-anti-patterns
description: "Audit SQL queries, schemas and adapters for injection, lock problems, missing indexes and null handling."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [techne, quality, sql]
---

# Techne Code SQL Anti-Patterns

**Status:** canonical-candidate  
**AuthorityEffect:** None

Specialist skill for detecting, isolating, and remediating SQL and persistence anti-patterns and certifying dual healthy patterns across `omega_engine_operations/infrastructure/` and relational stores.

## Operational Scope

Operates directly against database adapters, migration scripts, and repository queries in SQLite, PostgreSQL, and BigQuery. Consults the canonical catalog at `omega_engine_operads/patterns/anti/sql/`.

### Canonical Anti-Patterns & Dual Healthy Patterns

| ID | Anti-Pattern | Hazard | Dual Healthy Pattern |
|---|---|---|---|
| `AP_SQL_001` | Unparameterized String Concatenation | SQL injection vulnerabilities, query cache defeat | [`HP_SQL_001`](../../patterns/helpful/sql/HP_SQL_001_parameterized_query_binding.md) Parameterized Query Binding |
| `AP_SQL_002` | Unbounded Transaction Leak | Database lock deadlocks, connection exhaustion | [`HP_SQL_002`](../../patterns/helpful/sql/HP_SQL_002_unit_of_work_transaction_fence.md) Unit of Work Transaction Fence |

## Review & Audit Rubric

1. **Parameter Binding Audit:**
   - Scan for Python f-strings or format operations in `cursor.execute(...)` and ORM raw clauses.
   - Enforce positional (`?`, `$1`) or named (`:param`) parameters across all queries.
   - Recognize cross-dialect parameterization parity: standard DB-API 2.0 `cursor.execute(sql, (p1, p2))` compiles query plans natively via `sqlite3_prepare_v2` / server-side prepared statements, eliminating the need for dynamic SQL shims (such as T-SQL `sp_executesql`).
2. **Transaction Lifecycle & Context Management:**
   - Scan for raw connection transactions without context managers (`with conn:`).
   - Ensure every transaction has a fail-closed rollback path on error.
3. **Relational Contract Fences:**
   - Check null totality: all critical relational schema columns must specify `NOT NULL` with default values where applicable.
   - Ensure candidate keys have unique constraints and index coverage.

## Automated Anti-Pattern Audit Script

The canonical automated auditor is available at [`scripts/sql_anti_pattern_auditor.py`](scripts/sql_anti_pattern_auditor.py).

### Usage

```bash
# Audit a specific module or persistence layer
py -3.12 omega_engine_operads/skills/techne-code-sql-anti-patterns/scripts/sql_anti_pattern_auditor.py --path omega_engine_operations/infrastructure/

# Fail-closed check returning non-zero exit code on BLOCKER/MAJOR anti-patterns
py -3.12 omega_engine_operads/skills/techne-code-sql-anti-patterns/scripts/sql_anti_pattern_auditor.py --path . --check

# Generate Markdown audit report
py -3.12 omega_engine_operads/skills/techne-code-sql-anti-patterns/scripts/sql_anti_pattern_auditor.py --path omega_engine_education/ --report-out reports/sql_anti_pattern_report.md
```

## Integration with Pattern Hunter

This skill is invoked directly by [`auto-code-anti-pattern-hunter`](../auto-code-anti-pattern-hunter/SKILL.md) and by [`auto-oe-autop`](../auto-oe-autop/SKILL.md).

