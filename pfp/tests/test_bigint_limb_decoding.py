"""Exact num-bigint wire vectors and malformed-input controls.

AuthorityEffect: None.
"""

from fractions import Fraction

import pytest

from omega_engine_pfp.domain.cochain import _parse_bigint, _parse_fraction


@pytest.mark.parametrize(
    ("wire", "expected"),
    [
        ([0, []], 0),
        ([0, [0]], 0),
        ([1, []], 0),
        ([1, [4294967295]], 4294967295),
        ([1, [0, 1]], 4294967296),
        ([-1, [4294967295, 1]], -8589934591),
    ],
)
def test_exact_sign_and_little_endian_uint32_vectors(wire, expected) -> None:
    assert _parse_bigint(wire) == expected


@pytest.mark.parametrize("sign", [True, False, 1.0, "1", -2, 2, 4294967296])
@pytest.mark.parametrize("digits", [[], [1]])
def test_invalid_sign_refuses_even_with_empty_magnitude(sign, digits) -> None:
    with pytest.raises((TypeError, ValueError)):
        _parse_bigint([sign, digits])


@pytest.mark.parametrize("digit", [True, False, 0.5, 1.0, "1", -1, 4294967296])
def test_limb_coercion_and_out_of_range_values_refuse(digit) -> None:
    with pytest.raises((TypeError, ValueError)):
        _parse_bigint([1, [digit]])


def test_zero_sign_cannot_erase_nonzero_magnitude() -> None:
    with pytest.raises(ValueError, match="nonzero magnitude"):
        _parse_bigint([0, [0, 1]])


def test_fraction_consumer_preserves_exact_limb_values() -> None:
    assert _parse_fraction([[1, [0, 1]], [1, [3]]]) == Fraction(4294967296, 3)
    with pytest.raises(TypeError):
        _parse_fraction([[1, [1.5]], [1, [3]]])
