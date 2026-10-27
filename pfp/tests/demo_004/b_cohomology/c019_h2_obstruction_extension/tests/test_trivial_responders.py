"""C019 judge: the second checker verifies mode Z witnesses and strict types.

Before the 2026-09-28 correction the second checker accepted any mode Z answer
whose verdict was EXTENDS_INTEGRAL or OBSTRUCTED_INTEGRAL, whatever its witness,
and first-checker `int()` casts accepted floats; a float or Boolean in place of an
integer passed on 12 and 28 judge cases respectively.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.judge_packet.checkers.independent_checker import (
    check_independent_h2,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.reference_solver.solver import (
    solve,
)

CASES_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases"
JUDGE_CASES = sorted(CASES_DIR.glob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _mode_z_case() -> dict:
    return next(_load(p) for p in JUDGE_CASES if _load(p).get("mode") == "Z")


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 40


def test_reference_answers_pass_every_judge_case() -> None:
    failures = [p.name for p in JUDGE_CASES if not evaluate_dual(_load(p), solve(_load(p))[0])[0]]
    assert failures == []


@pytest.mark.parametrize(
    "answer",
    [
        {"status": "SOLVED", "mode": "Z", "verdict": "EXTENDS_INTEGRAL", "A": {}},
        {
            "status": "SOLVED",
            "mode": "Z",
            "verdict": "OBSTRUCTED_INTEGRAL",
            "modulus": "2",
            "chain": {},
            "pairing_mod": "1",
        },
    ],
    ids=["extends_with_empty_potential", "obstructed_with_empty_chain"],
)
def test_second_checker_rejects_mode_z_shape_only_answers(answer: dict) -> None:
    """Counterexample: checker 2 returned True for any mode Z verdict string."""
    case = _mode_z_case()
    assert check_independent_h2(case, {"id": case["id"], **answer})[0] is False


def test_second_checker_accepts_the_reference_mode_z_witness() -> None:
    case = _mode_z_case()
    ref, _ = solve(case)
    assert check_independent_h2(case, ref)[0] is True


@pytest.mark.parametrize("field", ["modulus", "pairing_mod"])
@pytest.mark.parametrize("bad", [2.0, True], ids=["float", "boolean"])
def test_float_or_boolean_integer_fields_are_rejected(field: str, bad: object) -> None:
    case = _mode_z_case()
    ref, _ = solve(case)
    if field == "pairing_mod" and bad is True and ref["pairing_mod"] == "1":
        bad = 1.0
    assert evaluate_dual(case, {**ref, field: bad})[0] is False


def test_float_chain_entry_is_rejected() -> None:
    case = _mode_z_case()
    ref, _ = solve(case)
    chain = dict(ref["chain"])
    key = next(iter(chain))
    chain[key] = float(chain[key])
    assert evaluate_dual(case, {**ref, "chain": chain})[0] is False


def test_boolean_phi2_in_mode_q_is_rejected() -> None:
    case = next(_load(p) for p in JUDGE_CASES if p.name.startswith("base_q_extends_"))
    ref, _ = solve(case)
    assert ref["phi2"] == "0"
    assert evaluate_dual(case, {**ref, "phi2": False})[0] is False


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"},
        {"status": "OUT_OF_SCOPE", "witness": {"reason": "BOUNDARY_NOT_NILPOTENT"}},
    ],
    ids=["empty_object", "refusal", "false_out_of_scope"],
)
def test_trivial_responders_fail_on_every_nilpotent_case(answer: dict) -> None:
    in_scope = [p for p in JUDGE_CASES if not p.name.startswith("poison_non_nilpotent")]
    passes = [
        p.name for p in in_scope if evaluate_dual(_load(p), {"id": _load(p)["id"], **answer})[0]
    ]
    assert passes == []
