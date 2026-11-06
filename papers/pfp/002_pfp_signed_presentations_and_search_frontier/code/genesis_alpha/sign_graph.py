"""Exact finite sign holonomy for declared presentation rewrites.

AuthorityEffect: None. This is a host checker for a supplied signed graph. It
does not derive exchange, a Hamiltonian path integral, or a physical FSP claim.
An odd self-loop is permitted: it models a presentation identified with itself
by a sign-changing rewrite, and is the smallest failure of sign descent.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence, Union


@dataclass(frozen=True)
class SignedRewrite:
    source: str
    target: str
    odd: int


@dataclass(frozen=True)
class GaugeWitness:
    vertices: tuple[str, ...]
    bits: tuple[int, ...]


@dataclass(frozen=True)
class OddCycleWitness:
    # Each step is (edge index, departure vertex, arrival vertex).
    steps: tuple[tuple[int, str, str], ...]


SignResult = Union[GaugeWitness, OddCycleWitness]


def _validate(vertices: tuple[str, ...], edges: tuple[SignedRewrite, ...]) -> None:
    if any(not isinstance(v, str) for v in vertices) or len(set(vertices)) != len(vertices):
        raise ValueError("vertices must be distinct strings")
    names = set(vertices)
    for edge in edges:
        if not isinstance(edge, SignedRewrite):
            raise ValueError("rewrite must be a SignedRewrite record")
        if not isinstance(edge.source, str) or not isinstance(edge.target, str):
            raise ValueError("rewrite endpoints must be strings")
        if edge.source not in names or edge.target not in names:
            raise ValueError("rewrite endpoint outside declared carrier")
        if type(edge.odd) is not int or edge.odd not in (0, 1):
            raise ValueError("rewrite parity must be exactly 0 or 1")


def verify_gauge(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], witness: GaugeWitness
) -> bool:
    """Check every equation alpha(source) XOR alpha(target) = odd."""
    vs, es = tuple(vertices), tuple(edges)
    _validate(vs, es)
    if not isinstance(witness, GaugeWitness):
        return False
    if not isinstance(witness.vertices, tuple) or not isinstance(witness.bits, tuple):
        return False
    if witness.vertices != vs or len(witness.bits) != len(vs):
        return False
    if any(type(bit) is not int or bit not in (0, 1) for bit in witness.bits):
        return False
    alpha = dict(zip(vs, witness.bits))
    return all((alpha[e.source] ^ alpha[e.target]) == e.odd for e in es)


def verify_odd_cycle(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], witness: OddCycleWitness
) -> bool:
    """Check a closed edge walk with odd parity, independent of the solver."""
    vs, es = tuple(vertices), tuple(edges)
    _validate(vs, es)
    if not isinstance(witness, OddCycleWitness):
        return False
    if not isinstance(witness.steps, tuple) or not witness.steps:
        return False
    parity = 0
    first_step = witness.steps[0]
    if not isinstance(first_step, tuple) or len(first_step) != 3:
        return False
    first = first_step[1]
    previous = first
    for step in witness.steps:
        if not isinstance(step, tuple) or len(step) != 3:
            return False
        edge_id, departure, arrival = step
        if not isinstance(departure, str) or not isinstance(arrival, str):
            return False
        if type(edge_id) is not int or not 0 <= edge_id < len(es):
            return False
        edge = es[edge_id]
        if departure != previous or {departure, arrival} != {edge.source, edge.target}:
            return False
        parity ^= edge.odd
        previous = arrival
    return previous == first and parity == 1


def classify_sign_graph(
    vertices: Sequence[str], edges: Sequence[SignedRewrite]
) -> SignResult:
    """Return an exact gauge or a checkable odd closed walk.

    This exhausts only vertex Z2 gauges on this finite graph. It says nothing
    about alternative representations, determinant positivity, or regrouping.
    """
    vs, es = tuple(vertices), tuple(edges)
    _validate(vs, es)
    adjacency: dict[str, list[tuple[str, int, int]]] = {v: [] for v in vs}
    for edge_id, edge in enumerate(es):
        adjacency[edge.source].append((edge.target, edge_id, edge.odd))
        if edge.target != edge.source:
            adjacency[edge.target].append((edge.source, edge_id, edge.odd))

    alpha: dict[str, int] = {}
    parent: dict[str, tuple[str, int] | None] = {}
    for root in vs:
        if root in alpha:
            continue
        alpha[root] = 0
        parent[root] = None
        queue = deque([root])
        while queue:
            source = queue.popleft()
            for target, edge_id, odd in adjacency[source]:
                required = alpha[source] ^ odd
                if target not in alpha:
                    alpha[target] = required
                    parent[target] = (source, edge_id)
                    queue.append(target)
                elif alpha[target] != required:
                    cycle = _conflict_cycle(source, target, edge_id, parent)
                    witness = OddCycleWitness(cycle)
                    if not verify_odd_cycle(vs, es, witness):
                        raise RuntimeError("internal odd-cycle construction failed verification")
                    return witness
    witness = GaugeWitness(vs, tuple(alpha[v] for v in vs))
    if not verify_gauge(vs, es, witness):
        raise RuntimeError("internal gauge construction failed verification")
    return witness


def _conflict_cycle(
    source: str, target: str, chord_id: int,
    parent: dict[str, tuple[str, int] | None],
) -> tuple[tuple[int, str, str], ...]:
    ancestors: dict[str, int] = {}
    up_source: list[tuple[int, str, str]] = []
    current = source
    ancestors[current] = 0
    while parent[current] is not None:
        ancestor, edge_id = parent[current]
        up_source.append((edge_id, current, ancestor))
        current = ancestor
        ancestors[current] = len(up_source)

    up_target: list[tuple[int, str, str]] = []
    current = target
    while current not in ancestors:
        item = parent[current]
        if item is None:
            raise AssertionError("conflict endpoints must share a tree root")
        ancestor, edge_id = item
        up_target.append((edge_id, current, ancestor))
        current = ancestor
    tree_to_lca = up_source[:ancestors[current]]
    lca_to_target = [(i, b, a) for i, a, b in reversed(up_target)]
    return tuple(tree_to_lca + lca_to_target + [(chord_id, target, source)])


def matrix_sign_graph(matrix: Sequence[Sequence[int | Fraction]]) -> tuple[tuple[str, ...], tuple[SignedRewrite, ...]]:
    """Adapt a pinned real symmetric matrix to the diagonal sign-gauge graph.

    A positive off-diagonal entry requires an odd gauge difference. This is
    only a fixed-basis stoquasticity adapter; the matrix-to-physics adapter is
    a separate obligation.
    """
    rows = tuple(tuple(row) for row in matrix)
    size = len(rows)
    if any(len(row) != size for row in rows):
        raise ValueError("matrix must be square")
    if any(type(value) not in (int, Fraction) for row in rows for value in row):
        raise ValueError("matrix entries must be exact integers or Fractions")
    if any(rows[i][j] != rows[j][i] for i in range(size) for j in range(i)):
        raise ValueError("matrix must be symmetric")
    vertices = tuple(str(i) for i in range(size))
    edges = tuple(
        SignedRewrite(str(i), str(j), int(rows[i][j] > 0))
        for i in range(size) for j in range(i + 1, size) if rows[i][j] != 0
    )
    return vertices, edges


def classify_matrix_sign_gauge(matrix: Sequence[Sequence[int | Fraction]]) -> SignResult:
    vertices, edges = matrix_sign_graph(matrix)
    return classify_sign_graph(vertices, edges)
