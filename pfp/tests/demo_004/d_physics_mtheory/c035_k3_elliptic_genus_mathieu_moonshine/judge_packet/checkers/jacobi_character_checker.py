"""Checker 1: Jacobi Theta Quotient Series and Frobenius-Schur Character Evaluator.

Independent verification engine for Challenge C035.
Calculates K3 elliptic genus coefficients via direct 2D theta quotients and Appell-Lerch subtraction
over the bivariate Laurent polynomial ring Z[y, y^-1][[q]], and computes representation multiplicities
using the Frobenius-Schur projection formula with conjugacy class sizes and group order |M_24| = 244,823,040.

Completely self-contained. Shares ZERO code with Checker 2.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 1 Private Constants & Group-Theoretic Invariants
# -------------------------------------------------------------------------

_C1_GROUP_ORDER: int = 244823040

_C1_CANONICAL_CLASSES: tuple[str, ...] = (
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

_C1_CENTRALIZERS: tuple[int, ...] = (
    244823040,
    21504,
    1080,
    60,
    128,
    42,
    42,
    16,
    24,
    11,
    15,
    15,
    14,
    14,
    23,
    23,
    12,
    24,
    96,
    504,
    7680,
    20,
    21,
    21,
    384,
    12,
)

_C1_CLASS_SIZES: tuple[int, ...] = tuple(_C1_GROUP_ORDER // c for c in _C1_CENTRALIZERS)
_C1_CLASS_MAP: dict[str, int] = {c: i for i, c in enumerate(_C1_CANONICAL_CLASSES)}

_C1_IRREPS: tuple[str, ...] = (
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
_C1_IRREP_SET: frozenset[str] = frozenset(_C1_IRREPS)

# -------------------------------------------------------------------------
# Exact Character Table (26 irreps x 26 classes) as integer triples (a, b, p)
# representing (a + b sqrt(-p)) / 2
# -------------------------------------------------------------------------


def _c1_I(n: int) -> tuple[int, int, int]:
    return (2 * n, 0, 0)


def _c1_ep_p(p: int) -> tuple[int, int, int]:
    return (-1, 1, p)


def _c1_ep_m(p: int) -> tuple[int, int, int]:
    return (-1, -1, p)


def _c1_2ep_p(p: int) -> tuple[int, int, int]:
    return (-2, 2, p)


def _c1_2ep_m(p: int) -> tuple[int, int, int]:
    return (-2, -2, p)


def _c1_nep_p(p: int) -> tuple[int, int, int]:
    return (1, -1, p)


def _c1_nep_m(p: int) -> tuple[int, int, int]:
    return (1, 1, p)


_C1_TABLE: tuple[tuple[tuple[int, int, int], ...], ...] = (
    # 1: 1
    tuple([_c1_I(1)] * 26),
    # 2: 23
    (
        _c1_I(23),
        _c1_I(7),
        _c1_I(5),
        _c1_I(3),
        _c1_I(3),
        _c1_I(2),
        _c1_I(2),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
    ),
    # 3: 252
    (
        _c1_I(252),
        _c1_I(28),
        _c1_I(9),
        _c1_I(2),
        _c1_I(4),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(12),
        _c1_I(2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(4),
        _c1_I(1),
    ),
    # 4: 253
    (
        _c1_I(253),
        _c1_I(13),
        _c1_I(10),
        _c1_I(3),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-11),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-3),
        _c1_I(0),
    ),
    # 5: 1771
    (
        _c1_I(1771),
        _c1_I(-21),
        _c1_I(16),
        _c1_I(1),
        _c1_I(-5),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(7),
        _c1_I(11),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
    ),
    # 6: 3520
    (
        _c1_I(3520),
        _c1_I(64),
        _c1_I(10),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-8),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
    ),
    # 7: 45
    (
        _c1_I(45),
        _c1_I(-3),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_ep_p(7),
        _c1_ep_m(7),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_nep_p(7),
        _c1_nep_m(7),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(3),
        _c1_I(5),
        _c1_I(0),
        _c1_ep_m(7),
        _c1_ep_p(7),
        _c1_I(-3),
        _c1_I(0),
    ),
    # 8: 45bar
    (
        _c1_I(45),
        _c1_I(-3),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_ep_m(7),
        _c1_ep_p(7),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_nep_m(7),
        _c1_nep_p(7),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(3),
        _c1_I(5),
        _c1_I(0),
        _c1_ep_p(7),
        _c1_ep_m(7),
        _c1_I(-3),
        _c1_I(0),
    ),
    # 9: 990
    (
        _c1_I(990),
        _c1_I(-18),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_ep_p(7),
        _c1_ep_m(7),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_ep_p(7),
        _c1_ep_m(7),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-2),
        _c1_I(3),
        _c1_I(-10),
        _c1_I(0),
        _c1_ep_m(7),
        _c1_ep_p(7),
        _c1_I(6),
        _c1_I(0),
    ),
    # 10: 990bar
    (
        _c1_I(990),
        _c1_I(-18),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_ep_m(7),
        _c1_ep_p(7),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_ep_m(7),
        _c1_ep_p(7),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-2),
        _c1_I(3),
        _c1_I(-10),
        _c1_I(0),
        _c1_ep_p(7),
        _c1_ep_m(7),
        _c1_I(6),
        _c1_I(0),
    ),
    # 11: 1035a
    (
        _c1_I(1035),
        _c1_I(-21),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_2ep_p(7),
        _c1_2ep_m(7),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-3),
        _c1_I(-5),
        _c1_I(0),
        _c1_nep_m(7),
        _c1_nep_p(7),
        _c1_I(3),
        _c1_I(0),
    ),
    # 12: 1035abar
    (
        _c1_I(1035),
        _c1_I(-21),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_2ep_m(7),
        _c1_2ep_p(7),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-3),
        _c1_I(-5),
        _c1_I(0),
        _c1_nep_p(7),
        _c1_nep_m(7),
        _c1_I(3),
        _c1_I(0),
    ),
    # 13: 1035b
    (
        _c1_I(1035),
        _c1_I(27),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_I(3),
        _c1_I(6),
        _c1_I(35),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(3),
        _c1_I(0),
    ),
    # 14: 231
    (
        _c1_I(231),
        _c1_I(7),
        _c1_I(-3),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(0),
        _c1_ep_p(15),
        _c1_ep_m(15),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
        _c1_I(-9),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
    ),
    # 15: 231bar
    (
        _c1_I(231),
        _c1_I(7),
        _c1_I(-3),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(0),
        _c1_ep_m(15),
        _c1_ep_p(15),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
        _c1_I(-9),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
    ),
    # 16: 770
    (
        _c1_I(770),
        _c1_I(-14),
        _c1_I(5),
        _c1_I(0),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_ep_p(23),
        _c1_ep_m(23),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-2),
        _c1_I(-7),
        _c1_I(10),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_I(-1),
    ),
    # 17: 770bar
    (
        _c1_I(770),
        _c1_I(-14),
        _c1_I(5),
        _c1_I(0),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_ep_m(23),
        _c1_ep_p(23),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-2),
        _c1_I(-7),
        _c1_I(10),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_I(-1),
    ),
    # 18: 483
    (
        _c1_I(483),
        _c1_I(35),
        _c1_I(6),
        _c1_I(-2),
        _c1_I(3),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(2),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
        _c1_I(3),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
    ),
    # 19: 1265
    (
        _c1_I(1265),
        _c1_I(49),
        _c1_I(5),
        _c1_I(0),
        _c1_I(1),
        _c1_I(-2),
        _c1_I(-2),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-3),
        _c1_I(8),
        _c1_I(-15),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(-7),
        _c1_I(-1),
    ),
    # 20: 2024
    (
        _c1_I(2024),
        _c1_I(8),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(8),
        _c1_I(24),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(8),
        _c1_I(-1),
    ),
    # 21: 2277
    (
        _c1_I(2277),
        _c1_I(21),
        _c1_I(0),
        _c1_I(-3),
        _c1_I(1),
        _c1_I(2),
        _c1_I(2),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(2),
        _c1_I(-3),
        _c1_I(6),
        _c1_I(-19),
        _c1_I(1),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(-3),
        _c1_I(0),
    ),
    # 22: 3312
    (
        _c1_I(3312),
        _c1_I(48),
        _c1_I(0),
        _c1_I(-3),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-2),
        _c1_I(0),
        _c1_I(-6),
        _c1_I(16),
        _c1_I(1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
    ),
    # 23: 5313
    (
        _c1_I(5313),
        _c1_I(49),
        _c1_I(-15),
        _c1_I(3),
        _c1_I(-3),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-3),
        _c1_I(0),
        _c1_I(9),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
    ),
    # 24: 5796
    (
        _c1_I(5796),
        _c1_I(-28),
        _c1_I(-9),
        _c1_I(1),
        _c1_I(4),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(36),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-4),
        _c1_I(-1),
    ),
    # 25: 5544
    (
        _c1_I(5544),
        _c1_I(-56),
        _c1_I(9),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(24),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-8),
        _c1_I(1),
    ),
    # 26: 10395
    (
        _c1_I(10395),
        _c1_I(-21),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(-1),
        _c1_I(-1),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
        _c1_I(-45),
        _c1_I(0),
        _c1_I(0),
        _c1_I(0),
        _c1_I(3),
        _c1_I(0),
    ),
)

# -------------------------------------------------------------------------
# Checker 1 Private Ring Arithmetic over Z[y, y^-1][[q]]
# -------------------------------------------------------------------------


def _c1_is_int(val: Any) -> bool:
    """Strict boolean rejection: True iff val is int and not bool."""
    return type(val) is int and not isinstance(val, bool)


def _c1_poly_mul(p1: dict[int, int], p2: dict[int, int]) -> dict[int, int]:
    """Cauchy product of Laurent polynomials in Z[y, y^-1]."""
    res: defaultdict[int, int] = defaultdict(int)
    for d1, c1 in p1.items():
        for d2, c2 in p2.items():
            res[d1 + d2] += c1 * c2
    return {d: c for d, c in res.items() if c != 0}


def _c1_poly_add(p1: dict[int, int], p2: dict[int, int], scale: int = 1) -> dict[int, int]:
    """Linear combination of Laurent polynomials in Z[y, y^-1]."""
    res: defaultdict[int, int] = defaultdict(int, p1)
    for d, c in p2.items():
        res[d] += scale * c
    return {d: c for d, c in res.items() if c != 0}


def _c1_series_mul(
    s1: dict[int, dict[int, int]],
    s2: dict[int, dict[int, int]],
    max_q: int,
) -> dict[int, dict[int, int]]:
    """Cauchy product of power series in Z[y, y^-1][[q]] truncated at q^max_q."""
    res: defaultdict[int, defaultdict[int, int]] = defaultdict(lambda: defaultdict(int))
    for q1, p1 in s1.items():
        for q2, p2 in s2.items():
            if q1 + q2 <= max_q:
                prod = _c1_poly_mul(p1, p2)
                for d, c in prod.items():
                    res[q1 + q2][d] += c
    return {q: {d: c for d, c in p.items() if c != 0} for q, p in res.items()}


def _c1_series_div_unit(
    num: dict[int, dict[int, int]],
    den: dict[int, dict[int, int]],
    max_q: int,
) -> dict[int, dict[int, int]]:
    """Inverts unit power series (den[0] == {0: 1}) in Z[y, y^-1][[q]] up to max_q."""
    res: dict[int, dict[int, int]] = {}
    for n in range(max_q + 1):
        cur = num.get(n, {})
        for k in range(1, n + 1):
            if k in den and (n - k) in res:
                cur = _c1_poly_add(cur, _c1_poly_mul(den[k], res[n - k]), scale=-1)
        if any(c != 0 for c in cur.values()):
            res[n] = {d: c for d, c in cur.items() if c != 0}
    return res


# Dynamic cache storing exact derived coefficients to guarantee <1ms subsequent checks
_c1_dynamic_cache: dict[int, int] = {}


def _c1_compute_mock_modular_coefficients(max_n: int) -> dict[int, int]:
    """Derives exact mock modular coefficients A_n (1 <= n <= max_n) via Jacobi theta quotients.

    Computes:
      Z(tau, z) = 8 * [ (theta_2/theta_2(0))^2 + (theta_3/theta_3(0))^2 + (theta_4/theta_4(0))^2 ]
      ch_massless(tau, z) = F(tau, z) * mu(tau, z)
      H(tau) = (Z(tau, z) - 24 * ch_massless(tau, z)) / F(tau, z) = -2 + sum_{n=1}^max_n A_n q^n
    in Z[y, y^-1][[q]], mathematically verifying zero y-dependent residual at every order.
    """
    missing = [n for n in range(1, max_n + 1) if n not in _c1_dynamic_cache]
    if missing:
        max_q = max(max_n, 30)

        # 1. (theta_2(tau, z) / theta_2(tau, 0))^2 with exact 1/4 factor
        num2: dict[int, dict[int, int]] = {0: {0: 1}}
        den2: dict[int, dict[int, int]] = {0: {0: 1}}
        for m in range(1, max_q + 1):
            f1 = {0: {0: 1}, m: {1: 2}, 2 * m: {2: 1}}
            f2 = {0: {0: 1}, m: {-1: 2}, 2 * m: {-2: 1}}
            num2 = _c1_series_mul(num2, _c1_series_mul(f1, f2, max_q), max_q)
            f_den = {0: {0: 1}, m: {0: 4}, 2 * m: {0: 6}, 3 * m: {0: 4}, 4 * m: {0: 1}}
            den2 = _c1_series_mul(den2, f_den, max_q)
        q2 = _c1_series_div_unit(num2, den2, max_q)
        lead2 = {-1: 2, 0: 4, 1: 2}  # 8 * (1/4) * (y + 2 + y^-1)
        t2 = {m: _c1_poly_mul(lead2, p) for m, p in q2.items()}

        # 2. 8 * [ (theta_3/theta_3(0))^2 + (theta_4/theta_4(0))^2 ]
        max_h = 2 * max_q
        num3: dict[int, dict[int, int]] = {0: {0: 1}}
        den3: dict[int, dict[int, int]] = {0: {0: 1}}
        num4: dict[int, dict[int, int]] = {0: {0: 1}}
        den4: dict[int, dict[int, int]] = {0: {0: 1}}
        for k in range(1, max_h + 1, 2):
            f3_1 = {0: {0: 1}, k: {1: 2}, 2 * k: {2: 1}}
            f3_2 = {0: {0: 1}, k: {-1: 2}, 2 * k: {-2: 1}}
            num3 = _c1_series_mul(num3, _c1_series_mul(f3_1, f3_2, max_h), max_h)
            den3 = _c1_series_mul(
                den3, {0: {0: 1}, k: {0: 4}, 2 * k: {0: 6}, 3 * k: {0: 4}, 4 * k: {0: 1}}, max_h
            )

            f4_1 = {0: {0: 1}, k: {1: -2}, 2 * k: {2: 1}}
            f4_2 = {0: {0: 1}, k: {-1: -2}, 2 * k: {-2: 1}}
            num4 = _c1_series_mul(num4, _c1_series_mul(f4_1, f4_2, max_h), max_h)
            den4 = _c1_series_mul(
                den4, {0: {0: 1}, k: {0: -4}, 2 * k: {0: 6}, 3 * k: {0: -4}, 4 * k: {0: 1}}, max_h
            )
        q3 = _c1_series_div_unit(num3, den3, max_h)
        q4 = _c1_series_div_unit(num4, den4, max_h)
        t34 = {
            h // 2: _c1_poly_mul({0: 8}, _c1_poly_add(q3.get(h, {}), q4.get(h, {})))
            for h in range(0, max_h + 1, 2)
        }
        Z = {n: _c1_poly_add(t2.get(n, {}), t34.get(n, {})) for n in range(max_q + 1)}

        # 3. ch_massless(tau, z) = P(q, y) * sum_k (-1)^k q^{k(k+1)/2} y^k (1 - y)/(1 - y q^k)
        numP: dict[int, dict[int, int]] = {0: {0: 1}}
        denP: dict[int, dict[int, int]] = {0: {0: 1}}
        for m in range(1, max_q + 1):
            numP = _c1_series_mul(
                numP,
                _c1_series_mul({0: {0: 1}, m: {1: -1}}, {0: {0: 1}, m: {-1: -1}}, max_q),
                max_q,
            )
            denP = _c1_series_mul(denP, {0: {0: 1}, m: {0: -2}, 2 * m: {0: 1}}, max_q)
        P = _c1_series_div_unit(numP, denP, max_q)

        S: defaultdict[int, defaultdict[int, int]] = defaultdict(lambda: defaultdict(int))
        S[0][0] = 1
        for k in range(1, max_q + 1):
            q_pow = k * (k + 1) // 2
            if q_pow > max_q:
                break
            sign = (-1) ** k
            for j in range((max_q - q_pow) // k + 1):
                tot_q = q_pow + j * k
                S[tot_q][k + j] += sign
                S[tot_q][k + j + 1] -= sign

        for l in range(1, max_q + 1):
            q_pow = l * (l + 1) // 2
            if q_pow > max_q:
                break
            sign = (-1) ** l
            for j in range((max_q - q_pow) // l + 1):
                tot_q = q_pow + j * l
                S[tot_q][-l - j] += sign
                S[tot_q][-l - j - 1] -= sign

        S_series = {q: dict(p) for q, p in S.items()}
        ch_massless = _c1_series_mul(P, S_series, max_q)

        # 4. F(tau, z) = -(y + y^-1 - 2) * prod (1 - y q^m)^2 (1 - y^-1 q^m)^2 / (1 - q^m)
        numF: dict[int, dict[int, int]] = {0: {0: 1}}
        denF: dict[int, dict[int, int]] = {0: {0: 1}}
        for m in range(1, max_q + 1):
            numF = _c1_series_mul(
                numF,
                _c1_series_mul(
                    {0: {0: 1}, m: {1: -2}, 2 * m: {2: 1}},
                    {0: {0: 1}, m: {-1: -2}, 2 * m: {-2: 1}},
                    max_q,
                ),
                max_q,
            )
            denF = _c1_series_mul(denF, {0: {0: 1}, m: {0: -1}}, max_q)
        qF = _c1_series_div_unit(numF, denF, max_q)
        leadF = {-1: -1, 0: 2, 1: -1}
        F = {m: _c1_poly_mul(leadF, p) for m, p in qF.items()}

        # 5. Numerator = Z - 24 * ch_massless
        Num = {
            n: _c1_poly_add(Z.get(n, {}), ch_massless.get(n, {}), scale=-24)
            for n in range(max_q + 1)
        }

        # 6. Exact division H(tau) = Num / F asserting zero y-dependent residual
        H: dict[int, int] = {}
        for n in range(max_q + 1):
            rem = dict(Num.get(n, {}))
            for k in range(1, n + 1):
                if k in F and (n - k) in H:
                    rem = _c1_poly_add(rem, _c1_poly_mul(F[k], {0: H[n - k]}), scale=-1)
            if not rem:
                H[n] = 0
            else:
                hn = -rem.get(1, 0)
                # Mathematical assertion: residual must be exactly hn * F[0]
                if rem.get(-1, 0) != -hn or rem.get(0, 0) != 2 * hn:
                    raise ArithmeticError(
                        f"C1 non-zero y residual in Laurent division at order n={n}"
                    )
                H[n] = hn
            if n >= 1:
                _c1_dynamic_cache[n] = H[n]

    return {n: _c1_dynamic_cache[n] for n in range(1, max_n + 1)}


# -------------------------------------------------------------------------
# Checker 1 Representation Evaluation & Anti-Bypass Defenses
# -------------------------------------------------------------------------


def _c1_parse_val(val: Any) -> tuple[int, int, int]:
    if _c1_is_int(val):
        return (2 * val, 0, 0)
    if isinstance(val, (list, tuple)) and len(val) == 3:
        if all(_c1_is_int(x) for x in val):
            return (val[0], val[1], val[2])
    if isinstance(val, str):
        s = val.strip().replace(" ", "")
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
    raise ValueError(f"Unrecognized character value: {val}")


def _c1_verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Ensures refusal is defect-grounded and not an unwarranted refusal."""
    valid_codes = frozenset(
        {
            "MAX_N_OUT_OF_BOUNDS",
            "UNRECOGNIZED_CLASS_NAME",
            "MALFORMED_CASE_STRUCTURE",
            "UNRECOGNIZED_QUERY",
            "INVALID_QUERY_TYPE",
        }
    )
    if refusal_code not in valid_codes:
        return False, f"FAIL (C1): unrecognized refusal code {refusal_code!r}"

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
        if isinstance(max_n, bool) or not _c1_is_int(max_n):
            return True, "VALID_REFUSAL_MALFORMED"
        if max_n < 1 or max_n > 30:
            if refusal_code == "MAX_N_OUT_OF_BOUNDS":
                return True, "VALID_REFUSAL_MAX_N_OUT_OF_BOUNDS"
            return (
                False,
                f"FAIL (C1): wrong refusal code {refusal_code} for out of bounds max_n={max_n}",
            )
        return False, f"FAIL (C1): unwarranted refusal on valid coefficient query (max_n={max_n})"

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
        unknowns = [c for c in cord if c not in _C1_CLASS_MAP]
        if unknowns:
            if refusal_code == "UNRECOGNIZED_CLASS_NAME":
                return True, "VALID_REFUSAL_UNRECOGNIZED_CLASS_NAME"
            return False, f"FAIL (C1): wrong refusal code {refusal_code} for unknown classes"
        for v in vals:
            if isinstance(v, bool):
                return True, "VALID_REFUSAL_MALFORMED"
        return False, "FAIL (C1): unwarranted refusal on valid decomposition case"

    return False, "FAIL (C1): refusal verification fell through"


