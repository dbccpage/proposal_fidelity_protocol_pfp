"""Exact scalar and matrix helpers for the PO-001 certificate rail.

The functions in this module intentionally reject binary floating-point values.
Callers must choose either the exact rail (integers, ``Fraction``, strings, or
exact rationals) or the explicitly labelled numerical-replay rail.

2026-08-31: this module now builds on the stdlib-only ``exactsym`` engine
instead of SymPy, so the deposit runs on stdlib+numpy+pytest alone.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from fractions import Fraction
from typing import TypeAlias

from exactsym import Abs, Basic, Matrix, MatrixBase, Rational, simplify

ExactInput: TypeAlias = int | Fraction | str | Rational


def check_2cell_coboundary_zero(theta_e01: ExactInput, theta_e12: ExactInput, theta_e20: ExactInput) -> bool:
    """Verify 2-cell boundary coboundary sum delta^1 theta = 0 over a 3-cycle (e01, e12, e20)."""
    r01 = as_rational(theta_e01)
    r12 = as_rational(theta_e12)
    r20 = as_rational(theta_e20)
    return bool(r01 + r12 + r20 == 0)


def as_rational(value: ExactInput) -> Rational:
    """Convert an exact scalar representation to ``Rational``.

    ``float`` is deliberately absent from ``ExactInput`` and is rejected at
    runtime as well. Converting a float through its decimal rendering would
    hide the distinction between proof-oriented arithmetic and replay.
    """

    if isinstance(value, bool):
        raise TypeError("Boolean values are not valid exact scalars; use int or Rational")
    if isinstance(value, Rational):
        return value
    if isinstance(value, int):
        return Rational(value)
    if isinstance(value, Fraction):
        return Rational(value.numerator, value.denominator)
    if isinstance(value, str):
        return Rational(value)
    raise TypeError(f"exact arithmetic rejects {type(value).__name__}; use an exact scalar")


def exact_matrix(rows: Sequence[Sequence[ExactInput]]) -> Matrix:
    """Build an exact matrix and reject ragged or floating-point rows."""

    if not rows:
        return Matrix(0, 0, [])
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix rows must have equal length")
    return Matrix([[as_rational(value) for value in row] for row in rows])


def exact_matrix_from_matrix(value: MatrixBase) -> Matrix:
    """Copy a matrix through the exact scalar gate.

    A generic matrix constructor could accept binary floats, so exact public
    APIs must not use it as a validation boundary.
    """

    return Matrix(
        value.rows,
        value.cols,
        [as_rational(value[row, col]) for row in range(value.rows) for col in range(value.cols)],
    )


def exact_column(values: Iterable[ExactInput]) -> Matrix:
    """Build an exact column vector."""

    return Matrix([as_rational(value) for value in values])


def l1_norm(vector: MatrixBase) -> Basic:
    r"""Return the exact :math:`\ell^1` norm of a vector."""

    if vector.cols != 1:
        raise ValueError("l1_norm expects a column vector")
    return simplify(sum(Abs(value) for value in vector))


def exact_equal(left: MatrixBase | Basic, right: MatrixBase | Basic) -> bool:
    """Decide exact equality after canonical simplification."""

    if isinstance(left, MatrixBase) and isinstance(right, MatrixBase):
        return left.shape == right.shape and all(
            bool(simplify(a - b) == 0) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, MatrixBase) or isinstance(right, MatrixBase):
        return False
    return bool(simplify(left - right) == 0)


def expression_text(value: object) -> str:
    """Canonical text used in deterministic JSON evidence."""

    if isinstance(value, MatrixBase):
        return str([[str(simplify(v)) for v in value.row(i)] for i in range(value.rows)])
    if isinstance(value, Basic):
        return str(simplify(value))
    return str(value)
