"""C047 second checker: empty, all-zero and vacuous certificates must fail.

Counterexamples named by these tests (all passed the old independent checker):
- {"status": "SOLVED", "kind": "RECURRENCE", "polys": []} (no residual equation is checked);
- {"status": "SOLVED", "kind": "NONE_WITHIN_BOUNDS", "minor_rows": []} (the empty determinant is 1);
- an all-zero recurrence, and the empty object with a mismatched case ID.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c047_sequence_law_discovery.judge_packet.independent_checker import (
    independent_check,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "participant_packet" / "examples"


def _example(name: str) -> tuple[dict, dict]:
    data = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    return data["input"], data["expected"]


FIB_CASE, FIB_ANSWER = _example("ex_01_fibonacci.json")
DECOY_CASE, DECOY_ANSWER = _example("ex_07_pseudo_random_decoy.json")


def _answer(case: dict, **fields: object) -> dict:
    return {"case_id": case["case_id"], "status": "SOLVED", **fields}


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"case_id": FIB_CASE["case_id"]},
        {"case_id": FIB_CASE["case_id"], "status": "UNKNOWN"},
        _answer(FIB_CASE, kind="RECURRENCE", polys=[]),
        _answer(FIB_CASE, kind="RECURRENCE"),
        _answer(FIB_CASE, kind="RECURRENCE", polys=[["0"], ["0"], ["0"]]),
        _answer(FIB_CASE, kind="RECURRENCE", polys=[["1"], ["0"]]),
        _answer(FIB_CASE, kind="RECURRENCE", polys=[[-1], [-1], [1]]),
        _answer(FIB_CASE, kind="RECURRENCE", polys=[["-1"], ["-1"], ["1"]], start=True),
        _answer(FIB_CASE, kind="NONE_WITHIN_BOUNDS", order=2, degree=0, minor_rows=[]),
        _answer(FIB_CASE, kind="NONE_WITHIN_BOUNDS", order=2, degree=0, minor_rows=[0]),
    ],
    ids=[
        "empty",
        "id_only",
        "unknown",
        "empty_polys",
        "no_polys",
        "all_zero",
        "order0_leading_zero",
        "int_coeffs",
        "bool_start",
        "empty_minor",
        "short_minor",
    ],
)
def test_trivial_certificates_rejected(answer: dict) -> None:
    ok, msg = independent_check(FIB_CASE, answer)
    assert ok is False, msg


def test_reference_certificates_accepted() -> None:
    assert independent_check(FIB_CASE, FIB_ANSWER)[0] is True
    assert independent_check(DECOY_CASE, DECOY_ANSWER)[0] is True


def test_duplicate_minor_rows_rejected() -> None:
    rows = DECOY_ANSWER["minor_rows"]
    forged = dict(DECOY_ANSWER, minor_rows=[rows[0]] * len(rows))
    ok, msg = independent_check(DECOY_CASE, forged)
    assert ok is False, msg


def test_float_term_is_not_an_integer_term() -> None:
    case = {"case_id": "f", "terms": ["1", 2.5, "3"], "r_max": 1, "d_max": 0}
    ok, _ = independent_check(
        case,
        {
            "case_id": "f",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "NON_INTEGER_TERM", "index": 1},
        },
    )
    assert ok is True
    ok, _ = independent_check(
        case,
        {
            "case_id": "f",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "NON_INTEGER_TERM", "index": 0},
        },
    )
    assert ok is False
