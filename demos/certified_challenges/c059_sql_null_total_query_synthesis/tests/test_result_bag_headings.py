"""Result bags cannot discard extra columns or turn missing columns into NULL."""

from __future__ import annotations

import pytest

from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from c059_sql_null_total_query_synthesis.relational_contract import (
    compare_bags,
)


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ([{"id": 1}], [{"id": 1, "extra": 2}]),
        ([{"id": None}], [{"other": 2}]),
        ([{"id": None}], [{}]),
        ([{"id": 1}, {"id": None}], [{"id": 1}, {"other": None}]),
        ([{"id": 1}, {"other": None}], [{"id": 1}, {"id": None}]),
    ],
)
def test_every_row_must_have_the_same_exact_heading(expected, actual):
    assert compare_bags(expected, actual)[0] is False
    assert compare_bags(actual, expected)[0] is False


def test_row_and_column_order_do_not_change_null_safe_bag_equality():
    first = [{"id": 1, "name": None}, {"id": 2, "name": "x"}, {"id": 1, "name": None}]
    second = [{"name": None, "id": 1}, {"name": None, "id": 1}, {"name": "x", "id": 2}]
    assert compare_bags(first, second)[0] is True
    assert compare_bags(first, second[:2])[0] is False
    assert compare_bags([], [])[0] is True


@pytest.mark.parametrize("judge", [verify_candidate, independent_check])
@pytest.mark.parametrize("sql", ["SELECT NULL AS id, 2 AS extra FROM t", "SELECT 2 AS other FROM t"])
def test_candidate_sql_cannot_impersonate_null_rows_with_a_different_heading(judge, sql):
    case = {
        "case_id": "heading-boundary",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "protected": [],
        "test_databases": [{"t": [{"id": None}]}],
    }
    candidate = {
        "case_id": case["case_id"],
        "status": "SOLVED",
        "sql": sql,
        "preflight_sql": "SELECT 1 WHERE 0",
        "null_ledger": [],
    }
    assert judge(case, candidate)[0] is False
