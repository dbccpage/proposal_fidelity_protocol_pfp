"""Checker 2: Weak Jacobi Discriminant and Exact Rational Matrix Inversion Evaluator.

Independent verification engine for Challenge C035.
Verifies K3 elliptic genus coefficients via 1D EOT torsion half-period modular reductions
over Q[[q]], and determines representation multiplicities by exact rational Gauss-Jordan elimination
over Q without using class sizes or group order.

Completely self-contained. Shares ZERO code with Checker 1.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 2 Private Constants & Independent Data Structures
# -------------------------------------------------------------------------

_C2_CLASSES: tuple[str, ...] = (
    "1A",
    "2A",
    "3A",
    "5A",
    "4B",
    "7A",
    "7B",
    "8A",
    "6A",
    "11A",
    "15A",
    "15B",
    "14A",
    "14B",
    "23A",
    "23B",
    "12B",
    "6B",
    "4C",
    "3B",
    "2B",
    "10A",
    "21A",
    "21B",
    "4A",
    "12A",
)
_C2_CLASS_INDEX: dict[str, int] = {c: i for i, c in enumerate(_C2_CLASSES)}

_C2_REPRESENTATIONS: tuple[str, ...] = (
    "1",
    "23",
    "252",
    "253",
    "1771",
    "3520",
    "45",
    "45bar",
    "990",
    "990bar",
    "1035a",
    "1035abar",
    "1035b",
    "231",
    "231bar",
    "770",
    "770bar",
    "483",
    "1265",
    "2024",
    "2277",
    "3312",
    "5313",
    "5796",
    "5544",
    "10395",
)
_C2_REP_SET: frozenset[str] = frozenset(_C2_REPRESENTATIONS)

# -------------------------------------------------------------------------
# Exact Representation Table as integer triples (a, b, p) for (a + b sqrt(-p))/2
# -------------------------------------------------------------------------


def _c2_int(n: int) -> tuple[int, int, int]:
    return (2 * n, 0, 0)


def _c2_surd_p(p: int) -> tuple[int, int, int]:
    return (-1, 1, p)


def _c2_surd_m(p: int) -> tuple[int, int, int]:
    return (-1, -1, p)


def _c2_2surd_p(p: int) -> tuple[int, int, int]:
    return (-2, 2, p)


def _c2_2surd_m(p: int) -> tuple[int, int, int]:
    return (-2, -2, p)


def _c2_nsurd_p(p: int) -> tuple[int, int, int]:
    return (1, -1, p)


def _c2_nsurd_m(p: int) -> tuple[int, int, int]:
    return (1, 1, p)


_C2_CHAR_MATRIX: tuple[tuple[tuple[int, int, int], ...], ...] = (
    # 1: 1
    tuple([_c2_int(1)] * 26),
    # 2: 23
    (
        _c2_int(23),
        _c2_int(7),
        _c2_int(5),
        _c2_int(3),
        _c2_int(3),
        _c2_int(2),
        _c2_int(2),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
    ),
    # 3: 252
    (
        _c2_int(252),
        _c2_int(28),
        _c2_int(9),
        _c2_int(2),
        _c2_int(4),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(12),
        _c2_int(2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(4),
        _c2_int(1),
    ),
    # 4: 253
    (
        _c2_int(253),
        _c2_int(13),
        _c2_int(10),
        _c2_int(3),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-11),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-3),
        _c2_int(0),
    ),
    # 5: 1771
    (
        _c2_int(1771),
        _c2_int(-21),
        _c2_int(16),
        _c2_int(1),
        _c2_int(-5),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(7),
        _c2_int(11),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
    ),
    # 6: 3520
    (
        _c2_int(3520),
        _c2_int(64),
        _c2_int(10),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-8),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
    ),
    # 7: 45
    (
        _c2_int(45),
        _c2_int(-3),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_surd_p(7),
        _c2_surd_m(7),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_nsurd_p(7),
        _c2_nsurd_m(7),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(3),
        _c2_int(5),
        _c2_int(0),
        _c2_surd_m(7),
        _c2_surd_p(7),
        _c2_int(-3),
        _c2_int(0),
    ),
    # 8: 45bar
    (
        _c2_int(45),
        _c2_int(-3),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_surd_m(7),
        _c2_surd_p(7),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_nsurd_m(7),
        _c2_nsurd_p(7),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(3),
        _c2_int(5),
        _c2_int(0),
        _c2_surd_p(7),
        _c2_surd_m(7),
        _c2_int(-3),
        _c2_int(0),
    ),
    # 9: 990
    (
        _c2_int(990),
        _c2_int(-18),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_surd_p(7),
        _c2_surd_m(7),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_surd_p(7),
        _c2_surd_m(7),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-2),
        _c2_int(3),
        _c2_int(-10),
        _c2_int(0),
        _c2_surd_m(7),
        _c2_surd_p(7),
        _c2_int(6),
        _c2_int(0),
    ),
    # 10: 990bar
    (
        _c2_int(990),
        _c2_int(-18),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_surd_m(7),
        _c2_surd_p(7),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_surd_m(7),
        _c2_surd_p(7),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-2),
        _c2_int(3),
        _c2_int(-10),
        _c2_int(0),
        _c2_surd_p(7),
        _c2_surd_m(7),
        _c2_int(6),
        _c2_int(0),
    ),
    # 11: 1035a
    (
        _c2_int(1035),
        _c2_int(-21),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_2surd_p(7),
        _c2_2surd_m(7),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-3),
        _c2_int(-5),
        _c2_int(0),
        _c2_nsurd_m(7),
        _c2_nsurd_p(7),
        _c2_int(3),
        _c2_int(0),
    ),
    # 12: 1035abar
    (
        _c2_int(1035),
        _c2_int(-21),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_2surd_m(7),
        _c2_2surd_p(7),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-3),
        _c2_int(-5),
        _c2_int(0),
        _c2_nsurd_p(7),
        _c2_nsurd_m(7),
        _c2_int(3),
        _c2_int(0),
    ),
    # 13: 1035b
    (
        _c2_int(1035),
        _c2_int(27),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_int(3),
        _c2_int(6),
        _c2_int(35),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(3),
        _c2_int(0),
    ),
    # 14: 231
    (
        _c2_int(231),
        _c2_int(7),
        _c2_int(-3),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(0),
        _c2_surd_p(15),
        _c2_surd_m(15),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
        _c2_int(-9),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
    ),
    # 15: 231bar
    (
        _c2_int(231),
        _c2_int(7),
        _c2_int(-3),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(0),
        _c2_surd_m(15),
        _c2_surd_p(15),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
        _c2_int(-9),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
    ),
    # 16: 770
    (
        _c2_int(770),
        _c2_int(-14),
        _c2_int(5),
        _c2_int(0),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_surd_p(23),
        _c2_surd_m(23),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-2),
        _c2_int(-7),
        _c2_int(10),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_int(-1),
    ),
    # 17: 770bar
    (
        _c2_int(770),
        _c2_int(-14),
        _c2_int(5),
        _c2_int(0),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_surd_m(23),
        _c2_surd_p(23),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-2),
        _c2_int(-7),
        _c2_int(10),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_int(-1),
    ),
    # 18: 483
    (
        _c2_int(483),
        _c2_int(35),
        _c2_int(6),
        _c2_int(-2),
        _c2_int(3),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(2),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
        _c2_int(3),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
    ),
    # 19: 1265
    (
        _c2_int(1265),
        _c2_int(49),
        _c2_int(5),
        _c2_int(0),
        _c2_int(1),
        _c2_int(-2),
        _c2_int(-2),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-3),
        _c2_int(8),
        _c2_int(-15),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(-7),
        _c2_int(-1),
    ),
    # 20: 2024
    (
        _c2_int(2024),
        _c2_int(8),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(8),
        _c2_int(24),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(8),
        _c2_int(-1),
    ),
    # 21: 2277
    (
        _c2_int(2277),
        _c2_int(21),
        _c2_int(0),
        _c2_int(-3),
        _c2_int(1),
        _c2_int(2),
        _c2_int(2),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(2),
        _c2_int(-3),
        _c2_int(6),
        _c2_int(-19),
        _c2_int(1),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(-3),
        _c2_int(0),
    ),
    # 22: 3312
    (
        _c2_int(3312),
        _c2_int(48),
        _c2_int(0),
        _c2_int(-3),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-2),
        _c2_int(0),
        _c2_int(-6),
        _c2_int(16),
        _c2_int(1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
    ),
    # 23: 5313
    (
        _c2_int(5313),
        _c2_int(49),
        _c2_int(-15),
        _c2_int(3),
        _c2_int(-3),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-3),
        _c2_int(0),
        _c2_int(9),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
    ),
    # 24: 5796
    (
        _c2_int(5796),
        _c2_int(-28),
        _c2_int(-9),
        _c2_int(1),
        _c2_int(4),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(36),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-4),
        _c2_int(-1),
    ),
    # 25: 5544
    (
        _c2_int(5544),
        _c2_int(-56),
        _c2_int(9),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(24),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-8),
        _c2_int(1),
    ),
    # 26: 10395
    (
        _c2_int(10395),
        _c2_int(-21),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(-1),
        _c2_int(-1),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
        _c2_int(-45),
        _c2_int(0),
        _c2_int(0),
        _c2_int(0),
        _c2_int(3),
        _c2_int(0),
    ),
)

# -------------------------------------------------------------------------
# Checker 2 Private 1D Power Series Arithmetic over Q[[q]]
# -------------------------------------------------------------------------


def _c2_is_int(v: Any) -> bool:
    """Strict boolean rejection: True iff v is int and not bool."""
    return type(v) is int and not isinstance(v, bool)


def _c2_series_mul(
    s1: Mapping[int, Fraction | int],
    s2: Mapping[int, Fraction | int],
    limit: int,
) -> dict[int, Fraction]:
    """Cauchy product of 1D rational power series in Q[[q]] truncated at q^limit."""
    res: defaultdict[int, Fraction] = defaultdict(Fraction)
    for q1, c1 in s1.items():
        for q2, c2 in s2.items():
            if q1 + q2 <= limit:
                res[q1 + q2] += Fraction(c1) * Fraction(c2)
    return {k: v for k, v in res.items() if v != 0}


def _c2_series_div(
    num: Mapping[int, Fraction | int],
    den: Mapping[int, Fraction | int],
    limit: int,
) -> dict[int, Fraction]:
    """Exact division of 1D power series in Q[[q]] where den[0] != 0."""
    res: dict[int, Fraction] = {}
    d0 = Fraction(den.get(0, 0))
    if d0 == 0:
        raise ZeroDivisionError("C2 1D series division by zero constant term")
    for n in range(limit + 1):
        cur = Fraction(num.get(n, 0))
        for k in range(1, n + 1):
            if k in den and (n - k) in res:
                cur -= Fraction(den[k]) * res[n - k]
        res[n] = cur / d0
    return res


# Dynamic cache storing exact derived coefficients to guarantee <1ms subsequent checks
_c2_dynamic_cache: dict[int, int] = {}


def _c2_compute_discriminant_coefficients(max_n: int) -> dict[int, int]:
    """Derives exact mock modular coefficients A_n via 1D EOT torsion half-period modular reduction.

    Computes:
      Z(tau, 1/2) = 8 * [ (theta_4(tau, 0)/theta_3(tau, 0))^2 + (theta_3(tau, 0)/theta_4(tau, 0))^2 ]
      F(tau, 1/2) = 4 * prod_{m=1}^max_q (1 + q^m)^4 / (1 - q^m)
      mu(tau, 1/2) = [ 1/4 + sum_{k>=1} q^{k(k+1)/2} / (1 + q^k) ] / [ sum_{n>=0} q^{n(n+1)/2} ]
      H(tau) = Z(tau, 1/2) / F(tau, 1/2) - 24 * mu(tau, 1/2)
    in Q[[q]], returning exact integer coefficients A_n without any 2D polynomial expansions.
    """
    missing = [n for n in range(1, max_n + 1) if n not in _c2_dynamic_cache]
    if missing:
        max_q = max(max_n, 30)
        max_h = 2 * max_q

        # 1. Jacobi theta nullwerte series theta_3(tau, 0) and theta_4(tau, 0) in half-powers h = 2*q
        t3: defaultdict[int, int] = defaultdict(int)
        t4: defaultdict[int, int] = defaultdict(int)
        for n in range(-15, 16):
            h = n * n
            if h <= max_h:
                t3[h] += 1
                t4[h] += (-1) ** n

        t3_sq = _c2_series_mul(t3, t3, max_h)
        t4_sq = _c2_series_mul(t4, t4, max_h)

        q34 = _c2_series_div(t4_sq, t3_sq, max_h)
        q43 = _c2_series_div(t3_sq, t4_sq, max_h)
        # Z(tau, 1/2) has non-zero coefficients only at even powers of half-order (integer powers of q)
        z_1d = {
            h // 2: Fraction(8) * (q34.get(h, Fraction(0)) + q43.get(h, Fraction(0)))
            for h in range(0, max_h + 1, 2)
        }

        # 2. Prefactor F(tau, 1/2) = 4 * prod_{m=1}^max_q (1 + q^m)^4 / (1 - q^m)
        num_f: dict[int, Fraction] = {0: Fraction(1)}
        den_f: dict[int, Fraction] = {0: Fraction(1)}
        for m in range(1, max_q + 1):
            f_num = {
                0: Fraction(1),
                m: Fraction(4),
                2 * m: Fraction(6),
                3 * m: Fraction(4),
                4 * m: Fraction(1),
            }
            num_f = _c2_series_mul(num_f, f_num, max_q)
            den_f = _c2_series_mul(den_f, {0: Fraction(1), m: Fraction(-1)}, max_q)
        q_f = _c2_series_div(num_f, den_f, max_q)
        f_1d = {m: Fraction(4) * q_f[m] for m in range(max_q + 1)}

        # 3. Z(tau, 1/2) / F(tau, 1/2)
        z_div_f = _c2_series_div(z_1d, f_1d, max_q)

        # 4. mu(tau, 1/2) * q^{1/8} = [ 1/4 + sum_{k>=1} q^{k(k+1)/2} / (1 + q^k) ] / [ sum_{n>=0} q^{n(n+1)/2} ]
        den_mu: defaultdict[int, Fraction] = defaultdict(Fraction)
        for n in range(25):
            p = n * (n + 1) // 2
            if p <= max_q:
                den_mu[p] += Fraction(1)

        num_mu: defaultdict[int, Fraction] = defaultdict(Fraction)
        num_mu[0] = Fraction(1, 4)
        for k in range(1, max_q + 1):
            p = k * (k + 1) // 2
            if p > max_q:
                break
            for j in range((max_q - p) // k + 1):
                num_mu[p + j * k] += Fraction((-1) ** j)

        mu_1d = _c2_series_div(num_mu, den_mu, max_q)

        # 5. H(tau) = Z(tau, 1/2) / F(tau, 1/2) - 24 * mu(tau, 1/2)
        for n in range(1, max_q + 1):
            val = z_div_f.get(n, Fraction(0)) - Fraction(24) * mu_1d.get(n, Fraction(0))
            if val.denominator != 1:
                raise ArithmeticError(f"C2 non-integral coefficient at order n={n}: {val}")
            _c2_dynamic_cache[n] = int(val)

    return {n: _c2_dynamic_cache[n] for n in range(1, max_n + 1)}


# -------------------------------------------------------------------------
# Checker 2 Exact Rational Gauss-Jordan Decomposition & Defenses
# -------------------------------------------------------------------------


def _c2_parse_val(v: Any) -> tuple[int, int, int]:
    if _c2_is_int(v):
        return (2 * v, 0, 0)
    if isinstance(v, (list, tuple)) and len(v) == 3:
        if all(_c2_is_int(x) for x in v):
            return (v[0], v[1], v[2])
    if isinstance(v, str):
        s = v.strip().replace(" ", "")
        m = {
            "e7+": (-1, 1, 7),
            "e7-": (-1, -1, 7),
            "-e7+": (1, -1, 7),
            "-e7-": (1, 1, 7),
            "2e7+": (-2, 2, 7),
            "2e7-": (-2, -2, 7),
            "e15+": (-1, 1, 15),
            "e15-": (-1, -1, 15),
            "e23+": (-1, 1, 23),
            "e23-": (-1, -1, 23),
        }
        if s in m:
            return m[s]
        try:
            return (2 * int(s), 0, 0)
        except ValueError:
            pass
    raise ValueError(f"Unrecognized value format: {v}")


def _c2_verify_refusal_warranted(case: Mapping[str, Any], rcode: str) -> tuple[bool, str]:
    """Defect-grounded refusal validation in Checker 2."""
    valid_codes = frozenset(
        {
            "MAX_N_OUT_OF_BOUNDS",
            "UNRECOGNIZED_CLASS_NAME",
            "MALFORMED_CASE_STRUCTURE",
            "UNRECOGNIZED_QUERY",
            "INVALID_QUERY_TYPE",
        }
    )
    if rcode not in valid_codes:
        return False, f"FAIL (C2): unrecognized refusal code {rcode!r}"

    if not isinstance(case, Mapping):
        return True, "VALID_REFUSAL_MALFORMED"

    cid = case.get("case_id") or case.get("id")
    if not cid:
        return True, "VALID_REFUSAL_MALFORMED"

    query = case.get("query")
    if query not in ("coefficients", "decompose", "specialization_z0"):
        return True, "VALID_REFUSAL_UNRECOGNIZED_QUERY"

    if query == "coefficients":
        max_n = case.get("max_n")
        if isinstance(max_n, bool) or not _c2_is_int(max_n):
            return True, "VALID_REFUSAL_MALFORMED"
        if max_n < 1 or max_n > 30:
            if rcode == "MAX_N_OUT_OF_BOUNDS":
                return True, "VALID_REFUSAL_MAX_N_OUT_OF_BOUNDS"
            return False, f"FAIL (C2): wrong refusal code {rcode} for max_n={max_n}"
        return False, f"FAIL (C2): unwarranted refusal on valid coefficient query (max_n={max_n})"

    if query == "decompose":
        cord = case.get("class_order")
        vals = case.get("values")
        if (
            not isinstance(cord, list)
            or not isinstance(vals, list)
            or len(cord) != 26
            or len(vals) != 26
            or len(set(cord)) != 26
        ):
            return True, "VALID_REFUSAL_MALFORMED"
        unknowns = [c for c in cord if c not in _C2_CLASS_INDEX]
        if unknowns:
            if rcode == "UNRECOGNIZED_CLASS_NAME":
                return True, "VALID_REFUSAL_UNRECOGNIZED_CLASS_NAME"
            return False, f"FAIL (C2): wrong refusal code {rcode} for unknown classes"
        for v in vals:
            if isinstance(v, bool):
                return True, "VALID_REFUSAL_MALFORMED"
        return False, "FAIL (C2): unwarranted refusal on valid decomposition case"

    return False, "FAIL (C2): refusal verification fell through"


def _c2_gauss_jordan_decompose(
    class_order: list[str],
    values: list[Any],
) -> tuple[str, dict[str, Any] | None, dict[str, int] | None]:
    """Exact rational Gauss-Jordan elimination on character matrix over Q without group order."""
    # 1. Map values to canonical order
    canonical_vals: list[tuple[int, int, int]] = [None] * 26  # type: ignore[list-item]
    for c_name, v in zip(class_order, values):
        if c_name not in _C2_CLASS_INDEX:
            return "UNKNOWN", {"refusal_code": "UNRECOGNIZED_CLASS_NAME"}, None
        idx = _C2_CLASS_INDEX[c_name]
        try:
            canonical_vals[idx] = _c2_parse_val(v)
        except Exception:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # 2. Build augmented matrix [M | target] over Fraction
    rows: list[list[Fraction]] = []
    for j in range(26):
        # Real part equation
        r_row: list[Fraction] = []
        for i in range(26):
            a, b, p = _C2_CHAR_MATRIX[i][j]
            r_row.append(Fraction(a, 2))
        r_row.append(Fraction(canonical_vals[j][0], 2))
        rows.append(r_row)

        # Imaginary part equation
        has_imag = (
            any(_C2_CHAR_MATRIX[i][j][1] != 0 for i in range(26)) or canonical_vals[j][1] != 0
        )
        if has_imag:
            im_row: list[Fraction] = []
            for i in range(26):
                a, b, p = _C2_CHAR_MATRIX[i][j]
                im_row.append(Fraction(b, 2))
            im_row.append(Fraction(canonical_vals[j][1], 2))
            rows.append(im_row)

    # 3. Exact rational Gauss-Jordan
    num_rows = len(rows)
    num_cols = 26
    pivot_row = 0
    for col in range(num_cols):
        pivot_idx = None
        for r in range(pivot_row, num_rows):
            if rows[r][col] != 0:
                pivot_idx = r
                break
        if pivot_idx is None:
            continue

        rows[pivot_row], rows[pivot_idx] = rows[pivot_idx], rows[pivot_row]
        pv = rows[pivot_row][col]
        rows[pivot_row] = [x / pv for x in rows[pivot_row]]

        for r in range(num_rows):
            if r != pivot_row and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [rows[r][c] - factor * rows[pivot_row][c] for c in range(num_cols + 1)]

        pivot_row += 1

    # Check for residual inconsistency in zero-row equations
    for r in range(pivot_row, num_rows):
        if rows[r][num_cols] != 0:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "non_integral_multiplicity",
                    "irrep": "1",
                    "value": str(rows[r][num_cols]),
                },
                None,
            )

    # Extract rational multiplicities
    mults: dict[str, int] = {}
    for i in range(26):
        rep_name = _C2_REPRESENTATIONS[i]
        frac_val = rows[i][num_cols]

        if frac_val.denominator != 1:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "non_integral_multiplicity",
                    "irrep": rep_name,
                    "value": str(frac_val),
                },
                None,
            )

        int_val = frac_val.numerator
        if int_val < 0:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "negative_multiplicity",
                    "irrep": rep_name,
                    "value": int_val,
                },
                None,
            )

        if int_val > 0:
            mults[rep_name] = int_val

    return "SOLVED", None, mults


# -------------------------------------------------------------------------
# Checker 2 Main Certificate Verification
# -------------------------------------------------------------------------


def verify_matrix_inversion_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Verifies candidate result using Checker 2 (rational Gauss-Jordan matrix inversion & 1D EOT reduction)."""
    if not isinstance(result, Mapping):
        return False, "FAIL (C2): result is not a dictionary"

    status = result.get("status")
    if not isinstance(status, str):
        return False, "FAIL (C2): status must be a string"

    query = case.get("query") if isinstance(case, Mapping) else None

    # Strict Closed Whitelist
    if status == "SOLVED":
        if query == "coefficients":
            allowed = frozenset({"id", "case_id", "status", "A"})
        elif query == "decompose":
            allowed = frozenset({"id", "case_id", "status", "multiplicities", "zero_elsewhere"})
        elif query == "specialization_z0":
            allowed = frozenset({"id", "case_id", "status", "constant"})
        else:
            return False, f"FAIL (C2): SOLVED on unrecognized query {query}"
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C2): phantom keys in SOLVED answer: {set(result.keys()) - allowed}",
            )
    elif status == "OUT_OF_SCOPE":
        allowed = frozenset({"id", "case_id", "status", "witness"})
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C2): phantom keys in OUT_OF_SCOPE answer: {set(result.keys()) - allowed}",
            )
    elif status == "UNKNOWN":
        allowed = frozenset({"id", "case_id", "status", "refusal_code", "refusal"})
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C2): phantom keys in UNKNOWN answer: {set(result.keys()) - allowed}",
            )
    else:
        return False, f"FAIL (C2): unrecognized or lowercase status: {status!r}"

    # Case ID Parity
    c_id = (
        str(case.get("case_id") or case.get("id") or "")
        if isinstance(case, Mapping)
        else "malformed"
    )
    r_id = str(result.get("id") or result.get("case_id") or "")
    if c_id and r_id != c_id:
        return False, f"FAIL (C2): case ID mismatch: case={c_id} vs result={r_id}"

    # Handle UNKNOWN
    if status == "UNKNOWN":
        rcode = str(result.get("refusal_code") or result.get("refusal") or "")
        if not rcode:
            return False, "FAIL (C2): UNKNOWN status missing refusal_code"
        ok, msg = _c2_verify_refusal_warranted(case, rcode)
        return ok, msg

    # Handle specialization_z0
    if query == "specialization_z0":
        if result.get("constant") != 24:
            return (
                False,
                f"FAIL (C2): specialization constant mismatch: expected 24, got {result.get('constant')}",
            )
        return True, "PASS (C2): specialization constant 24 verified"

    # Handle coefficients
    if query == "coefficients":
        max_n = case.get("max_n")
        if isinstance(max_n, bool) or not _c2_is_int(max_n) or max_n < 1 or max_n > 30:
            return False, f"FAIL (C2): invalid max_n={max_n} but solver returned {status}"

        a_dict = result.get("A")
        if not isinstance(a_dict, dict) or not a_dict:
            return False, "FAIL (C2): missing or empty 'A' dictionary"

        if len(a_dict) != max_n:
            return False, f"FAIL (C2): expected {max_n} coefficients, got {len(a_dict)}"

        # Compute expected coefficients dynamically via 1D EOT torsion reduction over Q[[q]]
        expected_a = _c2_compute_discriminant_coefficients(max_n)

        for n in range(1, max_n + 1):
            s_n = str(n)
            if s_n not in a_dict:
                return False, f"FAIL (C2): missing order {s_n} in coefficient dict"
            val = a_dict[s_n]
            if not _c2_is_int(val):
                return (
                    False,
                    f"FAIL (C2): coefficient at order {s_n} is not an exact integer: {val!r}",
                )
            expected = expected_a[n]
            if val != expected:
                return (
                    False,
                    f"FAIL (C2): coefficient mismatch at order {s_n}: expected {expected}, got {val}",
                )

        return True, "PASS (C2): coefficients exact match"

    # Handle decompose
    if query == "decompose":
        cord = case.get("class_order")
        vals = case.get("values")
        if (
            not isinstance(cord, list)
            or not isinstance(vals, list)
            or len(cord) != 26
            or len(vals) != 26
        ):
            return False, "FAIL (C2): malformed decomposition input parameters"

        expected_verdict, witness, exp_mults = _c2_gauss_jordan_decompose(cord, vals)

        if expected_verdict == "OUT_OF_SCOPE":
            if status != "OUT_OF_SCOPE":
                return False, f"FAIL (C2): case warrants OUT_OF_SCOPE, but got status {status}"
            ans_witness = result.get("witness")
            if not isinstance(ans_witness, dict):
                return False, "FAIL (C2): OUT_OF_SCOPE missing witness dictionary"
            if set(ans_witness.keys()) - frozenset({"kind", "irrep", "value"}):
                return False, "FAIL (C2): phantom keys in witness payload"
            if ans_witness.get("kind") not in (
                "non_integral_multiplicity",
                "negative_multiplicity",
                "non_zero_imaginary",
            ):
                return False, f"FAIL (C2): invalid witness kind {ans_witness.get('kind')}"
            if ans_witness.get("irrep") not in _C2_REP_SET:
                return False, f"FAIL (C2): witness irrep {ans_witness.get('irrep')} not in M_24"
            return True, "PASS (C2): OUT_OF_SCOPE correctly verified"

        # Case is SOLVED
        if status != "SOLVED":
            return False, f"FAIL (C2): expected SOLVED, got {status}"

        mults = result.get("multiplicities")
        if not isinstance(mults, dict) or mults is None:
            return False, "FAIL (C2): missing 'multiplicities' dictionary"

        if result.get("zero_elsewhere") is not True:
            return False, "FAIL (C2): 'zero_elsewhere' must be strictly boolean True"

        # Strict integer check on all multiplicities
        for irr, m in mults.items():
            if irr not in _C2_REP_SET:
                return False, f"FAIL (C2): unrecognized irrep name {irr!r}"
            if not _c2_is_int(m):
                return False, f"FAIL (C2): multiplicity for {irr} is not an exact integer: {m!r}"
            if m <= 0:
                return (
                    False,
                    f"FAIL (C2): non-positive multiplicity in sparse dictionary: {irr}={m}",
                )

        if mults != exp_mults:
            return False, f"FAIL (C2): multiplicity mismatch: expected {exp_mults}, got {mults}"

        # Matrix-vector reconstruction check across all 26 classes (Anti-Dimension Trap)
        for j, c_name in enumerate(_C2_CLASSES):
            recon_re4 = 0
            for irr, m in mults.items():
                r_idx = _C2_REPRESENTATIONS.index(irr)
                a, b, p = _C2_CHAR_MATRIX[r_idx][j]
                recon_re4 += 2 * m * a

            c_idx_in_input = cord.index(c_name)
            inp_val = _c2_parse_val(vals[c_idx_in_input])
            inp_re4 = 2 * inp_val[0]
            if recon_re4 != inp_re4:
                return (
                    False,
                    f"FAIL (C2): matrix reconstruction mismatch at class {c_name}: expected {inp_val[0]}, reconstructed {recon_re4 // 2}",
                )

        return True, "PASS (C2): Gauss-Jordan linear decomposition verified across all 26 classes"

    return False, f"FAIL (C2): unhandled query type {query}"
