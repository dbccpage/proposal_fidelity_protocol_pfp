"""Exact arithmetic for the triangle example in Section 3 of Paper 009.

The triangle has vertices 0, 1 and 2 and the oriented edges (0, 1), (1, 2) and
(2, 0). A potential assigns a value to each vertex. Its edge differences are
df(u, v) = f(v) - f(u). Values must be integers or ``Fraction`` objects; floats
and Booleans are refused rather than converted.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

EDGES: tuple[tuple[int, int], ...] = ((0, 1), (1, 2), (2, 0))

Triple = tuple[Fraction, Fraction, Fraction]


def exact_triple(values: Sequence[object], name: str) -> Triple:
    """Return three exact values, refusing any other length or type."""
    if isinstance(values, (str, bytes)) or len(values) != 3:
        raise ValueError(f"{name} must have exactly three entries")
    exact: list[Fraction] = []
    for value in values:
        if type(value) is bool or not isinstance(value, (int, Fraction)):
            raise TypeError(f"{name} entries must be int or Fraction, not {type(value).__name__}")
        exact.append(Fraction(value))
    return (exact[0], exact[1], exact[2])


def edge_differences(potential: Sequence[object]) -> Triple:
    """Return df on the three oriented edges."""
    f = exact_triple(potential, "potential")
    first, second, third = (f[head] - f[tail] for tail, head in EDGES)
    return (first, second, third)


def cycle_sum(edge_values: Sequence[object]) -> Fraction:
    """Return the sum of the edge values around the oriented cycle."""
    return sum(exact_triple(edge_values, "edge values"), Fraction(0))


def subtract(claims: Sequence[object], differences: Sequence[object]) -> Triple:
    """Return claims minus differences, edge by edge."""
    h = exact_triple(claims, "claims")
    d = exact_triple(differences, "differences")
    return (h[0] - d[0], h[1] - d[1], h[2] - d[2])
