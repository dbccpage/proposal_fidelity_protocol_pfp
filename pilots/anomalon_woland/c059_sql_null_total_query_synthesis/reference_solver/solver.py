"""Reference solver for C059 SQL Synthesis under Three-Valued-Logic Fences."""

from typing import Any, Dict

from ..relational_contract import validate_schema_and_spec
from .compiler import SQLCompiler


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Compiles relational algebra specification to null-safe SQL."""
    case_id = case.get("case_id", "unknown")
    schema = case.get("schema")
    spec = case.get("spec")
    protected = case.get("protected", [])

    if schema is None or spec is None:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MISSING_SCHEMA_OR_SPEC"},
        }

    is_valid, err_code, wit = validate_schema_and_spec(schema, spec)
    if not is_valid:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": wit or {"reason": err_code},
        }

    try:
        compiler = SQLCompiler(schema)
        sql, preflight_sql, null_ledger = compiler.compile(spec, protected)
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "sql": sql,
            "preflight_sql": preflight_sql,
            "null_ledger": null_ledger,
        }
    except Exception as e:
        return {"case_id": case_id, "status": "UNKNOWN", "code": f"UNSUPPORTED_NODE: {str(e)}"}
