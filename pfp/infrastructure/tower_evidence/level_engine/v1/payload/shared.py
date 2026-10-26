"""Helpers the payload specs share: the rows of a relation, an element's
position in its sort, exact pairs, and the text of a level's certificate
module (one theorem per evaluated fixture and value clause, each re-decided
by the kernel).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from engine.exact.q import ONE, ZERO, Q
from engine.exact.qi import QI
from engine.level import Fixture, FixtureVerdict
from engine.structure import FiniteStructure

Data = Callable[[FiniteStructure], Sequence[tuple[str, str, str]]]
Table = list[list[QI]]
NOUGHT, UNIT = QI(ZERO, ZERO), QI(ONE, ZERO)


def rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    """The tuples of one relation symbol, in hosted order."""
    return [a for n, a in fs.tuples if n == name]


def position(fs: FiniteStructure, sort: str, e: int) -> int | None:
    """The position of ``e`` in the declared order of ``sort``, or ``None``."""
    els = fs.elements(sort)
    return els.index(e) if e in els else None


def pair_of(fs: FiniteStructure, a: int, b: int) -> QI | None:
    """The exact pair ``a + b i`` carried by two value elements."""
    x, y = fs.value(a), fs.value(b)
    return None if x is None or y is None else QI(x, y)


def one_pair(fs: FiniteStructure, name: str) -> QI | None:
    """The one pair a two-place symbol carries; ``None`` when it is absent,
    repeated or undecodable."""
    got = rows(fs, name)
    return pair_of(fs, got[0][0], got[0][1]) if len(got) == 1 else None


def grid(fs: FiniteStructure, name: str, keys: Sequence[Sequence[int]]) -> dict[tuple[int, ...], QI] | None:
    """A relation whose last two places are a pair, keyed by its other places;
    ``None`` when a key is repeated, a pair undecodable, or a key of
    ``keys`` (the product of the given element lists) missing."""
    got: dict[tuple[int, ...], QI] = {}
    for args in rows(fs, name):
        z = pair_of(fs, args[-2], args[-1])
        if z is None or args[:-2] in got:
            return None
        got[args[:-2]] = z
    want: list[tuple[int, ...]] = [()]
    for ks in keys:
        want = [w + (k,) for w in want for k in ks]
    return got if all(w in got for w in want) else None


def tmul(a: Table, b: Table) -> Table:
    """The product of two square tables of pairs."""
    n = len(a)
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            acc = NOUGHT
            for t in range(n):
                acc = acc + a[i][t] * b[t][j]
            row.append(acc)
        out.append(row)
    return out


def tadd(a: Table, b: Table) -> Table:
    return [[x + y for x, y in zip(r, s)] for r, s in zip(a, b)]


def mirrored(a: Table) -> Table:
    """The mirrored transpose."""
    return [[a[j][i].conj() for j in range(len(a))] for i in range(len(a))]


def unit_table(n: int) -> Table:
    return [[UNIT if i == j else NOUGHT for j in range(n)] for i in range(n)]


def tapply(a: Table, v: Sequence[QI]) -> list[QI]:
    out = []
    for r in a:
        acc = NOUGHT
        for x, y in zip(r, v):
            acc = acc + x * y
        out.append(acc)
    return out


def size_of(v: Sequence[QI]) -> Q:
    return sum((z.norm2() for z in v), ZERO)


def certificates(module: str, clauses: Sequence[str], verdicts: Sequence[FixtureVerdict],
                 key: str) -> list[tuple[str, str, str]]:
    """(declaration, fixture, clause) for every fixture whose value clauses
    were evaluated (``key`` is one of them)."""
    out = []
    for v in verdicts:
        if dict(v.decoded).get(key) in ("PASS", "FAIL"):
            out += [(f"{module}.{v.fid}_{c}", v.fid, c) for c in clauses]
    return out


def render(module: str, title: str, defs: Sequence[str], fixtures: Sequence[Fixture],
           verdicts: Sequence[FixtureVerdict], certs: Sequence[tuple[str, str, str]], data: Data,
           calls: Mapping[str, str]) -> str:
    """A certificate module: the definitions, each evaluated fixture's data,
    and one theorem per certificate stating the verdict the engine computed."""
    from engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(module, title, defs)
    order = [v.fid for v in verdicts]
    for fid in sorted({fid for _, fid, _ in certs}, key=order.index):
        for name, typ, text in data(by[fid].structure):
            lines += [f"def {name}_{fid} : {typ} :=", f"  {text}", ""]
    decoded = {v.fid: dict(v.decoded) for v in verdicts}
    for name, fid, clause in certs:
        verdict = "true" if decoded[fid][clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {calls[clause].format(f=fid)} = {verdict} := by decide", ""]
    lines += [f"end {module}", ""]
    return "\n".join(lines)


def lean_q(x: Q) -> str:
    return f"QN.ofPair ({x.num}) {x.den}"


def lean_pair(z: QI) -> str:
    return f"({lean_q(z.re)}, {lean_q(z.im)})"


def lean_list(items: Sequence[str]) -> str:
    return "[" + ", ".join(items) + "]"


PAIR_DEFS = (
    "/-- An exact pair `a + b i`. -/",
    "abbrev Pair := Prod QN QN",
    "",
    "def padd (x y : Pair) : Pair := (x.1 + y.1, x.2 + y.2)",
    "",
    "def pmul (x y : Pair) : Pair := (x.1 * y.1 - x.2 * y.2, x.1 * y.2 + x.2 * y.1)",
    "",
    "/-- The mirror of a pair: `a - b i`. -/",
    "def mirror (x : Pair) : Pair := (x.1, -x.2)",
    "",
    "/-- The size of a pair: `a * a + b * b`. -/",
    "def size (x : Pair) : QN := x.1 * x.1 + x.2 * x.2",
    "",
    "/-- The sum of a list of pairs. -/",
    "def psum (xs : List Pair) : Pair := xs.foldl padd (0, 0)",
    "",
    "/-- The sum of the sizes of a row. -/",
    "def rowSize (xs : List Pair) : QN := xs.foldl (fun acc x => acc + size x) 0",
    "",
)

TABLE_DEFS = PAIR_DEFS + (
    "abbrev PTable := List (List Pair)",
    "",
    "def pentry (t : PTable) (i j : Nat) : Pair := (t.getD i []).getD j (0, 0)",
    "",
    "/-- The product of two `n` by `n` tables of pairs. -/",
    "def pmm (a b : PTable) (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j =>",
    "    psum ((List.range n).map fun t => pmul (pentry a i t) (pentry b t j))",
    "",
    "/-- The mirrored transpose. -/",
    "def mirrorT (a : PTable) (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j => mirror (pentry a j i)",
    "",
    "def unitT (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j => if i = j then (1, 0) else (0, 0)",
    "",
    "def zeroT (n : Nat) : PTable := (List.range n).map fun _ => (List.range n).map fun _ => (0, 0)",
    "",
    "def ptadd (a b : PTable) : PTable := List.zipWith (List.zipWith padd) a b",
    "",
    "/-- A table times a row. -/",
    "def papply (u : PTable) (v : List Pair) : List Pair := u.map fun r => psum (List.zipWith pmul r v)",
    "",
    "/-- Self-mirrored and idempotent. -/",
    "def isSplitMember (p : PTable) : Bool :=",
    "  decide (mirrorT p p.length = p) && decide (pmm p p p.length = p)",
    "",
    "/-- A complete family: members sum to the unit table and are pairwise orthogonal. -/",
    "def isComplete (n : Nat) (ps : List PTable) : Bool :=",
    "  decide (ps.foldl ptadd (zeroT n) = unitT n) &&",
    "    (List.range ps.length).all fun i => (List.range ps.length).all fun j =>",
    "      i == j || decide (pmm (ps.getD i []) (ps.getD j []) n = zeroT n)",
    "",
)


def lean_table(t: Table) -> str:
    return lean_list([lean_list([lean_pair(z) for z in r]) for r in t])
