"""The sides of a hosted complex agree with the sides of its cells, and the
cells carry a consistent choice of sign.

Claim-only part: each cell's three sides are present.

Existential part: a witness form ``orient(cell, sgn)`` picks one of two sign
data per cell.  With the points of a cell listed in order, its first and last
sides enter its edge sum with the same coefficient and its outer side with
the opposite one.  Two different cells that list a common side must traverse
it in opposite directions: equal coefficients force different signs, and
opposite coefficients force equal signs.  The sign data are a sort of two
elements with no other fact about them (unless a claim names one).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Atom, Closure, Forbid, Functional, Req, Total
from engine.level import Compiled, Fixture

CHALLENGE_ID = "cell_orientation"
ANSWER_TYPE = "D"
BOUND = 3
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()

# position of a side in a cell (points in order x, y, z) and its coefficient
POSITIONS: tuple[tuple[str, int], ...] = (("first", 1), ("last", 1), ("outer", -1))


def _face(face: int, cell: str, pos: str, u: str, v: str, w: str) -> Atom:
    if pos == "first":
        return (face, (cell, u, v, w))
    if pos == "last":
        return (face, (cell, w, u, v))
    return (face, (cell, u, w, v))


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    side, face = e.form("side"), e.form("face")
    cell, sgn = e.form("cell"), e.form("sgn")
    apart, flip = e.form("apart"), e.form("flip")
    orient = e.n_claim_forms()  # the declared witness form comes right after the claim forms
    f = (face, ("c", "x", "y", "z"))
    reqs: list[Req] = [
        Closure("side_first", (f,), ((side, ("x", "y")),)),
        Closure("side_last", (f,), ((side, ("y", "z")),)),
        Closure("side_outer", (f,), ((side, ("x", "z")),)),
        Total("every_cell_signed", ((cell, ("c",)),), ((orient, ("c", "s")), (sgn, ("s",)))),
        Functional("one_sign", orient, 1),
    ]
    for p1, e1 in POSITIONS:
        for p2, e2 in POSITIONS:
            body = [
                _face(face, "c1", p1, "u", "v", "w1"),
                _face(face, "c2", p2, "u", "v", "w2"),
                (apart, ("c1", "c2")),
            ]
            if e1 == e2:
                body += [(orient, ("c1", "s")), (orient, ("c2", "s"))]
            else:
                body += [(orient, ("c1", "s")), (orient, ("c2", "t")), (flip, ("s", "t"))]
            reqs.append(Forbid(f"coherent_{p1}_{p2}", tuple(body)))
    return Compiled(tuple(reqs), witness_forms=((2, (cell, sgn)),), witness_needed=True)