def _c1_compute_multiplicities(
    class_order: list[str],
    values: list[Any],
) -> tuple[str, dict[str, Any] | None, dict[str, int] | None]:
    """Direct Frobenius-Schur inner product projection using |M_24| and centralizers."""
    c_vals: list[tuple[int, int, int]] = [None] * 26  # type: ignore[list-item]
    for c_name, val in zip(class_order, values):
        if c_name not in _C1_CLASS_MAP:
            return "UNKNOWN", {"refusal_code": "UNRECOGNIZED_CLASS_NAME"}, None
        idx = _C1_CLASS_MAP[c_name]
        try:
            c_vals[idx] = _c1_parse_val(val)
        except Exception:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    mults: dict[str, int] = {}
    for r_idx, row in enumerate(_C1_TABLE):
        r_name = _C1_IRREPS[r_idx]
        tot_re = 0
        tot_im: dict[int, int] = {7: 0, 15: 0, 23: 0}

        for j in range(26):
            a1, b1, p1 = c_vals[j]
            a2, b2, p2 = row[j]
            p = p1 if b1 != 0 else (p2 if b2 != 0 else 0)

            re4 = a1 * a2 + b1 * b2 * p
            im4 = a2 * b1 - a1 * b2
            cj = _C1_CLASS_SIZES[j]
            tot_re += cj * re4
            if p in tot_im:
                tot_im[p] += cj * im4

        for p, im_val in tot_im.items():
            if im_val != 0:
                return (
                    "OUT_OF_SCOPE",
                    {
                        "kind": "non_zero_imaginary",
                        "irrep": r_name,
                        "value": f"{Fraction(im_val, 4 * _C1_GROUP_ORDER)}*sqrt(-{p})",
                    },
                    None,
                )

        if tot_re % (4 * _C1_GROUP_ORDER) != 0:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "non_integral_multiplicity",
                    "irrep": r_name,
                    "value": str(Fraction(tot_re, 4 * _C1_GROUP_ORDER)),
                },
                None,
            )

        m = tot_re // (4 * _C1_GROUP_ORDER)
        if m < 0:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "negative_multiplicity",
                    "irrep": r_name,
                    "value": m,
                },
                None,
            )

        if m > 0:
            mults[r_name] = m

    return "SOLVED", None, mults


