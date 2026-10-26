"""Solver claims about propositional clause sets, each accepted only with an
object the kernel here replays: an unsatisfiable answer with a resolution
refutation (every step resolves two available clauses on a pivot that
occurs positively in the first and negatively in the second, its clause is
the resolvent, and the last derived clause is empty), a satisfiable answer
with a consistent model satisfying every clause.  A bare success flag is
refused.

The claim: variables, claims and clauses (each in declared order; a
claim's given clauses come first, then its steps, as the kernel numbers
them), ``pos_in(k, v)`` and ``neg_in(k, v)`` (literals of clause ``k``),
``of_claim(k, c)``, ``resolves(k, a, b, v)`` (clause ``k`` is a step
resolving ``a`` with ``b`` on ``v``), ``unsat(c)``, ``sat(c)``,
``true_in(c, v)`` and ``false_in(c, v)`` (the claimed model).

Relational clauses, carried by derivability over the hosted claim:
``clauses_owned``, ``one_owner``, ``pivot_positive``, ``pivot_negative``,
``model_consistent`` and ``one_resolution``.

Decoded clauses, decided outside the grammar, over the replay:
``answered`` (an unsatisfiable claim has steps, a satisfiable one a model:
the refused case is a success flag with no proof object),
``steps_available`` (a step reads clauses already available),
``resolvents_exact``, ``refutes`` (the last derived clause is empty) and
``model_satisfies``.  Resolvents are recomputed and never read: later steps
see the recomputed clauses.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "resolution_claims"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("answered", "steps_available", "resolvents_exact", "refutes", "model_satisfies")
Lit = tuple[int, bool]


def literals(fs: FiniteStructure, k: int) -> frozenset[Lit]:
    return frozenset({(v, True) for kk, v in rows(fs, "pos_in") if kk == k}
                     | {(v, False) for kk, v in rows(fs, "neg_in") if kk == k})


def claims(fs: FiniteStructure) -> list[tuple[int, list[int], list[tuple[int, int, int, int]]]]:
    """(claim, given clauses, steps (clause, a, b, pivot)) in declared order."""
    owner = {k: c for k, c in rows(fs, "of_claim")}
    res = {k: (a, b, v) for k, a, b, v in rows(fs, "resolves")}
    out = []
    for c in fs.elements("claim"):
        mine = [k for k in fs.elements("clause") if owner.get(k) == c]
        out.append((c, [k for k in mine if k not in res], [(k,) + res[k] for k in mine if k in res]))
    return out


def replay(fs: FiniteStructure, given: list[int], steps: list[tuple[int, int, int, int]]
           ) -> tuple[bool, list[frozenset[Lit]]]:
    """Whether every step reads available clauses with a good pivot, and the
    recomputed resolvents."""
    index = {k: i for i, k in enumerate(given + [s[0] for s in steps])}
    available = [literals(fs, k) for k in given]
    out: list[frozenset[Lit]] = []
    for k, a, b, v in steps:
        i, j = index.get(a, len(index)), index.get(b, len(index))
        if i >= len(available) or j >= len(available):
            return False, out
        left, right = available[i], available[j]
        if (v, True) not in left or (v, False) not in right:
            return False, out
        r = (left - {(v, True)}) | (right - {(v, False)})
        out.append(r)
        available.append(r)
    return True, out


def answered(fs: FiniteStructure, _o: Oracle) -> bool:
    unsat = {c for (c,) in rows(fs, "unsat")}
    sat = {c for (c,) in rows(fs, "sat")}
    model = {c for c, _ in rows(fs, "true_in")} | {c for c, _ in rows(fs, "false_in")}
    return all((c in unsat and bool(steps)) or (c in sat and c in model) for c, _, steps in claims(fs))


def _unsat(fs: FiniteStructure) -> list[tuple[int, list[int], list[tuple[int, int, int, int]]]]:
    unsat = {c for (c,) in rows(fs, "unsat")}
    return [x for x in claims(fs) if x[0] in unsat]


def steps_available(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(replay(fs, g, s)[0] for _, g, s in _unsat(fs))


def resolvents_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    for _, g, s in _unsat(fs):
        ok, rs = replay(fs, g, s)
        if not ok or any(literals(fs, k) != r for (k, _, _, _), r in zip(s, rs)):
            return False
    return True


def refutes(fs: FiniteStructure, _o: Oracle) -> bool:
    for _, g, s in _unsat(fs):
        ok, rs = replay(fs, g, s)
        if not ok or not rs or rs[-1]:
            return False
    return True


def model_satisfies(fs: FiniteStructure, _o: Oracle) -> bool:
    sat = {c for (c,) in rows(fs, "sat")}
    for c, given, _ in claims(fs):
        if c not in sat:
            continue
        chosen = {(v, True) for cc, v in rows(fs, "true_in") if cc == c} | {
            (v, False) for cc, v in rows(fs, "false_in") if cc == c}
        if any((v, not s) in chosen for v, s in chosen) or not all(literals(fs, k) & chosen for k in given):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"resolvents": [[sorted([v, s] for v, s in r) for r in replay(fs, g, s)[1]] for _, g, s in _unsat(fs)]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    clause, claim = e.form("clause"), e.form("claim")
    pos_in, neg_in, of_claim, resolves = e.form("pos_in"), e.form("neg_in"), e.form("of_claim"), e.form("resolves")
    true_in, false_in = e.form("true_in"), e.form("false_in")
    return Compiled(
        (
            Total("clauses_owned", ((clause, ("k",)),), ((of_claim, ("k", "c")),)),
            Functional("one_owner", of_claim, 1),
            Closure("pivot_positive", ((resolves, ("k", "a", "b", "v")),), ((pos_in, ("a", "v")),)),
            Closure("pivot_negative", ((resolves, ("k", "a", "b", "v")),), ((neg_in, ("b", "v")),)),
            Forbid("model_consistent", ((true_in, ("c", "v")), (false_in, ("c", "v")))),
            Functional("one_resolution", resolves, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("answered", answered), ("steps_available", steps_available), ("resolvents_exact", resolvents_exact),
            ("refutes", refutes), ("model_satisfies", model_satisfies))),
    )
