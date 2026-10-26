"""Admission of integers, names and rationals (RULE_PY_002, RULE_PY_004).

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:admission:v1
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pfp_lab.core.admission import (
    MAX_RATIONAL_CHARS,
    AdmissionError,
    ErrorCode,
    admit_int,
    admit_name,
    format_rational,
    parse_rational,
)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, Fraction(1)])
def test_admit_int_refuses_non_integers(value: object) -> None:
    with pytest.raises(AdmissionError) as caught:
        admit_int(value, minimum=0, maximum=5, field="w")
    assert caught.value.code is ErrorCode.ADMISSION
    assert "w must be an integer" in caught.value.message


@pytest.mark.parametrize(("value", "admitted"), [(0, True), (5, True), (-1, False), (6, False)])
def test_admit_int_enforces_inclusive_bounds(value: int, admitted: bool) -> None:
    if admitted:
        assert admit_int(value, minimum=0, maximum=5, field="w") == value
    else:
        with pytest.raises(AdmissionError, match="between 0 and 5"):
            admit_int(value, minimum=0, maximum=5, field="w")


@pytest.mark.parametrize("value", ["a", "A_1", "x.y-z", "q" * 32])
def test_admit_name_accepts_pattern(value: str) -> None:
    assert admit_name(value, field="n") == value


@pytest.mark.parametrize("value", ["", "q" * 33, "a b", "a/b", "é", 3, None])
def test_admit_name_refuses(value: object) -> None:
    with pytest.raises(AdmissionError):
        admit_name(value, field="n")


@pytest.mark.parametrize(
    ("text", "value"),
    [("0", Fraction(0)), ("7", Fraction(7)), ("-2", Fraction(-2)), ("3/2", Fraction(3, 2)), ("-1/3", Fraction(-1, 3))],
)
def test_parse_rational_accepts_canonical(text: str, value: Fraction) -> None:
    parsed = parse_rational(text, field="r")
    assert parsed == value
    assert type(parsed) is Fraction


@pytest.mark.parametrize(
    "text",
    ["-0", "01", "2/4", "3/1", "1/0", "1/-2", "+1", "1.5", "0.1", "1e3", " 1", "1 ", "", "/2", "NaN", "inf", "1/01"],
)
def test_parse_rational_refuses_non_canonical(text: str) -> None:
    with pytest.raises(AdmissionError):
        parse_rational(text, field="r")


@pytest.mark.parametrize("value", [1, 0.5, True, None, Fraction(1, 2)])
def test_parse_rational_refuses_non_strings(value: object) -> None:
    with pytest.raises(AdmissionError, match="must be a rational string"):
        parse_rational(value, field="r")


def test_parse_rational_refuses_oversized_text() -> None:
    longest = "9" * MAX_RATIONAL_CHARS
    assert parse_rational(longest, field="r") == Fraction(int(longest))
    with pytest.raises(AdmissionError, match="exceeds"):
        parse_rational("9" * (MAX_RATIONAL_CHARS + 1), field="r")


@given(st.fractions(max_denominator=10**6).filter(lambda f: abs(f.numerator) < 10**12))
def test_format_then_parse_round_trips(value: Fraction) -> None:
    text = format_rational(value)
    assert parse_rational(text, field="r") == value
    assert format_rational(parse_rational(text, field="r")) == text


def test_format_rational_spellings() -> None:
    assert format_rational(Fraction(4, 2)) == "2"
    assert format_rational(Fraction(-6, 4)) == "-3/2"
    assert format_rational(Fraction(0)) == "0"


def test_documented_limits() -> None:
    # The wire contract documents 64-character rationals and 32-character names.
    assert parse_rational("1" * 64, field="r") == int("1" * 64)
    with pytest.raises(AdmissionError):
        parse_rational("1" * 65, field="r")
    assert admit_name("n" * 32, field="n") == "n" * 32
