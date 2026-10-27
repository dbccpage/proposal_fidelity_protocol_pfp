"""Schema headings survive empty rows and positional set operations."""

import subprocess
import sys
from pathlib import Path

import pytest

from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)


def answer(case, sql, preflight="SELECT 1 WHERE 0"):
    return {
        "case_id": case["case_id"],
        "status": "SOLVED",
        "sql": sql,
        "preflight_sql": preflight,
        "null_ledger": [],
    }


def test_empty_query_requires_heading_even_without_any_rows():
    case = {
        "case_id": "empty",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "test_databases": [{"t": []}],
    }
    assert independent_check(case, answer(case, "SELECT id FROM t"))[0]
    assert not independent_check(case, answer(case, "SELECT id AS other FROM t"))[0]


@pytest.mark.parametrize("left", [[], [{"id": 1}]])
def test_union_uses_left_names_and_right_positions(left):
    case = {
        "case_id": "union",
        "schema": {"l": {"id": "INTEGER"}, "r": {"other": "INTEGER"}},
        "spec": {"op": "union_all", "left": "l", "right": "r"},
        "test_databases": [{"l": left, "r": [{"other": 2}]}],
    }
    assert independent_check(case, answer(case, "SELECT id FROM l UNION ALL SELECT other FROM r"))[
        0
    ]
    assert not independent_check(case, answer(case, "SELECT id FROM l UNION ALL SELECT 99 FROM r"))[
        0
    ]


@pytest.mark.parametrize(
    "right_node", ["r", {"op": "rename", "from": "r", "map": {"value": "renamed"}}]
)
def test_empty_right_left_join_null_extends_declared_heading(right_node):
    case = {
        "case_id": "left-empty",
        "schema": {"l": {"id": "INTEGER"}, "r": {"value": "TEXT"}},
        "spec": {"op": "join", "type": "left", "left": "l", "right": right_node},
        "test_databases": [{"l": [{"id": 1}], "r": []}],
    }
    label = "value" if isinstance(right_node, str) else "renamed"
    assert independent_check(case, answer(case, f"SELECT id, NULL AS {label} FROM l"))[0]
    assert not independent_check(case, answer(case, "SELECT id FROM l"))[0]


def test_empty_protected_preflight_requires_its_source_heading():
    case = {
        "case_id": "preflight-empty",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "protected": ["id"],
        "test_databases": [{"t": []}],
    }
    assert independent_check(
        case, answer(case, "SELECT id FROM t", "SELECT id FROM t WHERE id IS NULL")
    )[0]
    assert not independent_check(
        case, answer(case, "SELECT id FROM t", "SELECT 1 AS unrelated WHERE 0")
    )[0]


def test_no_protected_columns_still_require_empty_preflight():
    case = {
        "case_id": "no-protected",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "test_databases": [{"t": []}],
    }
    assert independent_check(
        case, answer(case, "SELECT id FROM t", "SELECT 1 AS arbitrary WHERE 0")
    )[0]
    assert not independent_check(case, answer(case, "SELECT id FROM t", "SELECT 1 AS arbitrary"))[0]


def test_union_positions_follow_schema_not_row_dictionary_insertion_order():
    case = {
        "case_id": "positions",
        "schema": {"l": {"a": "INTEGER", "b": "INTEGER"}, "r": {"x": "INTEGER", "y": "INTEGER"}},
        "spec": {"op": "union_all", "left": "l", "right": "r"},
        "test_databases": [{"l": [], "r": [{"y": 20, "x": 10}]}],
    }
    assert independent_check(case, answer(case, "SELECT a,b FROM l UNION ALL SELECT x,y FROM r"))[0]
    assert not independent_check(
        case, answer(case, "SELECT a,b FROM l UNION ALL SELECT y,x FROM r")
    )[0]


