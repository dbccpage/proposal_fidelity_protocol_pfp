"""C054 judge corrections: typed rejections instead of checker exceptions.

Counterexamples from the 2026-09-28 audit:

- a JSON-array reply crashed the exact checker (``AttributeError``) and aborted
  the whole model sweep;
- ``rank_rows: ["0"]`` crashed the exact checker (``TypeError`` comparing str and int);
- both checkers accepted the non-canonical strings "4/1" and "0/1";
- the independent checker accepted any SOLVED reply on the 0 x 0 system.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c054_exact_linear_systems.judge_packet import (
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
JUDGE_DIR = PACKAGE_DIR / "judge_packet"
CHECKERS = (
    ("exact", exact_checker.check_exact),
    ("independent", independent_checker.independent_check),
)
CASES = [
    json.loads(p.read_text(encoding="utf-8")) for p in sorted((JUDGE_DIR / "cases").glob("*.json"))
]
CASE = {"case_id": "t", "A": [["1", "0"], ["0", "0"]], "b": ["4", "0"]}
GOOD = {
    "case_id": "t",
    "status": "SOLVED",
    "kind": "CONSISTENT",
    "x": ["4", "0"],
    "rank": 1,
    "rank_rows": [0],
    "rank_cols": [0],
    "null_basis": [["0", "1"]],
    "null_rows": [1],
}


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_valid_certificate_is_accepted(name, checker):
    ok, msg = checker(CASE, GOOD)
    assert ok is True, (name, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("reply", [[], [GOOD], "CONSISTENT", 7, None])
def test_non_object_reply_is_a_typed_rejection(name, checker, reply):
    ok, msg = checker(CASE, reply)
    assert ok is False and isinstance(msg, str), (name, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize(
    "field,value",
    [
        ("rank_rows", ["0"]),
        ("rank_rows", [True]),
        ("rank_rows", [0.0]),
        ("rank_cols", ["0"]),
        ("rank_cols", [False]),
        ("null_rows", ["1"]),
        ("null_rows", [True]),
        ("null_rows", [1.0]),
    ],
)
def test_non_integer_index_lists_are_typed_rejections(name, checker, field, value):
    ok, msg = checker(CASE, {**GOOD, field: value})
    assert ok is False and isinstance(msg, str), (name, field, value, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize(
    "field,value",
    [
        ("x", ["4/1", "0"]),
        ("x", ["4", "0/1"]),
        ("x", [" 4", "0"]),
        ("x", [4, 0]),
        ("x", ["4.0", "0"]),
        ("null_basis", [["0", "1/1"]]),
    ],
)
def test_non_canonical_entries_are_rejected(name, checker, field, value):
    ok, msg = checker(CASE, {**GOOD, field: value})
    assert ok is False, (name, field, value, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_empty_system_requires_a_real_certificate(name, checker):
    case = next(c for c in CASES if c["case_id"] == "c054_b31_edge_empty_0x0")
    cid = case["case_id"]
    assert checker(case, {"case_id": cid, "status": "SOLVED"})[0] is False, name
    full = {
        "case_id": cid,
        "status": "SOLVED",
        "kind": "CONSISTENT",
        "x": [],
        "rank": 0,
        "rank_rows": [],
        "rank_cols": [],
        "null_basis": [],
        "null_rows": [],
    }
    assert checker(case, full)[0] is True, name


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_trivial_responders_fail_on_every_in_scope_case(name, checker):
    in_scope = [
        c
        for c in CASES
        if checker(
            c, {"case_id": c["case_id"], "status": "OUT_OF_SCOPE", "witness": {"reason": "X"}}
        )[0]
        is False
    ]
    assert len(in_scope) == 52
    for case in in_scope:
        cid = case["case_id"]
        for answer in (
            {},
            [],
            {"case_id": cid, "status": "UNKNOWN"},
            {"case_id": cid, "status": "SOLVED"},
            {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "INCONSISTENT",
                "y": ["0"] * len(case["A"]),
            },
        ):
            assert checker(case, answer)[0] is False, (name, cid)


def test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers():
    from c054_exact_linear_systems.reference_solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, case["case_id"])
    mutations = sorted((JUDGE_DIR / "hostile_mutations").glob("*.json"))
    assert len(mutations) == 48
    for path in mutations:
        mutation = json.loads(path.read_text(encoding="utf-8"))
        bad = mutation.get("mutated_result", mutation.get("corrupted_result"))
        for name, checker in CHECKERS:
            assert checker(mutation["case"], bad)[0] is False, (name, path.name)
