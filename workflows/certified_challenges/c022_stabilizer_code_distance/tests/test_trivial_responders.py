"""C022 judge: independent distance verification and trivial responders.

Before the 2026-09-28 correction checker 1 compared every answer with the
reference solver's output, including byte equality with a one-line synthetic
"LRAT" proof, so a correct certificate with a different minimum-weight logical
operator, or with any other proof bytes, was rejected. The judge now verifies the
distance itself by enumerating all Pauli operators below the claimed weight.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from c022_stabilizer_code_distance.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c022_stabilizer_code_distance.reference_solver.solver import (
    solve,
)

CASES_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases"
JUDGE_CASES = sorted(CASES_DIR.glob("*.json"))
FIVE_QUBIT = {"id": "five", "num_qubits": 5, "generators": ["+XZZXI", "+IXZZX", "+XIXZZ", "+ZXIXZ"]}
SHOR = {
    "id": "shor",
    "num_qubits": 9,
    "generators": [
        "+ZZIIIIIII",
        "+IZZIIIIII",
        "+IIIZZIIII",
        "+IIIIZZIII",
        "+IIIIIIZZI",
        "+IIIIIIIZZ",
        "+XXXXXXIII",
        "+IIIXXXXXX",
    ],
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 40


def test_valid_certificate_with_a_non_reference_logical_passes() -> None:
    """Counterexample: the old judge rejected a correct Shor-code certificate whose
    weight-3 logical differed from the reference's choice."""
    reference = solve(SHOR)
    assert reference["distance"] == 3
    other = "XXXIIIIII" if reference["logical"] != "XXXIIIIII" else "IIIXXXIII"
    answer = {
        "id": "shor",
        "status": "SOLVED",
        "distance": 3,
        "logical": other,
        "lower_bound": None,
    }
    ok, reason, _ = evaluate_dual(SHOR, answer)
    assert ok, reason


def test_synthetic_lrat_object_is_not_accepted() -> None:
    answer = {
        **solve(FIVE_QUBIT),
        "lower_bound": {"format": "lrat", "encoding_sha256": "0" * 64, "proof_b64gz": ""},
    }
    assert evaluate_dual(FIVE_QUBIT, answer)[0] is False


@pytest.mark.parametrize("distance", [2, 4], ids=["underclaimed", "overclaimed"])
def test_wrong_distance_with_a_matching_weight_operator_is_rejected(distance: int) -> None:
    logical = "XZIII" if distance == 2 else "XZZXI"
    answer = {
        "id": "five",
        "status": "SOLVED",
        "distance": distance,
        "logical": logical,
        "lower_bound": None,
    }
    assert evaluate_dual(FIVE_QUBIT, answer)[0] is False


def test_overclaimed_distance_is_refuted_by_enumeration() -> None:
    """XXXXX is a genuine logical of the five-qubit code, but weight-3 logicals exist."""
    answer = {
        "id": "five",
        "status": "SOLVED",
        "distance": 5,
        "logical": "XXXXX",
        "lower_bound": None,
    }
    ok, reason, _ = evaluate_dual(FIVE_QUBIT, answer)
    assert ok is False
    assert "lighter" in reason.lower()


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "UNKNOWN", "refusal_code": "BUDGET_EXHAUSTED"},
        {"status": "OUT_OF_SCOPE", "witness": {"kind": "anticommuting", "pair": [0, 1]}},
        {
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "dependent", "linear_combination": [1, 0, 0, 0]},
        },
    ],
    ids=["empty_object", "refusal", "false_anticommuting", "false_dependency"],
)
def test_trivial_responders_fail_on_every_valid_code(answer: dict) -> None:
    valid = [p for p in JUDGE_CASES if "poison" not in p.name]
    passes = [p.name for p in valid if evaluate_dual(_load(p), {"id": _load(p)["id"], **answer})[0]]
    assert passes == []


def test_boolean_and_float_distances_are_rejected() -> None:
    good = solve(FIVE_QUBIT)
    assert evaluate_dual(FIVE_QUBIT, good)[0] is True
    assert evaluate_dual(FIVE_QUBIT, {**good, "distance": 3.0})[0] is False
    minus = {"id": "m", "num_qubits": 2, "generators": ["+XI"]}
    one = solve(minus)
    assert one["distance"] == 1
    assert evaluate_dual(minus, {**one, "distance": True})[0] is False


def test_reference_answers_pass_every_judge_case() -> None:
    failures = [p.name for p in JUDGE_CASES if not evaluate_dual(_load(p), solve(_load(p)))[0]]
    assert failures == []


def test_any_valid_out_of_scope_witness_is_accepted() -> None:
    """-I as a generator is both a zero F2 row and a -I product; both witnesses are valid."""
    case = {"id": "mi", "num_qubits": 3, "generators": ["-III"]}
    dependent = {
        "id": "mi",
        "status": "OUT_OF_SCOPE",
        "witness": {"kind": "dependent", "linear_combination": [1]},
    }
    minus_identity = {
        "id": "mi",
        "status": "OUT_OF_SCOPE",
        "witness": {"kind": "minus_identity", "subset": [0]},
    }
    assert evaluate_dual(case, dependent)[0] is True
    assert evaluate_dual(case, minus_identity)[0] is True
    plus = {"id": "pi", "num_qubits": 3, "generators": ["+III"]}
    assert evaluate_dual(plus, {**minus_identity, "id": "pi"})[0] is False


FULL_RANK_WITNESS = {"kind": "full_rank"}


@pytest.mark.parametrize(
    "case",
    [
        {"id": "z1", "num_qubits": 1, "generators": ["+Z"]},
        {"id": "bell", "num_qubits": 2, "generators": ["+XX", "-ZZ"]},
    ],
    ids=["single_qubit_z", "bell_pair"],
)
def test_full_rank_code_has_an_accepted_answer(case: dict) -> None:
    """Counterexample (review of e6fbc15cf): with m = n there is no logical operator, the
    reference answered UNKNOWN/NO_LOGICAL_OPERATOR_FOUND, and both checkers rejected every answer."""
    reference = solve(case)
    assert reference == {"id": case["id"], "status": "OUT_OF_SCOPE", "witness": FULL_RANK_WITNESS}
    ok, reason, _ = evaluate_dual(case, reference)
    assert ok, reason


def test_full_rank_witness_is_rejected_when_logical_qubits_exist() -> None:
    answer = {"id": "five", "status": "OUT_OF_SCOPE", "witness": FULL_RANK_WITNESS}
    assert evaluate_dual(FIVE_QUBIT, answer)[0] is False


def test_full_rank_witness_is_rejected_for_an_invalid_group_of_size_n() -> None:
    case = {"id": "anti", "num_qubits": 2, "generators": ["+XI", "+ZI"]}
    answer = {"id": "anti", "status": "OUT_OF_SCOPE", "witness": FULL_RANK_WITNESS}
    assert evaluate_dual(case, answer)[0] is False
    assert evaluate_dual(case, solve(case))[0] is True


def test_solved_is_rejected_on_a_full_rank_code() -> None:
    case = {"id": "z1", "num_qubits": 1, "generators": ["+Z"]}
    answer = {"id": "z1", "status": "SOLVED", "distance": 1, "logical": "Z", "lower_bound": None}
    assert evaluate_dual(case, answer)[0] is False
