"""Deterministic mirror of ``lean4/Derivation/HigherStructure.lean``:
the declared cell calculus, the four-occurrence demonstration
complex, and the named invariants.

Dimension guards encode the ladder invariant: a ``k+1``-cell is
admissible exactly over a complete, unfilled boundary of ``k``-cells
— the passage's two-rule shape, recurring one dimension up.  The
boundary/coefficient calculus is a separate declaration; its
composite vanishes on the demonstration complex, and two distinct
conventions both work (the non-forcing countermodel).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

Edge = tuple[int, int]
Tri = tuple[int, int, int]
Tet = tuple[int, int, int, int]
CEvent = tuple[object, ...]


@dataclass(frozen=True)
class Complex:
    c0: tuple[int, ...] = ()
    c1: tuple[Edge, ...] = ()
    c2: tuple[Tri, ...] = ()
    c3: tuple[Tet, ...] = ()


EMPTY_COMPLEX = Complex()


def shell1(cx: Complex, i: int, j: int) -> bool:
    return (i in cx.c0 and j in cx.c0 and i != j
            and (i, j) not in cx.c1)


def shell2(cx: Complex, i: int, j: int, k: int) -> bool:
    return ((i, j) in cx.c1 and (j, k) in cx.c1 and (i, k) in cx.c1
            and (i, j, k) not in cx.c2)


def shell3(cx: Complex, i: int, j: int, k: int, l: int) -> bool:
    return ((j, k, l) in cx.c2 and (i, k, l) in cx.c2
            and (i, j, l) in cx.c2 and (i, j, k) in cx.c2
            and (i, j, k, l) not in cx.c3)


def cstep(cx: Complex, e: CEvent) -> Complex:
    kind = e[0]
    if kind == "addV":
        v = e[1]
        assert isinstance(v, int)
        if v in cx.c0:
            return cx
        return replace(cx, c0=cx.c0 + (v,))
    if kind == "addE":
        i, j = e[1], e[2]
        assert isinstance(i, int) and isinstance(j, int)
        if shell1(cx, i, j):
            return replace(cx, c1=cx.c1 + ((i, j),))
        return cx
    if kind == "addT":
        i, j, k = e[1], e[2], e[3]
        assert (isinstance(i, int) and isinstance(j, int)
                and isinstance(k, int))
        if shell2(cx, i, j, k):
            return replace(cx, c2=cx.c2 + ((i, j, k),))
        return cx
    if kind == "addQ":
        i, j, k, l = e[1], e[2], e[3], e[4]
        assert (isinstance(i, int) and isinstance(j, int)
                and isinstance(k, int) and isinstance(l, int))
        if shell3(cx, i, j, k, l):
            return replace(cx, c3=cx.c3 + ((i, j, k, l),))
        return cx
    raise ValueError(f"unknown cell event: {kind!r}")


def creplay(events: list[CEvent], cx: Complex) -> Complex:
    for e in events:
        cx = cstep(cx, e)
    return cx


def k4_events() -> list[CEvent]:
    return [("addV", 0), ("addV", 1), ("addV", 2), ("addV", 3),
            ("addE", 0, 1), ("addE", 1, 2), ("addE", 2, 3),
            ("addE", 0, 2), ("addE", 1, 3), ("addE", 0, 3),
            ("addT", 0, 1, 2), ("addT", 0, 1, 3), ("addT", 0, 2, 3),
            ("addT", 1, 2, 3), ("addQ", 0, 1, 2, 3)]


def k4() -> Complex:
    return creplay(k4_events(), EMPTY_COMPLEX)


def k4_boundary() -> Complex:
    return creplay(k4_events()[:14], EMPTY_COMPLEX)


def alt_num(cx: Complex) -> int:
    """The occurrence alternation number."""
    return len(cx.c0) - len(cx.c1) + len(cx.c2) - len(cx.c3)


def subsets_of(xs: list[int]) -> list[list[int]]:
    if not xs:
        return [[]]
    rest = subsets_of(xs[1:])
    return rest + [[xs[0]] + s for s in rest]


def cut_census(n: int, a: int, b: int) -> int:
    """The cut census: faithful two-block observations of an
    ``n``-carrier separating the designated pair."""
    return len([s for s in subsets_of(list(range(n)))
                if a in s and b not in s])


# ---------------------------------------------------------------------------
# The declared boundary calculus


def bd1(e: Edge) -> list[tuple[int, int]]:
    return [(1, e[1]), (-1, e[0])]


def bd2(t: Tri) -> list[tuple[int, Edge]]:
    return [(1, (t[1], t[2])), (-1, (t[0], t[2])), (1, (t[0], t[1]))]


def bd2_neg(t: Tri) -> list[tuple[int, Edge]]:
    """The opposite orientation convention (non-forcing witness)."""
    return [(-1, (t[1], t[2])), (1, (t[0], t[2])),
            (-1, (t[0], t[1]))]


def bd3(q: Tet) -> list[tuple[int, Tri]]:
    return [(1, (q[1], q[2], q[3])), (-1, (q[0], q[2], q[3])),
            (1, (q[0], q[1], q[3])), (-1, (q[0], q[1], q[2]))]


def push1(ch: list[tuple[int, Edge]]) -> list[tuple[int, int]]:
    return [(c * d, v) for (c, e) in ch for (d, v) in bd1(e)]


def push2(ch: list[tuple[int, Tri]]) -> list[tuple[int, Edge]]:
    return [(c * d, e) for (c, t) in ch for (d, e) in bd2(t)]


def coeff_v(v: int, ch: list[tuple[int, int]]) -> int:
    return sum(c for (c, w) in ch if w == v)


def coeff_e(e: Edge, ch: list[tuple[int, Edge]]) -> int:
    return sum(c for (c, f) in ch if f == e)


def d2_zero_triangles(cx: Complex) -> bool:
    return all(coeff_v(v, push1(bd2(t))) == 0
               for t in cx.c2 for v in cx.c0)


def d2_zero_tet(cx: Complex, q: Tet) -> bool:
    return all(coeff_e(e, push2(bd3(q))) == 0 for e in cx.c1)


def boundary_not_forced(t: Tri) -> bool:
    """Two distinct boundary conventions, both with vanishing
    composite: the convention is declared, not derived."""
    verts = sorted({t[0], t[1], t[2]})
    return (bd2(t) != bd2_neg(t)
            and all(coeff_v(v, push1(bd2(t))) == 0 for v in verts)
            and all(coeff_v(v, push1(bd2_neg(t))) == 0
                    for v in verts))
