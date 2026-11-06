"""Real database execution is required; a candidate cannot mutate its fixtures."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from c059_sql_null_total_query_synthesis.reference_solver import (
    solve,
)
from c059_sql_null_total_query_synthesis.sqlite_read_boundary import (
    restrict_to_read_queries,
)

JUDGES = (verify_candidate, independent_check)
PACKAGE = Path(__file__).resolve().parents[1]
CASES = sorted((PACKAGE / "judge_packet/cases").glob("*.json"))
MUTATIONS = sorted((PACKAGE / "judge_packet/hostile_mutations").glob("*.json"))


def _case(rows=None):
    return {
        "case_id": "read_boundary",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "protected": [],
        "test_databases": [{"t": [{"id": 1}] if rows is None else rows}],
    }


def _answer(sql="SELECT id FROM t"):
    return {
        "case_id": "read_boundary",
        "status": "SOLVED",
        "sql": sql,
        "preflight_sql": "SELECT 1 WHERE 0",
        "null_ledger": [],
    }


@pytest.mark.parametrize("judge", JUDGES)
def test_real_read_query_is_accepted(judge):
    assert judge(_case(), _answer())[0] is True


@pytest.mark.parametrize("judge", JUDGES)
def test_one_executed_empty_database_is_not_an_empty_suite(judge):
    assert judge(_case(rows=[]), _answer())[0] is True


@pytest.mark.parametrize("judge", JUDGES)
@pytest.mark.parametrize("suite", [None, [], {}, "databases"])
def test_no_database_execution_cannot_verify_a_solution(judge, suite):
    case = _case()
    if suite is None:
        del case["test_databases"]
    else:
        case["test_databases"] = suite
    assert judge(case, _answer("not even SQL"))[0] is False


@pytest.mark.parametrize("judge", JUDGES)
def test_delete_returning_cannot_impersonate_a_read_query(judge):
    assert judge(_case(), _answer("DELETE FROM t RETURNING id"))[0] is False


@pytest.mark.parametrize("judge", JUDGES)
@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM t",
        "UPDATE t SET id = 2",
        "DROP TABLE t",
        "CREATE TABLE intrusion (x INTEGER)",
        "ATTACH DATABASE ':memory:' AS intrusion",
        "PRAGMA query_only = OFF",
    ],
)
def test_nonquery_statement_is_not_an_empty_result(judge, sql):
    assert judge(_case(rows=[]), _answer(sql))[0] is False


@pytest.mark.parametrize("judge", JUDGES)
def test_preflight_query_also_cannot_mutate_the_fixture(judge):
    answer = _answer()
    answer["preflight_sql"] = "UPDATE t SET id = id RETURNING id"
    assert judge(_case(), answer)[0] is False


@pytest.mark.parametrize("judge", JUDGES)
@pytest.mark.parametrize("construct", [None, "", " ", 3, True, [], {}])
def test_malformed_ledger_construct_is_a_refusal_not_a_crash(judge, construct):
    answer = _answer()
    answer["null_ledger"] = [{"construct": construct}]
    assert judge(_case(), answer)[0] is False


def test_denied_write_leaves_real_sqlite_rows_unchanged():
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE t (id INTEGER)")
        connection.execute("INSERT INTO t VALUES (1)")
        connection.commit()
        restrict_to_read_queries(connection)
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            connection.execute("DELETE FROM t")
        if sqlite3.sqlite_version_info >= (3, 35, 0):
            with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
                connection.execute("DELETE FROM t RETURNING id")
        assert connection.execute("SELECT id FROM t").fetchall() == [(1,)]
        assert connection.execute(
            "WITH RECURSIVE c(x) AS (VALUES (1) UNION ALL SELECT x+1 FROM c WHERE x<3) "
            "SELECT sum(x) FROM c"
        ).fetchall() == [(6,)]


@pytest.mark.parametrize("judge", JUDGES)
def test_nested_preflight_uses_queried_table_not_unrelated_schema_order(judge):
    case = _case()
    case["schema"] = {"other": {"id": "INTEGER"}, "t": {"id": "INTEGER"}}
    case["spec"] = {"op": "distinct", "from": {"op": "select", "from": "t"}}
    case["protected"] = ["id"]
    case["test_databases"] = [{"other": [{"id": None}], "t": [{"id": 1}]}]
    answer = solve(case)
    assert answer["status"] == "SOLVED"
    assert judge(case, answer)[0] is True


def test_retained_case_and_mutation_inventory_is_not_empty():
    assert len(CASES) == 64
    assert len(MUTATIONS) == 48


@pytest.mark.parametrize("path", CASES, ids=lambda path: path.stem)
def test_existing_case_reference_answers_remain_accepted(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    answer = solve(case)
    for judge in JUDGES:
        ok, detail = judge(case, answer)
        assert ok is True, f"{judge.__name__}: {detail}"


@pytest.mark.parametrize("path", MUTATIONS, ids=lambda path: path.stem)
def test_every_retained_hostile_mutation_is_rejected_by_each_judge(path):
    record = json.loads(path.read_text(encoding="utf-8"))
    for judge in JUDGES:
        ok, detail = judge(record["case"], record["candidate"])
        assert ok is False, f"{judge.__name__}: {detail}"
