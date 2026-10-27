"""C053 judge corrections: one canonical-rational parser and a pinned determinant.

Counterexamples from the 2026-09-28 audit:

- both checkers accepted the non-canonical strings "4/1" and "0/1";
- the exact checker accepted A = I with det "5", adjugate 5I and inverse I,
  because A adj(A) = det I and inv = adj / det hold for any scalar det.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c053_bareiss_fraction_free_matrix_inversion.judge_packet import (
    canonical_rational,
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
JUDGE_DIR = PACKAGE_DIR / "judge_packet"
CHECKERS = (
    ("exact", exact_checker.check_solution),
    ("independent", independent_checker.check_solution),
)
CASES = [
    json.loads(p.read_text(encoding="utf-8")) for p in sorted((JUDGE_DIR / "cases").glob("*.json"))
]
IDENTITY = {"case_id": "eye", "matrix": [["1", "0"], ["0", "1"]]}


@pytest.mark.parametrize(
    "text",
    [
        "4/1",
        "0/1",
        "-0",
        " 4",
        "4 ",
        "+4",
        "04",
        "1.5",
        "1e3",
        "2/4",
        "0/5",
        "1/-2",
        "-1/-2",
        "１",
        "",
        "1/0",
    ],
)
def test_parser_rejects_non_canonical_strings(text):
    with pytest.raises(canonical_rational.NonCanonicalRational):
        canonical_rational.parse_canonical_rational(text)


@pytest.mark.parametrize("value", [4, 4.0, True, None, ["4"]])
def test_parser_rejects_non_strings(value):
    with pytest.raises(canonical_rational.NonCanonicalRational):
        canonical_rational.parse_canonical_rational(value)


@pytest.mark.parametrize(
    "text,num,den",
    [
        ("0", 0, 1),
        ("-7", -7, 1),
        ("1/2", 1, 2),
        ("-3/4", -3, 4),
        ("123456789012345678901/2", 123456789012345678901, 2),
    ],
)
def test_parser_accepts_canonical_strings(text, num, den):
    value = canonical_rational.parse_canonical_rational(text)
    assert (value.numerator, value.denominator) == (num, den)
    assert canonical_rational.canonical_rational(value) == text


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_scaled_determinant_and_adjugate_are_rejected(name, checker):
    """A = I with det "5" and adjugate 5I satisfies A adj = det I; det(A) is 1."""
    bad = {
        "case_id": "eye",
        "status": "SOLVED",
        "kind": "INVERTIBLE",
        "det": "5",
        "adjugate": [["5", "0"], ["0", "5"]],
        "inverse": [["1", "0"], ["0", "1"]],
    }
    ok, msg = checker(IDENTITY, bad)
    assert ok is False, (name, msg)
    good = {**bad, "det": "1", "adjugate": [["1", "0"], ["0", "1"]]}
    assert checker(IDENTITY, good)[0] is True


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_non_canonical_answer_entries_are_rejected(name, checker):
    case = {"case_id": "d", "matrix": [["4", "0"], ["0", "1"]]}
    good = {
        "case_id": "d",
        "status": "SOLVED",
        "kind": "INVERTIBLE",
        "det": "4",
        "adjugate": [["1", "0"], ["0", "4"]],
        "inverse": [["1/4", "0"], ["0", "1"]],
    }
    assert checker(case, good)[0] is True
    for field, value in (
        ("det", "4/1"),
        ("adjugate", [["1", "0/1"], ["0", "4"]]),
        ("inverse", [["1/4", "0"], ["0", " 1"]]),
    ):
        ok, msg = checker(case, {**good, field: value})
        assert ok is False, (name, field, msg)
    singular = {"case_id": "s", "matrix": [["1", "1"], ["1", "1"]]}
    answer = {
        "case_id": "s",
        "status": "SOLVED",
        "kind": "SINGULAR",
        "det": "0",
        "null_vector": ["1", "-1"],
    }
    assert checker(singular, answer)[0] is True
    for det in ("0/1", 0, "-0"):
        assert checker(singular, {**answer, "det": det})[0] is False, (name, det)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_trivial_responders_fail_on_every_in_scope_case(name, checker):
    in_scope = [
        c
        for c in CASES
        if checker(
            c, {"case_id": c["case_id"], "status": "OUT_OF_SCOPE", "witness": {"reason": "X"}}
        )[0]
        is False
    ]
    assert len(in_scope) == 51
    for case in in_scope:
        cid = case["case_id"]
        for answer in (
            {},
            [],
            {"case_id": cid, "status": "UNKNOWN"},
            {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "SINGULAR",
                "det": "0",
                "null_vector": ["0"] * len(case["matrix"]),
            },
        ):
            assert checker(case, answer)[0] is False, (name, cid)


def test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers():
    from c053_bareiss_fraction_free_matrix_inversion.reference_solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, case["case_id"])
    mutations = sorted((JUDGE_DIR / "hostile_mutations").glob("*.json"))
    assert len(mutations) == 48
    for path in mutations:
        mutation = json.loads(path.read_text(encoding="utf-8"))
        for name, checker in CHECKERS:
            assert checker(mutation["case"], mutation["corrupted_result"])[0] is False, (
                name,
                path.name,
            )


def test_c053_and_c054_share_one_canonical_parser_text():
    other = (
        PACKAGE_DIR.parent / "c054_exact_linear_systems" / "judge_packet" / "canonical_rational.py"
    )
    assert (JUDGE_DIR / "canonical_rational.py").read_bytes() == other.read_bytes()


def test_bareiss_determinant_matches_known_values():
    from fractions import Fraction

    det = exact_checker.bareiss_determinant
    assert det([[Fraction(4), Fraction(7)], [Fraction(2), Fraction(6)]]) == 10
    assert det([[Fraction(1, 3), Fraction(2, 5)], [Fraction(1, 2), Fraction(3, 4)]]) == Fraction(
        1, 20
    )
    assert det([[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]) == -1
    assert det([[Fraction(1), Fraction(2)], [Fraction(2), Fraction(4)]]) == 0
