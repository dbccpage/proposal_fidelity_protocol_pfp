"""C043: an UNKNOWN refusal is an abstention and must never count as a verified answer.

Counterexample named by this test: the refuse-all responder
{"status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"} passed both checkers on every case,
so abstaining scored the same as a certified construction.
"""

import json
from pathlib import Path

import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.independent_checker import (
    check_independent,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.ramsey_vdw_checker import (
    check,
)

EXAMPLES = sorted(
    (Path(__file__).resolve().parent.parent / "participant_packet" / "examples").glob("*.json")
)


def _case(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("case", data)


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
@pytest.mark.parametrize(
    "answer",
    [
        {"status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"},
        {"status": "UNKNOWN"},
        {},
    ],
    ids=["refuse_all", "bare_unknown", "empty_object"],
)
def test_trivial_responders_never_verified(path: Path, answer: dict) -> None:
    case = _case(path)
    assert check(case, answer)[0] is False
    assert check_independent(case, answer)[0] is False
    ok, _msg, receipt = evaluate_dual(case, answer)
    assert ok is False
    assert receipt["abstained"] is (answer.get("status") == "UNKNOWN")
