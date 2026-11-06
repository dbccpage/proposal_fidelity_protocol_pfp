"""The first judge cannot inherit a coherently corrupted proposer answer."""

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
from c059_sql_null_total_query_synthesis.judge_packet.sqlite_relational_oracle import (
    SQLiteRelationalOracle,
)
from c059_sql_null_total_query_synthesis.reference_solver.compiler import (
    SQLCompiler,
)


def case_and_answer(rows=None):
    case = {
        "case_id": "first-owner",
        "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"},
        "protected": [],
        "test_databases": [{"t": [{"id": 1}] if rows is None else rows}],
    }
    answer = {
        "case_id": case["case_id"],
        "status": "SOLVED",
        "sql": "SELECT id FROM t",
        "preflight_sql": "SELECT 1 WHERE 0",
        "null_ledger": [],
    }
    return case, answer


def test_coherent_proposer_corruption_is_rejected(monkeypatch):
    case, answer = case_and_answer()
    assert verify_candidate(case, answer)[0]
    monkeypatch.setattr(
        SQLCompiler, "compile", lambda *args: ("SELECT 99 AS id", "SELECT 1 WHERE 0", [])
    )
    assert not verify_candidate(case, dict(answer, sql="SELECT 99 AS id"))[0]
    assert verify_candidate(case, answer)[0]


