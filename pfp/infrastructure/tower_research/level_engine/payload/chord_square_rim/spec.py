# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of research-tree evidence: a square split by a chord into two
triangular faces, its two incidence tables and its rim, all the tree's own.

The witness is ``research/natural_sections`` (read only, through the
vendored clone at its pin; admitted by the author's ruling of 2026-09-25):
its chord square, four corners with the sides 0-1, 1-3, 3-2, 2-0 and the
chord 0-3, each edge in the tree's one orientation, and the two triangular
faces 0-1-3 and 0-3-2 named in its committed receipt.  The tree's code
holds the rest: a signed sum of edge values around each face, the edge
equation (a value on the edge from a to b is the corner value at b minus
the corner value at a) with its search for corner values, and the sum along
the outer walk over the four sides, which its survey finds equal to the two
face sums added on every assignment, at every modulus it surveys.  The
chord lies on both faces and cancels from that sum.

Clauses:

* ``tree_cells``: the corners, oriented edges and faces are the tree's, and
  each face is three distinct corners whose sides are declared edges;
* ``rows_compose``: the claimed face rows times the claimed edge rows is
  zero, with shapes that compose;
* ``rows_replayed``: the claimed edge rows are the tree's edge equation on
  its oriented edges, and the tree's search finds corner values for every
  column; the claimed face rows are the tree's face sums, read on each
  single-edge assignment at every modulus the tree surveys;
* ``rim_replayed``: the declared rim edges are the edges on which exactly
  one of the tree's face sums is nonzero, which must be the edges of the
  tree's outer walk, with the tree's survey finding the outer sum equal to
  the face sums added; the declared rim corners are the ends of those edges;
* ``off_rim_counts``: the counts of corners, edges and faces off that rim.

The refused case is the chord declared on the rim, though both faces run
along it.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from types import ModuleType
from typing import Literal

from operations.use_cases.level_engine.research_engine.level import LevelResult
from operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result, tree_json, tree_module

CHALLENGE_ID = "chord_square_rim"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "natural_sections"
RECEIPT = "receipts/two_complex.json"
SOURCES = (f"research/{TREE}/two_complex.py", f"research/{TREE}/{RECEIPT}")
CLAUSES = ("tree_cells", "rows_compose", "rows_replayed", "rim_replayed", "off_rim_counts")
UNIT_ENTRIES = (-1, 0, 1)


def tree() -> ModuleType:
    return tree_module(TREE, "two_complex")


def _sums() -> tuple[Callable[[tuple[int, ...], int], int], ...]:
    """The tree's two face sums, in the order its receipt names the faces."""
    t = tree()
    return (t.flux_t1, t.flux_t2)


def _directed() -> list[tuple[int, int]]:
    """The tree's oriented edges, in its edge order."""
    return [(a, b) for a, b, _ in sorted(tree().DIRECTED, key=lambda d: d[2])]


def _corners() -> list[int]:
    return sorted({v for edge in _directed() for v in edge})


def _faces() -> list[list[int]]:
    """The faces as the tree's committed receipt names them ("T1=0-1-3,
    T2=0-3-2")."""
    doc = tree_json(TREE, RECEIPT)
    assert isinstance(doc, dict)
    named = str(doc["fixture"]).split("faces", 1)[1]
    return [[int(c) for c in part.split("=", 1)[1].strip().split("-")] for part in named.split(",")]


def _unit(e: int) -> tuple[int, ...]:
    return tuple(int(i == e) for i in range(len(_directed())))


def _lift(v: int, n: int) -> int:
    """A residue read as the nearest integer to zero."""
    return v if v <= n // 2 else v - n


def edge_rows() -> list[list[int]]:
    """The tree's edge equation, as rows: minus one at the edge's source
    corner, one at its target."""
    return [[-1 if v == a else 1 if v == b else 0 for v in _corners()] for a, b in _directed()]


def face_rows() -> list[list[int]]:
    """The tree's face sums on each single-edge assignment, read at its
    largest modulus."""
    n = max(tree().MODULI)
    return [[_lift(s(_unit(e), n), n) for e in range(len(_directed()))] for s in _sums()]


@lru_cache(maxsize=1)
def tree_rim() -> tuple[int, ...]:
    """The edges on which exactly one face sum is nonzero, checked against
    the tree's outer walk and its survey; empty if the tree disagrees."""
    t = tree()
    n = max(t.MODULI)
    k = len(_directed())
    rim = tuple(e for e in range(k) if sum(1 for s in _sums() if s(_unit(e), n) % n) == 1)
    outer = tuple(e for e in range(k) if t.flux_outer(_unit(e), n) % n)
    agrees = all(t.survey(m)["boundary_identity_everywhere"] is True for m in t.MODULI)
    return rim if rim == outer and agrees else ()


def _rim_corners() -> list[int]:
    ends = _directed()
    return sorted({v for e in tree_rim() for v in ends[e]})


def positive() -> Packet:
    faces = _faces()
    return {"corners": _corners(), "edges": [list(e) for e in _directed()], "faces": faces,
            "edge_rows": edge_rows(), "face_rows": face_rows(), "rim_edges": list(tree_rim()),
            "rim_corners": _rim_corners(),
            "off_rim": [len(_corners()) - len(_rim_corners()), len(_directed()) - len(tree_rim()), len(faces)]}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _table(value: object) -> list[list[int]] | None:
    if not isinstance(value, list) or not all(isinstance(r, list) for r in value):
        return None
    if not all(isinstance(x, int) and not isinstance(x, bool) for r in value for x in r):
        return None
    return value


def _cells_ok(pk: Packet) -> bool:
    corners, edges, faces = pk["corners"], pk["edges"], pk["faces"]
    if corners != _corners() or edges != [list(e) for e in _directed()] or faces != _faces():
        return False
    assert isinstance(edges, list) and isinstance(faces, list) and isinstance(corners, list)
    sides = {tuple(e) for e in edges} | {(b, a) for a, b in edges}
    return all(len(set(f)) == 3 and set(f) <= set(corners)
               and all((f[i], f[(i + 1) % 3]) in sides for i in range(3)) for f in faces)


def _composes(pk: Packet) -> bool:
    d0, d1 = _table(pk["edge_rows"]), _table(pk["face_rows"])
    if d0 is None or d1 is None or not d0 or len({len(r) for r in d0}) != 1:
        return False
    if any(len(r) != len(d0) for r in d1):
        return False
    return all(sum(r[e] * d0[e][v] for e in range(len(d0))) == 0 for r in d1 for v in range(len(d0[0])))


def _rows_ok(pk: Packet) -> bool:
    t = tree()
    d0, d1 = _table(pk["edge_rows"]), _table(pk["face_rows"])
    if d0 is None or d1 is None or d0 != edge_rows():
        return False
    if not all(t.potential_exists(tuple(row[v] % n for row in d0), n) for v in range(len(_corners()))
               for n in t.MODULI):
        return False
    k = len(_directed())
    if len(d1) != len(_sums()) or any(len(r) != k or any(x not in UNIT_ENTRIES for x in r) for r in d1):
        return False
    return all((r[e] - s(_unit(e), n)) % n == 0 for r, s in zip(d1, _sums()) for e in range(k) for n in t.MODULI)


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    if not _cells_ok(pk):
        failed.append("tree_cells")
    if not _composes(pk):
        failed.append("rows_compose")
    if not _rows_ok(pk):
        failed.append("rows_replayed")
    rim = tree_rim()
    if not rim or pk["rim_edges"] != list(rim) or pk["rim_corners"] != _rim_corners():
        failed.append("rim_replayed")
    if pk["off_rim"] != [len(_corners()) - len(_rim_corners()), len(_directed()) - len(rim), len(_faces())]:
        failed.append("off_rim_counts")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"corners": len(_corners()), "edges": len(_directed()), "faces": len(_faces()),
             "moduli": list(tree().MODULI), "rim_edges": list(tree_rim())}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
