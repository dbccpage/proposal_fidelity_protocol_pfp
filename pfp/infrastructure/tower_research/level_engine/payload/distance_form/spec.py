# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A hosted finite point set declares a squared distance for every ordered
pair of its points; the form built from those squared distances is positive
definite.  Incidence is checked before anything is computed from values.

Relational clauses, carried by derivability over the hosted claim:
``complete`` (every ordered pair has a value), ``symmetric``, ``one_value``
and ``typed``.

Decoded clauses, decided over exact values outside the grammar (the sealed
grammar does no arithmetic): ``diagonal_zero`` and ``form_positive``, with
``G[i][j] = (d(0,i) + d(0,j) - d(i,j)) / 2`` over exact Q and Sylvester's
criterion on leading minors.  Their Lean certificates need the exact
rational library in Lean (``ExactRat``): each evaluated fixture's value
clauses are re-decided by the kernel in ``lean/DistanceForm.lean``, and the
row names every certificate the axiom report lacks.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import first_nonpositive_minor, leading_minors
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "distance_form"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
EXACT = ("py.exact.q", "py.exact.linalg")


def table(fs: FiniteStructure) -> dict[tuple[int, int], Q] | None:
    """Decoded squared distances by ordered pair; ``None`` when a pair is
    missing, carries two values, differs between its two orders, or a value
    is undecodable."""
    pts = fs.elements("pt")
    out: dict[tuple[int, int], Q] = {}
    for name, args in fs.tuples:
        if name != "sq" or len(args) != 3:
            continue
        x, y, v = args
        val = fs.value(v)
        if val is None or (x, y) in out:
            return None
        out[(x, y)] = val
    if any((x, y) not in out for x in pts for y in pts):
        return None
    if any(out[(x, y)] != out[(y, x)] for x in pts for y in pts):
        return None
    return out


def form(fs: FiniteStructure) -> list[list[Q]] | None:
    d = table(fs)
    if d is None:
        return None
    pts = fs.elements("pt")
    o, rest = pts[0], pts[1:]
    two = Q(2)
    return [[(d[(o, i)] + d[(o, j)] - d[(i, j)]) / two for j in rest] for i in rest]


def diagonal_zero(fs: FiniteStructure, _o: Oracle) -> bool:
    d = table(fs)
    return d is not None and all(d[(x, x)].is_zero() for x in fs.elements("pt"))


def form_positive(fs: FiniteStructure, _o: Oracle) -> bool:
    g = form(fs)
    return g is not None and first_nonpositive_minor(g) is None


def describe(fs: FiniteStructure) -> dict[str, object]:
    g = form(fs)
    if g is None:
        return {"form": None}
    return {
        "first_nonpositive_minor": first_nonpositive_minor(g),
        "form": [[fmt_q(x) for x in row] for row in g],
        "leading_minors": [fmt_q(x) for x in leading_minors(g)],
    }


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    """(declaration, fixture, clause) for every fixture whose value clauses
    were evaluated: the kernel re-decides the diagonal, the form, and the
    index of the first non-positive leading minor."""
    out = []
    for v in verdicts:
        if dict(v.decoded).get("form_positive") in ("PASS", "FAIL"):
            out.append((f"DistanceForm.{v.fid}_diagonal_zero", v.fid, "diagonal_zero"))
            out.append((f"DistanceForm.{v.fid}_form_positive", v.fid, "form_positive"))
            out.append((f"DistanceForm.{v.fid}_first_nonpositive", v.fid, "form_positive"))
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    sq, pt, val = e.form("sq"), e.form("pt"), e.form("val")
    return Compiled(
        (
            Total("complete", ((pt, ("x",)), (pt, ("y",))), ((sq, ("x", "y", "v")), (val, ("v",)))),
            Closure("symmetric", ((sq, ("x", "y", "v")),), ((sq, ("y", "x", "v")),)),
            Functional("one_value", sq, 2),
            Closure("typed", ((sq, ("x", "y", "v")),), ((pt, ("x",)), (pt, ("y",)), (val, ("v",)))),
        ),
        decoded=(
            DecodedClause("diagonal_zero", diagonal_zero, EXACT),
            DecodedClause("form_positive", form_positive, EXACT),
        ),
    )
