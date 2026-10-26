# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A proof over a declared list of axioms bound by digest, rechecked step by
step against the two rules of the table (cite an axiom; detach from two
earlier lines), never accepted on its own report of having been checked.

The claim: terms, axioms, lines and one seal (each in declared order), the
seal carrying the bound digest as a value, ``imp(t, a, b)`` (term ``t`` is
``a`` implies ``b``; a term with no such row is an atom), ``states(k, t)``
(axiom ``k`` states term ``t``), ``claims(l, t)`` (line ``l`` claims term
``t``), ``cites(l, k)`` (line ``l`` cites axiom ``k``), ``detaches(l, i,
j)`` (line ``l`` detaches from lines ``i`` and ``j``, ``j`` claiming that
``i``'s term implies ``l``'s), ``reports(l)`` (line ``l`` rests on its own
report of having been checked) and ``concludes(t)``.

A term is written as the atom ``p<k>`` (``k`` its place among the atoms) or
as ``["->", a, b]``; the axiom list is bound by the SHA-256 of its canonical
JSON (sorted keys, no white space, ASCII), a declared convention.

Relational clauses, carried by derivability over the hosted claim:
``states_given``, ``one_state``, ``claims_given``, ``one_claim``,
``one_imp``, ``imp_typed``, ``concluded`` and ``one_conclusion``.

