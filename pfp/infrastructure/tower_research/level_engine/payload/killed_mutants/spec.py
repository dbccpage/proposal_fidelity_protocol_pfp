# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Changed fixtures must fail for the intended invariant: the base list holds
every declared invariant, every mutant's operator changes it, every mutant
is killed by some declared invariant, a killed mutant is killed by its
intended invariant, and the recorded kills are the recomputed ones.

The invariants and the operators are pinned here, supplied and restated
exactly: ``nondecreasing``, ``distinct`` and ``nonempty`` over lists of
naturals; ``set`` (the position gets the mutant's value), ``delete``
(remove the position), ``duplicate`` (insert a copy after the position) and
``swap`` (exchange the position and the next).  The engine applies every
operator itself, so a changed list is computed, never supplied, and
evaluates every declared invariant on it.  Every declared mutant counts as
dangerous: one that no declared invariant kills survives.

The claim: entries (each carrying a natural; the base list, in declared
order), invariants and operators (each carrying its pinned name as a text),
mutants (each carrying the value ``set`` reads); ``at(m, x)`` (the entry a
mutant acts at), ``applies(m, o)``, ``intends(m, v)`` and ``kills(m, v)``
(the recorded kills).

Relational clauses, carried by derivability over the hosted claim:
``position_given``, ``one_position``, ``positions_are_entries``,
``operator_given``, ``one_operator``, ``intent_given``, ``one_intent``,
``intents_declared`` and ``kills_declared``.

Decoded clauses, decided outside the grammar, over the applied operators:
``well_formed``, ``base_holds``, ``mutants_change``, ``mutants_killed``
(the refused case: a surviving mutant), ``intended_kills`` (over the
killed mutants; a survivor is ``mutants_killed``'s business) and
``matrix_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import nat
from ..shared import position, rows

CHALLENGE_ID = "killed_mutants"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "base_holds", "mutants_change", "mutants_killed", "intended_kills", "matrix_exact")
MAX_LENGTH = 64
INVARIANTS: dict[str, Callable[[list[int]], bool]] = {
    "distinct": lambda xs: len(set(xs)) == len(xs),
    "nondecreasing": lambda xs: all(a <= b for a, b in zip(xs, xs[1:])),
    "nonempty": lambda xs: len(xs) > 0,
}
OPERATORS = ("set", "delete", "duplicate", "swap")


def mutate(base: list[int], operator: str, at: int, value: int) -> list[int] | None:
    """The changed list; ``None`` when the operator cannot act there."""
    out = list(base)
    if not 0 <= at < len(out):
        return None
    if operator == "set":
        out[at] = value
    elif operator == "delete":
        del out[at]
    elif operator == "duplicate":
        out.insert(at + 1, out[at])
    elif operator == "swap" and at + 1 < len(out):
        out[at], out[at + 1] = out[at + 1], out[at]
    else:
        return None
    return out


def _one(rel: list[tuple[int, ...]], m: int) -> int | None:
    got = [b for a, b in rel if a == m]
    return got[0] if len(got) == 1 else None


def base(fs: FiniteStructure) -> list[int]:
    return [nat(fs, x) for x in fs.elements("entry")]


def declared(fs: FiniteStructure) -> dict[int, str]:
    return {v: str(fs.text(v)) for v in fs.elements("invariant")}


def changed(fs: FiniteStructure, m: int) -> list[int] | None:
    o, x = _one(rows(fs, "applies"), m), _one(rows(fs, "at"), m)
    k = None if x is None else position(fs, "entry", x)
    if o is None or k is None or nat(fs, m) < 0:
        return None
    return mutate(base(fs), str(fs.text(o)), k, nat(fs, m))


def killed_by(fs: FiniteStructure, m: int) -> set[int] | None:
    """The declared invariants the mutant violates, recomputed."""
    xs = changed(fs, m)
    if xs is None:
        return None
    return {v for v, name in declared(fs).items() if name in INVARIANTS and not INVARIANTS[name](xs)}


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    names = list(declared(fs).values())
    xs = base(fs)
    return (bool(names) and len(set(names)) == len(names) and set(names) <= set(INVARIANTS)
            and all(fs.text(o) in OPERATORS for o in fs.elements("operator"))
            and -1 not in xs and len(xs) <= MAX_LENGTH and bool(fs.elements("mutant"))
            and all(changed(fs, m) is not None for m in fs.elements("mutant")))


def base_holds(fs: FiniteStructure, _o: Oracle) -> bool:
    xs = base(fs)
    return all(name in INVARIANTS and INVARIANTS[name](xs) for name in declared(fs).values())


def mutants_change(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(changed(fs, m) != base(fs) for m in fs.elements("mutant"))


def mutants_killed(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(bool(killed_by(fs, m)) for m in fs.elements("mutant"))


def intended_kills(fs: FiniteStructure, _o: Oracle) -> bool:
    for m in fs.elements("mutant"):
        got = killed_by(fs, m)
        if got is None or (got and _one(rows(fs, "intends"), m) not in got):
            return False
    return True


def matrix_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    for m in fs.elements("mutant"):
        if killed_by(fs, m) != {v for mm, v in rows(fs, "kills") if mm == m}:
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    names = declared(fs)
    out: list[object] = []
    for m in fs.elements("mutant"):
        got = killed_by(fs, m)
        out.append(None if got is None else sorted(names[v] for v in got))
    return {"changed": [changed(fs, m) for m in fs.elements("mutant")], "kills": out}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    mutant, entry, invariant = e.form("mutant"), e.form("entry"), e.form("invariant")
    at, applies, intends, kills = e.form("at"), e.form("applies"), e.form("intends"), e.form("kills")
    return Compiled(
        (
            Total("position_given", ((mutant, ("m",)),), ((at, ("m", "x")),)),
            Functional("one_position", at, 1),
            Closure("positions_are_entries", ((at, ("m", "x")),), ((entry, ("x",)),)),
            Total("operator_given", ((mutant, ("m",)),), ((applies, ("m", "o")),)),
            Functional("one_operator", applies, 1),
            Total("intent_given", ((mutant, ("m",)),), ((intends, ("m", "v")),)),
            Functional("one_intent", intends, 1),
            Closure("intents_declared", ((intends, ("m", "v")),), ((invariant, ("v",)),)),
            Closure("kills_declared", ((kills, ("m", "v")),), ((mutant, ("m",)), (invariant, ("v",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("base_holds", base_holds), ("mutants_change", mutants_change),
            ("mutants_killed", mutants_killed), ("intended_kills", intended_kills),
            ("matrix_exact", matrix_exact))),
    )
