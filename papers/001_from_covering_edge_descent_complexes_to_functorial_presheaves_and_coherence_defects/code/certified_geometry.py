"""Independent rational geometry controls: Euler atan, dyadic bisection sqrt.

Rust uses alternating atan, Machin pi, integer sqrt and Gaussian elimination.
This paper reference uses positive Euler coefficients, pi=4atan(1), bisection,
and SymPy determinants/inversion. Neither uses floats as certificate evidence.
"""

from dataclasses import dataclass
from fractions import Fraction as Q

from sympy import Matrix


def rational(x: object) -> Q:
    if type(x) is not Q:
        raise ValueError("Fraction input required")
    return x


def precision(eps: Q) -> None:
    rational(eps)
    if eps <= 0:
        raise ValueError("positive precision required")


@dataclass(frozen=True)
class Interval:
    lo: Q
    hi: Q

    def __post_init__(self):
        rational(self.lo)
        rational(self.hi)
        if self.lo > self.hi:
            raise ValueError("misordered interval")

    @property
    def width(self) -> Q:
        return self.hi - self.lo

    def add(self, other):
        return Interval(self.lo + other.lo, self.hi + other.hi)

    def sub(self, other):
        return Interval(self.lo - other.hi, self.hi - other.lo)

    def scale(self, scalar):
        a, b = self.lo * scalar, self.hi * scalar
        return Interval(min(a, b), max(a, b))


def root_interval(q: Q, eps: Q) -> Interval:
    rational(q)
    precision(eps)
    if q < 0:
        raise ValueError("negative radicand")
    lo, hi = Q(0), max(Q(1), q)
    for _ in range(4096):
        if hi - lo <= eps:
            return Interval(lo, hi)
        middle = (lo + hi) / 2
        if middle**2 == q:
            return Interval(middle, middle)
        if middle**2 < q:
            lo = middle
        else:
            hi = middle
    raise ValueError("bisection budget exhausted")


def euler_atan(x: Q, eps: Q) -> Interval:
    """For 0<=x<=1: atan x=x/(1+x²) sum c_k z^k, c_k<=1."""
    z = x * x / (1 + x * x)
    total, term = Q(0), x / (1 + x * x)
    for n in range(1, 4097):
        total += term
        tail = x * z**n
        if tail <= eps:
            return Interval(total, total + tail)
        term *= z * Q(2 * n, 2 * n + 1)
    raise ValueError("Euler series budget exhausted")


def pi_interval(eps: Q) -> Interval:
    precision(eps)
    return euler_atan(Q(1), eps / 4).scale(Q(4))


def atan_interval(x: Q, eps: Q) -> Interval:
    rational(x)
    precision(eps)
    if x < 0:
        return atan_interval(-x, eps).scale(Q(-1))
    if x <= 1:
        return euler_atan(x, eps)
    return pi_interval(eps).scale(Q(1, 2)).sub(euler_atan(1 / x, eps / 2))


def dihedral(squared: list[list[Q]], eps: Q) -> tuple[Interval, tuple[Q, Q, Q]]:
    precision(eps)
    if len(squared) != 5 or any(len(row) != 5 for row in squared):
        raise ValueError("5x5 squared metric required")
    for i in range(5):
        for j in range(5):
            rational(squared[i][j])
            if (
                squared[i][j] != squared[j][i]
                or (i == j and squared[i][j] != 0)
                or (i != j and squared[i][j] <= 0)
            ):
                raise ValueError("invalid squared metric")
    gram = Matrix(
        4, 4, lambda i, j: (squared[0][i + 1] + squared[0][j + 1] - squared[i + 1][j + 1]) / 2
    )
    if any(gram[:k, :k].det() <= 0 for k in range(1, 5)):
        raise ValueError("Gram matrix not positive definite")
    normal = gram[2:, 2:] - gram[2:, :2] * gram[:2, :2].inv() * gram[:2, 2:]
    aa, bb, ab = Q(normal[0, 0]), Q(normal[1, 1]), Q(normal[0, 1])
    if ab == 0:
        return pi_interval(eps).scale(Q(1, 2)), (aa, bb, ab)
    root = root_interval(aa * bb - ab * ab, abs(ab) * eps / 4)
    lower = atan_interval(root.lo / abs(ab), eps / 4)
    upper = atan_interval(root.hi / abs(ab), eps / 4)
    theta = Interval(lower.lo, upper.hi)
    if ab < 0:
        theta = pi_interval(eps / 4).sub(theta)
    return theta, (aa, bb, ab)


def deficit(
    hinge: tuple[int, int, int], cycle: tuple[int, ...], edges: dict[tuple[int, int], Q], eps: Q
) -> Interval:
    precision(eps)
    if (
        not 3 <= len(cycle) <= 16
        or len(set(hinge + cycle)) != 3 + len(cycle)
        or any(type(x) is not int for x in hinge + cycle)
    ):
        raise ValueError("distinct hinge and cyclic link required")
    simplices = [hinge + (cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
    required = {
        tuple(sorted((s[i], s[j]))) for s in simplices for i in range(5) for j in range(i + 1, 5)
    }
    if set(edges) != required or any(rational(q) <= 0 for q in edges.values()):
        raise ValueError("exact shared edge coverage required")
    tol = eps / (len(cycle) + 2)
    result = pi_interval(tol).scale(Q(2))
    for s in simplices:
        squared = [
            [Q(0) if i == j else edges[tuple(sorted((s[i], s[j])))] for j in range(5)]
            for i in range(5)
        ]
        result = result.sub(dihedral(squared, tol)[0])
    return result