def test_empty_result_still_requires_expected_heading():
    case, answer = case_and_answer([])
    assert verify_candidate(case, answer)[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT id AS other FROM t"))[0]


def test_first_judge_executes_without_any_proposer_import():
    script = r"""
import importlib.abc
import sys
class NoProposer(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if "reference_solver" in fullname.split("."):
            raise AssertionError("proposer import attempted")
sys.meta_path.insert(0, NoProposer())
try:
    importlib.import_module("c059_sql_null_total_query_synthesis.reference_solver")
except AssertionError:
    pass
else:
    raise AssertionError("negative control did not fire")
from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import verify_candidate
case = {"case_id": "blocked", "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"}, "test_databases": [{"t": [{"id": 1}]}]}
answer = {"case_id": "blocked", "status": "SOLVED", "sql": "SELECT id FROM t",
          "preflight_sql": "SELECT 1 WHERE 0", "null_ledger": []}
assert verify_candidate(case, answer)[0]
assert not verify_candidate(case, dict(answer, sql="SELECT 99 AS id"))[0]
assert not any("reference_solver" in name.split(".") for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("spec", "sql"),
    [
        (
            {"op": "select", "from": "t", "where": {"eq3": ["id", {"val": "01"}]}},
            "SELECT * FROM t WHERE id = '01'",
        ),
        ({"op": "project", "from": "t", "columns": ["x"]}, "SELECT x FROM t"),
        (
            {"op": "rename", "from": {"op": "select", "from": "t"}, "map": {"id": "newid"}},
            "SELECT id AS newid, x FROM t",
        ),
        (
            {
                "op": "join",
                "type": "left",
                "left": "t",
                "right": "r",
                "on": {"eq3": ["t.id", "r.rid"]},
            },
            "SELECT * FROM t LEFT JOIN r ON t.id = r.rid",
        ),
        (
            {
                "op": "anti_join",
                "match": "sql_not_in",
                "left": "t",
                "right": "r",
                "on": {"eq3": ["t.id", "r.rid"]},
            },
            "SELECT * FROM t WHERE id NOT IN (SELECT rid FROM r)",
        ),
        (
            {
                "op": "semi_join",
                "left": "t",
                "right": "r",
                "on": {"not_distinct": ["t.id", "r.rid"]},
            },
            "SELECT * FROM t WHERE EXISTS (SELECT 1 FROM r WHERE t.id IS NOT DISTINCT FROM r.rid)",
        ),
        (
            {
                "op": "group",
                "from": "t",
                "by": ["x"],
                "agg": {"n": {"func": "count_star"}, "s": {"func": "sum", "arg": "id"}},
            },
            "SELECT x, COUNT(*) AS n, SUM(id) AS s FROM t GROUP BY x",
        ),
        (
            {
                "op": "union_all",
                "left": {"op": "project", "from": "t", "columns": ["id"]},
                "right": {"op": "project", "from": "r", "columns": ["rid"]},
            },
            "SELECT id FROM t UNION ALL SELECT rid FROM r",
        ),
        ({"op": "distinct", "from": "t"}, "SELECT DISTINCT * FROM t"),
    ],
)
@pytest.mark.parametrize("right", [[], [{"rid": 1, "value": "v"}], [{"rid": None, "value": "v"}]])
def test_all_relational_operators_against_separately_written_sql(spec, sql, right):
    case, answer = case_and_answer()
    case.update(
        schema={"t": {"id": "INTEGER", "x": "TEXT"}, "r": {"rid": "INTEGER", "value": "TEXT"}},
        spec=spec,
        test_databases=[
            {"t": [{"id": 1, "x": "01"}, {"id": None, "x": None}, {"id": 1, "x": "01"}], "r": right}
        ],
    )
    assert verify_candidate(case, dict(answer, sql=sql))[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT 999 AS wrong"))[0]


@pytest.mark.parametrize(("kind", "value", "literal"), [("INTEGER", 1, "01"), ("TEXT", "1", 1)])
def test_views_preserve_column_affinity(kind, value, literal):
    case, answer = case_and_answer()
    case.update(
        schema={"t": {"id": kind}},
        spec={"op": "select", "from": "t", "where": {"eq3": ["id", {"val": literal}]}},
        test_databases=[{"t": [{"id": value}]}],
    )
    sql_literal = repr(literal)
    assert verify_candidate(case, dict(answer, sql=f"SELECT id FROM t WHERE id = {sql_literal}"))[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT id FROM t WHERE 0"))[0]


def test_candidate_cannot_read_oracle_staging():
    case, answer = case_and_answer()
    assert verify_candidate(case, answer)[0]
    ok, reason = verify_candidate(case, dict(answer, sql="SELECT c0 AS id FROM __c059_node_1"))
    assert not ok and "no such table" in reason


def test_not_in_unqualified_keys_bind_to_their_respective_operands():
    case, answer = case_and_answer()
    case.update(
        schema={"l": {"id": "INTEGER"}, "r": {"id": "INTEGER"}},
        spec={
            "op": "anti_join",
            "match": "sql_not_in",
            "left": "l",
            "right": "r",
            "on": {"eq3": ["id", "id"]},
        },
        test_databases=[{"l": [{"id": 1}, {"id": 2}], "r": [{"id": 2}]}],
    )
    assert verify_candidate(
        case, dict(answer, sql="SELECT * FROM l WHERE id NOT IN (SELECT id FROM r)")
    )[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT * FROM l WHERE 0"))[0]


def test_oracle_corruption_changes_only_first_judge(monkeypatch):
    case, answer = case_and_answer()
    assert verify_candidate(case, answer)[0] and independent_check(case, answer)[0]
    monkeypatch.setattr(
        SQLiteRelationalOracle, "read", lambda *args: (frozenset({"id"}), [{"id": 99}])
    )
    assert not verify_candidate(case, answer)[0]
    assert independent_check(case, answer)[0]


def test_not_negates_the_entire_multi_key_predicate():
    case, answer = case_and_answer()
    case.update(
        schema={"t": {"id": "INTEGER", "x": "INTEGER"}},
        spec={
            "op": "select",
            "from": "t",
            "where": {"not": {"eq3": ["id", {"val": 1}], "is_null": "x"}},
        },
        test_databases=[{"t": [{"id": 1, "x": 5}]}],
    )
    assert verify_candidate(
        case, dict(answer, sql="SELECT * FROM t WHERE NOT (id=1 AND x IS NULL)")
    )[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT * FROM t WHERE 0"))[0]


def test_column_discriminant_keeps_existing_priority_over_literal():
    case, answer = case_and_answer()
    case["spec"]["where"] = {"eq3": [{"col": "id", "val": 99}, {"val": 1}]}
    assert verify_candidate(case, dict(answer, sql="SELECT id FROM t WHERE id=1"))[0]
    assert not verify_candidate(case, dict(answer, sql="SELECT id FROM t WHERE 0"))[0]
