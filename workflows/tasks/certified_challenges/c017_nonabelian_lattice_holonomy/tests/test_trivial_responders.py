"""C017 judge: orientation-free plaquettes, verified loops, and trivial responders.

Before the 2026-09-28 correction the checkers accepted a plaquette only in one
vertex order (four correct model answers were rejected in retained runs), the
second checker accepted any FLAT_NONTRIVIAL loops without evaluating them, both
checkers rejected the reference's correct refusals on out-of-bounds cases, and
both imported the reference solver's holonomy code.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest
from c017_nonabelian_lattice_holonomy.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c017_nonabelian_lattice_holonomy.judge_packet.checkers.independent_checker import (
    check_independent_holonomy,
)
from c017_nonabelian_lattice_holonomy.reference_solver.solver import (
    solve,
)

CHECKERS_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parent
CASES_DIR = CHECKERS_DIR.parent / "cases"
JUDGE_CASES = sorted(CASES_DIR.rglob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _case(name: str) -> dict:
    return _load(next(p for p in JUDGE_CASES if p.name == name))


def _inverse(case: dict, element: str) -> str:
    return case["group"]["inverses"][element]


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 40


def test_reference_answers_pass_every_judge_case() -> None:
    """Counterexample: the reference's LATTICE_SIZE_OUT_OF_BOUNDS refusal on L = 15 was rejected."""
    failures = [p.name for p in JUDGE_CASES if not evaluate_dual(_load(p), solve(_load(p))[0])[0]]
    assert failures == []


@pytest.mark.parametrize("shift", [1, 2, 3])
def test_rotated_plaquette_start_is_accepted(shift: int) -> None:
    case = _case("base_01.json")
    ref, _ = solve(case)
    plaq = ref["plaquette"][shift:] + ref["plaquette"][:shift]
    loop = plaq + plaq[:1]
    table, edges = case["group"]["table"], case["edges"]
    hol = case["group"]["identity"]
    for u, v in zip(loop, loop[1:]):
        hol = table[hol][edges[f"{u}->{v}"]]
    ok, reason, _ = evaluate_dual(case, {**ref, "plaquette": plaq, "holonomy": hol})
    assert ok, reason


def test_reversed_plaquette_orientation_is_accepted() -> None:
    case = _case("base_01.json")
    ref, _ = solve(case)
    reversed_plaq = [ref["plaquette"][0]] + ref["plaquette"][:0:-1]
    ok, reason, _ = evaluate_dual(
        case, {**ref, "plaquette": reversed_plaq, "holonomy": _inverse(case, ref["holonomy"])}
    )
    assert ok, reason


def test_reversed_plaquette_with_unreversed_holonomy_is_rejected() -> None:
    case = _case("base_01.json")
    ref, _ = solve(case)
    if _inverse(case, ref["holonomy"]) == ref["holonomy"]:
        pytest.skip("holonomy is an involution")
    reversed_plaq = [ref["plaquette"][0]] + ref["plaquette"][:0:-1]
    assert evaluate_dual(case, {**ref, "plaquette": reversed_plaq})[0] is False


def test_second_checker_evaluates_flat_nontrivial_loops() -> None:
    """Counterexample: checker 2 accepted FLAT_NONTRIVIAL with any loops and holonomies."""
    case = _case("base_03.json")
    ref, _ = solve(case)
    assert ref["verdict"] == "FLAT_NONTRIVIAL"
    assert check_independent_holonomy(case, ref)[0] is True
    swapped = {**ref, "hol_a": ref["hol_b"], "hol_b": ref["hol_a"]}
    assert check_independent_holonomy(case, swapped)[0] is False
    bogus_loop = {**ref, "loop_a": ["0,0", "0,1", "0,0"], "hol_a": "e"}
    assert check_independent_holonomy(case, bogus_loop)[0] is False


def test_second_checker_verifies_the_submitted_gauge() -> None:
    case = next(_load(p) for p in JUDGE_CASES if solve(_load(p))[0].get("verdict") == "PURE_GAUGE")
    ref, _ = solve(case)
    assert check_independent_holonomy(case, ref)[0] is True
    wrong = {**ref, "gauge": {v: case["group"]["identity"] for v in ref["gauge"]}}
    if any(e != case["group"]["identity"] for e in case["edges"].values()):
        assert check_independent_holonomy(case, wrong)[0] is False


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {
            "status": "UNKNOWN",
            "refusal": "LATTICE_SIZE_OUT_OF_BOUNDS",
            "refusal_code": "LATTICE_SIZE_OUT_OF_BOUNDS",
        },
        {"status": "UNKNOWN", "refusal": "MALFORMED_INPUT", "refusal_code": "MALFORMED_INPUT"},
        {"status": "SOLVED", "verdict": "PURE_GAUGE", "gauge": {}},
        {"status": "OUT_OF_SCOPE", "witness": {"reason": "INVERSE_MISMATCH", "edge": "0,0->0,1"}},
    ],
    ids=[
        "empty_object",
        "refuse_size",
        "refuse_malformed",
        "constant_pure_gauge",
        "false_inverse_mismatch",
    ],
)
def test_trivial_responders_fail_on_in_scope_cases(answer: dict) -> None:
    in_scope = [p for p in JUDGE_CASES if solve(_load(p))[0].get("status") == "SOLVED"]
    assert len(in_scope) >= 40
    passes = [
        p.name for p in in_scope if evaluate_dual(_load(p), {"id": _load(p)["id"], **answer})[0]
    ]
    assert passes == []


def test_checkers_do_not_import_the_reference_solver() -> None:
    for name in ("algebraic_holonomy_checker.py", "independent_checker.py"):
        tree = ast.parse((CHECKERS_DIR / name).read_text(encoding="utf-8"))
        modules = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not any("reference_solver" in m for m in modules), (name, modules)
