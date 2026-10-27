# C059 Task: SQL Synthesis under Three-Valued-Logic Fences

## Objective
Synthesize a frozen Python solver module exposing `def solve(case: dict) -> dict` that translates a relational algebra JSON specification into null-safe, dialect-neutral SQL adhering strictly to Kleene Three-Valued Logic (3VL), totality preflights on protected columns, and exact result bag preservation.

## Contract & Specification
Your solver must expose:
```python
def solve(case: dict) -> dict: ...
```

### Input Schema (`case`)
```json
{
  "case_id": "c059_ex01",
  "schema": {
    "table_name": {
      "col_name": "INTEGER | TEXT"
    }
  },
  "spec": {
    "op": "select | project | rename | join | anti_join | semi_join | group | union_all | distinct",
    ...
  },
  "protected": ["col1", "col2"],
  "test_databases": [...]
}
```

### Output Schema
If the spec is valid and supported:
```json
{
  "case_id": "c059_ex01",
  "status": "SOLVED",
  "sql": "SELECT ...",
  "preflight_sql": "SELECT ...",
  "null_ledger": [
    {"node": "where.distinct", "construct": "IS DISTINCT FROM"},
    ...
  ]
}
```
If the schema or spec is malformed, references non-existent tables/columns, or contains unhandled syntax:
```json
{
  "case_id": "c059_ex01",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "UNKNOWN_COLUMN",
    "path": "spec.where.eq3[1]"
  }
}
```

## Three-Valued Logic Rules
1. `distinct`: Must emit `IS DISTINCT FROM` to distinguish NULL from non-NULL values without dropping rows where one operand is NULL.
2. `not_distinct`: Must emit `IS NOT DISTINCT FROM`.
3. `eq3`: Must emit `=` (evaluates to UNKNOWN if either operand is NULL, filtered out by WHERE).
4. `anti_join`:
   - If `match: "null_safe"`, emit `WHERE NOT EXISTS (SELECT 1 FROM ... WHERE ...)`.
   - If `match: "sql_not_in"`, emit `WHERE col NOT IN (SELECT col FROM ...)`. Note that if the right subquery contains any NULL, SQL 3VL causes NOT IN to return zero rows.
5. `preflight_sql`: For all declared `protected` columns present in the target table, emit a query that retrieves all rows where any protected column IS NULL:
   `SELECT * FROM table WHERE col1 IS NULL OR col2 IS NULL`.
