"""Exact signed terms with a cancellation record: pairs of exact opposites, a
rest, and the claimed total.

The claim: terms (in declared order), values, ``weight(t, v)`` (term ``t``
is the value ``v``), ``paired(s, t)`` (terms ``s`` and ``t`` cancel),
``rest(t)`` (term ``t`` is left over) and ``total(v)``.

Relational clauses, carried by derivability over the hosted claim:
``weights_given``, ``one_weight``, ``typed``, ``pairs_typed``,
``total_given`` and ``one_total``.

Decoded clauses, decided over exact values outside the grammar:
``partition`` (every term is used exactly once, in a pair or in the rest),
``opposite_pairs`` (each pair sums to exactly zero and is not zero),
``rest_one_sign`` (the rest is all of one sign: a zero total with unpaired
terms of both signs is not a cancellation) and ``total_exact``.  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.q import ZERO, Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, lean_q, position, render, rows

CHALLENGE_ID = "signed_totals"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SignedTotals"
EXACT = ("py.exact.q",)
CLAUSES = ("partition", "opposite_pairs", "rest_one_sign", "total_exact")


def terms(fs: FiniteStructure) -> list[Q] | None:
    got: dict[int, Q] = {}
    for t, v in rows(fs, "weight"):
        x = fs.value(v)
        if x is None or t in got:
            return None
        got[t] = x
    ts = fs.elements("term")
    return [got[t] for t in ts] if all(t in got for t in ts) else None


def placed(fs: FiniteStructure) -> tuple[list[tuple[int, int]], list[int]]:
    """The pairs and the rest, as positions in the declared order of terms."""
    pairs = []
    for s, t in rows(fs, "paired"):
        i, j = position(fs, "term", s), position(fs, "term", t)
        if i is not None and j is not None:
            pairs.append((i, j))
    rest = [k for (t,) in rows(fs, "rest") if (k := position(fs, "term", t)) is not None]
    return pairs, rest


def claimed(fs: FiniteStructure) -> Q | None:
    got = rows(fs, "total")
    return fs.value(got[0][0]) if len(got) == 1 else None


def partition(fs: FiniteStructure, _o: Oracle) -> bool:
    ts = terms(fs)
    pairs, rest = placed(fs)
    used = [k for p in pairs for k in p] + rest
    return ts is not None and sorted(used) == list(range(len(ts)))


def opposite_pairs(fs: FiniteStructure, _o: Oracle) -> bool:
    ts = terms(fs)
    return ts is not None and all((ts[i] + ts[j]).is_zero() and not ts[i].is_zero() for i, j in placed(fs)[0])


def rest_one_sign(fs: FiniteStructure, _o: Oracle) -> bool:
    ts = terms(fs)
    if ts is None:
        return False
    signs = {ts[k].sign() for k in placed(fs)[1]} - {0}
    return len(signs) <= 1


def total_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    ts, t = terms(fs), claimed(fs)
    return ts is not None and t is not None and sum(ts, ZERO) == t


def describe(fs: FiniteStructure) -> dict[str, object]:
    ts = terms(fs)
    return {"sum": None if ts is None else fmt_q(sum(ts, ZERO))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "total_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    term, val, weight = e.form("term"), e.form("val"), e.form("weight")
    paired, total = e.form("paired"), e.form("total")
    return Compiled(
        (
            Total("weights_given", ((term, ("t",)),), ((weight, ("t", "v")),)),
            Functional("one_weight", weight, 1),
            Closure("typed", ((weight, ("t", "v")),), ((term, ("t",)), (val, ("v",)))),
            Closure("pairs_typed", ((paired, ("s", "t")),), ((term, ("s",)), (term, ("t",)))),
            Total("total_given", (), ((total, ("v",)),)),
            Functional("one_total", total, 0),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("partition", partition), ("opposite_pairs", opposite_pairs), ("rest_one_sign", rest_one_sign),
            ("total_exact", total_exact))),
    )


LEAN_DEFS = (
    "def tv (ts : List QN) (i : Nat) : QN := ts.getD i 0",
    "",
    "/-- Every term is used exactly once, in a pair or in the rest. -/",
    "def partition (ts : List QN) (ps : List (Prod Nat Nat)) (rs : List Nat) : Bool :=",
    "  let used := ps.foldr (fun p acc => p.1 :: p.2 :: acc) rs",
    "  (List.range ts.length).all (fun i => used.count i == 1) && used.all (fun i => decide (i < ts.length))",
    "",
    "/-- Each pair sums to zero and is not zero. -/",
    "def oppositePairs (ts : List QN) (ps : List (Prod Nat Nat)) : Bool :=",
    "  ps.all fun p => decide (tv ts p.1 + tv ts p.2 = 0) && !decide (tv ts p.1 = 0)",
    "",
    "/-- The rest is all of one sign. -/",
    "def restOneSign (ts : List QN) (rs : List Nat) : Bool :=",
    "  (rs.all fun i => !QN.pos (tv ts i)) || (rs.all fun i => !QN.pos (-(tv ts i)))",
    "",
    "def totalExact (ts : List QN) (t : QN) : Bool := decide (ts.foldl (fun acc x => acc + x) 0 = t)",
    "",
)
LEAN_CALLS = {"partition": "partition terms_{f} pairs_{f} rest_{f}", "opposite_pairs": "oppositePairs terms_{f} pairs_{f}",
              "rest_one_sign": "restOneSign terms_{f} rest_{f}", "total_exact": "totalExact terms_{f} total_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ts, t = terms(fs), claimed(fs)
    assert ts is not None and t is not None
    pairs, rest = placed(fs)
    return [("terms", "List QN", lean_list([lean_q(x) for x in ts])),
            ("pairs", "List (Prod Nat Nat)", lean_list([f"({i}, {j})" for i, j in pairs])),
            ("rest", "List Nat", lean_list([str(k) for k in rest])),
            ("total", "QN", lean_q(t))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `signed_totals`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
