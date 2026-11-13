"""Exact finite sign switching in a specified real Hamiltonian basis.

For a real symmetric matrix H and a diagonal sign gauge
S = diag((-1)**alpha_i), this module decides whether S H S has
nonpositive off-diagonal entries.  Every nonzero off-diagonal entry
imposes one Z2 constraint:

    alpha_i XOR alpha_j = 1 if H[i][j] > 0, else 0.

The spanning-forest assignment is a complete decision procedure for
*this fixed-basis diagonal-sign gauge family*.  A failed constraint yields
a closed cycle with odd constraint parity, which proves that no such gauge
exists.  Neither outcome decides general BQNF-FSIGN sign freedom or supplies
a sign-reversing meron involution on path-integral configurations.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Sequence


Matrix = tuple[tuple[Fraction, ...], ...]


@dataclass(frozen=True)
class SignGaugeResult:
    """One exact certificate for the specified diagonal-sign gauge family.

    On success, ``gauge`` gives alpha bits and ``transformed`` is S H S.
    On failure, ``cycle`` is a closed vertex walk over nonzero edges whose
    required XOR labels sum to 1.  Exactly one certificate kind is present.
    """

    matrix: Matrix
    gauge: tuple[int, ...] | None
    cycle: tuple[int, ...] | None
    transformed: Matrix | None

    @property
    def gaugeable(self) -> bool:
        return self.gauge is not None


def _rational(value: object, i: int, j: int) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"H[{i}][{j}] must be exact rational, not {type(value).__name__}")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"H[{i}][{j}] must be finite")
        return Fraction(value)
    if isinstance(value, (int, Fraction)):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"H[{i}][{j}] is not an exact rational string") from exc
    raise ValueError(f"H[{i}][{j}] must be an exact rational value")


def parse_matrix(matrix: Sequence[Sequence[object]]) -> Matrix:
    """Validate and canonicalize a nonempty finite real symmetric matrix.

    Accepted scalar encodings are integers, Fractions, finite Decimals, and
    rational strings (for lossless JSON transport).  Binary floats, bools,
    nonfinite values, complex values, ragged rows, and asymmetry are rejected.
    """

    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError("H must be a nonempty square matrix")
    n = len(matrix)
    rows: list[tuple[Fraction, ...]] = []
    for i, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise ValueError(f"H row {i} must have exactly {n} entries")
        rows.append(tuple(_rational(value, i, j) for j, value in enumerate(row)))
    result = tuple(rows)
    for i in range(n):
        for j in range(i + 1, n):
            if result[i][j] != result[j][i]:
                raise ValueError(f"H must be symmetric at ({i}, {j})")
    return result


def _transform(matrix: Matrix, gauge: tuple[int, ...]) -> Matrix:
    signs = tuple(1 if bit == 0 else -1 for bit in gauge)
    return tuple(
        tuple(signs[i] * matrix[i][j] * signs[j] for j in range(len(matrix)))
        for i in range(len(matrix))
    )


def verify_gauge(matrix: Sequence[Sequence[object]], gauge: Sequence[int]) -> bool:
    """Check a proposed alpha witness against every off-diagonal entry."""

    h = parse_matrix(matrix)
    if not isinstance(gauge, (list, tuple)) or len(gauge) != len(h):
        return False
    if any(type(bit) is not int or bit not in (0, 1) for bit in gauge):
        return False
    for i in range(len(h)):
        for j in range(i + 1, len(h)):
            if (1 if gauge[i] == gauge[j] else -1) * h[i][j] > 0:
                return False
    return True


def verify_cycle(matrix: Sequence[Sequence[object]], cycle: Sequence[int]) -> bool:
    """Check an odd-parity, nonzero-edge cycle obstruction."""

    h = parse_matrix(matrix)
    if not isinstance(cycle, (list, tuple)) or len(cycle) < 4:
        return False
    if any(type(v) is not int or v < 0 or v >= len(h) for v in cycle):
        return False
    if cycle[0] != cycle[-1] or len(set(cycle[:-1])) != len(cycle) - 1:
        return False
    parity = 0
    for u, v in zip(cycle, cycle[1:]):
        if h[u][v] == 0:
            return False
        parity ^= int(h[u][v] > 0)
    return parity == 1


def _fundamental_cycle(u: int, v: int, parent: list[int]) -> tuple[int, ...]:
    u_to_root: list[int] = []
    x = u
    while x != -1:
        u_to_root.append(x)
        x = parent[x]
    u_ancestors = {vertex: index for index, vertex in enumerate(u_to_root)}
    v_to_lca: list[int] = []
    x = v
    while x not in u_ancestors:
        v_to_lca.append(x)
        x = parent[x]
    path = u_to_root[: u_ancestors[x] + 1] + list(reversed(v_to_lca))
    return tuple(path + [u])


def classify_sign_gauge(matrix: Sequence[Sequence[object]]) -> SignGaugeResult:
    """Decide exact stoquasticity under diagonal ±1 basis changes.

    The algorithm is linear in the number of nonzero off-diagonal entries
    after the unavoidable O(n²) matrix validation.  Components have their
    root bit fixed to zero, making the returned gauge deterministic.
    """

    h = parse_matrix(matrix)
    n = len(h)
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if h[i][j] != 0:
                label = int(h[i][j] > 0)
                adjacency[i].append((j, label))
                adjacency[j].append((i, label))

    alpha: list[int | None] = [None] * n
    parent = [-1] * n
    for root in range(n):
        if alpha[root] is not None:
            continue
        alpha[root] = 0
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v, label in adjacency[u]:
                expected = alpha[u] ^ label  # type: ignore[operator]
                if alpha[v] is None:
                    alpha[v] = expected
                    parent[v] = u
                    queue.append(v)
                elif alpha[v] != expected:
                    cycle = _fundamental_cycle(u, v, parent)
                    assert verify_cycle(h, cycle)
                    return SignGaugeResult(h, None, cycle, None)

    gauge = tuple(bit for bit in alpha if bit is not None)
    assert len(gauge) == n and verify_gauge(h, gauge)
    return SignGaugeResult(h, gauge, None, _transform(h, gauge))


__all__ = [
    "Matrix",
    "SignGaugeResult",
    "parse_matrix",
    "classify_sign_gauge",
    "verify_gauge",
    "verify_cycle",
]
