# AuthorityEffect: None.
"""Trivial responders must fail the C030 judge; verified refusals must pass.

Before the 2026-09-28 correction an UNKNOWN / BOUND_NOT_MET answer was accepted
without any check for every network with N > 12, so the constant refusal passed
on 28 of 46 judge cases. The rule now: N <= 12 needs the judge's exact optimum
to exceed the bounds (or a valid witness); N > 12 needs an open-leg witness.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c030_tensor_network_contraction_order.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c030_tensor_network_contraction_order.reference_solver.solver import (
    solve,
)

CASES_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases"
JUDGE_CASES = sorted(CASES_DIR.glob("*.json"))
REFUSAL = {"status": "UNKNOWN", "refusal_code": "BOUND_NOT_MET"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _n(case: dict) -> int:
    return len(case["tensors"]) if isinstance(case.get("tensors"), dict) else -1


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 40


def test_constant_bound_not_met_fails_on_every_large_network() -> None:
    """Counterexample: the constant UNKNOWN/BOUND_NOT_MET passed on all 24 cases with N > 12."""
    large = [p for p in JUDGE_CASES if _n(_load(p)) > 12 and _n(_load(p)) <= 30]
    assert large
    passes = [
        p.name for p in large if evaluate_dual(_load(p), {"id": _load(p)["case_id"], **REFUSAL})[0]
    ]
    assert passes == []


def test_constant_bound_not_met_passes_only_where_the_optimum_exceeds_the_bound() -> None:
    passes = sorted(
        p.name
        for p in JUDGE_CASES
        if evaluate_dual(_load(p), {"id": _load(p)["case_id"], **REFUSAL})[0]
    )
    for name in passes:
        case = _load(CASES_DIR / name)
        assert _n(case) <= 12, name
        assert solve(case)["status"] == "UNKNOWN", name


def test_reference_answers_pass_every_judge_case() -> None:
    failures = [p.name for p in JUDGE_CASES if not evaluate_dual(_load(p), solve(_load(p)))[0]]
    assert failures == []


@pytest.mark.parametrize(
    "witness",
    [
        {"kind": "open_legs_exceed_size_bound", "open_size": "1"},
        {"kind": "open_legs_exceed_cost_bound", "open_size": "32768"},
        {"kind": "search_exhausted", "open_size": "32768"},
        {"kind": "open_legs_exceed_size_bound", "open_size": 32768},
    ],
    ids=["wrong_open_size", "cost_bound_not_exceeded", "unknown_kind", "integer_not_string"],
)
def test_invalid_witnesses_are_rejected(witness: dict) -> None:
    case = _load(next(p for p in JUDGE_CASES if p.name.startswith("c030_base_24_")))
    good = solve(case)
    assert good["witness"] == {"kind": "open_legs_exceed_size_bound", "open_size": "32768"}
    assert evaluate_dual(case, good)[0] is True
    assert evaluate_dual(case, {**good, "witness": witness})[0] is False


def test_valid_witness_on_a_feasible_case_is_impossible() -> None:
    """A size witness cannot pass where the open-leg product fits the bound."""
    case = _load(next(p for p in JUDGE_CASES if p.name.startswith("c030_base_13_")))
    answer = {
        "id": case["case_id"],
        **REFUSAL,
        "witness": {"kind": "open_legs_exceed_cost_bound", "open_size": "16384"},
    }
    assert evaluate_dual(case, answer)[0] is False


@pytest.mark.parametrize(
    "answer",
    [{}, {"status": "SOLVED"}, {"status": "OUT_OF_SCOPE", "witness": {}}],
    ids=["empty_object", "bare_solved", "oos_empty_witness"],
)
def test_constant_responders_fail_on_every_valid_network(answer: dict) -> None:
    valid = [p for p in JUDGE_CASES if not p.name.startswith("c030_poison_")]
    passes = [
        p.name for p in valid if evaluate_dual(_load(p), {"id": _load(p)["case_id"], **answer})[0]
    ]
    assert passes == []


def test_float_and_boolean_costs_are_rejected() -> None:
    case = _load(next(p for p in JUDGE_CASES if p.name.startswith("c030_base_01_")))
    good = solve(case)
    assert evaluate_dual(case, good)[0] is True
    assert evaluate_dual(case, {**good, "total_cost": float(good["total_cost"])})[0] is False
    assert evaluate_dual(case, {**good, "total_cost": int(good["total_cost"])})[0] is False
    assert evaluate_dual(case, {**good, "optimal": 1})[0] is False
