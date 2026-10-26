"""Triples over one natural-number variable in a finite interval: a
precondition interval, a step that adds a constant, a postcondition
interval, and a standing (proved, refuted, or neither) with its witness.

The claim: numbers (values that are naturals), claims, ``domain(lo, hi)``,
``pre(c, lo, hi)``, ``post(c, lo, hi)``, ``adds(c, k)``, ``proved(c)``,
``refuted(c)``, ``certified(c)`` (a witness is given for a proved claim) and
``case(c, x)`` (a value of that witness: every case of a proved claim, or
the one counterexample of a refuted claim).

Relational clauses, carried by derivability over the hosted claim:
``domain_given``, ``one_domain``, ``pre_given``, ``one_pre``,
``post_given``, ``one_post``, ``adds_given``, ``one_adds``,
``one_standing`` (no claim is both proved and refuted), ``witnessed`` (a
proved claim carries a witness: without one it stays unproved) and
``refuted_has_case``.

Decoded clauses, decided over exact values outside the grammar:
``cases_complete`` (a proved claim's cases are exactly the domain values in
its precondition), ``cases_hold`` (each case, after the step, is in the
postcondition) and ``refutation_exact`` (a refuted claim has one case: a
domain value in the precondition whose step leaves the postcondition).  The
witness is replayed by enumeration; nothing else is trusted.  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, render, rows

CHALLENGE_ID = "witnessed_triples"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "WitnessedTriples"
EXACT = ("py.exact.q",)
CLAUSES = ("cases_complete", "cases_hold", "refutation_exact")
PENDING, PROVED, REFUTED = 0, 1, 2


@dataclass(frozen=True)
class Triple:
    pre: tuple[int, int]
    step: int
    post: tuple[int, int]
    standing: int
    certified: bool
    cases: tuple[int, ...]


def _nat(fs: FiniteStructure, e: int) -> int | None:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 and v.num >= 0 else None


def _pair(fs: FiniteStructure, a: int, b: int) -> tuple[int, int] | None:
    x, y = _nat(fs, a), _nat(fs, b)
    return None if x is None or y is None else (x, y)


def domain(fs: FiniteStructure) -> tuple[int, int] | None:
    got = rows(fs, "domain")
    return _pair(fs, *got[0]) if len(got) == 1 else None


def triples(fs: FiniteStructure) -> list[Triple] | None:
    """Every claim in declared order; ``None`` when a part is missing,
    repeated or not a natural number."""
    out = []
    proved = {c for (c,) in rows(fs, "proved")}
    refuted = {c for (c,) in rows(fs, "refuted")}
    certified = {c for (c,) in rows(fs, "certified")}
    for c in fs.elements("claim"):
        pre = [_pair(fs, lo, hi) for cc, lo, hi in rows(fs, "pre") if cc == c]
        post = [_pair(fs, lo, hi) for cc, lo, hi in rows(fs, "post") if cc == c]
        step = [_nat(fs, k) for cc, k in rows(fs, "adds") if cc == c]
        cases = [_nat(fs, x) for cc, x in rows(fs, "case") if cc == c]
        if len(pre) != 1 or len(post) != 1 or len(step) != 1:
            return None
        p, q, s = pre[0], post[0], step[0]
        if p is None or q is None or s is None or any(x is None for x in cases):
            return None
        standing = PROVED if c in proved else REFUTED if c in refuted else PENDING
        out.append(Triple(p, s, q, standing, c in certified, tuple(sorted(x for x in cases if x is not None))))
    return out


def _within(x: int, iv: tuple[int, int]) -> bool:
    return iv[0] <= x <= iv[1]


def models(d: tuple[int, int], t: Triple) -> list[int]:
    return [x for x in range(d[0], d[1] + 1) if _within(x, t.pre)]


def cases_complete(fs: FiniteStructure, _o: Oracle) -> bool:
    d, ts = domain(fs), triples(fs)
    return d is not None and ts is not None and all(
        list(t.cases) == models(d, t) for t in ts if t.standing == PROVED)


def cases_hold(fs: FiniteStructure, _o: Oracle) -> bool:
    ts = triples(fs)
    return ts is not None and all(_within(x + t.step, t.post) for t in ts if t.standing == PROVED for x in t.cases)


def refutation_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    d, ts = domain(fs), triples(fs)
    if d is None or ts is None:
        return False
    for t in ts:
        if t.standing != REFUTED:
            continue
        if len(t.cases) != 1:
            return False
        x = t.cases[0]
        if not (_within(x, d) and _within(x, t.pre) and not _within(x + t.step, t.post)):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    d, ts = domain(fs), triples(fs)
    return {"models": None if d is None or ts is None else [models(d, t) for t in ts]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "cases_complete")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    claim, domain_f, pre, post = e.form("claim"), e.form("domain"), e.form("pre"), e.form("post")
    adds, proved, refuted = e.form("adds"), e.form("proved"), e.form("refuted")
    certified, case = e.form("certified"), e.form("case")
    return Compiled(
        (
            Total("domain_given", (), ((domain_f, ("lo", "hi")),)),
            Functional("one_domain", domain_f, 0),
            Total("pre_given", ((claim, ("c",)),), ((pre, ("c", "lo", "hi")),)),
            Functional("one_pre", pre, 1),
            Total("post_given", ((claim, ("c",)),), ((post, ("c", "lo", "hi")),)),
            Functional("one_post", post, 1),
            Total("adds_given", ((claim, ("c",)),), ((adds, ("c", "k")),)),
            Functional("one_adds", adds, 1),
            Forbid("one_standing", ((proved, ("c",)), (refuted, ("c",)))),
            Closure("witnessed", ((proved, ("c",)),), ((certified, ("c",)),)),
            Total("refuted_has_case", ((refuted, ("c",)),), ((case, ("c", "x")),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("cases_complete", cases_complete), ("cases_hold", cases_hold), ("refutation_exact", refutation_exact))),
    )


LEAN_DEFS = (
    "/-- A triple: precondition, step, postcondition, standing (0 neither, 1 proved, 2 refuted), cases. -/",
    "structure Triple where",
    "  preLo : Nat",
    "  preHi : Nat",
    "  step : Nat",
    "  postLo : Nat",
    "  postHi : Nat",
    "  standing : Nat",
    "  cases : List Nat",
    "",
    "def within (x lo hi : Nat) : Bool := decide (lo <= x) && decide (x <= hi)",
    "",
    "/-- The domain values in the precondition, in order. -/",
    "def models (lo hi : Nat) (t : Triple) : List Nat :=",
    "  ((List.range (hi + 1 - lo)).map (fun k => lo + k)).filter (fun x => within x t.preLo t.preHi)",
    "",
    "def casesComplete (lo hi : Nat) (ts : List Triple) : Bool :=",
    "  ts.all fun t => t.standing != 1 || decide (t.cases = models lo hi t)",
    "",
    "def casesHold (ts : List Triple) : Bool :=",
    "  ts.all fun t => t.standing != 1 || t.cases.all (fun x => within (x + t.step) t.postLo t.postHi)",
    "",
    "def refutationExact (lo hi : Nat) (ts : List Triple) : Bool :=",
    "  ts.all fun t => t.standing != 2 || (match t.cases with",
    "    | [x] => within x lo hi && within x t.preLo t.preHi && !within (x + t.step) t.postLo t.postHi",
    "    | _ => false)",
    "",
)
LEAN_CALLS = {"cases_complete": "casesComplete {{d}} triples_{f}", "cases_hold": "casesHold triples_{f}",
              "refutation_exact": "refutationExact {{d}} triples_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    d, ts = domain(fs), triples(fs)
    assert d is not None and ts is not None
    items = [f"{{ preLo := {t.pre[0]}, preHi := {t.pre[1]}, step := {t.step}, postLo := {t.post[0]}, "
             f"postHi := {t.post[1]}, standing := {t.standing}, cases := {lean_list([str(x) for x in t.cases])} }}"
             for t in ts]
    return [("lo", "Nat", str(d[0])), ("hi", "Nat", str(d[1])), ("triples", "List Triple", lean_list(items))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    calls = {k: v.replace("{{d}}", "lo_{f} hi_{f}") for k, v in LEAN_CALLS.items()}
    return render(LEAN_MODULE, "The value clauses of `witnessed_triples`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, calls)
