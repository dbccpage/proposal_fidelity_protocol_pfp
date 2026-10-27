# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A hosted weighted table of arcs carries a load, a level on each node and a
flow; the flow certifies the load's least weighted distance from a
difference of levels.  Beside it, freely adding a spare point to a plain set
and forgetting the point of a pointed set replay both round trips pointwise.

The first half, over exact values: arcs ``arc(u, v)`` with a positive weight
``w``, a load ``c`` and a flow ``y`` on each, a level ``s`` on each node, and
a declared price.  The primal value at ``s`` is ``sum w |c - (s(v) - s(u))|``;
the flow is feasible when it balances at every node and ``|y| <= w`` on every
arc; its dual value is ``sum c y``.  A zero gap is the two values being
equal, and the declared price is the dual value.

The second half, relational: a plain set (``plain``), a pointed set
(``kept`` with its ``base``) and one ``spare`` point.  The unit sends each
plain point into the plain set with the spare point added; the counit sends
the kept points and the spare point into the kept points.  Freely pointing
and then collapsing returns every plain point (the unit fixes it); forgetting
and then pointing returns every kept point (the counit fixes it); and the
counit sends the spare point to the base.

Relational clauses, carried by derivability: ``left_round_trip``,
``right_round_trip``, ``pointed``, ``one_unit``, ``one_counit``, and
``weighted``, ``loaded``, ``carried``, ``leveled`` with their ``one_*``
companions.

Decoded clauses, decided over exact values outside the grammar:
``within_capacity``, ``balanced``, ``zero_gap`` and ``price_matches``.  Their
Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "flow_certificate"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "FlowCertificate"
EXACT = ("py.exact.q",)
CLAUSES = ("within_capacity", "balanced", "zero_gap", "price_matches")


@dataclass(frozen=True)
class Network:
    """Arcs as node positions, in the declared order of arcs, with their
    weight, load and flow; the level of each node; the declared price."""

    nodes: int
    arcs: tuple[tuple[int, int], ...]
    weight: tuple[Q, ...]
    load: tuple[Q, ...]
    flow: tuple[Q, ...]
    level: tuple[Q, ...]
    price: Q


def _rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    return [a for n, a in fs.tuples if n == name]


def network(fs: FiniteStructure) -> Network | None:
    """The first half read over exact values; ``None`` when a datum is
    missing, repeated or undecodable."""
    nodes = fs.elements("node")
    arcs = sorted((u, v) for u, v in _rows(fs, "arc"))

    def per_arc(name: str) -> tuple[Q, ...] | None:
        got: dict[tuple[int, int], Q] = {}
        for u, v, x in _rows(fs, name):
            val = fs.value(x)
            if val is None or (u, v) in got:
                return None
            got[(u, v)] = val
        return None if any(a not in got for a in arcs) else tuple(got[a] for a in arcs)

    w, c, y = per_arc("weight"), per_arc("load"), per_arc("carry")
    levels: dict[int, Q] = {}
    for n, x in _rows(fs, "level"):
        val = fs.value(x)
        if val is None or n in levels:
            return None
        levels[n] = val
    prices = [fs.value(x) for (x,) in _rows(fs, "price")]
    if w is None or c is None or y is None or any(n not in levels for n in nodes) or len(prices) != 1:
        return None
    price = prices[0]
    if price is None or any(u not in nodes or v not in nodes for u, v in arcs):
        return None
    pos = {n: k for k, n in enumerate(nodes)}
    return Network(len(nodes), tuple((pos[u], pos[v]) for u, v in arcs), w, c, y,
                   tuple(levels[n] for n in nodes), price)


def magnitude(x: Q) -> Q:
    return x if x.sign() >= 0 else -x


def primal(n: Network) -> Q:
    return sum((w * magnitude(c - (n.level[v] - n.level[u])) for (u, v), w, c in zip(n.arcs, n.weight, n.load)), ZERO)


def dual(n: Network) -> Q:
    return sum((c * y for c, y in zip(n.load, n.flow)), ZERO)


def divergence(n: Network, x: int) -> Q:
    return (sum((y for (u, v), y in zip(n.arcs, n.flow) if v == x), ZERO)
            - sum((y for (u, v), y in zip(n.arcs, n.flow) if u == x), ZERO))


def within_capacity(fs: FiniteStructure, _o: Oracle) -> bool:
    n = network(fs)
    return n is not None and all(w.sign() > 0 and magnitude(y) <= w for w, y in zip(n.weight, n.flow))


def balanced(fs: FiniteStructure, _o: Oracle) -> bool:
    n = network(fs)
    return n is not None and all(divergence(n, x).is_zero() for x in range(n.nodes))


def zero_gap(fs: FiniteStructure, _o: Oracle) -> bool:
    n = network(fs)
    return n is not None and primal(n) == dual(n)


def price_matches(fs: FiniteStructure, _o: Oracle) -> bool:
    n = network(fs)
    return n is not None and n.price == dual(n)