Decoded clauses, decided outside the grammar: ``terms_finite`` (the
implication table has no cycle), ``bound`` (the axiom list hashes to the
seal's digest), ``rules_only`` (every line has exactly one support, a
citation or a detachment: the refused case is a line resting on its own
report), ``earlier_only`` (a detachment reads strictly earlier lines),
``steps_match`` (a cited axiom states the line's term; a detachment's second
line claims the first's term implying the line's) and ``concludes_last``
(the conclusion is the last line's term).  All but ``bound`` and
``terms_finite`` are re-decided by the kernel; SHA-256 stays computed.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Union

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.digest import digest_of
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "bound_axioms"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "BoundAxioms"
EXACT = ("py.exact.digest",)
CLAUSES = ("terms_finite", "bound", "rules_only", "earlier_only", "steps_match", "concludes_last")
LEAN_CLAUSES = ("rules_only", "earlier_only", "steps_match", "concludes_last")
Written = Union[str, list[object]]


def _imp(fs: FiniteStructure) -> dict[int, tuple[int, int]]:
    return {t: (a, b) for t, a, b in rows(fs, "imp")}


def terms_finite(fs: FiniteStructure, _o: Oracle) -> bool:
    imp = _imp(fs)
    state: dict[int, int] = {}

    def ok(t: int) -> bool:
        if state.get(t) == 1:
            return False
        if state.get(t) == 2 or t not in imp:
            return True
        state[t] = 1
        good = ok(imp[t][0]) and ok(imp[t][1])
        state[t] = 2
        return good

    return all(ok(t) for t in fs.elements("term"))


def written(fs: FiniteStructure, t: int) -> Written:
    """A term as the checker's formula; only called on a finite table."""
    imp = _imp(fs)
    atoms = [x for x in fs.elements("term") if x not in imp]
    if t in imp:
        return ["->", written(fs, imp[t][0]), written(fs, imp[t][1])]
    return f"p{atoms.index(t)}" if t in atoms else "?"


def _one(fs: FiniteStructure, name: str, key: int) -> int | None:
    got = [a[1] for a in rows(fs, name) if a[0] == key]
    return got[0] if len(got) == 1 else None


def axioms(fs: FiniteStructure) -> list[Written]:
    return [written(fs, t) if (t := _one(fs, "states", k)) is not None else "?" for k in fs.elements("axiom")]


def bound(fs: FiniteStructure, _o: Oracle) -> bool:
    if not terms_finite(fs, _o):
        return False
    seals = fs.elements("seal")
    return len(seals) == 1 and fs.digest(seals[0]) == digest_of(axioms(fs))


def supports(fs: FiniteStructure) -> list[list[tuple[object, ...]]]:
    """Each line's supports: ("cite", k), ("detach", i, j) or ("report",), by positions."""
    out: list[list[tuple[object, ...]]] = [[] for _ in fs.elements("line")]

    def lp(e: int) -> int:
        k = position(fs, "line", e)
        return -1 if k is None else k

    for l, k in rows(fs, "cites"):
        if lp(l) >= 0:
            out[lp(l)].append(("cite", position(fs, "axiom", k)))
    for l, i, j in rows(fs, "detaches"):
        if lp(l) >= 0:
            out[lp(l)].append(("detach", lp(i), lp(j)))
    for (l,) in rows(fs, "reports"):
        if lp(l) >= 0:
            out[lp(l)].append(("report",))
    return out


def rules_only(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(len(s) == 1 and s[0][0] in ("cite", "detach") for s in supports(fs))


def earlier_only(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(0 <= int(str(x[1])) < n and 0 <= int(str(x[2])) < n
               for n, s in enumerate(supports(fs)) for x in s if x[0] == "detach")


def claimed(fs: FiniteStructure) -> list[Written]:
    return [written(fs, t) if (t := _one(fs, "claims", l)) is not None else "?" for l in fs.elements("line")]


def steps_match(fs: FiniteStructure, _o: Oracle) -> bool:
    if not terms_finite(fs, _o):
        return False
    cl, ax = claimed(fs), axioms(fs)
    for n, s in enumerate(supports(fs)):
        for x in s:
            if x[0] == "cite" and (x[1] is None or ax[int(str(x[1]))] != cl[n]):
                return False
            if x[0] == "detach":
                i, j = int(str(x[1])), int(str(x[2]))
                if 0 <= i < len(cl) and 0 <= j < len(cl) and cl[j] != ["->", cl[i], cl[n]]:
                    return False
    return True


def concludes_last(fs: FiniteStructure, _o: Oracle) -> bool:
    got = [t for (t,) in rows(fs, "concludes")]
    return terms_finite(fs, _o) and len(got) == 1 and bool(claimed(fs)) and written(fs, got[0]) == claimed(fs)[-1]


def describe(fs: FiniteStructure) -> dict[str, object]:
    ok = terms_finite(fs, None)  # type: ignore[arg-type]
    return {"axioms": axioms(fs) if ok else None, "digest": "sha256:" + digest_of(axioms(fs)).hex() if ok else None}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "rules_only")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    term, axiom, line = e.form("term"), e.form("axiom"), e.form("line")
    imp, states, claims, concludes = e.form("imp"), e.form("states"), e.form("claims"), e.form("concludes")
    return Compiled(
        (
            Total("states_given", ((axiom, ("k",)),), ((states, ("k", "t")),)),
            Functional("one_state", states, 1),
            Total("claims_given", ((line, ("l",)),), ((claims, ("l", "t")),)),
            Functional("one_claim", claims, 1),
            Functional("one_imp", imp, 1),
            Closure("imp_typed", ((imp, ("t", "a", "b")),), ((term, ("t",)), (term, ("a",)), (term, ("b",)))),
            Total("concluded", (), ((concludes, ("t",)),)),
            Functional("one_conclusion", concludes, 0),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("terms_finite", terms_finite), ("bound", bound), ("rules_only", rules_only),
            ("earlier_only", earlier_only), ("steps_match", steps_match), ("concludes_last", concludes_last))),
    )


LEAN_DEFS = (
    "inductive Fm where",
    "  | atom (k : Nat)",
    "  | imp (a b : Fm)",
    "  deriving DecidableEq",
    "",
    "/-- A line's supports: a cited axiom, a detachment from two lines, or a report. -/",
    "inductive Support where",
    "  | cite (k : Nat)",
    "  | detach (i j : Nat)",
    "  | report",
    "  deriving DecidableEq",
    "",
    "def isRule : Support -> Bool",
    "  | .cite _ => true",
    "  | .detach _ _ => true",
    "  | .report => false",
    "",
    "def rulesOnly (sups : List (List Support)) : Bool :=",
    "  sups.all fun s => s.length == 1 && s.all isRule",
    "",
    "def earlierOnly (sups : List (List Support)) : Bool :=",
    "  (List.range sups.length).all fun n => (sups.getD n []).all fun",
    "    | .detach i j => i < n && j < n",
    "    | _ => true",
    "",
    "def stepsMatch (axs cls : List Fm) (sups : List (List Support)) : Bool :=",
    "  (List.range sups.length).all fun n => (sups.getD n []).all fun",
    "    | .cite k => k < axs.length && decide (axs.getD k (.atom 0) = cls.getD n (.atom 0))",
    "    | .detach i j => !(i < cls.length && j < cls.length) ||",
    "        decide (cls.getD j (.atom 0) = .imp (cls.getD i (.atom 0)) (cls.getD n (.atom 0)))",
    "    | .report => true",
    "",
    "def concludesLast (cls : List Fm) (c : Fm) : Bool := !cls.isEmpty && decide (cls.getLastD (.atom 0) = c)",
    "",
)
LEAN_CALLS = {"rules_only": "rulesOnly sups_{f}", "earlier_only": "earlierOnly sups_{f}",
              "steps_match": "stepsMatch axioms_{f} lines_{f} sups_{f}",
              "concludes_last": "concludesLast lines_{f} conclusion_{f}"}


def _lean_fm(w: Written) -> str:
    if isinstance(w, str):
        return f"(.atom {int(w[1:])})"
    return f"(.imp {_lean_fm(w[1])} {_lean_fm(w[2])})"  # type: ignore[arg-type]


def _lean_support(x: tuple[object, ...]) -> str:
    if x[0] == "cite":
        return f".cite {x[1]}"
    if x[0] == "detach":
        return f".detach {x[1]} {x[2]}"
    return ".report"


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    (c,) = [t for (t,) in rows(fs, "concludes")]
    assert all(x[0] != "cite" or x[1] is not None for s in supports(fs) for x in s)
    return [("axioms", "List Fm", lean_list([_lean_fm(w) for w in axioms(fs)])),
            ("lines", "List Fm", lean_list([_lean_fm(w) for w in claimed(fs)])),
            ("sups", "List (List Support)", lean_list([lean_list([_lean_support(x) for x in s]) for s in supports(fs)])),
            ("conclusion", "Fm", _lean_fm(written(fs, c)))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The step clauses of `bound_axioms`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
