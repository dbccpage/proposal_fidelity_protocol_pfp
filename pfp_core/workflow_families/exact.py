"""Exact host arithmetic shared by the workflow families.

Everything here is integer or ``Fraction`` arithmetic; no float reaches a
verdict. The graph helpers treat an edge cochain ``c`` on a graph with
oriented edges ``(u, v)``: the coboundary of a vertex potential ``phi`` is
``(delta phi)(u, v) = phi[v] - phi[u]``, and ``c`` is exact (``c = delta phi``)
iff every fundamental cycle sum of ``c`` is zero.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .base import canonical

Vertex = Hashable
Edge = tuple[Vertex, Vertex]


# ---------------------------------------------------------------- linear algebra

def rref(rows: Sequence[Sequence[Any]], modulus: int | None = None) -> tuple[list[list[Any]], list[int]]:
    """Reduced row echelon form over Q (``modulus=None``) or GF(p). Returns (rows, pivot columns)."""
    m = [[Fraction(x) if modulus is None else int(x) % modulus for x in r] for r in rows]
    pivots: list[int] = []
    width = len(m[0]) if m else 0
    r = 0
    for col in range(width):
        pivot = next((i for i in range(r, len(m)) if m[i][col] != 0), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        inv = (1 / m[r][col]) if modulus is None else pow(m[r][col], -1, modulus)
        m[r] = [x * inv if modulus is None else (x * inv) % modulus for x in m[r]]
        for i in range(len(m)):
            if i != r and m[i][col] != 0:
                f = m[i][col]
                row = [a - f * b for a, b in zip(m[i], m[r], strict=True)]
                m[i] = row if modulus is None else [x % modulus for x in row]
        pivots.append(col)
        r += 1
        if r == len(m):
            break
    return m, pivots


def rank(rows: Sequence[Sequence[Any]], modulus: int | None = None) -> int:
    return len(rref(rows, modulus)[1]) if rows else 0


@dataclass(frozen=True)
class LinearStatus:
    status: str  # 'unique' | 'inconsistent' | 'underdetermined'
    solution: tuple[Fraction, ...] | None
    rank_a: int
    rank_ab: int


def classify_linear(a: Sequence[Sequence[Any]], b: Sequence[Any]) -> LinearStatus:
    """Answerability of ``A x = b`` over Q by the Rouche-Capelli rank test."""
    n = len(a[0])
    ra = rank(a)
    aug = [list(row) + [bi] for row, bi in zip(a, b, strict=True)]
    rab = rank(aug)
    if ra != rab:
        return LinearStatus('inconsistent', None, ra, rab)
    if ra < n:
        return LinearStatus('underdetermined', None, ra, rab)
    m, pivots = rref(aug)
    x = [Fraction(0)] * n
    for row, col in zip(m, pivots, strict=False):
        x[col] = row[-1]
    return LinearStatus('unique', tuple(x), ra, rab)


def matmul(a: Sequence[Sequence[Any]], b: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def matvec(a: Sequence[Sequence[Any]], x: Sequence[Any]) -> list[Any]:
    return [sum(r * xi for r, xi in zip(row, x, strict=True)) for row in a]


def dot(x: Sequence[Any], y: Sequence[Any]) -> Any:
    return sum(a * b for a, b in zip(x, y, strict=True))


def det(a: Sequence[Sequence[Any]]) -> Fraction:
    """Exact determinant by Gaussian elimination over Q."""
    m = [[Fraction(x) for x in r] for r in a]
    n = len(m)
    out = Fraction(1)
    for col in range(n):
        pivot = next((i for i in range(col, n) if m[i][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            m[col], m[pivot] = m[pivot], m[col]
            out = -out
        out *= m[col][col]
        for i in range(col + 1, n):
            f = m[i][col] / m[col][col]
            m[i] = [x - f * y for x, y in zip(m[i], m[col], strict=True)]
    return out


def transpose(a: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(r) for r in zip(*a, strict=True)]


# ---------------------------------------------------------------- graph cochains

@dataclass(frozen=True)
class Graph:
    """Finite graph with oriented edges. Vertices are taken from the edges plus ``extra``."""
    edges: tuple[Edge, ...]
    extra: tuple[Vertex, ...] = ()

    @classmethod
    def of(cls, edges: Iterable[Sequence[Vertex]], extra: Iterable[Vertex] = ()) -> Graph:
        return cls(tuple((e[0], e[1]) for e in edges), tuple(extra))

    @property
    def vertices(self) -> list[Vertex]:
        seen: dict[Vertex, None] = {}
        for u, v in self.edges:
            seen.setdefault(u)
            seen.setdefault(v)
        for v in self.extra:
            seen.setdefault(v)
        return list(seen)

    def spanning_forest(self) -> tuple[dict[Vertex, tuple[Vertex, int, int] | None], list[int]]:
        """BFS forest: parent map (vertex -> (parent, edge index, sign)) and chord edge indices."""
        adj: dict[Vertex, list[tuple[Vertex, int, int]]] = {v: [] for v in self.vertices}
        for i, (u, v) in enumerate(self.edges):
            adj[u].append((v, i, 1))
            adj[v].append((u, i, -1))
        parent: dict[Vertex, tuple[Vertex, int, int] | None] = {}
        tree: set[int] = set()
        for root in self.vertices:
            if root in parent:
                continue
            parent[root] = None
            queue = [root]
            while queue:
                x = queue.pop(0)
                for y, i, sign in adj[x]:
                    if y not in parent:
                        parent[y] = (x, i, sign)
                        tree.add(i)
                        queue.append(y)
        return parent, [i for i in range(len(self.edges)) if i not in tree]

    @property
    def cycle_rank(self) -> int:
        """First Betti number b1 = |E| - |V| + #components."""
        return len(self.spanning_forest()[1])

    def coboundary(self, phi: Mapping[Vertex, Any]) -> list[Any]:
        return [phi[v] - phi[u] for u, v in self.edges]

    def potential(self, c: Sequence[Any], modulus: int | None = None) -> dict[Vertex, Any]:
        """Potential that matches ``c`` on the spanning forest (roots at 0)."""
        parent, _ = self.spanning_forest()
        phi: dict[Vertex, Any] = {}

        def value(v: Vertex) -> Any:
            if v in phi:
                return phi[v]
            p = parent[v]
            if p is None:
                phi[v] = 0
            else:
                u, i, sign = p
                # tree edge i oriented u->v (sign 1) gives phi[v] = phi[u] + c[i]
                val = value(u) + sign * c[i]
                phi[v] = val % modulus if modulus else val
            return phi[v]
        for v in self.vertices:
            value(v)
        return phi

    def residual(self, c: Sequence[Any], phi: Mapping[Vertex, Any] | None = None,
                 modulus: int | None = None) -> list[Any]:
        """``r = c - delta phi`` (mod ``modulus`` if given); zero iff ``phi`` explains ``c``."""
        phi = self.potential(c, modulus) if phi is None else phi
        r = [ci - di for ci, di in zip(c, self.coboundary(phi), strict=True)]
        return [x % modulus for x in r] if modulus else r

    def is_exact(self, c: Sequence[Any], modulus: int | None = None) -> bool:
        return not any(self.residual(c, modulus=modulus))

    def phi1(self, c: Sequence[Any], modulus: int | None = None) -> Any:
        """l1 size of the chord residual: zero iff ``c`` is a coboundary."""
        r = self.residual(c, modulus=modulus)
        return sum(min(x, modulus - x) if modulus else abs(x) for x in r)

    def fundamental_cycles(self) -> list[list[tuple[int, int]]]:
        """One signed edge list per chord: ``[(edge index, +1/-1), ...]``."""
        parent, chords = self.spanning_forest()

        def path_to_root(v: Vertex) -> list[tuple[Vertex, int, int]]:
            out = []
            while parent[v] is not None:
                u, i, sign = parent[v]
                out.append((v, i, sign))
                v = u
            return out
        cycles = []
        for ch in chords:
            u, v = self.edges[ch]
            pu, pv = path_to_root(u), path_to_root(v)
            on_u = {x[1] for x in pu}
            on_v = {x[1] for x in pv}
            common = on_u & on_v
            cyc = [(ch, 1)]
            # walk v -> lca along tree, then lca -> u
            cyc += [(i, -sign) for _, i, sign in pv if i not in common]
            cyc += [(i, sign) for _, i, sign in pu if i not in common]
            cycles.append(cyc)
        return cycles

    def cycle_sum(self, c: Sequence[Any], cycle: Sequence[tuple[int, int]], modulus: int | None = None) -> Any:
        s = sum(sign * c[i] for i, sign in cycle)
        return s % modulus if modulus else s


