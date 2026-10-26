"""Two prenex formulas over unary and binary symbols, the second the typed
translation of the first: every symbol of the first language is renamed to
a symbol of the second with the same number of places, and the second
formula is read back through the renaming.  Both formulas are evaluated
here on every structure of the declared fragment (every interpretation of
the first language's symbols on the domains {0, ..., n - 1}, 1 <= n <= k,
with k the hosted bound, at most 3), and they must agree on the whole
fragment.  A second prefix that reorders the first one's quantifiers (the
same quantifiers and variables, in another order) is accepted only when
that agreement holds: the reordering is then proved within the fragment,
and nowhere else.

The claim: two formulas, ``translates(g, f)`` (``g`` is the translation of
``f``); variables, each named by a text of one lower-case letter; symbols,
each named by a text, with ``unary(s)`` or ``binary(s)`` and
``declared(s, f)`` (``s`` belongs to the language of ``f``);
``renamed(s, t)``; quantifiers, with ``opens(q, f)`` (the prefix of ``f``
is its quantifiers in declared order, outermost first), ``every(q)`` or
``some(q)``, and ``binds(q, v)``; the nodes of the quantifier-free part,
with ``matrix(n, f)`` (the top node of ``f``), ``within(n, f)``,
``reads(n, s)`` with ``first(n, v)`` and ``second(n, v)``, ``equal(n)``
with ``first`` and ``second``, ``negates(n, m)``, ``both(n, l, r)`` and
``either(n, l, r)``; and one bound, carrying ``k``.

Relational clauses, carried by derivability over the hosted claim: the
renaming (``map_total``, ``map_typed``, ``one_image``, ``keeps_unary``,
``keeps_binary``), the typing of the formulas (``reads_declared``,
``two_places``, ``one_place``, ``first_given``, ``first_bound``,
``second_bound``, ``one_first``, ``one_second``, ``one_read``), the
placing of nodes and quantifiers (``nodes_placed``, ``one_formula``,
``tops_placed``, ``negation_placed``, ``both_placed``, ``either_placed``,
``quantifiers_placed``, ``one_opening``, ``binds_given``, ``one_bound``)
and ``one_arity`` and ``one_kind``.

Decoded clauses, decided outside the grammar: ``well_formed`` (every
element read one way, names as declared, the renaming one to one onto what
the translation reads, the bound at most 3 with at most 12 cells at the top
size), ``bound_once`` (no prefix binds a variable twice), ``swap_proved``
(a reordered prefix agrees with the first formula on the whole fragment:
the refused case is a quantifier swap that disagrees somewhere in it) and
``meaning_kept`` (any other second formula agrees on the whole fragment).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Iterator
from itertools import product
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "renamed_formulas"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "bound_once", "swap_proved", "meaning_kept")
MAX_SIZE = 3
MAX_CELLS = 12
LETTERS = "abcdefghijklmnopqrstuvwxyz"

# A node of the quantifier-free part, as a tree: ("reads", s, v, ...),
# ("equal", v, w), ("negates", m), ("both", l, r) or ("either", l, r), where
# s is a symbol, v and w are variables (elements) and m, l, r are trees.
Node = tuple[object, ...]
Prefix = tuple[tuple[str, int], ...]
Formula = tuple[Prefix, Node]
Reading = dict[int, frozenset[tuple[int, ...]]]
Language = tuple[tuple[int, int], ...]


def _one(fs: FiniteStructure, name: str, e: int) -> bool:
    return (e,) in set(rows(fs, name))


def sides(fs: FiniteStructure) -> tuple[int, int] | None:
    """(the first formula, its translation), or ``None``."""
    got = rows(fs, "translates")
    if len(got) != 1:
        return None
    g, f = got[0]
    if g == f or sorted(fs.elements("formula")) != sorted((f, g)):
        return None
    return f, g


def arity(fs: FiniteStructure, s: int) -> int | None:
    one, two = _one(fs, "unary", s), _one(fs, "binary", s)
    return 1 if one and not two else 2 if two and not one else None


def prefix(fs: FiniteStructure, f: int) -> Prefix | None:
    """The prefix of ``f``: its quantifiers in declared order, outermost
    first, each as its kind (``A`` every, ``E`` some) and its variable."""
    opens = set(rows(fs, "opens"))
    out = []
    for q in fs.elements("quantifier"):
        if (q, f) not in opens:
            continue
        kinds = [k for k, name in (("A", "every"), ("E", "some")) if _one(fs, name, q)]
        bound = [v for qq, v in rows(fs, "binds") if qq == q]
        if len(kinds) != 1 or len(bound) != 1:
            return None
        out.append((kinds[0], bound[0]))
    return tuple(out)


def _node(fs: FiniteStructure, n: int, names: frozenset[int], scope: frozenset[int], seen: list[int]
          ) -> Node | None:
    """The node ``n`` as a tree, when it is read one way, its variables are
    bound in ``scope`` and it reads only symbols of ``names``; ``None``
    otherwise.  ``seen`` collects the nodes met; a node met twice (a cycle
    or a shared part) stops the reading."""
    if n in seen or n not in fs.elements("node"):
        return None
    seen.append(n)
    reads = [s for m, s in rows(fs, "reads") if m == n]
    first = [v for m, v in rows(fs, "first") if m == n]
    second = [v for m, v in rows(fs, "second") if m == n]
    negates = [m for k, m in rows(fs, "negates") if k == n]
    both = [(a, b) for k, a, b in rows(fs, "both") if k == n]
    either = [(a, b) for k, a, b in rows(fs, "either") if k == n]
    equal = _one(fs, "equal", n)
    if len(reads) + len(negates) + len(both) + len(either) + int(equal) != 1:
        return None
    if len(first) > 1 or len(second) > 1 or any(v not in scope for v in first + second):
        return None
    places = tuple(first + second)
    if reads:
        s = reads[0]
        if s not in names or not first or arity(fs, s) != len(places):
            return None
        return ("reads", s) + places
    if equal:
        return ("equal",) + places if len(places) == 2 else None
    if places:
        return None
    if negates:
        sub = _node(fs, negates[0], names, scope, seen)
        return None if sub is None else ("negates", sub)
    kind, (a, b) = ("both", both[0]) if both else ("either", either[0])
    left = _node(fs, a, names, scope, seen)
    right = None if left is None else _node(fs, b, names, scope, seen)
    return None if left is None or right is None else (kind, left, right)


def formula(fs: FiniteStructure, f: int, seen: list[int]) -> Formula | None:
    pre = prefix(fs, f)
    tops = [n for n, ff in rows(fs, "matrix") if ff == f]
    if pre is None or len(tops) != 1:
        return None
    names = frozenset(s for s, ff in rows(fs, "declared") if ff == f)
    tree = _node(fs, tops[0], names, frozenset(v for _, v in pre), seen)
    return None if tree is None else (pre, tree)


def symbols_read(tree: Node) -> set[int]:
    if tree[0] == "reads":
        s = tree[1]
        return {s} if isinstance(s, int) else set()
    return {x for t in tree[1:] if isinstance(t, tuple) for x in symbols_read(t)}


class Parsed:
    """A well-formed claim: both formulas, the first language with its
    arities, the renaming read backwards, and the bound."""

    def __init__(self, first: Formula, second: Formula, language: Language, back: dict[int, int],
                 bound: int) -> None:
        self.first = first
        self.second = second
        self.language = language
        self.back = back
        self.bound = bound


def parse(fs: FiniteStructure) -> Parsed | None:
    got = sides(fs)
    if got is None:
        return None
    f, g = got
    seen: list[int] = []
    first, second = formula(fs, f, seen), formula(fs, g, seen)
    if first is None or second is None or sorted(seen) != list(fs.elements("node")):
        return None
    if any(arity(fs, s) is None or not fs.text(s) for s in fs.elements("symbol")):
        return None
    declared = set(rows(fs, "declared"))
    for side in (f, g):
        named = [fs.text(s) for s, ff in declared if ff == side]
        if len(set(named)) != len(named):
            return None
    letters = [fs.text(v) for v in fs.elements("variable")]
    if any(x is None or len(x) != 1 or x not in LETTERS for x in letters) or len(set(letters)) != len(letters):
        return None
    language = tuple((s, a) for s in fs.elements("symbol") if (s, f) in declared
                     for a in (arity(fs, s),) if a is not None)
    ren = rows(fs, "renamed")
    back = {t: s for s, t in ren}
    arities = dict(language)
    if len(back) != len(ren) or any(back.get(t) not in arities or arities[back[t]] != arity(fs, t)
                                    for t in symbols_read(second[1])):
        return None
    bounds = fs.elements("bound")
    v = fs.value(bounds[0]) if len(bounds) == 1 else None
    if v is None or v.den != 1 or not 1 <= v.num <= MAX_SIZE:
        return None
    if sum(v.num ** a for _, a in language) > MAX_CELLS:
        return None
    return Parsed(first, second, language, back, v.num)


def _holds(tree: Node, reading: Reading, env: dict[int, int], back: dict[int, int] | None) -> bool:
    kind = tree[0]
    if kind == "reads":
        s = int(str(tree[1]))
        name = s if back is None else back[s]
        return tuple(env[int(str(v))] for v in tree[2:]) in reading[name]
    if kind == "equal":
        return env[int(str(tree[1]))] == env[int(str(tree[2]))]
    subs = [t for t in tree[1:] if isinstance(t, tuple)]
    if kind == "negates":
        return not _holds(subs[0], reading, env, back)
    left, right = (_holds(t, reading, env, back) for t in subs)
    return (left and right) if kind == "both" else (left or right)


def truth(phi: Formula, reading: Reading, size: int, back: dict[int, int] | None,
          env: dict[int, int] | None = None, depth: int = 0) -> bool:
    """The formula on one structure; an inner binding of a variable hides
    an outer one."""
    env = {} if env is None else env
    pre, tree = phi
    if depth == len(pre):
        return _holds(tree, reading, env, back)
    kind, v = pre[depth]
    values = (truth(phi, reading, size, back, {**env, v: d}, depth + 1) for d in range(size))
    return all(values) if kind == "A" else any(values)


def structures(language: Language, size: int) -> Iterator[Reading]:
    """Every interpretation of the language on {0, ..., size - 1}."""
    cells = [(s, t) for s, a in language for t in product(range(size), repeat=a)]
    for bits in product((False, True), repeat=len(cells)):
        chosen: dict[int, set[tuple[int, ...]]] = {s: set() for s, _ in language}
        for (s, t), bit in zip(cells, bits):
            if bit:
                chosen[s].add(t)
        yield {s: frozenset(x) for s, x in chosen.items()}


_SEEN: dict[FiniteStructure, tuple[bool, int, int] | None] = {}


def compare(fs: FiniteStructure) -> tuple[bool, int, int] | None:
    """(whether the second prefix reorders the first, structures evaluated,
    structures on which the two formulas disagree), or ``None`` when the
    claim is not well formed.  Every structure of the fragment is
    evaluated, the second formula read back through the renaming."""
    if fs in _SEEN:
        return _SEEN[fs]
    p = parse(fs)
    out: tuple[bool, int, int] | None = None
    if p is not None:
        a, b = p.first[0], p.second[0]
        reorder = sorted(a) == sorted(b) and a != b
        seen = differ = 0
        for size in range(1, p.bound + 1):
            for reading in structures(p.language, size):
                seen += 1
                if truth(p.first, reading, size, None) != truth(p.second, reading, size, p.back):
                    differ += 1
        out = (reorder, seen, differ)
    _SEEN[fs] = out
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    return parse(fs) is not None


def bound_once(fs: FiniteStructure, _o: Oracle) -> bool:
    for f in fs.elements("formula"):
        pre = prefix(fs, f)
        if pre is None or len({v for _, v in pre}) != len(pre):
            return False
    return True


def swap_proved(fs: FiniteStructure, _o: Oracle) -> bool:
    got = compare(fs)
    return got is not None and (not got[0] or got[2] == 0)


def meaning_kept(fs: FiniteStructure, _o: Oracle) -> bool:
    got = compare(fs)
    return got is not None and (got[0] or got[2] == 0)


def describe(fs: FiniteStructure) -> dict[str, object]:
    got = compare(fs)
    return {"fragment": None if got is None else {"disagree": got[2], "reordered": got[0], "structures": got[1]}}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    node, quantifier = e.form("node"), e.form("quantifier")
    translates, declared, renamed = e.form("translates"), e.form("declared"), e.form("renamed")
    unary, binary, opens, binds = e.form("unary"), e.form("binary"), e.form("opens"), e.form("binds")
    every, some, matrix, within = e.form("every"), e.form("some"), e.form("matrix"), e.form("within")
    reads, first, second = e.form("reads"), e.form("first"), e.form("second")
    negates, both, either = e.form("negates"), e.form("both"), e.form("either")
    return Compiled(
        (
            Total("map_total", ((declared, ("s", "f")), (translates, ("g", "f"))), ((renamed, ("s", "t")),)),
            Closure("map_typed", ((renamed, ("s", "t")), (translates, ("g", "f"))),
                    ((declared, ("s", "f")), (declared, ("t", "g")))),
            Functional("one_image", renamed, 1),
            Closure("keeps_unary", ((renamed, ("s", "t")), (unary, ("s",))), ((unary, ("t",)),)),
            Closure("keeps_binary", ((renamed, ("s", "t")), (binary, ("s",))), ((binary, ("t",)),)),
            Forbid("one_arity", ((unary, ("s",)), (binary, ("s",)))),
            Closure("reads_declared", ((reads, ("n", "s")), (within, ("n", "f"))), ((declared, ("s", "f")),)),
            Total("two_places", ((reads, ("n", "s")), (binary, ("s",))), ((second, ("n", "v")),)),
            Forbid("one_place", ((reads, ("n", "s")), (unary, ("s",)), (second, ("n", "v")))),
            Total("first_given", ((reads, ("n", "s")),), ((first, ("n", "v")),)),
            Total("first_bound", ((first, ("n", "v")), (within, ("n", "f"))),
                  ((binds, ("q", "v")), (opens, ("q", "f")))),
            Total("second_bound", ((second, ("n", "v")), (within, ("n", "f"))),
                  ((binds, ("q", "v")), (opens, ("q", "f")))),
            Functional("one_first", first, 1),
            Functional("one_second", second, 1),
            Functional("one_read", reads, 1),
            Total("nodes_placed", ((node, ("n",)),), ((within, ("n", "f")),)),
            Functional("one_formula", within, 1),
            Closure("tops_placed", ((matrix, ("n", "f")),), ((within, ("n", "f")),)),
            Closure("negation_placed", ((negates, ("n", "m")), (within, ("n", "f"))), ((within, ("m", "f")),)),
            Closure("both_placed", ((both, ("n", "a", "b")), (within, ("n", "f"))),
                    ((within, ("a", "f")), (within, ("b", "f")))),
            Closure("either_placed", ((either, ("n", "a", "b")), (within, ("n", "f"))),
                    ((within, ("a", "f")), (within, ("b", "f")))),
            Total("quantifiers_placed", ((quantifier, ("q",)),), ((opens, ("q", "f")),)),
            Functional("one_opening", opens, 1),
            Total("binds_given", ((quantifier, ("q",)),), ((binds, ("q", "v")),)),
            Functional("one_bound", binds, 1),
            Forbid("one_kind", ((every, ("q",)), (some, ("q",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("bound_once", bound_once), ("swap_proved", swap_proved),
            ("meaning_kept", meaning_kept))),
    )
