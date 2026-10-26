"""Exact linear algebra over Q: determinant, leading minors, positive
definiteness, rank, characteristic polynomial.

In Clean Architecture, this module defines the domain Value Object types
(Matrix) and shape invariants, and delegates exact computational algorithms
to the injected ExactLinearAlgebraPort backed by omega_linear_algebra:
- omega_linear_algebra (determinant via Bareiss fraction-free elimination, exact LDLT, rank, SNF)
- omega_homology (simplicial chains, boundaries, orientations)
- omega_holonomy (connections, curvatures, loop holonomy)
- omega_functional (Phi_1, Gamma_2, Xi)

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..ports.exact_ports import ExactLinearAlgebraPort
from .errors import ExactError
from .poly import Poly
from .q import ONE, ZERO, Q

Matrix = tuple[tuple[Q, ...], ...]

_PORT: ExactLinearAlgebraPort | None = None


def set_linear_algebra_port(port: ExactLinearAlgebraPort) -> None:
    """Inject the active linear algebra port (composition root)."""
    global _PORT
    _PORT = port


def get_linear_algebra_port() -> ExactLinearAlgebraPort:
    """Return the active linear algebra port."""
    global _PORT
    if _PORT is None:
        raise ExactError(
            "PORT_UNBOUND",
            "ExactLinearAlgebraPort not configured. Inject RustExactEngineAdapter at composition root.",
        )
    return _PORT


def as_matrix(m: Sequence[Sequence[Q]]) -> Matrix:
    rows = tuple(tuple(r) for r in m)
    for r in rows:
        for x in r:
            if not isinstance(x, Q):
                raise ExactError("RR-FLOAT", "matrix entries must be exact rationals")
    if rows and any(len(r) != len(rows[0]) for r in rows):
        raise ExactError("RR-SHAPE", "ragged matrix")
    return rows


def _square(m: Matrix) -> int:
    n = len(m)
    if any(len(r) != n for r in m):
        raise ExactError("RR-SHAPE", "matrix is not square")
    return n


def is_symmetric(m: Sequence[Sequence[Q]]) -> bool:
    """True if m is square and m = m^T."""
    mm = as_matrix(m)
    n = _square(mm)
    return all(mm[i][j] == mm[j][i] for i in range(n) for j in range(n))


def det(m: Sequence[Sequence[Q]]) -> Q:
    """Exact determinant of square matrix m, delegating to omega_linear_algebra."""
    mm = as_matrix(m)
    _square(mm)
    return get_linear_algebra_port().determinant(mm)


def rank(m: Sequence[Sequence[Q]]) -> int:
    """Exact rank of rectangular matrix m, delegating to omega_linear_algebra."""
    mm = as_matrix(m)
    return get_linear_algebra_port().rank(mm)


def leading_minors(m: Sequence[Sequence[Q]]) -> tuple[Q, ...]:
    """All leading principal minors of square matrix m, delegating to omega_linear_algebra."""
    mm = as_matrix(m)
    _square(mm)
    return get_linear_algebra_port().leading_minors(mm)


def first_nonpositive_minor(m: Sequence[Sequence[Q]]) -> int | None:
    """1-based index of the first leading minor that is not positive, or
    ``None`` when every one is (Sylvester: positive definite).
    """
    if not is_symmetric(m):
        raise ExactError("RR-SHAPE", "positive definiteness needs a symmetric matrix")
    for k, v in enumerate(leading_minors(m), start=1):
        if v.sign() <= 0:
            return k
    return None


def is_positive_definite(m: Sequence[Sequence[Q]]) -> bool:
    """Sylvester's criterion for positive definiteness, delegating to omega_linear_algebra."""
    mm = as_matrix(m)
    if not is_symmetric(mm):
        raise ExactError("RR-SHAPE", "positive definiteness needs a symmetric matrix")
    return get_linear_algebra_port().is_positive_definite(mm)


def char_poly(m: Sequence[Sequence[Q]]) -> Poly:
    """Exact characteristic polynomial det(xI - m), delegating to omega_linear_algebra."""
    mm = as_matrix(m)
    _square(mm)
    return get_linear_algebra_port().characteristic_polynomial(mm)


__all__ = [
    "Matrix",
    "as_matrix",
    "char_poly",
    "det",
    "first_nonpositive_minor",
    "get_linear_algebra_port",
    "is_positive_definite",
    "is_symmetric",
    "leading_minors",
    "rank",
    "set_linear_algebra_port",
]
