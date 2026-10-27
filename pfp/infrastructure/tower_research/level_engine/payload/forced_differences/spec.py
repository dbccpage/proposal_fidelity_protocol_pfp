# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A Boolean structural model over uniform independent source bits, and a
claimed pair of differences for a treatment and an outcome: the observed
difference (conditioning) and the forced one (replacing the treatment's
equation by a constant and re-evaluating).  An observed correlation is
never labelled a forced effect.

The claim: sources, variables and patterns (each in declared order; a
pattern carries its index as a value), at most one claimed observed
difference and one claimed forced difference (each an exact value),
``parent(v, p)`` (``p`` is a parent of variable ``v``; parents are read in
declared order, sources first), ``fires(v, k)`` (``v`` is one on the parent
assignment of index ``k``, the first parent most significant),
``treatment(v)`` and ``outcome(v)``.

Relational clauses, carried by derivability over the hosted claim:
``treatment_given``, ``one_treatment``, ``outcome_given``,
``one_outcome`` and ``fires_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (pattern
indices 0, 1, ... in declared order, each firing index below ``2^k`` for a
variable of ``k`` parents, at most 12 sources, treatment and outcome
distinct), ``acyclic`` (the parent graph has no cycle), ``observed_exact``
(the claimed observed difference, or its absence when a conditioning event
is empty, is the recomputed one), ``not_relabelled`` (the claimed forced
difference does not repeat the observed one while the recomputed forced
difference differs from it: the refused case) and ``forced_exact`` (the
claimed forced difference is the recomputed one).  Probabilities are exact
counts over every source assignment.  The last four are re-decided by the
kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import product
from typing import Literal

from operations.use_cases.level_engine.research_engine import lean_text as T
from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, rows

CHALLENGE_ID = "forced_differences"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ForcedDifferences"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "acyclic", "observed_exact", "not_relabelled", "forced_exact")
LEAN_CLAUSES = CLAUSES[1:]


class Model:
    """Nodes are numbered sources first, then variables, in declared order."""

    def __init__(self, fs: FiniteStructure) -> None:
        self.src, self.var = fs.elements("source"), fs.elements("variable")
        nodes = self.src + self.var
        self.index = {e: i for i, e in enumerate(nodes)}
        pat = {e: q.num for e in fs.elements("pattern") if (q := fs.value(e)) is not None and q.den == 1}
        self.parents: dict[int, list[int]] = {self.index[v]: [] for v in self.var}
        for v, p in rows(fs, "parent"):
            if v in self.index and p in self.index and self.index[v] in self.parents:
                self.parents[self.index[v]].append(self.index[p])
        for v in self.parents:
            self.parents[v].sort()
        self.table: dict[int, set[int]] = {self.index[v]: set() for v in self.var}
        for v, k in rows(fs, "fires"):
            if v in self.index and self.index[v] in self.table and k in pat:
                self.table[self.index[v]].add(pat[k])
        t = [self.index[v] for (v,) in rows(fs, "treatment") if v in self.index]
        o = [self.index[v] for (v,) in rows(fs, "outcome") if v in self.index]
        self.x = t[0] if len(t) == 1 else -1
        self.y = o[0] if len(o) == 1 else -1
        self.order = self._order()

    def _order(self) -> list[int] | None:
        placed, order = set(range(len(self.src))), []
        for _ in range(len(self.parents)):
            for v in sorted(self.parents):
                if v not in placed and all(p in placed for p in self.parents[v]):
                    order.append(v)
                    placed.add(v)
        return order if len(order) == len(self.parents) else None

    def world(self, u: tuple[int, ...], forced: dict[int, int]) -> dict[int, int]:
        vals = dict(enumerate(u))
        for v in self.order or []:
            if v in forced:
                vals[v] = forced[v]
                continue
            k = 0
            for p in self.parents[v]:
                k = 2 * k + vals[p]
            vals[v] = 1 if k in self.table[v] else 0
        return vals

    def observed(self) -> Q | None:
        worlds = [self.world(u, {}) for u in product((0, 1), repeat=len(self.src))]
        rates = []
        for value in (1, 0):
            chosen = [w for w in worlds if w[self.x] == value]
            rates.append(None if not chosen else Q.of(sum(w[self.y] for w in chosen), len(chosen)))
        return None if rates[0] is None or rates[1] is None else rates[0] - rates[1]

    def forced(self) -> Q:
        out = []
        for value in (1, 0):
            runs = [self.world(u, {self.x: value}) for u in product((0, 1), repeat=len(self.src))]
            out.append(Q.of(sum(w[self.y] for w in runs), len(runs)))
        return out[0] - out[1]


