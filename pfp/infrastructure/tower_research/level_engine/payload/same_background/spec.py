# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A counterfactual on a finite model of two-valued variables: the
background values consistent with an observation are found by enumeration,
and each is run again with one variable forced, keeping the same
background.

Every variable after the first has one parent, earlier in the declared
order, and a table from the parent's value to its own; the first variable
is the background.  The claim: variables and bits (in declared order),
``parent(v, p)``, ``table(v, x, y)`` (when the parent is ``x``, ``v`` is
``y``), ``observed(v, x)``, ``forced(v, x)``, ``asked(v)``, twins,
``factual(t, x)`` and ``counter(t, x)`` (the background value of twin
``t``'s factual and counterfactual runs) and ``answer(x)`` (the claimed
values of the asked variable in the counterfactual runs).

Relational clauses, carried by derivability over the hosted claim:
``tables_given``, ``one_table``, ``one_parent``, ``forced_given``,
``one_forced``, ``asked_given``, ``one_asked``, ``twins_given`` and
``one_factual``, ``one_counter``.

Decoded clauses, decided outside the grammar: ``same_background`` (each
twin's counterfactual run keeps its factual background: a counterfactual
that draws the background again is refused), ``abduction_exact`` (the
twins' backgrounds are exactly the backgrounds consistent with the
observation) and ``answer_exact`` (the claimed answer is the set of values
of the asked variable over the counterfactual runs).  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "same_background"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SameBackground"
EXACT: tuple[str, ...] = ()
CLAUSES = ("same_background", "abduction_exact", "answer_exact")


def _p(fs: FiniteStructure, sort: str, e: int) -> int:
    k = position(fs, sort, e)
    return -1 if k is None else k


def model(fs: FiniteStructure) -> tuple[list[int], list[list[int]]]:
    """Each variable's parent (the first has none: -1) and table (images of
    the parent's values 0 and 1)."""
    vs = fs.elements("variable")
    parent = {v: _p(fs, "variable", p) for v, p in rows(fs, "parent")}
    table: dict[int, dict[int, int]] = {}
    for v, x, y in rows(fs, "table"):
        table.setdefault(v, {})[_p(fs, "bit", x)] = _p(fs, "bit", y)
    return ([parent.get(v, -1) for v in vs], [[table.get(v, {}).get(b, -1) for b in (0, 1)] for v in vs])


def run(fs: FiniteStructure, background: int, force: dict[int, int]) -> list[int]:
    parents, tables = model(fs)
    values: list[int] = []
    for k, (p, t) in enumerate(zip(parents, tables)):
        if k in force:
            values.append(force[k])
        elif k == 0:
            values.append(background)
        else:
            values.append(t[values[p]] if 0 <= p < k and values[p] in (0, 1) else -1)
    return values


def _pairs(fs: FiniteStructure, name: str, sort: str) -> dict[int, int]:
    return {_p(fs, sort, a): _p(fs, "bit", b) for a, b in rows(fs, name)}


def twins(fs: FiniteStructure) -> list[tuple[int, int]]:
    f, c = _pairs(fs, "factual", "twin"), _pairs(fs, "counter", "twin")
    return [(f.get(t, -1), c.get(t, -1)) for t in range(len(fs.elements("twin")))]


def consistent(fs: FiniteStructure) -> list[int]:
    obs = _pairs(fs, "observed", "variable")
    return [u for u in (0, 1) if all(run(fs, u, {})[v] == x for v, x in obs.items())]


