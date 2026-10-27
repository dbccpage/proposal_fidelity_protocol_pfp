"""C016 second checker: strict rank types, no reference imports, verified refusals.

Before the 2026-09-28 correction both checkers read ranks with `int()`, so a rank
of 1.9 or True was accepted as 1; the second checker imported the reference
solver's cohomology code.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.independent_checker import (
    check_independent_cup_products,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
    solve,
)

CHECKERS_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parent
JUDGE_CASES = sorted((CHECKERS_DIR.parent / "cases").rglob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _distinguished() -> tuple[dict, dict]:
    for path in JUDGE_CASES:
        case = _load(path)
        ref, _ = solve(case)
        if ref.get("verdict") == "DISTINGUISHED" and ref["X"]["rank"] == "1":
            return case, ref
    raise AssertionError("no DISTINGUISHED judge case with rank_X = 1")


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 30


@pytest.mark.parametrize(
    "bad_rank", [1.9, 1.0, True], ids=["float_1_9", "float_1_0", "boolean_true"]
)
def test_non_integer_rank_is_rejected(bad_rank: object) -> None:
    """Counterexample: rank 1.9 passed through int() as 1."""
    case, ref = _distinguished()
    assert evaluate_dual(case, ref)[0] is True
    bad = json.loads(json.dumps(ref))
    bad["X"]["rank"] = bad_rank
    assert check_independent_cup_products(case, bad)[0] is False
    assert evaluate_dual(case, bad)[0] is False


def test_second_checker_agrees_with_reference_on_every_judge_case() -> None:
    failures = [
        p.name
        for p in JUDGE_CASES
        if not check_independent_cup_products(_load(p), solve(_load(p))[0])[0]
    ]
    assert failures == []


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "UNKNOWN", "refusal": "INVALID_DEGREES", "refusal_code": "INVALID_DEGREES"},
        {"status": "SOLVED", "verdict": "DISTINGUISHED", "X": {"rank": "1"}, "Y": {"rank": "0"}},
    ],
    ids=["empty_object", "refusal_on_valid_degrees", "constant_distinguished"],
)
def test_trivial_responders_fail_the_second_checker_on_in_scope_cases(answer: dict) -> None:
    passes = []
    for path in JUDGE_CASES:
        case = _load(path)
        ref, _ = solve(case)
        if ref.get("status") == "UNKNOWN":
            continue
        same = (
            ref.get("status") == "SOLVED"
            and all(ref[k]["rank"] == answer.get(k, {}).get("rank") for k in ("X", "Y"))
            and ref.get("verdict") == answer.get("verdict")
        )
        if not same and check_independent_cup_products(case, {"id": case["id"], **answer})[0]:
            passes.append(path.name)
    assert passes == []


def test_second_checker_does_not_import_the_reference_solver() -> None:
    tree = ast.parse((CHECKERS_DIR / "independent_checker.py").read_text(encoding="utf-8"))
    modules = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any("reference_solver" in m for m in modules)
