"""C048 second checker: OUT_OF_SCOPE and trivial responders must not pass on integer forms.

Counterexample named by this test: the old independent checker returned True for any
{"status": "OUT_OF_SCOPE"}, so a refuse-all responder agreed with it on every case; it also
accepted a composite "prime" place and crashed on a non-integer coefficient.
"""

from __future__ import annotations

import pytest
from pfp.tests.demo_004.e_formal_math.c048_ternary_quadratic_forms.judge_packet.independent_checker import (
    independent_check,
)

CASE = {"case_id": "k", "a": 1, "b": 1, "c": -2}  # x^2 + y^2 - 2 z^2 = 0 has (1, 1, 1)
OBSTRUCTED = {"case_id": "o", "a": 1, "b": 1, "c": -3}  # obstructed at 3


@pytest.mark.parametrize(
    "answer",
    [
        {"case_id": "k", "status": "OUT_OF_SCOPE"},
        {
            "case_id": "k",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "NON_INTEGER_COEFFICIENT"},
        },
        {},
        {"case_id": "k"},
        {"case_id": "k", "status": "UNKNOWN"},
        {
            "case_id": "k",
            "status": "SOLVED",
            "kind": "RATIONAL_POINT",
            "x": "0",
            "y": "0",
            "z": "0",
        },
        {
            "case_id": "k",
            "status": "SOLVED",
            "kind": "RATIONAL_POINT",
            "x": True,
            "y": "1",
            "z": "1",
        },
        {
            "case_id": "k",
            "status": "SOLVED",
            "kind": "RATIONAL_POINT",
            "x": "1.0",
            "y": "1",
            "z": "1",
        },
    ],
    ids=[
        "oos_bare",
        "oos_witness",
        "empty",
        "id_only",
        "unknown",
        "zero_point",
        "bool_coord",
        "float_coord",
    ],
)
def test_trivial_responders_rejected_on_integer_form(answer: dict) -> None:
    ok, msg = independent_check(CASE, answer)
    assert ok is False, msg


def test_valid_point_accepted() -> None:
    ok, msg = independent_check(
        CASE,
        {
            "case_id": "k",
            "status": "SOLVED",
            "kind": "RATIONAL_POINT",
            "x": "1",
            "y": "1",
            "z": "1",
        },
    )
    assert ok is True, msg


def test_out_of_scope_accepted_only_with_non_integer_coefficient() -> None:
    case = {"case_id": "n", "a": "1.5", "b": 1, "c": -2}
    assert independent_check(case, {"case_id": "n", "status": "OUT_OF_SCOPE"})[0] is True
    assert (
        independent_check(
            case,
            {
                "case_id": "n",
                "status": "SOLVED",
                "kind": "RATIONAL_POINT",
                "x": "1",
                "y": "1",
                "z": "1",
            },
        )[0]
        is False
    )


def test_composite_place_rejected() -> None:
    assert (
        independent_check(
            OBSTRUCTED,
            {"case_id": "o", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": "3"},
        )[0]
        is True
    )
    assert (
        independent_check(
            OBSTRUCTED,
            {"case_id": "o", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": "9"},
        )[0]
        is False
    )
