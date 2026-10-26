"""Derivation trees of a use-once term language: a variable, a pair of two
terms, a copy (consumes a variable and binds two fresh names of its kind in
a body) and a discard (consumes a variable unused).  Use counts are
computed from the leaves and binders, never read: every available name is
consumed exactly once, copies and discards only on kinds declared
copyable, and the declared type is the computed pair type.

The claim: names, kinds, nodes and type nodes (each in declared order),
``in_context(x, k)``, ``copyable(k)``, ``root(n)``, ``var(n, x)``,
``pair(n, a, b)``, ``copy(n, x, y, z, body)``, ``discard(n, x, body)``,
``leaf(t, k)``, ``both(t, a, b)`` and ``declared(t)``.

Relational clauses, carried by derivability over the hosted claim:
``root_given``, ``one_root``, ``declared_given``, ``one_declared``,
``in_context_typed`` and ``var_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (the nodes
form a tree from the root, each with one constructor; the type nodes a
finite tree; copies bind two distinct fresh names), ``in_scope`` (every
consumed name is in the context or bound by an enclosing copy),
``at_most_once`` (no name is consumed twice: the refused case is a
protected resource used twice without a copy), ``at_least_once`` (every
name in scope is consumed), ``copy_kinds`` (a copy or discard consumes a
copyable kind) and ``type_exact`` (the declared type is the computed one).
The kernel re-decides the last five over the tree.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Union

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "use_once_terms"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "UseOnceTerms"
EXACT: tuple[str, ...] = ()
CLAUSES = ("well_formed", "in_scope", "at_most_once", "at_least_once", "copy_kinds", "type_exact")
LEAN_CLAUSES = CLAUSES[1:]
Ty = Union[int, tuple["Ty", "Ty"]]
# A term, by positions: ("var", x) | ("pair", a, b) | ("copy", x, y, z, body) | ("discard", x, body)
Tm = tuple[object, ...]


def _p(fs: FiniteStructure, sort: str, e: int) -> int:
    k = position(fs, sort, e)
    return -1 if k is None else k


def _ctors(fs: FiniteStructure) -> dict[int, list[Tm]]:
    out: dict[int, list[Tm]] = {}
    for n, x in rows(fs, "var"):
        out.setdefault(n, []).append(("var", _p(fs, "name", x)))
    for n, a, b in rows(fs, "pair"):
        out.setdefault(n, []).append(("pair", a, b))
    for n, x, y, z, body in rows(fs, "copy"):
        out.setdefault(n, []).append(("copy", _p(fs, "name", x), _p(fs, "name", y), _p(fs, "name", z), body))
    for n, x, body in rows(fs, "discard"):
        out.setdefault(n, []).append(("discard", _p(fs, "name", x), body))
    return out


def term(fs: FiniteStructure) -> Tm | None:
    """The tree from the root, with node elements replaced by subterms; None
    when it is not a finite tree with one constructor per node."""
    roots = [n for (n,) in rows(fs, "root")]
    ct = _ctors(fs)
    seen: set[int] = set()

    def go(n: int) -> Tm | None:
        if n in seen or len(ct.get(n, [])) != 1:
            return None
        seen.add(n)
        c = ct[n][0]
        if c[0] == "var":
            return c
        if c[0] == "pair":
            a, b = go(int(str(c[1]))), go(int(str(c[2])))
            return None if a is None or b is None else ("pair", a, b)
        if c[0] == "copy":
            body = go(int(str(c[4])))
            return None if body is None else (c[0], c[1], c[2], c[3], body)
        body = go(int(str(c[2])))
        return None if body is None else ("discard", c[1], body)

    t = go(roots[0]) if len(roots) == 1 else None
    return t if t is not None and seen == set(fs.elements("node")) else None


def context(fs: FiniteStructure) -> dict[int, int]:
    return {_p(fs, "name", x): _p(fs, "kind", k) for x, k in rows(fs, "in_context")}


def copyable(fs: FiniteStructure) -> set[int]:
    return {_p(fs, "kind", k) for (k,) in rows(fs, "copyable")}


class Walk:
    """One traversal recording each defect separately."""

    def __init__(self, fs: FiniteStructure, t: Tm) -> None:
        self.ok_scope = self.ok_once = self.ok_kinds = self.ok_fresh = True
        self.uses: dict[int, int] = {x: 0 for x in context(fs)}
        self.scope = dict(context(fs))
        self.copyable = copyable(fs)
        self.retired: set[int] = set()
        self.ty = self.walk(t)

    def consume(self, x: int) -> int:
        if x not in self.scope:
            self.ok_scope = False
            return -1
        self.uses[x] = self.uses.get(x, 0) + 1
        if self.uses[x] > 1:
            self.ok_once = False
        return self.scope[x]

    def walk(self, t: Tm) -> Ty:
        if t[0] == "var":
            return self.consume(int(str(t[1])))
        if t[0] == "pair":
            return (self.walk(t[1]), self.walk(t[2]))  # type: ignore[arg-type]
        if t[0] == "discard":
            if self.consume(int(str(t[1]))) not in self.copyable:
                self.ok_kinds = False
            return self.walk(t[2])  # type: ignore[arg-type]
        kind = self.consume(int(str(t[1])))
        if kind not in self.copyable:
            self.ok_kinds = False
        fresh = (int(str(t[2])), int(str(t[3])))
        if fresh[0] == fresh[1] or any(n in self.scope or n in self.retired for n in fresh):
            self.ok_fresh = False
        for n in fresh:
            self.scope[n] = kind
            self.uses[n] = 0
        out = self.walk(t[4])  # type: ignore[arg-type]
        for n in fresh:
            self.retired.add(n)
            self.scope.pop(n, None)
        return out


def declared_type(fs: FiniteStructure) -> Ty | None:
    leaves = {t: _p(fs, "kind", k) for t, k in rows(fs, "leaf")}
    pairs = {t: (a, b) for t, a, b in rows(fs, "both")}
    got = [t for (t,) in rows(fs, "declared")]

    def go(t: int, depth: int) -> Ty | None:
        if depth > len(fs.elements("tnode")):
            return None
        if t in leaves and t not in pairs:
            return leaves[t]
        if t in pairs and t not in leaves:
            a, b = go(pairs[t][0], depth + 1), go(pairs[t][1], depth + 1)
            return None if a is None or b is None else (a, b)
        return None

    return go(got[0], 0) if len(got) == 1 else None


def _walk(fs: FiniteStructure) -> Walk | None:
    t = term(fs)
    return None if t is None else Walk(fs, t)


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and w.ok_fresh and declared_type(fs) is not None


def in_scope(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and w.ok_scope


def at_most_once(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and w.ok_once


def at_least_once(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and all(k >= 1 for k in w.uses.values())


def copy_kinds(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and w.ok_kinds


def type_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    w = _walk(fs)
    return w is not None and w.ty == declared_type(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    w = _walk(fs)
    return {"uses": None if w is None else sorted(w.uses.items())}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "type_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    name, kind, node, tnode = e.form("name"), e.form("kind"), e.form("node"), e.form("tnode")
    root, declared, ctx, var = e.form("root"), e.form("declared"), e.form("in_context"), e.form("var")
    return Compiled(
        (
            Total("root_given", (), ((root, ("n",)),)),
            Functional("one_root", root, 0),
            Total("declared_given", (), ((declared, ("t",)),)),
            Functional("one_declared", declared, 0),
            Closure("in_context_typed", ((ctx, ("x", "k")),), ((name, ("x",)), (kind, ("k",)))),
            Closure("var_typed", ((var, ("n", "x")),), ((node, ("n",)), (name, ("x",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("in_scope", in_scope), ("at_most_once", at_most_once),
            ("at_least_once", at_least_once), ("copy_kinds", copy_kinds), ("type_exact", type_exact))),
    )


LEAN_DEFS = (
    "inductive Tm where",
    "  | var (x : Nat)",
    "  | pair (a b : Tm)",
    "  | copy (x y z : Nat) (body : Tm)",
    "  | discard (x : Nat) (body : Tm)",
    "",
    "inductive Ty where",
    "  | leaf (k : Nat)",
    "  | both (a b : Ty)",
    "  | none",
    "  deriving DecidableEq",
    "",
    "/-- The walk's state: scope (name, kind), use counts, retired names and four flags. -/",
    "structure St where",
    "  scope : List (Prod Nat Nat)",
    "  uses : List (Prod Nat Nat)",
    "  retired : List Nat",
    "  okScope : Bool",
    "  okOnce : Bool",
    "  okKinds : Bool",
    "",
    "def kindOf (s : St) (x : Nat) : Option Nat := (s.scope.find? fun p => p.1 == x).map (fun p => p.2)",
    "",
    "def bump (us : List (Prod Nat Nat)) (x : Nat) : List (Prod Nat Nat) :=",
    "  if us.any (fun p => p.1 == x) then us.map fun p => if p.1 == x then (p.1, p.2 + 1) else p else us ++ [(x, 1)]",
    "",
    "def countOf (us : List (Prod Nat Nat)) (x : Nat) : Nat := ((us.find? fun p => p.1 == x).map (fun p => p.2)).getD 0",
    "",
    "def consume (s : St) (x : Nat) : Prod St Ty :=",
    "  match kindOf s x with",
    "  | none => (St.mk s.scope s.uses s.retired false s.okOnce s.okKinds, .none)",
    "  | some k => let us := bump s.uses x",
    "      (St.mk s.scope us s.retired s.okScope (s.okOnce && countOf us x <= 1) s.okKinds, .leaf k)",
    "",
    "def kindNat : Ty -> Nat",
    "  | .leaf k => k",
    "  | _ => 1000000",
    "",
    "def walk (cp : List Nat) : Tm -> St -> Prod St Ty",
    "  | .var x, s => consume s x",
    "  | .pair a b, s => let r1 := walk cp a s",
    "      let r2 := walk cp b r1.1",
    "      (r2.1, .both r1.2 r2.2)",
    "  | .discard x body, s => let r := consume s x",
    "      walk cp body (St.mk r.1.scope r.1.uses r.1.retired r.1.okScope r.1.okOnce",
    "        (r.1.okKinds && cp.contains (kindNat r.2)))",
    "  | .copy x y z body, s => let r := consume s x",
    "      let k := kindNat r.2",
    "      let s1 := St.mk ((y, k) :: (z, k) :: r.1.scope) (r.1.uses ++ [(y, 0), (z, 0)]) r.1.retired",
    "        r.1.okScope r.1.okOnce (r.1.okKinds && cp.contains k)",
    "      let r2 := walk cp body s1",
    "      (St.mk (r2.1.scope.filter (fun p => p.1 != y && p.1 != z)) r2.1.uses (y :: z :: r2.1.retired)",
    "        r2.1.okScope r2.1.okOnce r2.1.okKinds, r2.2)",
    "",
    "def start (ctx : List (Prod Nat Nat)) : St :=",
    "  St.mk ctx (ctx.map (fun p => (p.1, 0))) [] true true true",
    "",
    "def inScope (ctx : List (Prod Nat Nat)) (cp : List Nat) (t : Tm) : Bool := (walk cp t (start ctx)).1.okScope",
    "",
    "def atMostOnce (ctx : List (Prod Nat Nat)) (cp : List Nat) (t : Tm) : Bool := (walk cp t (start ctx)).1.okOnce",
    "",
    "def atLeastOnce (ctx : List (Prod Nat Nat)) (cp : List Nat) (t : Tm) : Bool :=",
    "  (walk cp t (start ctx)).1.uses.all fun p => 1 <= p.2",
    "",
    "def copyKinds (ctx : List (Prod Nat Nat)) (cp : List Nat) (t : Tm) : Bool := (walk cp t (start ctx)).1.okKinds",
    "",
    "def typeExact (ctx : List (Prod Nat Nat)) (cp : List Nat) (t : Tm) (ty : Ty) : Bool :=",
    "  decide ((walk cp t (start ctx)).2 = ty)",
    "",
)
LEAN_CALLS = {"in_scope": "inScope ctx_{f} cp_{f} tm_{f}", "at_most_once": "atMostOnce ctx_{f} cp_{f} tm_{f}",
              "at_least_once": "atLeastOnce ctx_{f} cp_{f} tm_{f}", "copy_kinds": "copyKinds ctx_{f} cp_{f} tm_{f}",
              "type_exact": "typeExact ctx_{f} cp_{f} tm_{f} ty_{f}"}


def _lean_tm(t: Tm) -> str:
    if t[0] == "var":
        return f"(.var {t[1]})"
    if t[0] == "pair":
        return f"(.pair {_lean_tm(t[1])} {_lean_tm(t[2])})"  # type: ignore[arg-type]
    if t[0] == "copy":
        return f"(.copy {t[1]} {t[2]} {t[3]} {_lean_tm(t[4])})"  # type: ignore[arg-type]
    return f"(.discard {t[1]} {_lean_tm(t[2])})"  # type: ignore[arg-type]


def _lean_ty(t: Ty) -> str:
    if isinstance(t, int):
        return f"(.leaf {t})"
    return f"(.both {_lean_ty(t[0])} {_lean_ty(t[1])})"


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    t, ty = term(fs), declared_type(fs)
    assert t is not None and ty is not None
    return [("ctx", "List (Prod Nat Nat)", lean_list([f"({x}, {k})" for x, k in sorted(context(fs).items())])),
            ("cp", "List Nat", lean_list([str(k) for k in sorted(copyable(fs))])),
            ("tm", "Tm", _lean_tm(t)), ("ty", "Ty", _lean_ty(ty))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The use-count clauses of `use_once_terms`, decided by the kernel", LEAN_DEFS,
                  fixtures, verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
