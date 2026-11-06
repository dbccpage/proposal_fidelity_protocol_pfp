"""Independent checker for C059 SQL Synthesis under Three-Valued-Logic Fences.
Directly evaluates the relational algebra tree using a pure Python in-memory engine
and verifies candidate SQL against pure relational ground truth bags.
"""

import sqlite3
from typing import Any, Dict, Tuple

from ..relational_contract import compare_bags, validate_schema_and_spec
from ..sqlite_read_boundary import restrict_to_read_queries
from .relational_interpreter import execute_relational_spec, relation_heading


def _source_tables(spec):
    """Read base-table locators without calling the proposer's compiler."""
    pending = [spec]
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            pending.extend(node[key] for key in ("right", "left", "from") if key in node)


def independent_check(case: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """Independently verifies candidate SQL against relational algebra AST semantics."""
    if not isinstance(candidate, dict):
        return False, "INDEP_NOT_A_DICT"

    if candidate.get("case_id") != case.get("case_id"):
        return False, "INDEP_CASE_ID_MISMATCH"

    status = candidate.get("status")
    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:
        return False, f"INDEP_BAD_STATUS: {status}"

    schema = case.get("schema", {})
    spec = case.get("spec", {})
    protected = case.get("protected", [])
    test_dbs = case.get("test_databases", [])

    # 1. Structural validity check
    case_is_valid, err_code, _ = validate_schema_and_spec(schema, spec)
    if not case_is_valid:
        if status == "OUT_OF_SCOPE":
            return True, "INDEP_OUT_OF_SCOPE_ACCEPTED"
        return False, f"INDEP_EXPECTED_OUT_OF_SCOPE_GOT_{status}"

    if status == "OUT_OF_SCOPE":
        return False, "INDEP_FALSE_OUT_OF_SCOPE_ON_VALID_SPEC"

    if status == "UNKNOWN":
        return False, "INDEP_REJECTED_FALSE_UNKNOWN"

    if not isinstance(test_dbs, list) or not test_dbs or any(not isinstance(db, dict) for db in test_dbs):
        return False, "INDEP_MISSING_OR_INVALID_TEST_DATABASE_SUITE"
    sql = candidate.get("sql")
    preflight_sql = candidate.get("preflight_sql")
    null_ledger = candidate.get("null_ledger")

    if not isinstance(sql, str) or not sql.strip():
        return False, "INDEP_MISSING_SQL"
    if not isinstance(preflight_sql, str) or not preflight_sql.strip():
        return False, "INDEP_MISSING_PREFLIGHT_SQL"
    if not isinstance(null_ledger, list):
        return False, "INDEP_NULL_LEDGER_NOT_LIST"

    upper_sql = sql.upper()
    for entry in null_ledger:
        if not isinstance(entry, dict) or "construct" not in entry:
            return False, "INDEP_MALFORMED_NULL_LEDGER_ENTRY"
        if not isinstance(entry["construct"], str) or not entry["construct"].strip():
            return False, "INDEP_MALFORMED_NULL_LEDGER_CONSTRUCT"
        construct = entry["construct"].upper()
        first_word = construct.split()[0]
        if first_word not in upper_sql and construct not in upper_sql:
            return False, f"INDEP_NULL_LEDGER_CONSTRUCT_ABSENT_IN_SQL: {construct}"

    # Check execution on all test databases
    for db_idx, db_data in enumerate(test_dbs):
        # 1. Compute ground-truth bag using pure Python relational algebra evaluator
        try:
            expected_bag = execute_relational_spec(spec, db_data, schema)
            expected_heading = frozenset(relation_heading(spec, schema))
        except Exception as e:
            return False, f"INDEP_EVALUATOR_FAILED_ON_DB_{db_idx}: {str(e)}"

        # 2. Compute expected preflight bag in pure Python
        # Find base table containing protected columns (preferring the table queried by the spec)
        expected_preflight_bag = []
        expected_preflight_heading = None
        tables_to_check = list(_source_tables(spec)) or list(db_data.keys())
        for tbl in tables_to_check:
            tbl_rows = db_data.get(tbl, [])
            tbl_cols = set(schema.get(tbl, {}).keys())
            applicable = [c for c in protected if c in tbl_cols]
            if applicable:
                expected_preflight_heading = frozenset(schema[tbl])
                for r in tbl_rows:
                    if any(r.get(c) is None for c in applicable):
                        expected_preflight_bag.append({column: r.get(column) for column in schema[tbl]})
                break

        # 3. Execute candidate SQL in SQLite
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        try:
            for tbl, cols in schema.items():
                col_defs = [f'"{cname}" {ctype}' for cname, ctype in cols.items()]
                cur.execute(f'CREATE TABLE "{tbl}" ({", ".join(col_defs)})')
                tbl_rows = db_data.get(tbl, [])
                if tbl_rows:
                    # Every row uses the declared schema. The first row cannot
                    # erase fields supplied only by later fixture rows.
                    cnames = list(cols)
                    placeholders = ", ".join(["?"] * len(cnames))
                    quoted_cols = ", ".join([f'"{c}"' for c in cnames])
                    rows = [[r.get(c) for c in cnames] for r in tbl_rows]
                    cur.executemany(
                        f'INSERT INTO "{tbl}" ({quoted_cols}) VALUES ({placeholders})', rows
                    )
            con.commit()
            restrict_to_read_queries(con)

            # Execute candidate query
            try:
                cur.execute(sql)
                cand_heading = frozenset(column[0] for column in cur.description or ())
                cand_rows = [dict(r) for r in cur.fetchall()]
            except Exception as e:
                return False, f"INDEP_SQL_EXEC_ERROR_DB_{db_idx}: {str(e)}"

            # Execute candidate preflight query
            try:
                cur.execute(preflight_sql)
                cand_preflight_heading = frozenset(column[0] for column in cur.description or ())
                cand_preflight_rows = [dict(r) for r in cur.fetchall()]
            except Exception as e:
                return False, f"INDEP_PREFLIGHT_EXEC_ERROR_DB_{db_idx}: {str(e)}"

            # Compare candidate output against pure Python ground truth
            if expected_heading != cand_heading:
                return False, f"INDEP_RESULT_HEADING_DIFF_DB_{db_idx}"
            if expected_preflight_heading is not None and expected_preflight_heading != cand_preflight_heading:
                return False, f"INDEP_PREFLIGHT_HEADING_DIFF_DB_{db_idx}"
            ok_bag, msg_bag = compare_bags(expected_bag, cand_rows)
            if not ok_bag:
                return False, f"INDEP_RESULT_BAG_DIFF_DB_{db_idx}: {msg_bag}"

            ok_pre, msg_pre = compare_bags(expected_preflight_bag, cand_preflight_rows)
            if not ok_pre:
                return False, f"INDEP_PREFLIGHT_BAG_DIFF_DB_{db_idx}: {msg_pre}"

        finally:
            con.close()

    return True, "INDEPENDENT_VERIFICATION_PASSED"
