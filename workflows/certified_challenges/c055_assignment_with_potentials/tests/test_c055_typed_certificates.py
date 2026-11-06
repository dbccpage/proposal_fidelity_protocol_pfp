"""C055 judge corrections: typed permutations and a validated ``sense``.

Counterexamples from the 2026-09-28 audit:

- the Boolean permutation [false, true] passed both checkers (bool is an int);
- a float permutation [0.0, 1.0] crashed the exact checker with TypeError;
- ``"sense": "minimize"`` skipped every dual check in the exact checker, so a
  non-optimal assignment with arbitrary potentials passed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c055_assignment_with_potentials.judge_packet import (
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
JUDGE_DIR = PACKAGE_DIR / "judge_packet"
CHECKERS = (
    ("exact", exact_checker.check_exact),
    ("independent", independent_checker.independent_check),
)
CASE = {"case_id": "t", "cost": [["1", "5"], ["5", "1"]], "sense": "min"}
OPTIMUM = {
    "case_id": "t",
    "status": "SOLVED",
    "kind": "OPTIMAL",
    "sigma": [0, 1],
    "u": ["1", "1"],
    "v": ["0", "0"],
    "value": "2",
}
CASES = [
    json.loads(p.read_text(encoding="utf-8")) for p in sorted((JUDGE_DIR / "cases").glob("*.json"))
]


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_valid_certificate_is_accepted(name, checker):
    assert checker(CASE, OPTIMUM) == (True, checker(CASE, OPTIMUM)[1])


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_boolean_permutation_fails(name, checker):
    ok, msg = checker(CASE, {**OPTIMUM, "sigma": [False, True]})
    assert ok is False, (name, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("sigma", [[0.0, 1.0], [0, 1.0], ["0", "1"], [None, 1]])
def test_non_integer_permutation_is_a_typed_rejection_not_a_crash(name, checker, sigma):
    ok, msg = checker(CASE, {**OPTIMUM, "sigma": sigma})
    assert ok is False and isinstance(msg, str), (name, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("sense", ["minimize", "MIN", "", None, 1, True])
def test_sense_outside_min_max_is_refused(name, checker, sense):
    case = {**CASE, "sense": sense}
    # Non-optimal permutation with potentials that only match its value.
    bad = {
        "case_id": "t",
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [1, 0],
        "u": ["10", "0"],
        "v": ["0", "0"],
        "value": "10",
    }
    for answer in (OPTIMUM, bad):
        ok, msg = checker(case, answer)
        assert ok is False, (name, sense, msg)
    refusal = {"case_id": "t", "status": "OUT_OF_SCOPE", "witness": {"reason": "INVALID_SENSE"}}
    assert checker(case, refusal)[0] is True


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_boolean_cost_entry_makes_the_case_out_of_scope(name, checker):
    case = next(c for c in CASES if c["case_id"] == "c055_p16_boolean_in_cost")
    assert (
        checker(
            case, {"case_id": case["case_id"], "status": "OUT_OF_SCOPE", "witness": {"reason": "X"}}
        )[0]
        is True
    )


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize(
    "field,bad",
    [
        ("u", [" 1", "1"]),
        ("u", ["+1", "1"]),
        ("u", ["01", "1"]),
        ("u", [1, 1]),
        ("u", [1.0, 1.0]),
        ("u", [True, True]),
        ("v", [" 0", "0"]),
        ("v", ["-0", "0"]),
        ("v", ["00", "0"]),
        ("v", [0, 0]),
        ("v", [0.0, 0.0]),
        ("v", [False, False]),
        ("value", " 2"),
        ("value", 2),
        ("value", 2.0),
    ],
)
def test_non_canonical_potentials_and_value_fail(name, checker, field, bad):
    ok, msg = checker(CASE, {**OPTIMUM, field: bad})
    assert ok is False, (name, field, bad, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_trivial_responders_fail_on_every_in_scope_case(name, checker):
    in_scope = [
        c
        for c in CASES
        if exact_checker.check_exact(
            c, {"case_id": c["case_id"], "status": "OUT_OF_SCOPE", "witness": {"reason": "X"}}
        )[0]
        is False
    ]
    assert len(in_scope) == 53
    for case in in_scope:
        cid = case["case_id"]
        for answer in (
            {},
            [],
            "x",
            {"case_id": cid, "status": "UNKNOWN"},
            {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "INVALID_COST_MATRIX"},
            },
        ):
            assert checker(case, answer)[0] is False, (name, cid, answer)


def test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers():
    from c055_assignment_with_potentials.reference_solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, case["case_id"], answer)
    for path in sorted((JUDGE_DIR / "hostile_mutations").glob("*.json")):
        mutation = json.loads(path.read_text(encoding="utf-8"))
        case, bad = mutation.get("case"), mutation.get("mutated_result", mutation.get("result"))
        for name, checker in CHECKERS:
            assert checker(case, bad)[0] is False, (name, path.name)
