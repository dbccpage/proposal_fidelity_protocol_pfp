"""Trivial responders must fail the C014 judge; valid refusals and answers must pass.

Counterexamples named here were accepted by the judge before the 2026-09-28
correction: an UNKNOWN carrying any closed-enum refusal code passed on every
judge case (68 of 68), and floats were accepted as rationals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from c014_discrete_hodge_decomposition.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c014_discrete_hodge_decomposition.reference_solver.solver import (
    CLOSED_REFUSAL_ENUM,
    solve,
)

CASES_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases"
JUDGE_CASES = sorted(CASES_DIR.rglob("*.json"))


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 60


TRIANGLE = {
    "id": "tri",
    "vertices": ["v0", "v1", "v2"],
    "edges": ["e0_1", "e1_2", "e2_0"],
    "faces": [],
    "edge_endpoints": {"e0_1": ["v0", "v1"], "e1_2": ["v1", "v2"], "e2_0": ["v2", "v0"]},
    "face_boundaries": {},
    "flow": {"e0_1": "1", "e1_2": "1", "e2_0": "1"},
    "weights": {"e0_1": "1", "e1_2": "1", "e2_0": "1"},
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("code", sorted(CLOSED_REFUSAL_ENUM))
def test_refuse_all_responder_fails_on_every_in_scope_judge_case(code: str) -> None:
    """Counterexample: {"status": "UNKNOWN", "refusal": <any enum code>} passed 68/68."""
    passes = []
    for path in JUDGE_CASES:
        case = _load(path)
        answer = {"id": case["id"], "status": "UNKNOWN", "refusal": code, "refusal_code": code}
        if evaluate_dual(case, answer)["verdict"] == "PASS":
            passes.append(path.name)
    assert passes == [], f"refuse-all with {code} passed on {passes}"


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "SOLVED"},
        {"status": "OUT_OF_SCOPE", "witness": {}},
        {
            "status": "SOLVED",
            "phi": {},
            "psi": {},
            "h": {},
            "harmonic_dim": "0",
            "harmonic_basis": [],
        },
    ],
    ids=["empty_object", "bare_solved", "oos_empty_witness", "constant_zero_decomposition"],
)
def test_constant_responders_fail_on_every_judge_case(answer: dict) -> None:
    passes = [
        p.name for p in JUDGE_CASES if evaluate_dual(_load(p), dict(answer))["verdict"] == "PASS"
    ]
    assert passes == [], f"constant responder passed on {passes}"


def test_reference_answers_still_pass_every_judge_case() -> None:
    failures = []
    for path in JUDGE_CASES:
        case = _load(path)
        if evaluate_dual(case, solve(case))["verdict"] != "PASS":
            failures.append(path.name)
    assert failures == []


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda c: c.update(vertices=[f"v{i}" for i in range(81)]), "VERTEX_COUNT_OUT_OF_BOUNDS"),
        (lambda c: c["flow"].update(e0_1="1000"), "COEFFICIENT_BOUND_EXCEEDED"),
        (lambda c: c["weights"].update(e0_1="0"), "WEIGHT_NON_POSITIVE"),
        (lambda c: c["weights"].update(e0_1="1/13"), "WEIGHT_DENOMINATOR_EXCEEDED"),
        (lambda c: c.update(edges="not-a-list"), "MALFORMED_INPUT"),
    ],
)
def test_refusal_whose_condition_holds_is_accepted(mutation, code: str) -> None:
    case = json.loads(json.dumps(TRIANGLE))
    mutation(case)
    answer = {"id": "tri", "status": "UNKNOWN", "refusal": code, "refusal_code": code}
    assert evaluate_dual(case, answer)["verdict"] == "PASS"


def test_budget_exhausted_is_never_accepted() -> None:
    """BUDGET_EXHAUSTED has no checkable witness; every in-bounds case is decidable."""
    answer = {"id": "tri", "status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
    assert evaluate_dual(TRIANGLE, answer)["verdict"] == "FAIL"


def test_refusal_fields_must_agree() -> None:
    case = json.loads(json.dumps(TRIANGLE))
    case["weights"]["e0_1"] = "0"
    answer = {
        "id": "tri",
        "status": "UNKNOWN",
        "refusal": "WEIGHT_NON_POSITIVE",
        "refusal_code": "MALFORMED_INPUT",
    }
    assert evaluate_dual(case, answer)["verdict"] == "FAIL"


def test_float_rational_is_rejected() -> None:
    """Counterexample: a float 1/3 was accepted through limit_denominator."""
    good = solve(TRIANGLE)
    assert evaluate_dual(TRIANGLE, good)["verdict"] == "PASS"
    bad = json.loads(json.dumps(good))
    bad["h"] = {"e0_1": 1.0, "e1_2": 1.0, "e2_0": 1.0}
    assert evaluate_dual(TRIANGLE, bad)["verdict"] == "FAIL"


def test_boolean_harmonic_dim_is_rejected() -> None:
    bad = json.loads(json.dumps(solve(TRIANGLE)))
    bad["harmonic_dim"] = True
    assert evaluate_dual(TRIANGLE, bad)["verdict"] == "FAIL"


def test_non_canonical_rational_string_is_rejected() -> None:
    bad = json.loads(json.dumps(solve(TRIANGLE)))
    bad["h"] = {"e0_1": "2/2", "e1_2": "1", "e2_0": "1"}
    assert evaluate_dual(TRIANGLE, bad)["verdict"] == "FAIL"


def test_task_states_the_canonical_rational_rule_the_checker_enforces() -> None:
    """Review of e6fbc15cf: case_model rejects "2/2" and "-0", but C014's TASK.md did
    not say so; the rule appeared only in the theme-level b_cohomology/TASK.md."""
    task = " ".join(
        (
            Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[2]
            / "participant_packet"
            / "TASK.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )
    for phrase in (
        'no trailing `"/1"`',
        "lowest terms",
        "denominator $> 1$",
        '`"-0"`',
        "Binary floating point",
    ):
        assert phrase in task, phrase
    good = solve(TRIANGLE)
    assert (
        evaluate_dual(TRIANGLE, {**good, "h": {"e0_1": "1", "e1_2": "1", "e2_0": "1/1"}})["verdict"]
        == "FAIL"
    )
    assert (
        evaluate_dual(TRIANGLE, {**good, "h": {"e0_1": "1", "e1_2": "1", "e2_0": "1"}})["verdict"]
        == "PASS"
    )
