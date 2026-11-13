---
pattern_id: HP_SQL_002
name: unit_of_work_transaction_fence
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_SQL_002_unbounded_transaction_leak
language: sql
authority_effect: None
---

# Healthy Pattern: Unit of Work Transaction Fence (`HP_SQL_002`)

## Description

Encapsulate all SQL operations within context-managed Unit of Work or transaction scopes (`with transaction(conn):`) ensuring atomic commits on success and fail-closed rollbacks on exception.

## Remediation & Implementation

```python
# Context-managed Unit of Work pattern
from contextlib import contextmanager

@contextmanager
def transaction_scope(connection):
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

# Caller usage:
with transaction_scope(db_conn) as cur:
    cur.execute("UPDATE claim_nodes SET status = ? WHERE id = ?", ("VALIDATED", node_id))
    cur.execute("INSERT INTO audit_log (node_id, action) VALUES (?, ?)", (node_id, "APPROVE"))
```

## Operadic Property

Eliminates the `AP_SQL_002` leaked connection witness:
$$\|A_{\text{SQL-002}}(H_{\text{SQL-002}}(c))\| = 0$$
