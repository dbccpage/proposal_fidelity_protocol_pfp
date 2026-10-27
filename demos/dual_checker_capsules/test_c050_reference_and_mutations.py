"""Equational theorem proving capsule: two independent checkers, both directions.

1. Every case in judge_packet/cases is solved by the reference solver (a
   rewrite-proof search plus a finite countermodel search). Both the exact
   checker and the independent checker must accept the answer.
2. Every hostile mutation in judge_packet/hostile_mutations (a forged proof
   step, a skipped step, a bad substitution, a countermodel that does not
   refute the goal, a false OUT_OF_SCOPE, ...) must be rejected by both.

Standard library plus pytest. Run from the repository root:

    python -m pytest demos/dual_checker_capsules -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c050_equational_theorem_proving.judge_packet.exact_checker import check_solution
from c050_equational_theorem_proving.judge_packet.independent_checker import independent_check
from c050_equational_theorem_proving.reference_solver.solver import solve

PACKET = Path(__file__).resolve().parent / "c050_equational_theorem_proving" / "judge_packet"
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
def test_hostile_mutation_rejected_by_both_checkers(mut_path: Path) -> None:
    data = json.loads(mut_path.read_text(encoding="utf-8"))
    case, candidate = data["case"], data["candidate"]
    ok1, msg1 = check_solution(case, candidate)
    ok2, msg2 = independent_check(case, candidate)
    assert not ok1, f"exact checker accepted {mut_path.name}: {msg1}"
    assert not ok2, f"independent checker accepted {mut_path.name}: {msg2}"
