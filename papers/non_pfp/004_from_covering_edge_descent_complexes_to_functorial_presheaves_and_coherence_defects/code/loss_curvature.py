"""Independent rational controls for loss and actual path separation.

Reusable owner: omega_functional::loss_curvature. Inputs are exact SymPy
rational matrices; positivity or physical availability is never inferred.
"""

from dataclasses import dataclass

from sympy import ImmutableMatrix, Rational


def exact_matrix(value: object) -> ImmutableMatrix:
    result = ImmutableMatrix(value)
    if not result.rows or not result.cols or any(x.is_Rational is not True for x in result):
        raise ValueError("nonempty exact rational matrix required")
    return result


def norms(matrix: object) -> tuple[Rational, Rational]:
    m = exact_matrix(matrix)
    columns = [sum(abs(m[i, j]) for i in range(m.rows)) for j in range(m.cols)]
    return max(columns), sum(columns)


def question_loss(map_: object, x: object, y: object, question: object) -> tuple[bool, Rational]:
    p, a, b, q = map(exact_matrix, (map_, x, y, question))
    if a.shape != (p.cols, 1) or b.shape != a.shape or q.shape != (1, p.cols):
        raise ValueError("endpoint shape mismatch")
    return p * (a - b) == ImmutableMatrix.zeros(p.rows, 1), (q * (a - b))[0]


@dataclass(frozen=True)
class SeparationBound:
    curvature: ImmutableMatrix
    separation: Rational
    induced_norm: Rational
    entry_norm: Rational
    induced_floor: Rational
    entry_floor: Rational


def path_separation(
    composed: object, direct: object, difference: object, question: object, margin: Rational
) -> SeparationBound:
    b, r, d, q = map(exact_matrix, (composed, direct, difference, question))
    if b.shape != r.shape or d.shape != (r.cols, 1) or q.shape != (1, r.rows):
        raise ValueError("endpoint shape mismatch")
    if not isinstance(margin, Rational) or margin <= 0:
        raise ValueError("positive rational margin required")
    if r * d != ImmutableMatrix.zeros(r.rows, 1):
        raise ValueError("direct path does not collapse difference")
    separation = abs((q * b * d)[0])
    if separation < margin:
        raise ValueError("separation premise fails")
    k = b - r
    induced, entry = norms(k)
    qnorm = max(abs(x) for x in q)
    return SeparationBound(
        k,
        separation,
        induced,
        entry,
        margin / (qnorm * sum(abs(x) for x in d)),
        margin / (qnorm * max(abs(x) for x in d)),
    )
