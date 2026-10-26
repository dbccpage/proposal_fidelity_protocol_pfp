"""Replay of research-tree evidence: ordered products of link transports
around closed faces, and an open walk refused as a face.

The witness is ``research/natural_sections`` (read only, through the
vendored clone at its pin; admitted by the author's ruling of 2026-09-25),
two of its own objects side by side on one label set of three:

* its chord square: four corners, the sides 0-1, 1-3, 3-2, 2-0 and the chord
  0-3, each edge in the tree's one orientation, and the two triangular faces
  0-1-3 and 0-3-2 named in its committed receipt, each step read along or
  against its edge as the tree's face sums read it.  The edge values are the
  tree's separating assignment over the integers mod 3 (one on 1-3, minus
  one on 3-2, zero elsewhere, from its test of the outer walk).  The tree's
  edge equation (corner value at the target = corner value at the source
  plus the edge value) carries a value at a corner along an edge by adding;
  each edge's transport is that addition, a permutation of the three
  residues;
* its three-occupant run on the square of four sites: the four occupations
  are objects, each move of one occupant to the free neighbouring site is an
  edge (listed once, from the smaller occupation), its transport the
  permutation of sorted indices the tree computes from positions, and the
  face is the closed walk the committed receipt records for that run, with
  the product the receipt records.

The refused case is the chord square's first face with its chord step
dropped: the walk 0-1-3, which ends where it did not start.  At the
separating assignment the chord carries zero, so the dropped step changes no
product; only the closure refuses it.

Clauses, each decided on the packet:

* ``steps_declared``: every face step names a declared edge and a direction,
  along (``+``) or against (``-``);
* ``closed``: every face with declared steps is nonempty, its steps meet, and
  it ends where it starts;
* ``product_exact``: every claimed product is the ordered product of the
  face's transports (a step against its edge reads the inverse), by the
  tree's composition and inversion.

AuthorityEffect: None
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from types import ModuleType
from typing import Any, Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result, tree_json, tree_module

CHALLENGE_ID = "face_walk_products"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "natural_sections"
SQUARE_RECEIPT = "receipts/two_complex.json"
RUN_RECEIPT = "receipts/holonomy_group.json"
SOURCES = (f"research/{TREE}/two_complex.py", f"research/{TREE}/holonomy_group.py",
           f"research/{TREE}/holonomy_fixture.py", f"research/{TREE}/{SQUARE_RECEIPT}",
           f"research/{TREE}/{RUN_RECEIPT}")
CLAUSES = ("steps_declared", "closed", "product_exact")
N = 3
# The tree's separating assignment at modulus 3, edges in its order
# e01, e13, e32, e20, e03 (its test of the outer walk).
SEPARATING = (0, 1, N - 1, 0, 0)
RUN = "square_2x2"
OCCUPANTS = 3

Perm = tuple[int, ...]


def square() -> ModuleType:
    return tree_module(TREE, "two_complex")


def group() -> ModuleType:
    return tree_module(TREE, "holonomy_group")


def adding(a: int) -> Perm:
    """The tree's edge equation read as a transport: a value moves by adding
    the edge value, mod N."""
    return tuple((x + a) % N for x in range(N))


def ordered_product(links: list[Perm], k: int) -> Perm:
    """Links composed in step order by the tree's composition."""
    acc: Perm = group().identity(k)
    for link in links:
        acc = group().compose(link, acc)
    return acc


# ---- the chord square ------------------------------------------------------


def _directed() -> list[tuple[int, int, int]]:
    return sorted(square().DIRECTED, key=lambda d: d[2])


@lru_cache(maxsize=1)
def _corner_faces() -> list[list[int]]:
    """The faces as the tree's committed receipt names them ("T1=0-1-3,
    T2=0-3-2")."""
    doc = tree_json(TREE, SQUARE_RECEIPT)
    assert isinstance(doc, dict)
    named = str(doc["fixture"]).split("faces", 1)[1]
    return [[int(c) for c in part.split("=", 1)[1].strip().split("-")] for part in named.split(",")]


def _step(u: int, v: int) -> list[str]:
    names = square().EDGES
    for a, b, e in _directed():
        if (a, b) == (u, v):
            return [names[e], "+"]
        if (a, b) == (v, u):
            return [names[e], "-"]
    raise KeyError((u, v))


def square_faces() -> list[list[list[str]]]:
    return [[_step(f[i], f[(i + 1) % len(f)]) for i in range(len(f))] for f in _corner_faces()]


def faces_read_the_tree_sums() -> bool:
    """Each face step's direction is the sign of its edge in the tree's face
    sum, read on each single-edge assignment."""
    t = square()
    sums = (t.flux_t1, t.flux_t2)
    names = list(t.EDGES)
    for steps, total in zip(square_faces(), sums):
        signs = {names.index(e): (1 if d == "+" else N - 1) for e, d in steps}
        for e in range(len(names)):
            unit = tuple(int(i == e) for i in range(len(names)))
            if total(unit, N) != signs.get(e, 0):
                return False
    return True


