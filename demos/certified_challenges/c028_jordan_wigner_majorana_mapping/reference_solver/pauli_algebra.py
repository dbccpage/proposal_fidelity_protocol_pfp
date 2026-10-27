# AuthorityEffect: None.
"""
Exact phase-tracked Pauli string algebra for C028.

Tracks Pauli string products with exact powers of i: i^p for p in {0, 1, 2, 3}.
Handles addition and scalar multiplication over Gaussian rationals Q(i).
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Tuple, Union


def format_fraction(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def parse_fraction(val: Union[str, int, Fraction]) -> Fraction:
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    return Fraction(val)


# Single Pauli multiplication table: (P1, P2) -> (delta_power_of_i, P3)
# where P1 * P2 = i^delta * P3
_PAULI_MULT_TABLE = {
    ("I", "I"): (0, "I"),
    ("I", "X"): (0, "X"),
    ("I", "Y"): (0, "Y"),
    ("I", "Z"): (0, "Z"),
    ("X", "I"): (0, "X"),
    ("X", "X"): (0, "I"),
    ("X", "Y"): (1, "Z"),
    ("X", "Z"): (3, "Y"),
    ("Y", "I"): (0, "Y"),
    ("Y", "X"): (3, "Z"),
    ("Y", "Y"): (0, "I"),
    ("Y", "Z"): (1, "X"),
    ("Z", "I"): (0, "Z"),
    ("Z", "X"): (1, "Y"),
    ("Z", "Y"): (3, "X"),
    ("Z", "Z"): (0, "I"),
}


def multiply_pauli_strings(
    sign1: int,
    paulis1: str,
    sign2: int,
    paulis2: str,
) -> Tuple[Fraction, Fraction, str]:
    """
    Multiplies two signed Pauli strings: (sign1 * paulis1) * (sign2 * paulis2).
    Returns (coeff_real, coeff_imag, result_pauli_string) where coeff in Q(i).
    """
    if len(paulis1) != len(paulis2):
        raise ValueError(f"String length mismatch: {len(paulis1)} vs {len(paulis2)}")

    total_p = 0
    res_chars: List[str] = []
    for c1, c2 in zip(paulis1, paulis2):
        dp, p3 = _PAULI_MULT_TABLE[(c1, c2)]
        total_p = (total_p + dp) % 4
        res_chars.append(p3)

    res_str = "".join(res_chars)

    # Base sign: sign1 * sign2 in {+1, -1}
    net_sign = sign1 * sign2

    # i^total_p: 0 -> 1, 1 -> i, 2 -> -1, 3 -> -i
    if total_p == 0:
        return Fraction(net_sign, 1), Fraction(0, 1), res_str
    elif total_p == 1:
        return Fraction(0, 1), Fraction(net_sign, 1), res_str
    elif total_p == 2:
        return Fraction(-net_sign, 1), Fraction(0, 1), res_str
    else:  # total_p == 3
        return Fraction(0, 1), Fraction(-net_sign, 1), res_str
