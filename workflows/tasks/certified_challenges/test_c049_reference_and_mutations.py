"""Finite-category universal constructions: two independent checkers, both directions.

1. Every case in judge_packet/cases (products, equalizers, pullbacks and their
   duals in small finite categories, plus malformed inputs) is solved by the
   reference solver. Both the exact checker and the independent checker must
   accept the answer.
2. Every hostile mutation in judge_packet/hostile_mutations (a false
   "does not exist", a cone that does not commute, a non-unique mediating
   morphism, a false OUT_OF_SCOPE, ...) must be rejected by the exact checker.
   The independent checker is weaker: it checks shape and status but accepts
   most false refusals and some forged constructions, so that test is xfail.

Standard library plus pytest. Run from the repository root:

    python -m pytest demos/certified_challenges -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c049_finite_category_universal_constructions.judge_packet.exact_checker import check_solution
from c049_finite_category_universal_constructions.judge_packet.independent_checker import independent_check
from c049_finite_category_universal_constructions.reference_solver.solver import solve

PACKET = Path(__file__).resolve().parent / "c049_finite_category_universal_constructions" / "judge_packet"
CASE_FILES = sorted((PACKET / "cases").glob("*.json"))
MUTATION_FILES = sorted((PACKET / "hostile_mutations").glob("*.json"))


def test_inventory() -> None:
    assert len(CASE_FILES) == 64
    assert len(MUTATION_FILES) == 48


@pytest.mark.parametrize("case_path", CASE_FILES, ids=lambda p: p.stem)
def test_reference_answer_passes_both_checkers(case_path: Path) -> None:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    result = solve(case)
    ok1, msg1 = check_solution(case, result)
    ok2, msg2 = independent_check(case, result)
    assert ok1, f"exact checker rejected {case_path.name}: {msg1}"
    assert ok2, f"independent checker rejected {case_path.name}: {msg2}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_hostile_mutation_rejected_by_exact_checker(mut_path: Path) -> None:
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    ok, msg = check_solution(data["case"], data["candidate"])
    assert not ok, f"exact checker accepted {mut_path.name}: {msg}"


@pytest.mark.xfail(reason="C049's independent checker does not re-derive limits; it accepts 31 of 48 mutations")
def test_independent_checker_rejects_every_mutation() -> None:
    accepted = []
    for mut_path in MUTATION_FILES:
        data = json.loads(mut_path.read_text(encoding="utf-8"))
        if independent_check(data["case"], data["candidate"])[0]:
            accepted.append(mut_path.stem)
    assert not accepted, f"independent checker accepted {len(accepted)} mutations"
