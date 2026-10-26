# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A record computes the exact polynomial of a hosted finite table, and keeps
its scope to the table.

The evidence is a square table of exact entries (``entry(i, j, v)`` over the
``slot`` sort, in the declared order of slots).  A record declares the
coefficients of ``det(xI - A)`` (``coef(p, v)``: the power ``p`` is an exact
natural), rational roots it claims (``root``), intervals it claims each hold a
root (``fence(record, lo, hi)``) and a scope (``in_scope``: the first element
of the ``reach`` sort is the table itself, the second reaches past it).

Relational clauses, carried by derivability over the hosted claim:
``entries_complete``, ``one_entry``, ``entries_typed``, ``one_coef``,
``coef_typed``, ``scope_given``, ``one_scope``, and the fence clause
``scope_derived`` (a finite table supports only its own scope).

Decoded clauses, decided over exact values outside the grammar:
``polynomial`` (the declared coefficients are exactly those of
``det(xI - A)``, computed by the Faddeev-LeVerrier recurrence, never read),
``roots_vanish`` (every claimed root is a root of the computed polynomial:
an irrational root rounded to a rational is not) and ``fences_change_sign``
(each interval has ``lo < hi`` and the computed polynomial changes sign
across it).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import char_poly
from omega_engine_operations.use_cases.level_engine.research_engine.exact.poly import Poly
from omega_engine_operations.use_cases.level_engine.research_engine.exact.poly import evaluate as value_at
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "table_polynomial"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "TablePolynomial"
EXACT = ("py.exact.q", "py.exact.linalg")
CLAUSES = ("polynomial", "roots_vanish", "fences_change_sign")


def _rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    return [a for n, a in fs.tuples if n == name]


def table(fs: FiniteStructure) -> list[list[Q]] | None:
    """The square table in the declared order of slots; ``None`` when an
    entry is missing, repeated or undecodable."""
    slots = fs.elements("slot")
    got: dict[tuple[int, int], Q] = {}
    for i, j, v in _rows(fs, "entry"):
        val = fs.value(v)
        if val is None or (i, j) in got:
            return None
        got[(i, j)] = val
    if any((i, j) not in got for i in slots for j in slots):
        return None
    return [[got[(i, j)] for j in slots] for i in slots]


def computed(fs: FiniteStructure) -> Poly | None:
    """``det(xI - A)``, low to high degree."""
    a = table(fs)
    return None if a is None else char_poly(a)


def declared(fs: FiniteStructure) -> dict[int, Q] | None:
    """The declared coefficients by power; ``None`` when a power is not an
    exact natural, repeats, or a value is undecodable."""
    out: dict[int, Q] = {}
    for p, v in _rows(fs, "coef"):
        power, val = fs.value(p), fs.value(v)
        if power is None or val is None or power.den != 1 or power.num < 0 or power.num in out:
            return None
        out[power.num] = val
    return out


def roots(fs: FiniteStructure) -> list[Q | None]:
    return [fs.value(r) for _, r in _rows(fs, "root")]


def fences(fs: FiniteStructure) -> list[tuple[Q | None, Q | None]]:
    return [(fs.value(lo), fs.value(hi)) for _, lo, hi in _rows(fs, "fence")]


def polynomial(fs: FiniteStructure, _o: Oracle) -> bool:
    a, d = table(fs), declared(fs)
    if a is None or d is None:
        return False
    c = char_poly(a)
    n = len(a)
    full = [c[k] if k < len(c) else ZERO for k in range(n + 1)]
    return set(d) == set(range(n + 1)) and all(d[k] == full[k] for k in range(n + 1))


def roots_vanish(fs: FiniteStructure, _o: Oracle) -> bool:
    c = computed(fs)
    return c is not None and all(r is not None and value_at(c, r).is_zero() for r in roots(fs))


def fences_change_sign(fs: FiniteStructure, _o: Oracle) -> bool:
    c = computed(fs)
    if c is None:
        return False
    for lo, hi in fences(fs):
        if lo is None or hi is None or not (hi - lo).sign() > 0:
            return False
        if (value_at(c, lo) * value_at(c, hi)).sign() >= 0:
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    c = computed(fs)
    if c is None:
        return {"polynomial_high_to_low": None}
    return {
        "polynomial_high_to_low": [fmt_q(x) for x in reversed(c)],
        "at_roots": [None if r is None else fmt_q(value_at(c, r)) for r in roots(fs)],
        "at_fences": [None if lo is None or hi is None else [fmt_q(value_at(c, lo)), fmt_q(value_at(c, hi))]
                      for lo, hi in fences(fs)],
    }


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    """(declaration, fixture, clause) for every fixture whose value clauses
    were evaluated."""
    out = []
    for v in verdicts:
        if dict(v.decoded).get("polynomial") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, num, record = e.form("slot"), e.form("num"), e.form("record")
    entry, coef, in_scope = e.form("entry"), e.form("coef"), e.form("in_scope")
    far_reach = fx.structure.elements("reach")[1]
    return Compiled(
        (
            Total("entries_complete", ((slot, ("i",)), (slot, ("j",))), ((entry, ("i", "j", "v")),)),
            Functional("one_entry", entry, 2),
            Closure("entries_typed", ((entry, ("i", "j", "v")),), ((slot, ("i",)), (slot, ("j",)), (num, ("v",)))),
            Functional("one_coef", coef, 1),
            Closure("coef_typed", ((coef, ("p", "v")),), ((num, ("p",)), (num, ("v",)))),
            Total("scope_given", ((record, ("r",)),), ((in_scope, ("r", "x")),)),
            Functional("one_scope", in_scope, 1),
            Forbid("scope_derived", ((in_scope, ("r", far_reach)),)),
        ),
        decoded=(
            DecodedClause("polynomial", polynomial, EXACT),
            DecodedClause("roots_vanish", roots_vanish, EXACT),
            DecodedClause("fences_change_sign", fences_change_sign, EXACT),
        ),
    )


