---
pattern_id: HP_SQL_001
name: parameterized_query_binding
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_SQL_001_unparameterized_string_query
language: sql
authority_effect: None
---

# Healthy Pattern: Parameterized Query Binding (`HP_SQL_001`)

## Description

Enforce parameterized positional (`?` or `$1`) or named (`:param`) variable bindings across all database adapter ports. Never concatenate raw runtime inputs into SQL statement strings.

## Remediation & Implementation

```python
# In Python sqlite3 / SQLAlchemy / aiosqlite
# Correct: Parameterized tuple/dict binding
cursor.execute(
    "SELECT id, claim_id, status FROM claims WHERE status = ? AND owner_id = ?",
    (status, owner_id),
)
```

```rust
// In Rust sqlx / rusqlite
// Correct: Parameterized binding via query macro or params!
rusqlite::Connection::execute(
    &conn,
    "INSERT INTO nodes (node_id, state) VALUES (?1, ?2)",
    params![node_id, state_str],
)?;
```

## Dialect & Driver Parameterization Mapping

| Engine / Protocol | Binding Syntax | Parameter Passing Mechanism | Equivalent Construct |
|---|---|---|---|
| **SQLite (DB-API 2.0)** | `?` | `cursor.execute(sql, (p1, p2))` | Native `sqlite3_prepare_v2` + `sqlite3_bind_*` |
| **PostgreSQL (psycopg2 / asyncpg)** | `%s` or `$1` | `cursor.execute(sql, (p1, p2))` | Server-side prepared statement |
| **SQL Server (T-SQL)** | `@p1` | Stored procedure parameter list | `sp_executesql N'...', N'@p1 ...', @p1=...` |
| **Rust (rusqlite / sqlx)** | `?` or `$1` | `params![p1, p2]` or `query!(...).bind(p1)` | Type-checked native query plan |

*Note on Dynamic SQL Wrappers:* Python DB-API 2.0 does not require or use dynamic execution shims like `sp_executesql`. Passing a parameter tuple to `cursor.execute` automatically compiles the statement handle and binds parameters at the driver level, preventing token injection.

## Operadic Property

Eliminates the `AP_SQL_001` injection hazard witness:
$$\|A_{\text{SQL-001}}(H_{\text{SQL-001}}(c))\| = 0$$

