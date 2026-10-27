# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Operations with ordered input slots and one output, each slot and output
carrying a colour, cut off at a bound on the number of slots (the hosted
slot positions), with a unit operation for each colour and a substitution
table: a row puts one operation's output into a slot of another and names
the result.  Inside the bound, every substitution whose colours match has
exactly one row, units are units, and repeated substitution does not
depend on bracketing.

The claim: colours, slot positions and operations (each in declared order:
the slot positions are 0, 1, ... in order, and their number is the bound),
``input(o, i, c)`` (slot ``i`` of ``o`` has colour ``c``), ``output(o,
c)``, ``unit(c, e)`` (``e`` is the unit of colour ``c``) and ``subst(o, i,
p, r)`` (``p`` put into slot ``i`` of ``o`` gives ``r``).

Relational clauses, carried by derivability over the hosted claim:

* profiles: ``output_given``, ``one_output``, ``output_typed``,
  ``input_typed``, ``one_input``, ``inputs_start`` (every operation has a
  first slot) and ``inputs_contiguous_<k>`` for ``k >= 2`` (slot ``k``
  is used only after slot ``k - 1``; slot 1 after slot 0 is already
  ``inputs_start``);
* units: ``unit_given``, ``one_unit``, ``unit_typed``, ``unit_profile``
  and ``unit_one_slot``;
* the table: ``subst_typed``, ``one_result``, ``slot_exists``,
  ``colours_match`` (the output put into a slot has the slot's colour: the
  refused case), ``result_output``, ``unit_outside`` and ``unit_inside``.

Decoded clauses, decided outside the grammar (slot positions are
arithmetic): ``result_inputs`` (the result's slots are the outer
operation's, with the inner operation's slots in place of the one filled),
``table_full`` (every substitution whose colours match and whose result
fits the bound has a row) and ``brackets`` (for every row and every
further substitution into its result, the other bracketing, sequential or
side by side, gives the same operation wherever both are in the table).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Req, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import position, rows

CHALLENGE_ID = "coloured_slots"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("result_inputs", "table_full", "brackets")

Profile = tuple[tuple[int, ...], int]


def profiles(fs: FiniteStructure) -> dict[int, Profile]:
    """Each operation's slot colours in slot order and its output colour
    (-1 where a slot or the output is missing)."""
    ins: dict[int, dict[int, int]] = {}
    for o, i, c in rows(fs, "input"):
        k = position(fs, "slot", i)
        if k is not None:
            ins.setdefault(o, {})[k] = c
    out = {o: c for o, c in rows(fs, "output")}
    got = {}
    for o in fs.elements("op"):
        slots = ins.get(o, {})
        got[o] = (tuple(slots.get(k, -1) for k in range(max(slots) + 1)) if slots else (), out.get(o, -1))
    return got


def table(fs: FiniteStructure) -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for o, i, p, r in rows(fs, "subst"):
        k = position(fs, "slot", i)
        if k is not None:
            out[(o, k, p)] = r
    return out


def result_inputs(fs: FiniteStructure, _o: Oracle) -> bool:
    prof = profiles(fs)
    for (o, i, p), r in table(fs).items():
        if o not in prof or p not in prof or r not in prof:
            return False
        o_in, p_in = prof[o][0], prof[p][0]
        if prof[r][0] != o_in[:i] + p_in + o_in[i + 1:]:
            return False
    return True


def table_full(fs: FiniteStructure, _o: Oracle) -> bool:
    prof, comp, bound = profiles(fs), table(fs), len(fs.elements("slot"))
    return all((o, i, p) in comp
               for o, (o_in, _) in prof.items() for i, c in enumerate(o_in)
               for p, (p_in, p_out) in prof.items() if p_out == c and len(o_in) + len(p_in) - 1 <= bound)


def brackets(fs: FiniteStructure, _o: Oracle) -> bool:
    prof, comp = profiles(fs), table(fs)
    for (outer, i, inner), first in comp.items():
        if first not in prof or inner not in prof:
            continue
        width = len(prof[inner][0])
        for k, c in enumerate(prof[first][0]):
            for other, (x_in, x_out) in prof.items():
                left = comp.get((first, k, other))
                if x_out != c or left is None:
                    continue
                if i <= k < i + width:
                    mid = comp.get((inner, k - i, other))
                    right = None if mid is None else comp.get((outer, i, mid))
                elif k < i:
                    mid = comp.get((outer, k, other))
                    right = None if mid is None else comp.get((mid, i + len(x_in) - 1, inner))
                else:
                    mid = comp.get((outer, k - width + 1, other))
                    right = None if mid is None else comp.get((mid, i, inner))
                if right is not None and right != left:
                    return False
    return True


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    colour, op = e.form("colour"), e.form("op")
    slot = e.form("slot")
    inp, out, unit, sub = e.form("input"), e.form("output"), e.form("unit"), e.form("subst")
    slots = fx.structure.elements("slot")
    first = slots[0]
    contiguous: list[Req] = [
        Total(f"inputs_contiguous_{k}", ((inp, ("o", later, "c")),), ((inp, ("o", earlier, "d")),))
        for k, (earlier, later) in enumerate(zip(slots[1:], slots[2:]), start=2)
    ]
    one_slot: list[Req] = [Forbid("unit_one_slot", ((unit, ("c", "e")), (inp, ("e", slots[1], "d"))))] if len(
        slots) > 1 else []
    return Compiled(
        (
            Total("output_given", ((op, ("o",)),), ((out, ("o", "c")),)),
            Functional("one_output", out, 1),
            Closure("output_typed", ((out, ("o", "c")),), ((op, ("o",)), (colour, ("c",)))),
            Closure("input_typed", ((inp, ("o", "i", "c")),), ((op, ("o",)), (slot, ("i",)), (colour, ("c",)))),
            Functional("one_input", inp, 2),
            Total("inputs_start", ((op, ("o",)),), ((inp, ("o", first, "c")),)),
            *contiguous,
            Total("unit_given", ((colour, ("c",)),), ((unit, ("c", "e")),)),
            Functional("one_unit", unit, 1),
            Closure("unit_typed", ((unit, ("c", "e")),), ((colour, ("c",)), (op, ("e",)))),
            Closure("unit_profile", ((unit, ("c", "e")),), ((inp, ("e", first, "c")), (out, ("e", "c")))),
            *one_slot,
            Closure("subst_typed", ((sub, ("o", "i", "p", "r")),), ((op, ("o",)), (slot, ("i",)), (op, ("p",)),
                                                                     (op, ("r",)))),
            Functional("one_result", sub, 3),
            Total("slot_exists", ((sub, ("o", "i", "p", "r")),), ((inp, ("o", "i", "c")),)),
            Closure("colours_match", ((sub, ("o", "i", "p", "r")), (inp, ("o", "i", "c"))), ((out, ("p", "c")),)),
            Closure("result_output", ((sub, ("o", "i", "p", "r")), (out, ("o", "c"))), ((out, ("r", "c")),)),
            Closure("unit_outside", ((out, ("p", "c")), (unit, ("c", "e"))), ((sub, ("e", first, "p", "p")),)),
            Closure("unit_inside", ((inp, ("p", "i", "c")), (unit, ("c", "e"))), ((sub, ("p", "i", "e", "p")),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("result_inputs", result_inputs), ("table_full", table_full), ("brackets", brackets))),
    )