@pytest.mark.parametrize(
    ("spec", "sql"),
    [
        ({"op": "project", "from": "t", "columns": ["x"]}, "SELECT x FROM t"),
        ({"op": "rename", "from": "t", "map": {"id": "newid"}}, "SELECT id AS newid,x FROM t"),
        ({"op": "distinct", "from": "t"}, "SELECT DISTINCT * FROM t"),
        (
            {"op": "group", "from": "t", "by": ["x"], "agg": {"n": {"func": "count_star"}}},
            "SELECT x,COUNT(*) AS n FROM t GROUP BY x",
        ),
        (
            {"op": "group", "from": "t", "agg": {"n": {"func": "count_star"}}},
            "SELECT COUNT(*) AS n FROM t",
        ),
        (
            {"op": "semi_join", "left": "t", "right": "r"},
            "SELECT * FROM t WHERE EXISTS(SELECT 1 FROM r)",
        ),
        (
            {"op": "anti_join", "left": "t", "right": "r"},
            "SELECT * FROM t WHERE NOT EXISTS(SELECT 1 FROM r)",
        ),
        ({"op": "join", "left": "t", "right": "r"}, "SELECT * FROM t JOIN r ON 1"),
    ],
)
def test_schema_headings_propagate_through_empty_operators(spec, sql):
    case = {
        "case_id": "empty-operators",
        "schema": {"t": {"id": "INTEGER", "x": "TEXT"}, "r": {"value": "INTEGER"}},
        "spec": spec,
        "test_databases": [{"t": [], "r": []}],
    }
    assert independent_check(case, answer(case, sql))[0]
    assert not independent_check(case, answer(case, "SELECT 1 AS incorrect WHERE 0"))[0]


def test_second_judge_metadata_needs_neither_first_judge_nor_proposer():
    script = r"""
import importlib.abc
import sys
class BlockOtherEngines(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if "reference_solver" in fullname.split(".") or fullname.endswith((".exact_checker", ".sqlite_relational_oracle")):
            raise AssertionError("other engine attempted")
sys.meta_path.insert(0, BlockOtherEngines())
for name in ("reference_solver", "judge_packet.exact_checker", "judge_packet.sqlite_relational_oracle"):
    try:
        importlib.import_module("c059_sql_null_total_query_synthesis." + name)
    except AssertionError:
        pass
    else:
        raise AssertionError("negative import control failed")
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import independent_check
case={"case_id":"isolated","schema":{"l":{"id":"INTEGER"},"r":{"x":"TEXT"}},
      "spec":{"op":"join","type":"left","left":"l","right":"r"},
      "test_databases":[{"l":[{"id":1}],"r":[]}]}
candidate={"case_id":"isolated","status":"SOLVED","sql":"SELECT id,NULL AS x FROM l", "preflight_sql":"SELECT 1 WHERE 0","null_ledger":[]}
assert independent_check(case,candidate)[0]
assert not independent_check(case,dict(candidate,sql="SELECT id FROM l"))[0]
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("judge", [independent_check, verify_candidate])
@pytest.mark.parametrize("rows", [[{"id": 1}], [{"id": 1}, {"id": 2, "x": "kept"}]])
def test_fixture_schema_retains_missing_and_later_row_columns(judge, rows):
    case = {
        "case_id": "schema-rows",
        "schema": {"t": {"id": "INTEGER", "x": "TEXT"}},
        "spec": {"op": "select", "from": "t"},
        "test_databases": [{"t": rows}],
    }
    assert judge(case, answer(case, "SELECT id,x FROM t"))[0]
    assert not judge(case, answer(case, "SELECT id FROM t"))[0]
    if len(rows) > 1:
        assert not judge(case, answer(case, "SELECT id,NULL AS x FROM t"))[0]


@pytest.mark.parametrize("judge", [independent_check, verify_candidate])
def test_protected_preflight_null_pads_missing_declared_fields(judge):
    case = {
        "case_id": "missing-protected",
        "schema": {"t": {"id": "INTEGER", "x": "TEXT"}},
        "spec": {"op": "select", "from": "t"},
        "protected": ["x"],
        "test_databases": [{"t": [{"id": 1}]}],
    }
    assert judge(case, answer(case, "SELECT id,x FROM t", "SELECT id,x FROM t WHERE x IS NULL"))[0]
    assert not judge(case, answer(case, "SELECT id,x FROM t", "SELECT id FROM t WHERE x IS NULL"))[
        0
    ]
