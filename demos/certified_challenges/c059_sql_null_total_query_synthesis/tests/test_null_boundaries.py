"""Independent SQLite controls for NULL truth and an empty NOT IN subquery."""

from __future__ import annotations

import sqlite3

import pytest

from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from c059_sql_null_total_query_synthesis.judge_packet.relational_interpreter import (
    eval_predicate,
    execute_relational_spec,
)


@pytest.mark.parametrize(("left", "right"), [(None, None), (None, 0), (None, 1), (0, None), (1, None)])
@pytest.mark.parametrize("negated", [False, True])
def test_integer_or_null_coalesce_truth_agrees_with_direct_sqlite(left, right, negated):
    predicate = {"coalesce": [{"val": left}, {"val": right}]}
    sql = "SELECT COALESCE(?, ?)"
    if negated:
        predicate = {"not": predicate}
        sql = "SELECT NOT COALESCE(?, ?)"
    with sqlite3.connect(":memory:") as connection:
        observed = connection.execute(sql, (left, right)).fetchone()[0]
    expected = None if observed is None else bool(observed)
    assert eval_predicate(predicate, {}) is expected


@pytest.mark.parametrize("left", [None, 0, 1])
@pytest.mark.parametrize("right", [[], [None], [1], [1, None]])
def test_not_in_empty_and_null_subqueries_agree_with_direct_sqlite(left, right):
    spec = {
        "op": "anti_join", "match": "sql_not_in", "left": "l", "right": "r",
        "on": {"eq3": ["l.id", "r.other"]},
    }
    database = {"l": [{"id": left}], "r": [{"other": item} for item in right]}
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE r (other INTEGER)")
        connection.executemany("INSERT INTO r VALUES (?)", [(item,) for item in right])
        truth = connection.execute("SELECT ? NOT IN (SELECT other FROM r)", (left,)).fetchone()[0]
    expected = [{"id": left}] if truth == 1 else []
    assert execute_relational_spec(spec, database) == expected


def test_independent_judge_accepts_correct_not_coalesce_null_query():
    case = {
        "case_id": "null-coalesce-boundary",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t", "where": {
            "not": {"coalesce": ["id", {"val": None}]},
        }},
        "protected": [],
        "test_databases": [{"t": [{"id": None}]}],
    }
    candidate = {
        "case_id": case["case_id"], "status": "SOLVED",
        "sql": "SELECT id FROM t WHERE NOT COALESCE(id, NULL)",
        "preflight_sql": "SELECT 1 WHERE 0", "null_ledger": [],
    }
    assert independent_check(case, candidate)[0] is True
