# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Two parties, two settings each: every setting is a real unit row, each
correlation is the exact dot product of a near row and a far row, and the
claimed total, local bound and margin are recomputed, never read.

The claim: settings and slots (in declared order), values,
``near(x, s, v)`` and ``far(y, s, v)`` (the rows), ``corr(x, y, v)`` (the
claimed correlation of near setting ``x`` with far setting ``y``),
``total(v)``, ``bound(v)`` and ``excess(v)``.

Relational clauses, carried by derivability over the hosted claim:
``near_given``, ``one_near``, ``far_given``, ``one_far``, ``corr_given``,
``one_corr``, ``total_given``, ``bound_given`` and ``excess_given``.

Decoded clauses, decided over exact values outside the grammar:
``unit_rows`` (each setting row has size one), ``correlations_exact`` (each
claimed correlation is the dot product), ``total_exact`` (the total
``E00 + E01 + E10 - E11`` is computed from the recomputed correlations: a
total written as a label is refused), ``bound_exact`` (the local bound is
the largest total over the sixteen assignments of plus and minus one) and
``excess_exact`` (the margin is the total less the bound).  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import product
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, lean_q, render, rows

CHALLENGE_ID = "two_party_bound"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "TwoPartyBound"
EXACT = ("py.exact.q",)
CLAUSES = ("unit_rows", "correlations_exact", "total_exact", "bound_exact", "excess_exact")


def _grid(fs: FiniteStructure, name: str, first: str, second: str) -> list[list[Q]] | None:
    got: dict[tuple[int, int], Q] = {}
    for a, b, v in rows(fs, name):
        x = fs.value(v)
        if x is None or (a, b) in got:
            return None
        got[(a, b)] = x
    ks, ls = fs.elements(first), fs.elements(second)
    return [[got[(a, b)] for b in ls] for a in ks] if all((a, b) in got for a in ks for b in ls) else None


def _one(fs: FiniteStructure, name: str) -> Q | None:
    got = rows(fs, name)
    return fs.value(got[0][0]) if len(got) == 1 else None


def correlations(fs: FiniteStructure) -> list[list[Q]] | None:
    near, far = _grid(fs, "near", "setting", "slot"), _grid(fs, "far", "setting", "slot")
    if near is None or far is None:
        return None
    return [[sum((a * b for a, b in zip(n, f)), ZERO) for f in far] for n in near]


def total_of(e: list[list[Q]]) -> Q:
    return e[0][0] + e[0][1] + e[1][0] - e[1][1]


def local_bound() -> Q:
    return max(Q(a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1) for a0, a1, b0, b1 in product((-1, 1), repeat=4))


def unit_rows(fs: FiniteStructure, _o: Oracle) -> bool:
    near, far = _grid(fs, "near", "setting", "slot"), _grid(fs, "far", "setting", "slot")
    return near is not None and far is not None and all(sum((x * x for x in r), ZERO) == ONE for r in near + far)


def correlations_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    e, c = correlations(fs), _grid(fs, "corr", "setting", "setting")
    return e is not None and e == c


def total_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    e, t = correlations(fs), _one(fs, "total")
    return e is not None and t == total_of(e)


def bound_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return _one(fs, "bound") == local_bound()


def excess_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    e, x = correlations(fs), _one(fs, "excess")
    return e is not None and x == total_of(e) - local_bound()


def describe(fs: FiniteStructure) -> dict[str, object]:
    e = correlations(fs)
    return {"total": None if e is None else fmt_q(total_of(e)), "local_bound": fmt_q(local_bound())}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "total_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    setting, slot = e.form("setting"), e.form("slot")
    near, far, corr = e.form("near"), e.form("far"), e.form("corr")
    return Compiled(
        (
            Total("near_given", ((setting, ("x",)), (slot, ("s",))), ((near, ("x", "s", "v")),)),
            Functional("one_near", near, 2),
            Total("far_given", ((setting, ("y",)), (slot, ("s",))), ((far, ("y", "s", "v")),)),
            Functional("one_far", far, 2),
            Total("corr_given", ((setting, ("x",)), (setting, ("y",))), ((corr, ("x", "y", "v")),)),
            Functional("one_corr", corr, 2),
            Total("total_given", (), ((e.form("total"), ("v",)),)),
            Total("bound_given", (), ((e.form("bound"), ("v",)),)),
            Total("excess_given", (), ((e.form("excess"), ("v",)),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("unit_rows", unit_rows), ("correlations_exact", correlations_exact), ("total_exact", total_exact),
            ("bound_exact", bound_exact), ("excess_exact", excess_exact))),
    )


LEAN_DEFS = (
    "def dot (a b : List QN) : QN := (List.zipWith (fun x y => x * y) a b).foldl (fun acc x => acc + x) 0",
    "",
    "def unitRows (rs : List (List QN)) : Bool := rs.all fun r => decide (dot r r = 1)",
    "",
    "/-- The correlations: each near row against each far row. -/",
    "def corrs (near far : List (List QN)) : List (List QN) := near.map fun n => far.map fun f => dot n f",
    "",
    "def at2 (e : List (List QN)) (i j : Nat) : QN := (e.getD i []).getD j 0",
    "",
    "def totalOf (e : List (List QN)) : QN := at2 e 0 0 + at2 e 0 1 + at2 e 1 0 - at2 e 1 1",
    "",
    "/-- The largest total over the sixteen assignments of plus and minus one. -/",
    "def localBound : QN :=",
    "  let signs : List QN := [1, -1]",
    "  (signs.flatMap fun a0 => signs.flatMap fun a1 => signs.flatMap fun b0 => signs.map fun b1 =>",
    "    a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1).foldl (fun m x => if QN.pos (x - m) then x else m) (-4)",
    "",
    "def correlationsExact (near far c : List (List QN)) : Bool := decide (corrs near far = c)",
    "",
    "def totalExact (near far : List (List QN)) (t : QN) : Bool := decide (totalOf (corrs near far) = t)",
    "",
    "def boundExact (b : QN) : Bool := decide (localBound = b)",
    "",
    "def excessExact (near far : List (List QN)) (x : QN) : Bool := decide (totalOf (corrs near far) - localBound = x)",
    "",
)
LEAN_CALLS = {"unit_rows": "unitRows (near_{f} ++ far_{f})", "correlations_exact": "correlationsExact near_{f} far_{f} corr_{f}",
              "total_exact": "totalExact near_{f} far_{f} total_{f}", "bound_exact": "boundExact bound_{f}",
              "excess_exact": "excessExact near_{f} far_{f} excess_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    near, far = _grid(fs, "near", "setting", "slot"), _grid(fs, "far", "setting", "slot")
    corr = _grid(fs, "corr", "setting", "setting")
    t, b, x = _one(fs, "total"), _one(fs, "bound"), _one(fs, "excess")
    assert near is not None and far is not None and corr is not None and t is not None and b is not None and x is not None

    def mat(m: list[list[Q]]) -> str:
        return lean_list([lean_list([lean_q(v) for v in r]) for r in m])

    return [("near", "List (List QN)", mat(near)), ("far", "List (List QN)", mat(far)),
            ("corr", "List (List QN)", mat(corr)), ("total", "QN", lean_q(t)), ("bound", "QN", lean_q(b)),
            ("excess", "QN", lean_q(x))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `two_party_bound`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