# ---------------------------------------------------------------- custody

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seal_chain(seed: Any, payloads: Sequence[Any]) -> list[str]:
    """``h_0 = H(seed)``, ``h_i = H(h_{i-1} || payload_i)``; any edit changes every later link."""
    h = sha256_bytes(canonical(seed))
    out = [h]
    for p in payloads:
        h = sha256_bytes(h.encode('ascii') + canonical(p))
        out.append(h)
    return out


def commitment(salt: str, artifact: Any) -> str:
    return sha256_bytes(salt.encode('utf-8') + b'\x00' + canonical(artifact))


@dataclass(frozen=True)
class MutationScore:
    valid_total: int
    false_rejections: int
    mutants_total: int
    killed: int

    @property
    def kill_rate(self) -> Fraction:
        return Fraction(self.killed, self.mutants_total) if self.mutants_total else Fraction(0)

    @property
    def sound(self) -> bool:
        return self.false_rejections == 0


def mutation_score(checker: Callable[[Any], bool], valid: Sequence[Any], mutants: Sequence[Any]) -> MutationScore:
    """Run ``checker`` (True = accept) over valid cases and mutants. Exceptions count as rejection."""
    def accepts(x: Any) -> bool:
        try:
            return checker(x) is True
        except Exception:  # noqa: BLE001  (a crashing checker rejects; that is the point of the suite)
            return False
    false_rej = sum(1 for v in valid if not accepts(v))
    killed = sum(1 for m in mutants if not accepts(m))
    return MutationScore(len(valid), false_rej, len(mutants), killed)
