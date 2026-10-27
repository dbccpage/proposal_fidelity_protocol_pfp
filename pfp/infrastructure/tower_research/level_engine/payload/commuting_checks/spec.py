# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Checks and errors as two-part words over sites, and the claimed reading
of each error against each check.

The claim: sites, checks and errors (each in declared order),
``check_x(q, s)`` and ``check_z(q, s)`` (check ``q`` has a one in its first
or second part at site ``s``), ``error_x(e, s)`` and ``error_z(e, s)``
likewise, and ``reads(e, q)`` (the claimed reading of error ``e`` against
check ``q`` is one; otherwise zero).  Two words exchange at a site when one
has a first-part one and the other a second-part one there; they commute
when their exchange count is even.

Relational clauses, carried by derivability over the hosted claim: each
word part is over a declared word and site (``check_x_typed``,
``check_z_typed``, ``error_x_typed``, ``error_z_typed``) and each reading
is of an error against a check (``reads_typed``).  A word therefore has one
entry per site by construction.

Decoded clauses, decided outside the grammar (they count modulo two):
``checks_commute`` (every two checks commute: anticommuting checks are
refused), ``readings_distinct`` (the recomputed readings of the errors are
nonzero and pairwise distinct) and ``readings_exact`` (each claimed reading
is the recomputed one).  Their Lean certificates are re-decided by the
kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Oracle, Req
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, render, rows

CHALLENGE_ID = "commuting_checks"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "CommutingChecks"
EXACT: tuple[str, ...] = ()
CLAUSES = ("checks_commute", "readings_distinct", "readings_exact")
Word = tuple[tuple[int, ...], tuple[int, ...]]


def words(fs: FiniteStructure, kind: str) -> list[Word]:
    """Each check or error as (first part, second part), one bit per site."""
    sites = fs.elements("site")
    out = []
    for w in fs.elements(kind):
        x = {s for ww, s in rows(fs, f"{kind}_x") if ww == w}
        z = {s for ww, s in rows(fs, f"{kind}_z") if ww == w}
        out.append((tuple(int(s in x) for s in sites), tuple(int(s in z) for s in sites)))
    return out


def exchange(u: Word, v: Word) -> int:
    return sum(a * b for a, b in zip(u[0], v[1])) + sum(a * b for a, b in zip(u[1], v[0]))


def recomputed(fs: FiniteStructure) -> list[tuple[int, ...]]:
    checks = words(fs, "check")
    return [tuple(exchange(e, c) % 2 for c in checks) for e in words(fs, "error")]


def declared(fs: FiniteStructure) -> list[tuple[int, ...]]:
    got = set(rows(fs, "reads"))
    return [tuple(int((e, q) in got) for q in fs.elements("check")) for e in fs.elements("error")]


def checks_commute(fs: FiniteStructure, _o: Oracle) -> bool:
    cs = words(fs, "check")
    return all(exchange(u, v) % 2 == 0 for i, u in enumerate(cs) for v in cs[i + 1:])


def readings_distinct(fs: FiniteStructure, _o: Oracle) -> bool:
    rs = recomputed(fs)
    return all(any(r) for r in rs) and len(set(rs)) == len(rs)


def readings_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return recomputed(fs) == declared(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"readings": ["".join(map(str, r)) for r in recomputed(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "checks_commute")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    site, check, error = e.form("site"), e.form("check"), e.form("error")
    reqs: list[Req] = []
    for kind, sort in (("check", check), ("error", error)):
        for part in ("x", "z"):
            reqs.append(Closure(f"{kind}_{part}_typed", ((e.form(f"{kind}_{part}"), ("w", "s")),),
                                ((sort, ("w",)), (site, ("s",)))))
    reqs.append(Closure("reads_typed", ((e.form("reads"), ("w", "q")),), ((error, ("w",)), (check, ("q",)))))
    return Compiled(tuple(reqs), decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
        ("checks_commute", checks_commute), ("readings_distinct", readings_distinct),
        ("readings_exact", readings_exact))))


LEAN_DEFS = (
    "/-- A word: its first part and its second part, one bit per site. -/",
    "abbrev Word := Prod (List Nat) (List Nat)",
    "",
    "def dot (a b : List Nat) : Nat := (List.zipWith (fun x y => x * y) a b).foldl (fun acc x => acc + x) 0",
    "",
    "/-- The exchange count of two words. -/",
    "def exch (u v : Word) : Nat := dot u.1 v.2 + dot u.2 v.1",
    "",
    "def checksCommute (cs : List Word) : Bool :=",
    "  (List.range cs.length).all fun i => (List.range cs.length).all fun j =>",
    "    decide (j <= i) || exch (cs.getD i ([], [])) (cs.getD j ([], [])) % 2 == 0",
    "",
    "/-- An error's reading: the parity of its exchange count with each check. -/",
    "def reading (cs : List Word) (e : Word) : List Nat := cs.map fun c => exch e c % 2",
    "",
    "def readingsDistinct (cs es : List Word) : Bool :=",
    "  let rs := es.map (reading cs)",
    "  rs.all (fun r => r.any (fun b => b != 0)) && rs.all (fun r => rs.count r == 1)",
    "",
    "def readingsExact (cs es : List Word) (ds : List (List Nat)) : Bool := decide (es.map (reading cs) = ds)",
    "",
)
LEAN_CALLS = {"checks_commute": "checksCommute checks_{f}", "readings_distinct": "readingsDistinct checks_{f} errors_{f}",
              "readings_exact": "readingsExact checks_{f} errors_{f} readings_{f}"}


def _bits(b: Sequence[int]) -> str:
    return lean_list([str(x) for x in b])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    def text(ws: list[Word]) -> str:
        return lean_list([f"({_bits(x)}, {_bits(z)})" for x, z in ws])

    return [("checks", "List Word", text(words(fs, "check"))), ("errors", "List Word", text(words(fs, "error"))),
            ("readings", "List (List Nat)", lean_list([_bits(r) for r in declared(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `commuting_checks`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