def _claims(fs: FiniteStructure, sort: str) -> list[Q]:
    return [v for e in fs.elements(sort) if (v := fs.value(e)) is not None]


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    m = Model(fs)
    pats = [fs.value(e) for e in fs.elements("pattern")]
    return (pats == [Q(k) for k in range(len(pats))] and 1 <= len(m.src) <= 12 and m.x != m.y
            and m.x >= len(m.src) and m.y >= len(m.src) and len(_claims(fs, "forced")) == 1
            and len(fs.elements("observed")) <= 1
            and all(k < 2 ** len(m.parents[v]) for v in m.table for k in m.table[v]))


def acyclic(fs: FiniteStructure, _o: Oracle) -> bool:
    return Model(fs).order is not None


def observed_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    m = Model(fs)
    if m.order is None or m.x < 0 or m.y < 0:
        return False
    claim = _claims(fs, "observed")
    return (claim[0] if claim else None) == m.observed()


def not_relabelled(fs: FiniteStructure, _o: Oracle) -> bool:
    m = Model(fs)
    if m.order is None or m.x < 0 or m.y < 0 or not _claims(fs, "forced"):
        return False
    claim, obs, forced = _claims(fs, "forced")[0], m.observed(), m.forced()
    return not (claim == obs and forced != obs)


def forced_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    m = Model(fs)
    if m.order is None or m.x < 0 or m.y < 0 or not _claims(fs, "forced"):
        return False
    return _claims(fs, "forced")[0] == m.forced()