def square_part() -> tuple[list[str], list[list[Any]], list[list[Any]]]:
    t = square()
    corners = sorted({v for a, b, _ in _directed() for v in (a, b)})
    edges = [[t.EDGES[e], str(a), str(b), list(adding(SEPARATING[e]))] for a, b, e in _directed()]
    values = (t.flux_t1(SEPARATING, N), t.flux_t2(SEPARATING, N))
    faces = [[steps, list(adding(v))] for steps, v in zip(square_faces(), values)]
    return [str(c) for c in corners], edges, faces


# ---- the three-occupant run on the square ----------------------------------


def _run_graph() -> tuple[int, tuple[tuple[int, int], ...]]:
    sites, edges = next((s, e) for name, s, e in group().two.fixtures() if name == RUN)
    return sites, tuple(sorted((min(u, v), max(u, v)) for u, v in edges))


def _name(c: object) -> str:
    return "".join(str(x) for x in c)  # type: ignore[attr-defined]


@lru_cache(maxsize=1)
def recorded() -> dict[str, Any]:
    """The committed receipt's component for the run: its closed walk and
    its product."""
    doc = tree_json(TREE, RUN_RECEIPT)
    assert isinstance(doc, dict)
    run = next(r for r in doc["runs"][f"k{OCCUPANTS}"] if r["name"] == RUN)
    comp = run["components"][0]
    assert isinstance(comp, dict)
    return comp


def run_part() -> tuple[list[str], list[list[Any]], list[list[Any]]]:
    sites, edges = _run_graph()
    objs = list(combinations(range(sites), OCCUPANTS))
    links = []
    for a, b in combinations(objs, 2):
        p = group().hop_perm(edges, a, b)
        if p is not None:
            links.append([f"{_name(a)}-{_name(b)}", _name(a), _name(b), list(p)])
    walk = [_name(c) for c in recorded()["witness_closed_walk"]]
    steps = [[f"{u}-{v}", "+"] if u < v else [f"{v}-{u}", "-"] for u, v in zip(walk, walk[1:])]
    return [_name(c) for c in objs], links, [[steps, list(recorded()["witness_permutation"])]]


def run_checks() -> dict[str, bool]:
    """The run recomputed by the tree's code against its receipt, and each
    move's reverse carrying the inverse permutation."""
    sites, edges = _run_graph()
    fresh = group().analyse_k(RUN, sites, edges, OCCUPANTS).json()["components"][0]
    objs = list(combinations(range(sites), OCCUPANTS))
    reverse = all(group().hop_perm(edges, b, a) == group().inverse(p)
                  for a, b in combinations(objs, 2) if (p := group().hop_perm(edges, a, b)) is not None)
    return {"run_replayed": fresh == recorded(), "reverse_moves_are_inverse": reverse}


def positive() -> Packet:
    c1, e1, f1 = square_part()
    c2, e2, f2 = run_part()
    return {"edges": e1 + e2, "faces": f1 + f2, "labels": N, "objects": c1 + c2}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _links(steps: list[list[str]], edges: dict[str, tuple[str, str, Perm]]) -> list[Perm]:
    return [edges[e][2] if d == "+" else group().inverse(edges[e][2]) for e, d in steps]


def _closed(steps: list[list[str]], edges: dict[str, tuple[str, str, Perm]]) -> bool:
    if not steps:
        return False
    ends = [(edges[e][0], edges[e][1]) if d == "+" else (edges[e][1], edges[e][0]) for e, d in steps]
    return all(x[1] == y[0] for x, y in zip(ends, ends[1:])) and ends[-1][1] == ends[0][0]


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    k = pk["labels"]
    assert isinstance(k, int)
    edges = {str(n): (str(s), str(d), tuple(int(x) for x in t)) for n, s, d, t in pk["edges"]}  # type: ignore[attr-defined]
    faces = pk["faces"]
    assert isinstance(faces, list)
    declared = [all(isinstance(st, list) and len(st) == 2 and st[0] in edges and st[1] in ("+", "-")
                    for st in steps) for steps, _ in faces]
    if not all(declared):
        failed.append("steps_declared")
    kept = [(steps, claim) for (steps, claim), ok in zip(faces, declared) if ok]
    if not faces or not all(_closed(steps, edges) for steps, _ in kept):
        failed.append("closed")
    if any(claim != list(ordered_product(_links(steps, edges), k)) for steps, claim in kept):
        failed.append("product_exact")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    t = square()
    _, e2, f2 = run_part()
    by = {n: (s, d, tuple(p)) for n, s, d, p in e2}
    steps = f2[0][0]
    extra = {
        "labels": N, "faces": len(positive()["faces"]),  # type: ignore[arg-type]
        "square_face_values": [t.flux_t1(SEPARATING, N), t.flux_t2(SEPARATING, N)],
        "square_outer_value": t.flux_outer(SEPARATING, N),
        "square_corner_values_exist": t.potential_exists(SEPARATING, N),
        "faces_read_the_tree_sums": faces_read_the_tree_sums(),
        **run_checks(),
        "run_product_in_reverse_order": list(ordered_product(list(reversed(_links(steps, by))), N)),
    }
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