LEAN_DEFS = (
    "/-- Entry `(i, j)` of a table. -/",
    "def entry (a : Mat) (i j : Nat) : QN := (a.getD i []).getD j 0",
    "",
    "/-- The product of two `n` by `n` tables. -/",
    "def mmul (a b : Mat) (n : Nat) : Mat :=",
    "  (List.range n).map fun i => (List.range n).map fun j =>",
    "    (List.range n).foldl (fun acc t => acc + entry a i t * entry b t j) 0",
    "",
    "/-- The trace of an `n` by `n` table. -/",
    "def trace (a : Mat) (n : Nat) : QN := (List.range n).foldl (fun acc i => acc + entry a i i) 0",
    "",
    "/-- `a + cI`, as an `n` by `n` table. -/",
    "def addScalar (a : Mat) (c : QN) (n : Nat) : Mat :=",
    "  (List.range n).map fun i => (List.range n).map fun j => entry a i j + (if i = j then c else 0)",
    "",
    "/-- One Faddeev-LeVerrier step: `M_k = A M_(k-1) + c_(k-1) I`, then `c_k = -tr(A M_k) / k`. -/",
    "def flStep (a : Mat) (n : Nat) (acc : Prod (List QN) Mat) (k : Nat) : Prod (List QN) Mat :=",
    "  let mk := addScalar (mmul a acc.2 n) (acc.1.getLastD 1) n",
    "  (acc.1 ++ [-(trace (mmul a mk n) n) * QN.ofPair 1 (k + 1)], mk)",
    "",
    "/-- The coefficients of `det(xI - A)`, highest degree first. -/",
    "def charCoeffs (a : Mat) : List QN :=",
    "  ((List.range a.length).foldl (flStep a a.length) ([1], addScalar [] 0 a.length)).1",
    "",
    "/-- A polynomial, highest degree first, at `x` (Horner). -/",
    "def eval (cs : List QN) (x : QN) : QN := cs.foldl (fun acc c => acc * x + c) 0",
    "",
    "/-- The declared coefficients are the computed ones. -/",
    "def polynomial (a : Mat) (cs : List QN) : Bool := decide (charCoeffs a = cs)",
    "",
    "/-- Every claimed root is a root of the computed polynomial. -/",
    "def rootsVanish (a : Mat) (rs : List QN) : Bool := rs.all fun r => decide (eval (charCoeffs a) r = 0)",
    "",
    "/-- Each interval is proper and the computed polynomial changes sign across it. -/",
    "def fencesChangeSign (a : Mat) (fs : List (Prod QN QN)) : Bool :=",
    "  fs.all fun f => QN.pos (f.2 - f.1) && QN.pos (-(eval (charCoeffs a) f.1 * eval (charCoeffs a) f.2))",
    "",
)
LEAN_CALLS = {"polynomial": "polynomial table_{f} coefs_{f}", "roots_vanish": "rootsVanish table_{f} roots_{f}",
              "fences_change_sign": "fencesChangeSign table_{f} fences_{f}"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One table and its declared coefficients, roots and intervals per
    evaluated fixture; the kernel recomputes the polynomial and re-decides
    each clause."""
    from omega_engine_operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `table_polynomial`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        fs = by[fid].structure
        a, d = table(fs), declared(fs)
        assert a is not None and d is not None
        high = [d[k] for k in sorted(d, reverse=True)]
        rs = [r for r in roots(fs) if r is not None]
        fz = [(lo, hi) for lo, hi in fences(fs) if lo is not None and hi is not None]
        lines += [f"def table_{fid} : Mat :=", f"  {T.mat(a)}", "",
                  f"def coefs_{fid} : List QN := {T.row(high)}", "",
                  f"def roots_{fid} : List QN := {T.row(rs)}", "",
                  f"def fences_{fid} : List (Prod QN QN) := ["
                  + ", ".join(f"({T.q(lo)}, {T.q(hi)})" for lo, hi in fz) + "]", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause].format(f=fid)} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
