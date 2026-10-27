"""Commuting Pauli Hamiltonian ground-state capsule: reference answers pass both checkers.

Every case in judge_packet/cases (base, controls, poisoned) is solved by the
reference solver, and the dual evaluator must accept the answer: both
independent checkers agree and the verdict is PASS. The companion mutation
suite in judge_packet/mutation_suite checks the opposite direction (every
corrupted certificate is rejected).

Standard library plus pytest. Run from the repository root:

    python -m pytest demos/certified_challenges -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c021_q40_r.judge_packet.checkers.dual_evaluator import assert_dual_agreement
from c021_q40_r.reference_solver.solver import solve

CASES_DIR = Path(__file__).resolve().parent / "c021_q40_r" / "judge_packet" / "cases"
CASE_FILES = sorted(CASES_DIR.rglob("*.json"))


def test_case_inventory() -> None:
    counts = {d.name: len(list(d.glob("*.json"))) for d in CASES_DIR.iterdir() if d.is_dir()}
    assert counts == {'base': 30, 'controls': 8, 'poisoned': 6}


@pytest.mark.parametrize("case_path", CASE_FILES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_reference_answer_passes_both_checkers(case_path: Path) -> None:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    result = solve(case)
    assert result.get("status") in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}
    verdict = assert_dual_agreement(case, result)["verdict"]
    assert verdict == "PASS", f"{case_path.name}: verdict {verdict}"