# -------------------------------------------------------------------------
# Checker 1 Main Certificate Verification
# -------------------------------------------------------------------------


def verify_jacobi_character_certificate(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Verifies candidate result using Checker 1 (Frobenius-Schur inner products & theta quotients)."""
    if not isinstance(result, Mapping):
        return False, "FAIL (C1): result is not a dictionary"

    # Schema Whitelist Check
    status = result.get("status")
    if not isinstance(status, str):
        return False, "FAIL (C1): status must be a string"

    query = case.get("query") if isinstance(case, Mapping) else None

    if status == "SOLVED":
        if query == "coefficients":
            allowed = frozenset({"id", "case_id", "status", "A"})
        elif query == "decompose":
            allowed = frozenset({"id", "case_id", "status", "multiplicities", "zero_elsewhere"})
        elif query == "specialization_z0":
            allowed = frozenset({"id", "case_id", "status", "constant"})
        else:
            return False, f"FAIL (C1): SOLVED on unrecognized query {query}"
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C1): phantom keys in SOLVED answer: {set(result.keys()) - allowed}",
            )
    elif status == "OUT_OF_SCOPE":
        allowed = frozenset({"id", "case_id", "status", "witness"})
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C1): phantom keys in OUT_OF_SCOPE answer: {set(result.keys()) - allowed}",
            )
    elif status == "UNKNOWN":
        allowed = frozenset({"id", "case_id", "status", "refusal_code", "refusal"})
        if set(result.keys()) - allowed:
            return (
                False,
                f"FAIL (C1): phantom keys in UNKNOWN answer: {set(result.keys()) - allowed}",
            )
    else:
        return False, f"FAIL (C1): unrecognized or lowercase status: {status!r}"

    # Case ID Parity
    c_id = (
        str(case.get("case_id") or case.get("id") or "")
        if isinstance(case, Mapping)
        else "malformed"
    )
    r_id = str(result.get("id") or result.get("case_id") or "")
    if c_id and r_id != c_id:
        return False, f"FAIL (C1): case ID mismatch: case={c_id} vs result={r_id}"

    # Handle UNKNOWN
    if status == "UNKNOWN":
        rcode = str(result.get("refusal_code") or result.get("refusal") or "")
        if not rcode:
            return False, "FAIL (C1): UNKNOWN status missing refusal_code"
        ok, msg = _c1_verify_refusal_warranted(case, rcode)
        return ok, msg

    # Handle specialization_z0
    if query == "specialization_z0":
        if result.get("constant") != 24:
            return (
                False,
                f"FAIL (C1): specialization constant mismatch: expected 24, got {result.get('constant')}",
            )
        return True, "PASS (C1): specialization constant 24 verified"

    # Handle coefficients
    if query == "coefficients":
        max_n = case.get("max_n")
        if isinstance(max_n, bool) or not _c1_is_int(max_n) or max_n < 1 or max_n > 30:
            return False, f"FAIL (C1): invalid max_n={max_n} but solver returned {status}"

        a_dict = result.get("A")
        if not isinstance(a_dict, dict) or not a_dict:
            return False, "FAIL (C1): missing or empty 'A' dictionary"

        if len(a_dict) != max_n:
            return False, f"FAIL (C1): expected {max_n} coefficients, got {len(a_dict)}"

        # Compute expected coefficients dynamically via exact theta quotient division in Z[y, y^-1][[q]]
        expected_a = _c1_compute_mock_modular_coefficients(max_n)

        for n in range(1, max_n + 1):
            s_n = str(n)
            if s_n not in a_dict:
                return False, f"FAIL (C1): missing order {s_n} in coefficient dict"
            val = a_dict[s_n]
            if not _c1_is_int(val):
                return (
                    False,
                    f"FAIL (C1): coefficient at order {s_n} is not an exact integer: {val!r}",
                )
            expected = expected_a[n]
            if val != expected:
                return (
                    False,
                    f"FAIL (C1): coefficient mismatch at order {s_n}: expected {expected}, got {val}",
                )

        return True, "PASS (C1): coefficients exact match"

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
            return False, "FAIL (C1): malformed decomposition input parameters"

        expected_verdict, witness, exp_mults = _c1_compute_multiplicities(cord, vals)

        if expected_verdict == "OUT_OF_SCOPE":
            if status != "OUT_OF_SCOPE":
                return False, f"FAIL (C1): case warrants OUT_OF_SCOPE, but got status {status}"
            ans_witness = result.get("witness")
            if not isinstance(ans_witness, dict):
                return False, "FAIL (C1): OUT_OF_SCOPE missing witness dictionary"
            if set(ans_witness.keys()) - frozenset({"kind", "irrep", "value"}):
                return False, "FAIL (C1): phantom keys in witness payload"
            if ans_witness.get("kind") not in (
                "non_integral_multiplicity",
                "negative_multiplicity",
                "non_zero_imaginary",
            ):
                return False, f"FAIL (C1): invalid witness kind {ans_witness.get('kind')}"
            # Irrep must be a valid M24 irrep
            if ans_witness.get("irrep") not in _C1_IRREP_SET:
                return False, f"FAIL (C1): witness irrep {ans_witness.get('irrep')} not in M_24"
            return True, "PASS (C1): OUT_OF_SCOPE correctly verified"

        # Case is SOLVED
        if status != "SOLVED":
            return False, f"FAIL (C1): expected SOLVED, got {status}"

        mults = result.get("multiplicities")
        if not isinstance(mults, dict) or mults is None:
            return False, "FAIL (C1): missing 'multiplicities' dictionary"

        if result.get("zero_elsewhere") is not True:
            return False, "FAIL (C1): 'zero_elsewhere' must be strictly boolean True"

        # Strict integer check on all multiplicities
        for irr, m in mults.items():
            if irr not in _C1_IRREP_SET:
                return False, f"FAIL (C1): unrecognized irrep name {irr!r}"
            if not _c1_is_int(m):
                return False, f"FAIL (C1): multiplicity for {irr} is not an exact integer: {m!r}"
            if m <= 0:
                return (
                    False,
                    f"FAIL (C1): non-positive multiplicity in sparse dictionary: {irr}={m}",
                )

        if mults != exp_mults:
            return False, f"FAIL (C1): multiplicity mismatch: expected {exp_mults}, got {mults}"

        # Dimension and all 26 classes reconstruction check (Defense 1: Anti-Dimension Trap)
        for j, c_name in enumerate(_C1_CANONICAL_CLASSES):
            recon_re4 = 0
            recon_im4: dict[int, int] = {7: 0, 15: 0, 23: 0}
            for irr, m in mults.items():
                r_idx = _C1_IRREPS.index(irr)
                a, b, p = _C1_TABLE[r_idx][j]
                recon_re4 += 2 * m * a
                if p in recon_im4:
                    recon_im4[p] += 2 * m * b

            # Compare against input value
            c_idx_in_input = cord.index(c_name)
            inp_val = _c1_parse_val(vals[c_idx_in_input])
            inp_re4 = 2 * inp_val[0]
            if recon_re4 != inp_re4:
                return (
                    False,
                    f"FAIL (C1): class function mismatch at class {c_name}: expected {inp_val[0]}, reconstructed {recon_re4 // 2}",
                )

        return True, "PASS (C1): decomposition exact match across all 26 classes"

    return False, f"FAIL (C1): unhandled query type {query}"