def describe(fs: FiniteStructure) -> dict[str, object]:
    n = network(fs)
    if n is None:
        return {"primal": None}
    return {"divergence": [fmt_q(divergence(n, x)) for x in range(n.nodes)], "dual": fmt_q(dual(n)),
            "primal": fmt_q(primal(n))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    out = []
    for v in verdicts:
        if dict(v.decoded).get("zero_gap") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    node, arc = e.form("node"), e.form("arc")
    weight, load, carry, level = e.form("weight"), e.form("load"), e.form("carry"), e.form("level")
    plain, kept, spare, base = e.form("plain"), e.form("kept"), e.form("spare"), e.form("base")
    unit, counit = e.form("unit"), e.form("counit")
    a = ((arc, ("u", "v")),)
    return Compiled(
        (
            Total("weighted", a, ((weight, ("u", "v", "x")),)),
            Functional("one_weight", weight, 2),
            Total("loaded", a, ((load, ("u", "v", "x")),)),
            Functional("one_load", load, 2),
            Total("carried", a, ((carry, ("u", "v", "x")),)),
            Functional("one_carry", carry, 2),
            Total("leveled", ((node, ("n",)),), ((level, ("n", "x")),)),
            Functional("one_level", level, 1),
            Closure("left_round_trip", ((plain, ("x",)),), ((unit, ("x", "x")),)),
            Functional("one_unit", unit, 1),
            Closure("right_round_trip", ((kept, ("y",)),), ((counit, ("y", "y")),)),
            Closure("pointed", ((spare, ("s",)), (base, ("b",))), ((counit, ("s", "b")),)),
            Functional("one_counit", counit, 1),
        ),
        decoded=tuple(DecodedClause(c, f, EXACT) for c, f in (
            ("within_capacity", within_capacity), ("balanced", balanced), ("zero_gap", zero_gap),
            ("price_matches", price_matches))),
    )


LEAN_DEFS = (
    "/-- The absolute value. -/",
    "def absQ (x : QN) : QN := if QN.pos x then x else -x",
    "",
    "/-- The sum of a list. -/",
    "def total (xs : List QN) : QN := xs.foldl (fun acc x => acc + x) 0",
    "",
    "/-- A network: arcs as node positions, with weight, load and flow per arc. -/",
    "structure Net where",
    "  nodes : Nat",
    "  arcs : List (Prod Nat Nat)",
    "  weight : List QN",
    "  load : List QN",
    "  flow : List QN",
    "  level : List QN",
    "  price : QN",
    "",
    "def pick (xs : List QN) (i : Nat) : QN := xs.getD i 0",
    "",
    "/-- `sum w |c - (s(v) - s(u))|`. -/",
    "def primal (n : Net) : QN :=",
    "  total ((List.range n.arcs.length).map fun i =>",
    "    let e := n.arcs.getD i (0, 0)",
    "    pick n.weight i * absQ (pick n.load i - (pick n.level e.2 - pick n.level e.1)))",
    "",
    "/-- `sum c y`. -/",
    "def dual (n : Net) : QN := total ((List.range n.arcs.length).map fun i => pick n.load i * pick n.flow i)",
    "",
    "/-- Inflow minus outflow at node `x`. -/",
    "def divergence (n : Net) (x : Nat) : QN :=",
    "  total ((List.range n.arcs.length).map fun i =>",
    "    let e := n.arcs.getD i (0, 0)",
    "    (if e.2 = x then pick n.flow i else 0) - (if e.1 = x then pick n.flow i else 0))",
    "",
    "def withinCapacity (n : Net) : Bool :=",
    "  (List.range n.arcs.length).all fun i =>",
    "    QN.pos (pick n.weight i) && !QN.pos (absQ (pick n.flow i) - pick n.weight i)",
    "",
    "def balanced (n : Net) : Bool := (List.range n.nodes).all fun x => decide (divergence n x = 0)",
    "",
    "def zeroGap (n : Net) : Bool := decide (primal n = dual n)",
    "",
    "def priceMatches (n : Net) : Bool := decide (n.price = dual n)",
    "",
)
LEAN_CALLS = {"within_capacity": "withinCapacity", "balanced": "balanced", "zero_gap": "zeroGap",
              "price_matches": "priceMatches"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One network per evaluated fixture; the kernel re-decides each value clause."""
    from operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `flow_certificate`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        n = network(by[fid].structure)
        assert n is not None
        arcs = ", ".join(f"({u}, {v})" for u, v in n.arcs)
        lines += [f"def net_{fid} : Net :=",
                  f"  {{ nodes := {n.nodes}, arcs := [{arcs}], weight := {T.row(n.weight)},",
                  f"    load := {T.row(n.load)}, flow := {T.row(n.flow)},",
                  f"    level := {T.row(n.level)}, price := {T.q(n.price)} }}", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause]} net_{fid} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
