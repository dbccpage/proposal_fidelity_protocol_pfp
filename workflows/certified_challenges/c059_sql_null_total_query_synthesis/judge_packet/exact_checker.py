"""Exact checker for C059 SQL Synthesis under Three-Valued-Logic Fences.
Executes candidate SQL against reference databases in SQLite and compares result bags.
"""

import sqlite3
from typing import Any, Dict, List, Tuple

from ..relational_contract import compare_bags, validate_schema_and_spec
from ..sqlite_read_boundary import restrict_to_read_queries
from .sqlite_relational_oracle import SQLiteRelationalOracle


def setup_sqlite_database(
    schema: Dict[str, Any], data: Dict[str, List[Dict[str, Any]]]
) -> sqlite3.Connection:
    """Creates in-memory SQLite database populated with provided test data."""
    con = sqlite3.connect(":memory:")
    cur = con.cursor()

    for tbl, cols in schema.items():
        col_defs = []
        for cname, ctype in cols.items():
            col_defs.append(f'"{cname}" {ctype}')
        cur.execute(f'CREATE TABLE "{tbl}" ({", ".join(col_defs)})')

        tbl_data = data.get(tbl, [])
        if tbl_data:
            # Populate all declared fields, including later-row-only values.
            cnames = list(cols)
            placeholders = ", ".join(["?"] * len(cnames))
            quoted_cols = ", ".join([f'"{c}"' for c in cnames])
            insert_sql = f'INSERT INTO "{tbl}" ({quoted_cols}) VALUES ({placeholders})'
            rows = []
            for r in tbl_data:
                rows.append([r.get(c) for c in cnames])
            cur.executemany(insert_sql, rows)
    con.commit()
    return con


def run_query(con: sqlite3.Connection, sql: str) -> List[Dict[str, Any]]:
    """Runs SQL query and returns result as list of row dicts."""
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def verify_candidate(case: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """Verifies candidate SQL against case requirements across hidden test databases."""
    if not isinstance(candidate, dict):
        return False, "CANDIDATE_NOT_A_DICT"

    if candidate.get("case_id") != case.get("case_id"):
        return (
            False,
            f"CASE_ID_MISMATCH: expected {case.get('case_id')}, got {candidate.get('case_id')}",
        )

    status = candidate.get("status")
    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:
        return False, f"INVALID_STATUS: {status}"

    schema = case.get("schema", {})
    spec = case.get("spec", {})
    protected = case.get("protected", [])
    test_dbs = case.get("test_databases", [])

    # 1. Check if case is structurally invalid
    case_is_valid, err_code, _ = validate_schema_and_spec(schema, spec)
    if not case_is_valid:
        if status != "OUT_OF_SCOPE":
            return False, f"EXPECTED_OUT_OF_SCOPE_FOR_POISONED_CASE, got {status} ({err_code})"
        return True, "OUT_OF_SCOPE_CORRECTLY_IDENTIFIED"

    if status == "OUT_OF_SCOPE":
        return False, f"FALSE_OUT_OF_SCOPE_ON_VALID_CASE: case was well-formed ({err_code})"

    if status == "UNKNOWN":
        # Candidate claims spec cannot be compiled or supported
        # If case is standard and in scope, reject false UNKNOWN
        return False, "FALSE_UNKNOWN_ON_FEASIBLE_RELATIONAL_SPEC"

    # status == "SOLVED"
    if not isinstance(test_dbs, list) or not test_dbs or any(not isinstance(db, dict) for db in test_dbs):
        return False, "MISSING_OR_INVALID_TEST_DATABASE_SUITE"
    sql = candidate.get("sql")
    preflight_sql = candidate.get("preflight_sql")
    null_ledger = candidate.get("null_ledger")

    if not isinstance(sql, str) or not sql.strip():
        return False, "MISSING_OR_EMPTY_SQL"
    if not isinstance(preflight_sql, str) or not preflight_sql.strip():
        return False, "MISSING_OR_EMPTY_PREFLIGHT_SQL"
    if not isinstance(null_ledger, list):
        return False, "NULL_LEDGER_MUST_BE_LIST"

    # Test on all test databases
    for db_idx, db_data in enumerate(test_dbs):
        con = None
        oracle_con = None
        try:
            # Oracle staging is PRIVATE. A candidate never sees expected rows,
            # trusted views or constants, even via sqlite_temp_schema.
            oracle_con = setup_sqlite_database(schema, db_data)
            oracle = SQLiteRelationalOracle(oracle_con, schema)
            try:
                relation = oracle.evaluate(spec)
                ref_pre_heading, ref_preflight_rows = oracle.preflight(spec, protected)
                restrict_to_read_queries(oracle_con)
                ref_heading, ref_rows = oracle.read(relation)
            except Exception as e:
                return False, f"REFERENCE_ORACLE_ERROR_ON_DB_{db_idx}: {str(e)}"
            con = setup_sqlite_database(schema, db_data)
            restrict_to_read_queries(con)

            # Run candidate queries
            try:
                cursor = con.execute(sql)
                cand_heading = frozenset(column[0] for column in cursor.description or ())
                # Match the retained first-label-wins row dictionary contract.
                cand_rows = [dict(zip(reversed([column[0] for column in cursor.description]),
                                      reversed(row))) for row in cursor.fetchall()]
            except Exception as e:
                return False, f"CANDIDATE_SQL_RUNTIME_ERROR_ON_DB_{db_idx}: {str(e)}"

            try:
                cursor = con.execute(preflight_sql)
                cand_pre_heading = frozenset(column[0] for column in cursor.description or ())
                names = [column[0] for column in cursor.description]
                cand_preflight_rows = [dict(zip(reversed(names), reversed(row))) for row in cursor.fetchall()]
            except Exception as e:
                return False, f"CANDIDATE_PREFLIGHT_RUNTIME_ERROR_ON_DB_{db_idx}: {str(e)}"

            # Compare bags
            if ref_heading != cand_heading:
                return False, f"RESULT_HEADING_MISMATCH_ON_DB_{db_idx}"
            if ref_pre_heading is not None and ref_pre_heading != cand_pre_heading:
                return False, f"PREFLIGHT_HEADING_MISMATCH_ON_DB_{db_idx}"
            ok_bag, msg_bag = compare_bags(ref_rows, cand_rows)
            if not ok_bag:
                return False, f"RESULT_BAG_MISMATCH_ON_DB_{db_idx}: {msg_bag}"

            ok_pre, msg_pre = compare_bags(ref_preflight_rows, cand_preflight_rows)
            if not ok_pre:
                return False, f"PREFLIGHT_BAG_MISMATCH_ON_DB_{db_idx}: {msg_pre}"

        finally:
            if con:
                con.close()
            if oracle_con:
                oracle_con.close()

    # Verify null_ledger constructs appear in sql
    upper_sql = sql.upper()
    for entry in null_ledger:
        if not isinstance(entry, dict) or "construct" not in entry:
            return False, "MALFORMED_NULL_LEDGER_ENTRY"
        if not isinstance(entry["construct"], str) or not entry["construct"].strip():
            return False, "MALFORMED_NULL_LEDGER_CONSTRUCT"
        construct = entry["construct"].upper()
        # Clean construct words for detection
        first_word = construct.split()[0]
        if first_word not in upper_sql and construct not in upper_sql:
            return False, f"NULL_LEDGER_CONSTRUCT_ABSENT_IN_SQL: {construct}"

    return True, "SQL_VERIFIED_VALID"
