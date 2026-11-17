"""Exact discrete Hodge split instances and their reference answers. AuthorityEffect: None.

Standard library only. Every value is a Fraction; no float is created. Instance 0 is the
calibration bank's hodge_split task (workflows/tasks/calibration_task_bank/tasks/hodge_split),
so the reference here is cross-checked against that independent checker in the tests.
"""

from __future__ import annotations

import random
from fractions import Fraction

FIELDS = ("b0", "b1", "euler_characteristic", "potential", "gradient", "curl", "harmonic",
          "harmonic_norm_squared")

CALIBRATION = dict(
    vertices=6,
    edges=((0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (2, 4), (4, 5), (3, 5), (1, 5)),
    triangles=((0, 1, 2), (2, 3, 4)),
    flow=(3, -1, 2, 0, 4, 1, -2, 5, 1),
)


def text(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _d0(n, edges):
    rows = []
    for u, v in edges:
        row = [Fraction(0)] * n
        row[u], row[v] = Fraction(-1), Fraction(1)
        rows.append(row)
    return rows


def _d1(edges, triangles):
    index = {edge: i for i, edge in enumerate(edges)}
    rows = []
    for a, b, c in triangles:
        row = [Fraction(0)] * len(edges)
        row[index[(a, b)]] += 1
        row[index[(b, c)]] += 1
        row[index[(a, c)]] -= 1
        rows.append(row)
    return rows


def _t(m):
    return [list(col) for col in zip(*m)]


def _mm(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def _mv(m, v):
    return [sum(x * y for x, y in zip(row, v)) for row in m]


def _solve(a, b):
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[pivot] = m[pivot], m[col]
        m[col] = [x / m[col][col] for x in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                factor = m[r][col]
                m[r] = [x - factor * y for x, y in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def _rank(m) -> int:
    m = [row[:] for row in m]
    r = 0
    for col in range(len(m[0]) if m else 0):
        pivot = next((i for i in range(r, len(m)) if m[i][col] != 0), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        for i in range(len(m)):
            if i != r and m[i][col] != 0:
                factor = m[i][col] / m[r][col]
                m[i] = [x - factor * y for x, y in zip(m[i], m[r])]
        r += 1
    return r


def reference(inst: dict) -> dict:
    n, edges, tris = inst["vertices"], tuple(map(tuple, inst["edges"])), tuple(map(tuple, inst["triangles"]))
    f = [Fraction(x) for x in inst["flow"]]
    D0, D1 = _d0(n, edges), _d1(edges, tris)
    lap0 = _mm(_t(D0), D0)
    rhs0 = _mv(_t(D0), f)
    p = [Fraction(0)] + _solve([row[1:] for row in lap0[1:]], rhs0[1:])
    gradient = _mv(D0, p)
    q = _solve(_mm(D1, _t(D1)), _mv(D1, f))
    curl = _mv(_t(D1), q)
    harmonic = [x - g - c for x, g, c in zip(f, gradient, curl)]
    r0, r1 = _rank(D0), _rank(D1)
    return {"b0": n - r0, "b1": len(edges) - r0 - r1,
            "euler_characteristic": n - len(edges) + len(tris),
            "potential": [text(x) for x in p], "gradient": [text(x) for x in gradient],
            "curl": [text(x) for x in curl], "harmonic": [text(x) for x in harmonic],
            "harmonic_norm_squared": text(sum(x * x for x in harmonic))}


def _admissible(inst) -> bool:
    n = inst["vertices"]
    edges = [tuple(e) for e in inst["edges"]]
    tris = [tuple(t) for t in inst["triangles"]]
    D0, D1 = _d0(n, edges), _d1(edges, tris)
    if _rank(D0) != n - 1 or _rank(D1) != len(tris):  # connected; faces independent
        return False
    ref = reference(inst)
    return ref["b1"] >= 1 and any(h != "0" for h in ref["harmonic"]) and any(c != "0" for c in ref["curl"])


def generate(index: int) -> dict:
    """Deterministic instance `index`; 0 is the calibration task."""
    if index == 0:
        return {k: [list(x) if isinstance(x, tuple) else x for x in v] if isinstance(v, tuple) else v
                for k, v in CALIBRATION.items()}
    rng = random.Random(f"p1-hodge-{index}")
    while True:
        n = rng.choice((6, 7, 8))
        edges = set()
        for v in range(1, n):  # random spanning tree keeps the complex connected
            edges.add((rng.randrange(v), v))
        while len(edges) < n + rng.choice((2, 3, 4)):
            u, v = sorted(rng.sample(range(n), 2))
            edges.add((u, v))
        edges = sorted(edges, key=lambda e: (e[1], e[0]))
        es = set(edges)
        cliques = [(a, b, c) for a in range(n) for b in range(a + 1, n) for c in range(b + 1, n)
                   if {(a, b), (b, c), (a, c)} <= es]
        if not cliques:
            continue
        tris = sorted(rng.sample(cliques, min(len(cliques), rng.choice((1, 2)))))
        flow = [rng.randint(-5, 5) for _ in edges]
        inst = dict(vertices=n, edges=[list(e) for e in edges], triangles=[list(t) for t in tris], flow=flow)
        if _admissible(inst):
            return inst


SYSTEM = (
    "Answer with one JSON object only, with no code fence and no other text. Fields: "
    "b0 and b1, the Betti numbers over the rationals (integers); euler_characteristic, vertices "
    "minus edges plus filled triangles (integer); potential, p at each vertex in order with "
    "p(0) = \"0\"; gradient, d0 p by edge position; curl, d1^T q by edge position; harmonic, h by "
    "edge position; harmonic_norm_squared, the sum of the squares of the entries of h. Write every "
    "rational value as a string in lowest terms, such as \"-3/2\" or \"4\"."
)


def prose(inst) -> str:
    n, edges, tris, flow = inst["vertices"], inst["edges"], inst["triangles"], inst["flow"]
    rows = "\n".join(f"| {i} | ({u},{v}) |" for i, (u, v) in enumerate(edges))
    filled = " and ".join(f"({a},{b},{c})" for a, b, c in tris)
    return (
        "Compute the exact discrete Hodge decomposition of an edge flow on a finite 2-complex.\n\n"
        f"The complex has vertices {', '.join(str(v) for v in range(n))}. Every edge is oriented from its "
        "smaller vertex to its larger vertex. The edges, in this order, are:\n\n"
        f"| position | edge |\n|---|---|\n{rows}\n\n"
        f"The filled triangles are {filled}, each oriented by increasing vertex order. "
        "No other triangle is filled.\n\n"
        "Coboundary conventions:\n\n"
        "- d0 maps a vertex function p to the edge function (d0 p)(u,v) = p(v) - p(u).\n"
        "- d1 maps an edge function x to the triangle function (d1 x)(a,b,c) = x(a,b) + x(b,c) - x(a,c).\n\n"
        f"The edge flow is f = [{', '.join(str(x) for x in flow)}], listed by edge position.\n\n"
        "Find the unique decomposition f = d0 p + d1^T q + h, where h satisfies d0^T h = 0 and "
        "d1 h = 0, using the standard inner product on edges. Normalise the potential by p(0) = 0."
    )


def _wire_body(inst) -> list[str]:
    n, edges, tris, flow = inst["vertices"], inst["edges"], inst["triangles"], inst["flow"]
    return [
        "hodge<",
        f"  vert<{','.join(str(v) for v in range(n))}>",
        f"  edge<{','.join(f'{u}{v}' for u, v in edges)}>",
        f"  face<{','.join(f'{a}{b}{c}' for a, b, c in tris)}>",
        "  orient<edge=lowtohigh,face=increasing>",
        "  d0<(d0p)(uv)=p(v)-p(u)>",
        "  d1<(d1x)(abc)=x(ab)+x(bc)-x(ac)>",
        f"  flow<{','.join(str(x) for x in flow)}>",
        "  find<f=d0p+d1tq+h>",
        "  law<d0th=0,d1h=0>",
        "  inner<standard>",
        "  norm<p(0)=0>",
    ]


def wire(inst) -> str:
    """Head-word wire, the same content as the prose and nothing more."""
    return "\n".join(_wire_body(inst) + [">"])


def wire_qed(inst) -> str:
    """Symbol Game forcing form: the same wire plus a proof skeleton ending in qed."""
    return "\n".join(_wire_body(inst) + [
        "  proof<",
        "    derive<p:d0td0p=d0tf,p(0)=0>",
        "    derive<q:d1d1tq=d1f>",
        "    derive<h=f-d0p-d1tq>",
        "    check<d0th=0,d1h=0>",
        "    derive<b0,b1,euler>",
        "  >",
        "  qed<h=harmonic>",
        ">",
    ])
