"""A conjunctive question over typed tables, translated first and then
evaluated exactly: every atom names its table's own columns, every
variable has one type, every constant lies in its column's type, every
output variable occurs in an atom, every stored row fits its table, and the
claimed answers are exactly the recomputed answer set (a finite join, no
sampling; set semantics).

The claim: types, values, tables, columns, rows, atoms, variables, output
slots (in declared order) and answers; ``member(v, T)``, ``column_of(c,
R)``, ``typed(c, T)``, ``stored(r, R)``, ``cell(r, c, v)``, ``atom_on(a,
R)``, ``binds_var(a, c, x)``, ``binds_const(a, c, v)``, ``out(s, x)``
(output slot ``s`` is variable ``x``) and ``gives(n, s, v)`` (answer ``n``
has value ``v`` in slot ``s``).

Relational clauses, all carried by derivability over the hosted claim:
``columns_present`` and ``constant_columns_present`` (an atom names only its
table's columns: the refused case is an absent column), ``one_type`` (a
variable's columns share one type), ``constants_typed``, ``outputs_bound``,
``rows_full``, ``rows_within``, ``cells_typed``, ``one_typed``,
``one_column_of`` and ``one_answer_value``.

Decoded clause, decided outside the grammar: ``answers_exact`` (the claimed
answers are exactly the join's answer set).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "typed_queries"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("answers_exact",)


def found(fs: FiniteStructure) -> set[tuple[int, ...]]:
    """The join, atom by atom, over the stored rows."""
    stored: dict[int, list[dict[int, int]]] = {}
    cells: dict[int, dict[int, int]] = {}
    for r, c, v in rows(fs, "cell"):
        cells.setdefault(r, {})[c] = v
    for r, t in rows(fs, "stored"):
        stored.setdefault(t, []).append(cells.get(r, {}))
    atoms = []
    for a in fs.elements("atom"):
        on = [t for aa, t in rows(fs, "atom_on") if aa == a]
        bind = [(c, ("var", x)) for aa, c, x in rows(fs, "binds_var") if aa == a]
        bind += [(c, ("const", v)) for aa, c, v in rows(fs, "binds_const") if aa == a]
        atoms.append((on[0] if len(on) == 1 else -1, bind))
    slots = {s: x for s, x in rows(fs, "out")}
    output = [slots.get(s, -1) for s in fs.elements("slot")]
    out: set[tuple[int, ...]] = set()

    def extend(i: int, env: dict[int, int]) -> None:
        if i == len(atoms):
            if all(x in env for x in output):
                out.add(tuple(env[x] for x in output))
            return
        table, bind = atoms[i]
        for row in stored.get(table, []):
            trial, fits = dict(env), True
            for c, (kind, term) in bind:
                if c not in row:
                    fits = False
                    break
                if kind == "var":
                    if trial.setdefault(term, row[c]) != row[c]:
                        fits = False
                        break
                elif term != row[c]:
                    fits = False
                    break
            if fits:
                extend(i + 1, trial)

    extend(0, {})
    return out


def claimed(fs: FiniteStructure) -> set[tuple[int, ...]]:
    gives = {(n, s): v for n, s, v in rows(fs, "gives")}
    return {tuple(gives.get((n, s), -1) for s in fs.elements("slot")) for n in fs.elements("answer")}


def answers_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return len(claimed(fs)) == len(fs.elements("answer")) and claimed(fs) == found(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"answers": sorted(list(t) for t in found(fs))}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    member, column_of, typed = e.form("member"), e.form("column_of"), e.form("typed")
    stored, cell, atom_on = e.form("stored"), e.form("cell"), e.form("atom_on")
    bv, bc, out, gives = e.form("binds_var"), e.form("binds_const"), e.form("out"), e.form("gives")
    return Compiled(
        (
            Closure("columns_present", ((atom_on, ("a", "r")), (bv, ("a", "c", "x"))), ((column_of, ("c", "r")),)),
            Closure("constant_columns_present", ((atom_on, ("a", "r")), (bc, ("a", "c", "v"))),
                    ((column_of, ("c", "r")),)),
            Closure("one_type", ((bv, ("a", "c", "x")), (typed, ("c", "t")), (bv, ("b", "d", "x"))),
                    ((typed, ("d", "t")),)),
            Closure("constants_typed", ((bc, ("a", "c", "v")), (typed, ("c", "t"))), ((member, ("v", "t")),)),
            Total("outputs_bound", ((out, ("s", "x")),), ((bv, ("a", "c", "x")),)),
            Total("rows_full", ((stored, ("r", "t")), (column_of, ("c", "t"))), ((cell, ("r", "c", "v")),)),
            Closure("rows_within", ((cell, ("r", "c", "v")), (stored, ("r", "t"))), ((column_of, ("c", "t")),)),
            Closure("cells_typed", ((cell, ("r", "c", "v")), (typed, ("c", "t"))), ((member, ("v", "t")),)),
            Functional("one_typed", typed, 1),
            Functional("one_column_of", column_of, 1),
            Functional("one_answer_value", gives, 2),
        ),
        decoded=(DecodedClause("answers_exact", answers_exact, EXACT),),
    )