def describe(fs: FiniteStructure) -> dict[str, object]:
    m = Model(fs)
    if m.order is None or m.x < 0 or m.y < 0:
        return {"observed": None, "forced": None}
    obs = m.observed()
    return {"observed": None if obs is None else fmt_q(obs), "forced": fmt_q(m.forced())}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "forced_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    var, pat = e.form("variable"), e.form("pattern")
    treat, out, fires = e.form("treatment"), e.form("outcome"), e.form("fires")
    return Compiled(
        (
            Total("treatment_given", (), ((treat, ("v",)),)),
            Functional("one_treatment", treat, 0),
            Total("outcome_given", (), ((out, ("v",)),)),
            Functional("one_outcome", out, 0),
            Closure("fires_typed", ((fires, ("v", "k")),), ((var, ("v",)), (pat, ("k",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("acyclic", acyclic), ("observed_exact", observed_exact),
            ("not_relabelled", not_relabelled), ("forced_exact", forced_exact))),
    )


LEAN_DEFS = (
    "/-- A model: the number of sources, and for each variable (numbered after",
    "the sources) its parents and the indices on which it is one. -/",
    "structure Model where",
    "  sources : Nat",
    "  eqs : List (Prod (List Nat) (List Nat))",
    "",
    "def parentsOf (m : Model) (v : Nat) : List Nat := (m.eqs.getD (v - m.sources) ([], [])).1",
    "",
    "/-- The order of evaluation, with fuel; none on a cycle. -/",
    "def orderF (m : Model) : Nat -> List Nat -> List Nat -> Option (List Nat)",
    "  | 0, placed, acc => if acc.length == m.eqs.length then some acc else none",
    "  | fuel + 1, placed, acc =>",
    "    let ready := ((List.range m.eqs.length).map (fun i => i + m.sources)).filter fun v =>",
    "      !placed.contains v && (parentsOf m v).all (fun p => placed.contains p)",
    "    if ready.isEmpty then (if acc.length == m.eqs.length then some acc else none)",
    "    else orderF m fuel (placed ++ ready) (acc ++ ready)",
    "",
    "def order (m : Model) : Option (List Nat) := orderF m (m.eqs.length + 1) (List.range m.sources) []",
    "",
    "def acyclic (m : Model) : Bool := (order m).isSome",
    "",
    "def lookup (vals : List (Prod Nat Nat)) (v : Nat) : Nat := ((vals.find? fun p => p.1 == v).map (fun p => p.2)).getD 0",
    "",
    "/-- Evaluate one source assignment `u` (a bit mask), forcing `x` to `fx` when given. -/",
    "def world (m : Model) (ord : List Nat) (u : Nat) (force : Option (Prod Nat Nat)) : List (Prod Nat Nat) :=",
    "  ord.foldl (fun vals v =>",
    "    match force with",
    "    | some f => if f.1 == v then vals ++ [(v, f.2)] else",
    "        let k := (parentsOf m v).foldl (fun acc p => 2 * acc + lookup vals p) 0",
    "        vals ++ [(v, if ((m.eqs.getD (v - m.sources) ([], [])).2).contains k then 1 else 0)]",
    "    | none =>",
    "        let k := (parentsOf m v).foldl (fun acc p => 2 * acc + lookup vals p) 0",
    "        vals ++ [(v, if ((m.eqs.getD (v - m.sources) ([], [])).2).contains k then 1 else 0)])",
    "    ((List.range m.sources).map fun i => (i, (u / 2 ^ (m.sources - 1 - i)) % 2))",
    "",
    "def worlds (m : Model) (ord : List Nat) (force : Option (Prod Nat Nat)) : List (List (Prod Nat Nat)) :=",
    "  (List.range (2 ^ m.sources)).map fun u => world m ord u force",
    "",
    "def rate (ws : List (List (Prod Nat Nat))) (y : Nat) : QN :=",
    "  QN.ofPair (Int.ofNat ((ws.filter fun w => lookup w y == 1).length)) ws.length",
    "",
    "def observed (m : Model) (x y : Nat) : Option QN :=",
    "  match order m with",
    "  | none => none",
    "  | some ord =>",
    "    let ws := worlds m ord none",
    "    let w1 := ws.filter fun w => lookup w x == 1",
    "    let w0 := ws.filter fun w => lookup w x == 0",
    "    if w1.isEmpty || w0.isEmpty then none else some (rate w1 y - rate w0 y)",
    "",
    "def forced (m : Model) (x y : Nat) : QN :=",
    "  match order m with",
    "  | none => 0",
    "  | some ord => rate (worlds m ord (some (x, 1))) y - rate (worlds m ord (some (x, 0))) y",
    "",
    "def observedExact (m : Model) (x y : Nat) (c : Option QN) : Bool := (order m).isSome && decide (c = observed m x y)",
    "",
    "def notRelabelled (m : Model) (x y : Nat) (c : QN) : Bool :=",
    "  (order m).isSome && !(decide (some c = observed m x y) && !decide (some (forced m x y) = observed m x y))",
    "",
    "def forcedExact (m : Model) (x y : Nat) (c : QN) : Bool := (order m).isSome && decide (c = forced m x y)",
    "",
)
LEAN_CALLS = {"acyclic": "acyclic model_{f}", "observed_exact": "observedExact model_{f} x_{f} y_{f} obs_{f}",
              "not_relabelled": "notRelabelled model_{f} x_{f} y_{f} forc_{f}",
              "forced_exact": "forcedExact model_{f} x_{f} y_{f} forc_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    m = Model(fs)
    obs, forc = _claims(fs, "observed"), _claims(fs, "forced")
    eqs = [f"({lean_list([str(p) for p in m.parents[v]])}, {lean_list([str(k) for k in sorted(m.table[v])])})"
           for v in sorted(m.parents)]
    return [("model", "Model", f"{{ sources := {len(m.src)}, eqs := {lean_list(eqs)} }}"),
            ("x", "Nat", str(m.x)), ("y", "Nat", str(m.y)),
            ("obs", "Option QN", "none" if not obs else f"some ({T.q(obs[0])})"),
            ("forc", "QN", T.q(forc[0] if forc else ZERO))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render_module(fixtures, verdicts)


def render_module(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    from ..shared import render

    return render(LEAN_MODULE, "The clauses of `forced_differences`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