def same_background(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(f == c for f, c in twins(fs))


def abduction_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return sorted(f for f, _ in twins(fs)) == consistent(fs)


def answer(fs: FiniteStructure) -> list[int]:
    force = _pairs(fs, "forced", "variable")
    asked = [_p(fs, "variable", v) for (v,) in rows(fs, "asked")]
    return sorted({run(fs, f, force)[asked[0]] for f, _ in twins(fs)}) if asked else []


def answer_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return sorted(_p(fs, "bit", b) for (b,) in rows(fs, "answer")) == answer(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"consistent": consistent(fs), "answer": answer(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "answer_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    variable, bit, twin = e.form("variable"), e.form("bit"), e.form("twin")
    table, parent = e.form("table"), e.form("parent")
    return Compiled(
        (
            Total("tables_given", ((parent, ("v", "p")), (bit, ("x",))), ((table, ("v", "x", "y")),)),
            Functional("one_table", table, 2),
            Functional("one_parent", parent, 1),
            Total("forced_given", (), ((e.form("forced"), ("v", "x")),)),
            Functional("one_forced", e.form("forced"), 0),
            Total("asked_given", (), ((e.form("asked"), ("v",)),)),
            Functional("one_asked", e.form("asked"), 0),
            Total("twins_given", ((twin, ("t",)),), ((e.form("factual"), ("t", "x")), (e.form("counter"), ("t", "y")))),
            Functional("one_factual", e.form("factual"), 1),
            Functional("one_counter", e.form("counter"), 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("same_background", same_background), ("abduction_exact", abduction_exact),
            ("answer_exact", answer_exact))),
    )


LEAN_DEFS = (
    "/-- Run the model from a background value, some variables forced (as (variable, value) pairs). -/",
    "def run (parents : List Int) (tables : List (List Nat)) (u : Nat) (force : List (Prod Nat Nat)) : List Nat :=",
    "  (List.range parents.length).foldl (fun vals k =>",
    "    match force.find? (fun f => f.1 == k) with",
    "    | some f => vals ++ [f.2]",
    "    | none =>",
    "      if k == 0 then vals ++ [u]",
    "      else vals ++ [(tables.getD k []).getD (vals.getD (parents.getD k 0).toNat 2) 2]) []",
    "",
    "def consistent (ps : List Int) (ts : List (List Nat)) (obs : List (Prod Nat Nat)) : List Nat :=",
    "  [0, 1].filter fun u => obs.all fun o => (run ps ts u []).getD o.1 2 == o.2",
    "",
    "def sameBackground (tw : List (Prod Nat Nat)) : Bool := tw.all fun t => t.1 == t.2",
    "",
    "def sortNats (xs : List Nat) : List Nat := [0, 1].filter fun b => xs.contains b",
    "",
    "def abductionExact (ps : List Int) (ts : List (List Nat)) (obs : List (Prod Nat Nat)) (tw : List (Prod Nat Nat)) : Bool :=",
    "  let c := consistent ps ts obs",
    "  let fs := tw.map fun t => t.1",
    "  fs.length == c.length && c.all (fun u => fs.count u == 1)",
    "",
    "def answerExact (ps : List Int) (ts : List (List Nat)) (force : List (Prod Nat Nat)) (q : Nat)",
    "    (tw : List (Prod Nat Nat)) (ans : List Nat) : Bool :=",
    "  decide (sortNats (tw.map fun t => (run ps ts t.1 force).getD q 2) = ans)",
    "",
)
LEAN_CALLS = {"same_background": "sameBackground twins_{f}",
              "abduction_exact": "abductionExact parents_{f} tables_{f} observed_{f} twins_{f}",
              "answer_exact": "answerExact parents_{f} tables_{f} forced_{f} asked_{f} twins_{f} answer_{f}"}


def _nat_pairs(d: dict[int, int]) -> str:
    return lean_list([f"({a}, {b})" for a, b in sorted(d.items())])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    parents, tables = model(fs)
    asked = [_p(fs, "variable", v) for (v,) in rows(fs, "asked")]
    tw = twins(fs)
    assert all(x >= 0 for t in tables[1:] for x in t) and asked and all(a >= 0 and b >= 0 for a, b in tw)
    return [("parents", "List Int", lean_list([f"({p})" for p in parents])),
            ("tables", "List (List Nat)", lean_list([lean_list([str(max(x, 0)) for x in t]) for t in tables])),
            ("observed", "List (Prod Nat Nat)", _nat_pairs(_pairs(fs, "observed", "variable"))),
            ("forced", "List (Prod Nat Nat)", _nat_pairs(_pairs(fs, "forced", "variable"))),
            ("asked", "Nat", str(asked[0])), ("twins", "List (Prod Nat Nat)", lean_list([f"({a}, {b})" for a, b in tw])),
            ("answer", "List Nat", lean_list([str(_p(fs, "bit", b)) for (b,) in sorted(rows(fs, "answer"))]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `same_background`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
