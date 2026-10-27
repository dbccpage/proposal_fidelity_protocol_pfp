"""C045 second checker: trivial responders must fail and every value is recomputed.

Counterexamples named by these tests (all passed the old independent checker):
- the empty object {};
- a refuse-all responder {"status": "REFUSED", "reason": "NON_PLANAR", "witness": {}} on a
  valid diagram;
- an "unknot for everything" answer (bracket A^(-3w) (-1)^w, Jones 1, Alexander 1) with the
  correct writhe on the trefoil.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.judge_packet.checkers import (
    independent_checker,
)
from pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.judge_packet.checkers.independent_checker import (
    check_independent,
)
from pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.reference_solver.solver import (
    solve,
)

PKG = Path(__file__).resolve().parent.parent
HIDDEN = json.loads(
    next((PKG / "judge_packet" / "hidden_cases").glob("*.json")).read_text(encoding="utf-8")
)
TREFOIL = [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]
FIGURE_EIGHT = [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]]


def test_known_invariants_recomputed_without_reference() -> None:
    invariants = independent_checker._invariants
    right_trefoil = invariants(TREFOIL)
    assert right_trefoil["writhe"] == 3
    assert right_trefoil["jones_polynomial"] == {1: 1, 3: 1, 4: -1}
    assert right_trefoil["alexander_polynomial"] == {-1: 1, 0: -1, 1: 1}
    fig8 = invariants(FIGURE_EIGHT)
    assert fig8["jones_polynomial"] == {-2: 1, -1: -1, 0: 1, 1: -1, 2: 1}
    assert fig8["alexander_polynomial"] == {-1: -1, 0: 3, 1: -1}


@pytest.mark.parametrize("case", HIDDEN, ids=lambda c: c["case_id"])
def test_reference_answers_pass_independent_checker(case: dict) -> None:
    ok, msg = check_independent(case, solve(case))
    assert ok, msg


@pytest.mark.parametrize(
    "case", [c for c in HIDDEN if c.get("category") != "poisoned"], ids=lambda c: c["case_id"]
)
def test_trivial_responders_fail_on_valid_cases(case: dict) -> None:
    cid = case["case_id"]
    responders = [
        {},
        {"case_id": cid},
        {"case_id": cid, "status": "UNKNOWN"},
    ]
    for reason in (
        "NON_PLANAR",
        "EDGE_LABEL_MULTIPLICITY",
        "ORIENTATION_INCONSISTENT",
        "INVALID_CROSSING_COUNT",
        "PD_1_NON_PLANAR",
        "MALFORMED_INPUT",
    ):
        responders.append({"case_id": cid, "status": "REFUSED", "reason": reason, "witness": {}})
    for ans in responders:
        ok, msg = check_independent(case, ans)
        assert ok is False, f"{ans} accepted: {msg}"


def test_constant_unknot_answer_fails_on_trefoil() -> None:
    case = {"case_id": "t", "task": "COMPUTE_POLYNOMIALS", "pd": TREFOIL}
    fake = {
        "case_id": "t",
        "status": "SOLVED",
        "task": "COMPUTE_POLYNOMIALS",
        "writhe": 3,
        "kauffman_bracket": {"9": -1},
        "jones_polynomial": {"0": 1},
        "alexander_polynomial": {"0": 1},
        "identified_knot": "0_1",
    }
    ok, msg = check_independent(case, fake)
    assert ok is False, msg


def test_bool_or_float_coefficients_rejected() -> None:
    case = {"case_id": "t", "task": "COMPUTE_POLYNOMIALS", "pd": TREFOIL}
    good = solve(case)
    for field, bad in (("jones_polynomial", {"1": True, "3": 1, "4": -1}), ("writhe", 3.0)):
        ans = dict(good)
        ans[field] = bad
        ok, msg = check_independent(case, ans)
        assert ok is False, msg


def test_refusal_passes_only_with_matching_problem() -> None:
    bad_pd = [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 9]]
    case = {"case_id": "p", "task": "COMPUTE_POLYNOMIALS", "pd": bad_pd}
    ok, _ = check_independent(
        case,
        {"case_id": "p", "status": "REFUSED", "reason": "EDGE_LABEL_MULTIPLICITY", "witness": {}},
    )
    assert ok is True
    ok, _ = check_independent(
        case, {"case_id": "p", "status": "REFUSED", "reason": "NON_PLANAR", "witness": {}}
    )
    assert ok is False
