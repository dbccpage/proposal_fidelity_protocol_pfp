"""A skeletal table over cyclic groups: objects are the integers mod ``n``
under addition, every object's self-maps are the integers mod ``m``, and a
rebracketing value is given for every triple.  The two composites around
the five-term boundary must agree at every quadruple, and the claimed class
(a coboundary or not) is recomputed, never read.

The two composites at ``(w, x, y, z)`` are, additively, ``a(w + x, y, z) +
a(w, x, y + z)`` and ``a(x, y, z) + a(w, x + y, z) + a(w, x, y)``.  The
table is a coboundary when some two-argument table ``b`` has ``a(x, y, z) =
b(y, z) - b(x + y, z) + b(x, y + z) - b(x, y)`` everywhere; every ``b`` is
tried (``m^(n n)`` of them, at most 4096).

The claim: objects and self-maps (in declared order: position is the
residue) and one class mark, carrying 0 for "coboundary" and 1 for
"nontrivial" as its value; ``value(x, y, z, v)`` (the rebracketing value at
``(x, y, z)`` is ``v``).

Relational clauses, carried by derivability over the hosted claim:
``table_total``, ``one_value`` and ``value_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (one mark,
0 or 1, and at most 4096 tables ``b``), ``coherent`` (the two composites
agree at every quadruple: the refused case is two different composites
declared coherent) and ``class_exact`` (the claimed class is the recomputed
one).  The last two are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import product
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "associator_tables"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "AssociatorTables"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "coherent", "class_exact")
LEAN_CLAUSES = ("coherent", "class_exact")
MAX_TABLES = 4096


def sizes(fs: FiniteStructure) -> tuple[int, int]:
    return len(fs.elements("object")), len(fs.elements("selfmap"))


def table(fs: FiniteStructure) -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for x, y, z, v in rows(fs, "value"):
        a, b, c = position(fs, "object", x), position(fs, "object", y), position(fs, "object", z)
        w = position(fs, "selfmap", v)
        if a is not None and b is not None and c is not None and w is not None:
            out[(a, b, c)] = w
    return out


def mark(fs: FiniteStructure) -> int:
    got = [fs.value(c) for c in fs.elements("mark")]
    return got[0].num if len(got) == 1 and got[0] is not None and got[0].den == 1 else -1


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    n, m = sizes(fs)
    return n >= 1 and m >= 1 and m ** (n * n) <= MAX_TABLES and mark(fs) in (0, 1)


def coherent(fs: FiniteStructure, _o: Oracle) -> bool:
    n, m = sizes(fs)
    a = table(fs)
    for w, x, y, z in product(range(n), repeat=4):
        keys = [((w + x) % n, y, z), (w, x, (y + z) % n), (x, y, z), (w, (x + y) % n, z), (w, x, y)]
        if any(k not in a for k in keys):
            return False
        v = [a[k] for k in keys]
        if (v[0] + v[1] - v[2] - v[3] - v[4]) % m:
            return False
    return True


def is_coboundary(fs: FiniteStructure) -> bool:
    n, m = sizes(fs)
    a = table(fs)
    pairs = list(product(range(n), repeat=2))
    triples = list(product(range(n), repeat=3))
    if m ** len(pairs) > MAX_TABLES or any(t not in a for t in triples):
        return False
    for vals in product(range(m), repeat=len(pairs)):
        b = dict(zip(pairs, vals))
        if all((b[(y, z)] - b[((x + y) % n, z)] + b[(x, (y + z) % n)] - b[(x, y)] - a[(x, y, z)]) % m == 0
               for x, y, z in triples):
            return True
    return False


def class_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return mark(fs) == (0 if is_coboundary(fs) else 1)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"coboundary": is_coboundary(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "coherent")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    obj, sm, val = e.form("object"), e.form("selfmap"), e.form("value")
    return Compiled(
        (
            Total("table_total", ((obj, ("x",)), (obj, ("y",)), (obj, ("z",))), ((val, ("x", "y", "z", "v")),)),
            Functional("one_value", val, 3),
            Closure("value_typed", ((val, ("x", "y", "z", "v")),),
                    ((obj, ("x",)), (obj, ("y",)), (obj, ("z",)), (sm, ("v",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("coherent", coherent), ("class_exact", class_exact))),
    )


LEAN_DEFS = (
    "/-- The value at a triple, from the table's rows. -/",
    "def at3 (t : List (Prod (Prod Nat (Prod Nat Nat)) Nat)) (x y z : Nat) : Nat :=",
    "  ((t.find? fun r => r.1 == (x, (y, z))).map (fun r => r.2)).getD 0",
    "",
    "def coherent (n m : Nat) (t : List (Prod (Prod Nat (Prod Nat Nat)) Nat)) : Bool :=",
    "  (List.range n).all fun w => (List.range n).all fun x => (List.range n).all fun y => (List.range n).all fun z =>",
    "    (at3 t ((w + x) % n) y z + at3 t w x ((y + z) % n)) % m ==",
    "      (at3 t x y z + at3 t w ((x + y) % n) z + at3 t w x y) % m",
    "",
    "/-- Every two-argument table on `n` objects with values mod `m`, as value lists. -/",
    "def tables : Nat -> Nat -> List (List Nat)",
    "  | 0, _ => [[]]",
    "  | k + 1, m => (tables k m).flatMap fun b => (List.range m).map fun v => b ++ [v]",
    "",
    "def bAt (n : Nat) (b : List Nat) (x y : Nat) : Nat := b.getD (x * n + y) 0",
    "",
    "def isCoboundary (n m : Nat) (t : List (Prod (Prod Nat (Prod Nat Nat)) Nat)) : Bool :=",
    "  (tables (n * n) m).any fun b =>",
    "    (List.range n).all fun x => (List.range n).all fun y => (List.range n).all fun z =>",
    "      (bAt n b y z + bAt n b x ((y + z) % n) + m * m) % m ==",
    "        (bAt n b ((x + y) % n) z + bAt n b x y + at3 t x y z) % m",
    "",
    "def classExact (n m : Nat) (t : List (Prod (Prod Nat (Prod Nat Nat)) Nat)) (mk : Nat) : Bool :=",
    "  mk == (if isCoboundary n m t then 0 else 1)",
    "",
)
LEAN_CALLS = {"coherent": "coherent n_{f} m_{f} table_{f}", "class_exact": "classExact n_{f} m_{f} table_{f} mark_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    n, m = sizes(fs)
    return [("n", "Nat", str(n)), ("m", "Nat", str(m)),
            ("table", "List (Prod (Prod Nat (Prod Nat Nat)) Nat)",
             lean_list([f"(({x}, ({y}, {z})), {v})" for (x, y, z), v in sorted(table(fs).items())])),
            ("mark", "Nat", str(mark(fs)))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `associator_tables`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
