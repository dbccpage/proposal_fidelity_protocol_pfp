"""A claim about a hosted finite table of steps names one value, reads it as
a pole of the table's walk count, and keeps its scope to the table.  The
reading and the scope are derived from the evidence, never from the claim.

The evidence is a finite table of steps between nodes (its arcs).  A claim
names one value ``u`` (``names``), states a reading (``of_kind``: the first
element of the ``kind`` sort is the pole reading, the second a reading that
reaches past the table) and a scope (``in_scope``: the first element of the
``reach`` sort is the table itself, the second reaches past it).

Relational clauses, carried by derivability over the hosted claim:
``arcs_typed``, ``named`` and ``one_value``, ``kind_given`` and ``one_kind``,
``scope_given`` and ``one_scope``, and the two fence clauses
``kind_derived`` (no claim takes the far reading) and ``scope_derived`` (no
claim takes the far scope).  A finite table supports exactly the pole reading
and exactly its own scope, so both fences are fixed by the evidence type.

Decoded clause, decided over exact values outside the grammar:
``vanishes``, the determinant of ``I - uA`` is zero, where ``A`` is the 0/1
table of arcs in the declared order of nodes.  Its Lean certificate is
re-decided by the kernel with the exact-rational library.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.linalg import det
from engine.exact.q import ONE, ZERO, Q, fmt_q
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure

CHALLENGE_ID = "scope_fence"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
EXACT = ("py.exact.q", "py.exact.linalg")


def table(fs: FiniteStructure) -> list[list[Q]]:
    """The 0/1 table of arcs, rows and columns in the declared order of nodes."""
    nodes = fs.elements("node")
    arcs = {tuple(a) for n, a in fs.tuples if n == "arc"}
    return [[ONE if (x, y) in arcs else ZERO for y in nodes] for x in nodes]


def named_value(fs: FiniteStructure) -> Q | None:
    vals = [a[1] for n, a in fs.tuples if n == "names"]
    return fs.value(vals[0]) if len(vals) == 1 else None


def shifted(fs: FiniteStructure) -> list[list[Q]] | None:
    """``I - uA`` for the named value ``u``; ``None`` when no single value is named."""
    u = named_value(fs)
    if u is None:
        return None
    a = table(fs)
    n = len(a)
    return [[(ONE if i == j else ZERO) - u * a[i][j] for j in range(n)] for i in range(n)]


def vanishes(fs: FiniteStructure, _o: Oracle) -> bool:
    m = shifted(fs)
    return m is not None and det(m).is_zero()


def describe(fs: FiniteStructure) -> dict[str, object]:
    u, m = named_value(fs), shifted(fs)
    return {"determinant": None if m is None else fmt_q(det(m)), "value": None if u is None else fmt_q(u)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    """(declaration, fixture, clause) for every fixture whose value clause
    was evaluated: the kernel re-decides the determinant and the verdict."""
    out = []
    for v in verdicts:
        if dict(v.decoded).get("vanishes") in ("PASS", "FAIL"):
            out.append((f"ScopeFence.{v.fid}_determinant", v.fid, "vanishes"))
            out.append((f"ScopeFence.{v.fid}_vanishes", v.fid, "vanishes"))
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    node, arc, claim = e.form("node"), e.form("arc"), e.form("claim")
    names, of_kind, in_scope = e.form("names"), e.form("of_kind"), e.form("in_scope")
    far_kind = fx.structure.elements("kind")[1]
    far_reach = fx.structure.elements("reach")[1]
    return Compiled(
        (
            Closure("arcs_typed", ((arc, ("x", "y")),), ((node, ("x",)), (node, ("y",)))),
            Total("named", ((claim, ("c",)),), ((names, ("c", "v")),)),
            Functional("one_value", names, 1),
            Total("kind_given", ((claim, ("c",)),), ((of_kind, ("c", "k")),)),
            Functional("one_kind", of_kind, 1),
            Total("scope_given", ((claim, ("c",)),), ((in_scope, ("c", "r")),)),
            Functional("one_scope", in_scope, 1),
            Forbid("kind_derived", ((of_kind, ("c", far_kind)),)),
            Forbid("scope_derived", ((in_scope, ("c", far_reach)),)),
        ),
        decoded=(DecodedClause("vanishes", vanishes, EXACT),),
    )


LEAN_MODULE = "ScopeFence"


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """The certificate module: one table and one value per evaluated fixture,
    the determinant of ``I - uA`` and the verdict, each re-decided by the kernel."""
    from engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The determinant clause of `scope_fence`, decided by the kernel", [
        "/-- Entry `(i, j)` of a table. -/",
        "def entry (a : Mat) (i j : Nat) : QN := (a.getD i []).getD j 0",
        "",
        "/-- `I - uA`. -/",
        "def shifted (u : QN) (a : Mat) : Mat :=",
        "  (List.range a.length).map fun i =>",
        "    (List.range a.length).map fun j =>",
        "      (if i = j then 1 else 0) - u * entry a i j",
        "",
        "/-- The determinant of `I - uA` is zero. -/",
        "def vanishes (u : QN) (a : Mat) : Bool := decide (det (shifted u a) = 0)",
        "",
    ])
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        fs = by[fid].structure
        u = named_value(fs)
        assert u is not None
        lines += [f"def table_{fid} : Mat :=", f"  {T.mat(table(fs))}", "",
                  f"def value_{fid} : QN := {T.q(u)}", ""]
    for fid in fids:
        fs = by[fid].structure
        m = shifted(fs)
        assert m is not None
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)["vanishes"] == "PASS" else "false"
        lines += [f"theorem {fid}_determinant : det (shifted value_{fid} table_{fid}) = {T.q(det(m))} := by decide",
                  "",
                  f"theorem {fid}_vanishes : vanishes value_{fid} table_{fid} = {verdict} := by decide",
                  ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
