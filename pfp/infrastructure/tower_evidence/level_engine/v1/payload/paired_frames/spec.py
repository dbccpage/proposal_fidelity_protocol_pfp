"""Two named factor rows of exact pairs ``a + b i``, their joined row, the
declared reading (which factor runs slowest in the joined row) and, when
the second factor runs slowest, the exchange table that carries the joined
row back to the declared order.  Slot order travels as hosted data: every
slot and every joined place carries its index as a hosted natural, the
factor order is the hosted relation ``before``, the reading is the hosted
relation ``slowest`` and the exchange table is the hosted relation
``exchange`` over places.

The claim: factors (each carrying its name as a text), slots (each carrying
its index), places (each carrying its index), numbers (exact values),
``before(f, g)`` (factor ``f`` is declared before factor ``g``),
``slot_of(s, f)``, ``entry(s, a, b)`` (slot ``s`` holds ``a + b i``),
``joined(p, a, b)`` (place ``p`` of the joined row holds ``a + b i``),
``slowest(f)`` (the reading: factor ``f`` runs slowest), ``exchange(p, q)``
(the exchange table sends place ``p`` to place ``q``) and ``claimed(v)``
(the claimed size of the joined row).

Rows are read in the order of their slots' hosted indices, the joined row
in the order of its places' hosted indices; nothing is ordered by element
position.  With factor sizes m and n in the declared factor order, slot
(i, j) of the joined frame is place n i + j when the first factor runs
slowest.

Relational clauses, carried by derivability over the hosted claim: every
slot has one factor and one entry, every place one entry, one reading, one
factor order (never a factor before itself), one claimed size, and the
exchange table sends a place to at most one place.

Decoded clauses, decided over exact values outside the grammar:

* ``indices_in_line``: each factor's slot indices, and the place indices,
  are 0, 1, ... with none repeated;
* ``names_apart``: the two factors carry different names;
* ``size_claimed``: the claimed size is m n, and there are m n places;
* ``reading_transported``: when the second factor runs slowest, an exchange
  table is given (the refused case: a permuted reading with no transport);
* ``exchange_exact``: an exchange table is given only when the second
  factor runs slowest, and then it sends place n i + j to place m j + i,
  and nothing else (a missing table is ``reading_transported``'s refusal);
* ``product_exact``: the joined row is the product row, first factor
  slowest, carried through the hosted exchange table when one is given.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.exact.q import Q
from engine.exact.qi import QI
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import pair_of, rows

CHALLENGE_ID = "paired_frames"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("indices_in_line", "names_apart", "size_claimed", "reading_transported", "exchange_exact",
           "product_exact")


def _nat(x: Q | None) -> int | None:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else None


def by_index(fs: FiniteStructure, els: list[int]) -> list[int] | None:
    """Elements sorted by their hosted indices; ``None`` when one carries no
    natural index or two carry the same."""
    got: list[tuple[int, int]] = []
    for e in els:
        k = _nat(fs.value(e))
        if k is None:
            return None
        got.append((k, e))
    if len({k for k, _ in got}) != len(got):
        return None
    return [e for _, e in sorted(got)]


def order(fs: FiniteStructure) -> tuple[int, int] | None:
    """The two factors, first then second, by the hosted ``before``."""
    got = rows(fs, "before")
    if len(got) != 1 or got[0][0] == got[0][1] or set(got[0]) != set(fs.elements("factor")):
        return None
    return got[0][0], got[0][1]


def slots(fs: FiniteStructure, f: int) -> list[int] | None:
    mine = [s for s, g in rows(fs, "slot_of") if g == f]
    return by_index(fs, [s for s in fs.elements("slot") if s in mine])


def factor_row(fs: FiniteStructure, f: int) -> list[QI] | None:
    ss = slots(fs, f)
    if ss is None:
        return None
    got = {s: pair_of(fs, a, b) for s, a, b in rows(fs, "entry")}
    out = [got.get(s) for s in ss]
    return None if any(z is None for z in out) else [z for z in out if z is not None]


def places(fs: FiniteStructure) -> list[int] | None:
    return by_index(fs, list(fs.elements("place")))


def joined_row(fs: FiniteStructure) -> list[QI] | None:
    ps = places(fs)
    if ps is None:
        return None
    got = {p: pair_of(fs, a, b) for p, a, b in rows(fs, "joined")}
    out = [got.get(p) for p in ps]
    return None if any(z is None for z in out) else [z for z in out if z is not None]


def reading_second(fs: FiniteStructure) -> bool | None:
    """Whether the reading names the second factor."""
    o, got = order(fs), rows(fs, "slowest")
    if o is None or len(got) != 1 or got[0][0] not in o:
        return None
    return got[0][0] == o[1]


def table(fs: FiniteStructure) -> dict[int, int] | None:
    """The hosted exchange table as place rank to place rank (ranks in the
    order of hosted indices); ``None`` when no table is given."""
    ps, got = places(fs), rows(fs, "exchange")
    if not got or ps is None:
        return None
    return {ps.index(p): ps.index(q) for p, q in got if p in ps and q in ps}


def sizes(fs: FiniteStructure) -> tuple[int, int] | None:
    o = order(fs)
    if o is None:
        return None
    a, b = slots(fs, o[0]), slots(fs, o[1])
    return None if a is None or b is None else (len(a), len(b))


def _in_line(fs: FiniteStructure, els: list[int]) -> bool:
    ks = [k for e in els if (k := _nat(fs.value(e))) is not None]
    return len(ks) == len(els) and sorted(ks) == list(range(len(els)))


def indices_in_line(fs: FiniteStructure, _o: Oracle) -> bool:
    owned = rows(fs, "slot_of")
    return (all(_in_line(fs, [s for s, g in owned if g == f]) for f in fs.elements("factor"))
            and _in_line(fs, list(fs.elements("place"))))


def names_apart(fs: FiniteStructure, _o: Oracle) -> bool:
    names = [fs.text(f) for f in fs.elements("factor")]
    return None not in names and "" not in names and len(set(names)) == len(names)


def size_claimed(fs: FiniteStructure, _o: Oracle) -> bool:
    mn, got = sizes(fs), rows(fs, "claimed")
    if mn is None or len(got) != 1:
        return False
    claimed = _nat(fs.value(got[0][0]))
    return claimed == mn[0] * mn[1] and len(fs.elements("place")) == mn[0] * mn[1]


def reading_transported(fs: FiniteStructure, _o: Oracle) -> bool:
    """The refused case: the second factor runs slowest and no exchange
    table carries the joined row back."""
    second = reading_second(fs)
    return second is not None and (not second or bool(rows(fs, "exchange")))


def exchange_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    second, mn = reading_second(fs), sizes(fs)
    if second is None or mn is None:
        return False
    if not rows(fs, "exchange"):
        return True
    if not second:
        return False
    m, n = mn
    want = {n * i + j: m * j + i for i in range(m) for j in range(n)}
    return table(fs) == want and len(rows(fs, "exchange")) == len(want)


def product(fs: FiniteStructure) -> list[QI | None] | None:
    """The product row, first factor slowest, carried through the hosted
    exchange table when one is given."""
    o = order(fs)
    if o is None:
        return None
    left, right = factor_row(fs, o[0]), factor_row(fs, o[1])
    if left is None or right is None:
        return None
    prod = [x * y for x in left for y in right]
    t = table(fs)
    if t is None:
        return list(prod)
    moved: list[QI | None] = [None] * len(prod)
    for k, z in enumerate(prod):
        if k not in t or not 0 <= t[k] < len(moved):
            return None
        moved[t[k]] = z
    return moved


def product_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    p, j = product(fs), joined_row(fs)
    return p is not None and j is not None and p == list(j)


def describe(fs: FiniteStructure) -> dict[str, object]:
    p = product(fs)
    return {"product_row": None if p is None else [None if z is None else [str(z.re), str(z.im)] for z in p]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    factor, slot, place, num = e.form("factor"), e.form("slot"), e.form("place"), e.form("number")
    before, slot_of, entry, joined = e.form("before"), e.form("slot_of"), e.form("entry"), e.form("joined")
    slowest, exchange, claimed = e.form("slowest"), e.form("exchange"), e.form("claimed")
    return Compiled(
        (
            Total("slots_owned", ((slot, ("s",)),), ((slot_of, ("s", "f")), (factor, ("f",)))),
            Functional("one_owner", slot_of, 1),
            Total("rows_given", ((slot, ("s",)),), ((entry, ("s", "a", "b")), (num, ("a",)), (num, ("b",)))),
            Functional("one_entry", entry, 1),
            Total("joined_given", ((place, ("p",)),), ((joined, ("p", "a", "b")), (num, ("a",)), (num, ("b",)))),
            Functional("one_joined", joined, 1),
            Total("reading_given", (), ((slowest, ("f",)), (factor, ("f",)))),
            Functional("one_reading", slowest, 0),
            Total("order_given", (), ((before, ("f", "g")), (factor, ("f",)), (factor, ("g",)))),
            Functional("one_order", before, 0),
            Forbid("order_strict", ((before, ("f", "f")),)),
            Total("size_given", (), ((claimed, ("v",)), (num, ("v",)))),
            Functional("one_size", claimed, 0),
            Functional("one_exchange", exchange, 1),
            Closure("exchange_typed", ((exchange, ("p", "q")),), ((place, ("p",)), (place, ("q",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("indices_in_line", indices_in_line), ("names_apart", names_apart), ("size_claimed", size_claimed),
            ("reading_transported", reading_transported), ("exchange_exact", exchange_exact),
            ("product_exact", product_exact))),
    )
