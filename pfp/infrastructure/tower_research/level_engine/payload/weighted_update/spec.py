# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Hosted weights over alternatives are updated, one observation at a time,
by exact likelihoods: each observation carries positive evidence, and each
declared result is the current weight times the likelihood, divided by the
evidence.

The claim: alternatives, observations in their declared order, exact values,
``prior(h, v)``, ``likely(o, h, v)`` (the likelihood of observation ``o``
under alternative ``h``) and ``after(o, h, v)`` (the declared weight of ``h``
after the observations up to ``o``).

Relational clauses, carried by derivability over the hosted claim:
``prior_given``, ``one_prior``, ``likely_given``, ``one_likely``,
``after_given``, ``one_after`` and ``typed``.

Decoded clauses, decided over exact values outside the grammar:
``prior_normal`` (the prior is nonnegative and sums to one),
``likely_in_range`` (every likelihood lies in [0, 1]), ``evidence_positive``
(the evidence of each observation, the sum of current weight times
likelihood, is not zero) and ``results_exact`` (each declared weight is the
recomputed one).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "weighted_update"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "WeightedUpdate"
EXACT = ("py.exact.q",)
CLAUSES = ("prior_normal", "likely_in_range", "evidence_positive", "results_exact")


@dataclass(frozen=True)
class Update:
    prior: tuple[Q, ...]
    likely: tuple[tuple[Q, ...], ...]
    after: tuple[tuple[Q, ...], ...]


def update(fs: FiniteStructure) -> Update | None:
    """The claim over exact values, in the declared orders; ``None`` when a
    value is missing, repeated or undecodable."""
    hs, os = fs.elements("alt"), fs.elements("obs")

    def read(name: str, key_len: int) -> dict[tuple[int, ...], Q] | None:
        got: dict[tuple[int, ...], Q] = {}
        for n, args in fs.tuples:
            if n != name:
                continue
            key, v = tuple(args[:key_len]), fs.value(args[key_len])
            if v is None or key in got:
                return None
            got[key] = v
        return got

    p, lk, af = read("prior", 1), read("likely", 2), read("after", 2)
    if p is None or lk is None or af is None:
        return None
    if any((h,) not in p for h in hs) or any((o, h) not in lk or (o, h) not in af for o in os for h in hs):
        return None
    return Update(tuple(p[(h,)] for h in hs), tuple(tuple(lk[(o, h)] for h in hs) for o in os),
                  tuple(tuple(af[(o, h)] for h in hs) for o in os))


def steps(u: Update) -> list[tuple[Q, tuple[Q, ...] | None]]:
    """(evidence, recomputed weights) per observation; the weights are ``None``
    from the first observation whose evidence is zero."""
    out: list[tuple[Q, tuple[Q, ...] | None]] = []
    w: tuple[Q, ...] | None = u.prior
    for lk in u.likely:
        if w is None:
            out.append((ZERO, None))
            continue
        ev = sum((a * b for a, b in zip(w, lk)), ZERO)
        w = None if ev.is_zero() else tuple(a * b / ev for a, b in zip(w, lk))
        out.append((ev, w))
    return out


def prior_normal(fs: FiniteStructure, _o: Oracle) -> bool:
    u = update(fs)
    return u is not None and all(x.sign() >= 0 for x in u.prior) and sum(u.prior, ZERO) == ONE


def likely_in_range(fs: FiniteStructure, _o: Oracle) -> bool:
    u = update(fs)
    return u is not None and all(x.sign() >= 0 and x <= ONE for r in u.likely for x in r)


def evidence_positive(fs: FiniteStructure, _o: Oracle) -> bool:
    u = update(fs)
    return u is not None and all(not ev.is_zero() for ev, _ in steps(u))


def results_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    u = update(fs)
    return u is not None and all(w == declared for (_, w), declared in zip(steps(u), u.after))


def describe(fs: FiniteStructure) -> dict[str, object]:
    u = update(fs)
    if u is None:
        return {"evidence": None}
    return {"evidence": [fmt_q(ev) for ev, _ in steps(u)],
            "weights": [None if w is None else [fmt_q(x) for x in w] for _, w in steps(u)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    out = []
    for v in verdicts:
        if dict(v.decoded).get("results_exact") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    alt, obs, val = e.form("alt"), e.form("obs"), e.form("val")
    prior, likely, after = e.form("prior"), e.form("likely"), e.form("after")
    pair = ((obs, ("o",)), (alt, ("h",)))
    return Compiled(
        (
            Total("prior_given", ((alt, ("h",)),), ((prior, ("h", "v")),)),
            Functional("one_prior", prior, 1),
            Total("likely_given", pair, ((likely, ("o", "h", "v")),)),
            Functional("one_likely", likely, 2),
            Total("after_given", pair, ((after, ("o", "h", "v")),)),
            Functional("one_after", after, 2),
            Closure("typed", ((likely, ("o", "h", "v")),), ((obs, ("o",)), (alt, ("h",)), (val, ("v",)))),
        ),
        decoded=tuple(DecodedClause(c, f, EXACT) for c, f in (
            ("prior_normal", prior_normal), ("likely_in_range", likely_in_range),
            ("evidence_positive", evidence_positive), ("results_exact", results_exact))),
    )


LEAN_DEFS = (
    "def total (xs : List QN) : QN := xs.foldl (fun acc x => acc + x) 0",
    "",
    "def pairwise (xs ys : List QN) : List QN := (xs.zip ys).map fun p => p.1 * p.2",
    "",
    "/-- One update: the weights times the likelihoods, divided by the evidence. -/",
    "def step (w l : List QN) : List QN := (pairwise w l).map fun x => x * QN.inv (total (pairwise w l))",
    "",
    "/-- The weights after each observation in order. -/",
    "def run (w : List QN) : List (List QN) -> List (List QN)",
    "  | [] => []",
    "  | l :: ls => step w l :: run (step w l) ls",
    "",
    "def evidences (w : List QN) : List (List QN) -> List QN",
    "  | [] => []",
    "  | l :: ls => total (pairwise w l) :: evidences (step w l) ls",
    "",
    "structure Claim where",
    "  prior : List QN",
    "  likely : List (List QN)",
    "  after : List (List QN)",
    "",
    "def priorNormal (c : Claim) : Bool := c.prior.all (fun x => !QN.pos (-x)) && decide (total c.prior = 1)",
    "",
    "def likelyInRange (c : Claim) : Bool := c.likely.all fun r => r.all fun x => !QN.pos (-x) && !QN.pos (x - 1)",
    "",
    "def evidencePositive (c : Claim) : Bool := (evidences c.prior c.likely).all fun e => !decide (e = 0)",
    "",
    "def resultsExact (c : Claim) : Bool := evidencePositive c && decide (run c.prior c.likely = c.after)",
    "",
)
LEAN_CALLS = {"prior_normal": "priorNormal", "likely_in_range": "likelyInRange",
              "evidence_positive": "evidencePositive", "results_exact": "resultsExact"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One claim per evaluated fixture; the kernel re-decides each value clause."""
    from omega_engine_operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `weighted_update`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        u = update(by[fid].structure)
        assert u is not None
        lines += [f"def claim_{fid} : Claim :=",
                  f"  {{ prior := {T.row(u.prior)},",
                  f"    likely := [{', '.join(T.row(r) for r in u.likely)}],",
                  f"    after := [{', '.join(T.row(r) for r in u.after)}] }}", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause]} claim_{fid} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
