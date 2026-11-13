"""One stake and a stream: a two-sided standing commitment under growth.

Classification (assumption discipline):

* Everything here is metatheory apparatus layered on the sealed kernel and
  on the sibling ``research/identification_dual/dual.py``, both imported
  read-only and pinned in ``SOURCE_MANIFEST.json``.
* A ``Commitment`` is DECLARED METATHEORY: a condition on every pair of
  datum indices, present or future, assigning each pair apart, same, or
  free.  It is declared once at genesis by one ``Declare`` event, emits
  nothing, and reads no state.
* The demands of a state are DERIVED: the committed pairs among the held
  data that the state does not honour.  Nothing emits them; they are read
  off the profiles.  No event flips a demand kind, because both kinds are
  present in the one declaration.
* Growth is the sealed external continuation policy: one fresh opaque
  datum supplied and admitted.  It is the only external event after the
  declaration, and it happens only at a demand-free state.
* ``Answer`` is a no-op marker recorded before a response so the history
  says which demand the response answered; like ``Supply`` it changes no
  state.
* Responses use the sealed grammar, bounds, and measures, enumerated
  without the sealed pruning lemmas.  A response is valid when the
  augmented state honours the answered pair and regresses no committed
  pair among the previously held data that the base state honoured.
* The sibling's canonical key is retained as a diagnostic component, but
  the operational key also preserves datum and form indices.  The stake is
  defined on those indices and is not equivariant under every current-state
  automorphism; quotienting by current labels alone is unsound under growth.
"""

from __future__ import annotations

import pathlib
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional, Union

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
for _p in (str(REPO / "code"), str(REPO / "research" / "identification_dual")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from derivation.candidates import (  # noqa: E402
    Bounds,
    Delta,
    NewDatum,
    apply_delta,
    delta_events,
    iter_full_deltas,
    mu2,
)
from derivation.engine import READINGS, Reading, build_tree, delta_label  # noqa: E402
from derivation.model import (  # noqa: E402
    EMPTY,
    AdmissionError,
    AdmitDatum,
    Event,
    Pair,
    Regime,
    Supply,
    replay,
    step,
)
from derivation.observe import profiles  # noqa: E402
from dual import (  # noqa: E402
    State,
    StateKey,
    _delta_key,
    _has_noop_item,
    delta_json,
    item_kinds,
    regime_json,
    state_key,
)

APART = "apart"
SAME = "same"
FREE = "free"
MODE = "committed"


# ---------------------------------------------------------------------------
# The stake
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Commitment:
    """A rule on index pairs ``i < j`` giving apart, same, or free.  Declared
    once; reads no state; emits nothing."""

    name: str
    rule: Callable[[int, int], str]

    def label(self, i: int, j: int) -> str:
        lo, hi = (i, j) if i < j else (j, i)
        out = self.rule(lo, hi)
        if out not in (APART, SAME, FREE):
            raise ValueError(f"commitment {self.name} returned {out!r}")
        return out


def _total_apart(i: int, j: int) -> str:
    return APART


def _total_same(i: int, j: int) -> str:
    return SAME


def _parity(i: int, j: int) -> str:
    return SAME if (i - j) % 2 == 0 else APART


def _residue_three(i: int, j: int) -> str:
    return SAME if (i - j) % 3 == 0 else APART


def _chain(i: int, j: int) -> str:
    return APART if j - i == 1 else FREE


COMMITMENTS: tuple[Commitment, ...] = (
    Commitment("total_apart", _total_apart),
    Commitment("total_same", _total_same),
    Commitment("parity", _parity),
    Commitment("residue_three", _residue_three),
    Commitment("chain", _chain),
)


def commitment_named(name: str) -> Commitment:
    for c in COMMITMENTS:
        if c.name == name:
            return c
    raise KeyError(name)


# ---------------------------------------------------------------------------
# Events and replay
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Declare:
    """The one declaration: names the standing commitment."""

    commitment: str


@dataclass(frozen=True)
class Answer:
    """No-op marker: the demand the following response answers."""

    kind: str
    i: int
    j: int


TSEvent = Union[Event, Declare, Answer]


@dataclass(frozen=True)
class TState:
    """The sealed regime, the declared commitment's name, and the labels it
    induces on the held data, materialised into the sibling's ``State`` for
    its canonical diagnostic component.  Operational merging additionally
    preserves indices because future commitment labels depend on them."""

    regime: Regime
    commitment: str

    def labelled(self) -> State:
        c = commitment_named(self.commitment)
        n = self.regime.n_data()
        apart = frozenset(
            (i, j) for i in range(n) for j in range(i + 1, n) if c.label(i, j) == APART
        )
        same = frozenset(
            (i, j) for i in range(n) for j in range(i + 1, n) if c.label(i, j) == SAME
        )
        r = self.regime
        return State(Regime(r.data, r.forms, r.insts, r.rules, apart), same, MODE)


GENESIS_TSTATE = TState(EMPTY, "")


def ts_step(s: TState, e: TSEvent) -> TState:
    if isinstance(e, Declare):
        if s.commitment:
            raise AdmissionError("the commitment is declared once")
        commitment_named(e.commitment)
        return TState(s.regime, e.commitment)
    if isinstance(e, Answer):
        return s
    return TState(step(s.regime, e), s.commitment)


def ts_replay(history: tuple[TSEvent, ...], base: TState = GENESIS_TSTATE) -> TState:
    s = base
    for e in history:
        s = ts_step(s, e)
    return s


def certify(history: tuple[TSEvent, ...], claimed: TState) -> bool:
    return ts_replay(history) == claimed


# ---------------------------------------------------------------------------
# Demands, honour, validity
# ---------------------------------------------------------------------------


def honoured(r: Regime, label: str, pair: Pair) -> bool:
    profs = profiles(r)
    equal = profs[pair[0]] == profs[pair[1]]
    if label == APART:
        return not equal
    if label == SAME:
        return equal
    return True


def demands(s: TState) -> tuple[tuple[str, Pair], ...]:
    """Committed pairs among the held data that the state does not honour,
    ordered by pair."""
    c = commitment_named(s.commitment)
    n = s.regime.n_data()
    profs = profiles(s.regime)
    out: list[tuple[str, Pair]] = []
    for i in range(n):
        for j in range(i + 1, n):
            label = c.label(i, j)
            if label == FREE:
                continue
            equal = profs[i] == profs[j]
            if (label == APART and equal) or (label == SAME and not equal):
                out.append((label, (i, j)))
    return tuple(out)


def honoured_pairs(s: TState) -> frozenset[Pair]:
    c = commitment_named(s.commitment)
    n = s.regime.n_data()
    profs = profiles(s.regime)
    out: set[Pair] = set()
    for i in range(n):
        for j in range(i + 1, n):
            label = c.label(i, j)
            if label == FREE:
                continue
            equal = profs[i] == profs[j]
            if (label == APART and not equal) or (label == SAME and equal):
                out.add((i, j))
    return frozenset(out)


def response_valid(s: TState, target: tuple[str, Pair], delta: Delta) -> bool:
    """Full recomputation: the augmented regime honours the answered pair
    and every committed pair among the previously held data that the base
    honoured.  Pairs involving a fresh datum are new demands, not regress."""
    try:
        after = apply_delta(s.regime, delta)
    except AdmissionError:
        return False
    label, pair = target
    if not honoured(after, label, pair):
        return False
    before = honoured_pairs(s)
    c = commitment_named(s.commitment)
    for (i, j) in sorted(before):
        if not honoured(after, c.label(i, j), (i, j)):
            return False
    return True


@dataclass(frozen=True)
class Minima:
    measure: str
    cost: tuple[int, int]
    deltas: tuple[Delta, ...]
    valid_at_cost: int


def min_responses(
    s: TState, target: tuple[str, Pair], measure: str, bounds: Bounds
) -> Optional[Minima]:
    if measure not in ("mu1", "mu2"):
        raise ValueError(f"unknown measure: {measure}")
    for cost in range(0, bounds.max_items + 1):
        seen: set[Delta] = set()
        valid: list[Delta] = []
        for delta in iter_full_deltas(s.regime, cost, bounds):
            if delta in seen or _has_noop_item(s.regime, delta):
                continue
            seen.add(delta)
            if response_valid(s, target, delta):
                valid.append(delta)
        if not valid:
            continue
        if measure == "mu1":
            return Minima("mu1", (cost, -1), tuple(sorted(valid, key=_delta_key)), len(valid))
        best = min(mu2(d) for d in valid)
        chosen = tuple(sorted((d for d in valid if mu2(d) == best), key=_delta_key))
        return Minima("mu2", best, chosen, len(valid))
    return None


# ---------------------------------------------------------------------------
# Policy: every demanded pair
# ---------------------------------------------------------------------------


def closure_targets(s: TState) -> tuple[tuple[str, Pair], ...]:
    """Every demanded pair, without a current-state orbit quotient.

    An index-defined commitment need not extend a current automorphism when
    a fresh index arrives.  Dropping orbit-related targets would therefore
    discard future-distinct branches.
    """

    return demands(s)


IndexedRegimeKey = tuple[
    int,
    tuple[int, ...],
    tuple[tuple[int, tuple[int, ...]], ...],
    tuple[int, ...],
    tuple[Pair, ...],
]
TStateKey = tuple[StateKey, str, IndexedRegimeKey]


def key_of(s: TState) -> TStateKey:
    """A quotient key sound for an index-defined standing commitment.

    The canonical labelled-state key is preserved for comparison with the
    sibling, while the second component prevents a permutation of semantic
    datum or form indices from merging future-incompatible states.
    Presentation tokens remain forgotten; only the datum count is retained.
    """

    r = s.regime
    indexed: IndexedRegimeKey = (
        r.n_data(),
        tuple(r.forms),
        tuple(sorted(r.insts)),
        tuple(sorted(r.rules)),
        tuple(sorted(r.reqs)),
    )
    return (state_key(s.labelled()), s.commitment, indexed)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def diagnostics(s: TState, target: tuple[str, Pair], delta: Delta) -> dict[str, object]:
    after_regime = apply_delta(s.regime, delta)
    after = TState(after_regime, s.commitment)
    before_d = demands(s)
    after_d = demands(after)
    open_before = {pair for (_, pair) in before_d}
    open_after = {pair for (_, pair) in after_d}
    n0 = s.regime.n_data()
    honoured_at_once = sorted(p for p in open_before if p not in open_after)
    new_pairs = sorted(p for p in open_after if max(p) >= n0)
    kinds = item_kinds(delta)
    before_p = profiles(s.regime)
    after_p = profiles(after_regime)
    label, pair = target
    third = [d for d in range(n0) if d not in pair and before_p[d] != after_p[d]]
    return {
        "kind": label,
        "target": list(pair),
        "kinds": kinds,
        "contains_rule": "rule" in kinds,
        "fresh_form": "form" in kinds,
        "fresh_datum": "datum" in kinds,
        "demands_before": len(before_d),
        "demands_after": len(after_d),
        "honoured_at_once": [list(p) for p in honoured_at_once],
        "new_demands_from_fresh_datum": [list(p) for p in new_pairs],
        "third_party_changed": third,
    }


# ---------------------------------------------------------------------------
# The tree
# ---------------------------------------------------------------------------


@dataclass
class TNode:
    node_id: int
    history: tuple[TSEvent, ...]
    state: TState
    depth: int
    key: TStateKey
    status: str = "open"
    merged_count: int = 1
    certified: bool = False
    grown_from: bool = False


@dataclass
class TEdge:
    parent: int
    child: int
    round_no: int
    challenge: str
    label: str
    response: Delta
    tie_classes: int
    class_size: int
    cost: tuple[int, int]
    target_count: int
    kind: str
    info: dict[str, object] = field(default_factory=dict)


@dataclass
class TTree:
    reading: str
    commitment: str
    measure: str
    bounds: Bounds
    max_rounds: int
    guard: int
    max_data: int
    nodes: list[TNode] = field(default_factory=list)
    edges: list[TEdge] = field(default_factory=list)
    refusals: list[dict[str, object]] = field(default_factory=list)

    def stats(self) -> dict[str, object]:
        by_status: dict[str, int] = {}
        for n in self.nodes:
            by_status[n.status] = by_status.get(n.status, 0) + 1
        roles: dict[str, int] = {}
        for e in self.edges:
            if e.challenge == "grow":
                role = "grow"
            else:
                raw = e.info.get("kinds")
                kinds = [str(k) for k in raw] if isinstance(raw, list) else []
                role = str(e.info.get("kind")) + ":" + "+".join(kinds)
            roles[role] = roles.get(role, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "by_status": by_status,
            "roles": roles,
            "growth_edges": sum(1 for e in self.edges if e.challenge == "grow"),
            "expansions_with_ties": len(
                {(e.parent, e.challenge) for e in self.edges if e.tie_classes > 1}
            ),
            "max_depth": max((n.depth for n in self.nodes), default=0),
            "max_data": max((n.state.regime.n_data() for n in self.nodes), default=0),
            "max_forms": max((len(n.state.regime.forms) for n in self.nodes), default=0),
            "all_certified": all(n.certified for n in self.nodes),
        }


def genesis_history(reading: Reading, commitment: Commitment) -> tuple[TSEvent, ...]:
    history: tuple[TSEvent, ...] = tuple(reading.genesis)
    return history + (Declare(commitment.name),)


def build_ts_tree(
    reading: Reading,
    commitment: Commitment,
    measure: str,
    bounds: Bounds,
    max_rounds: int = 15,
    guard: int = 250,
    max_data: int = 5,
) -> TTree:
    tree = TTree(reading.name, commitment.name, measure, bounds, max_rounds, guard, max_data)
    history = genesis_history(reading, commitment)
    root_state = ts_replay(history)
    root = TNode(0, history, root_state, 0, key_of(root_state))
    root.certified = certify(root.history, root.state)
    tree.nodes.append(root)
    key_map: dict[TStateKey, int] = {root.key: 0}
    queue: deque[int] = deque([0])
    while queue:
        nid = queue.popleft()
        node = tree.nodes[nid]
        try:
            targets = closure_targets(node.state)
        except RuntimeError:
            node.status = "terminal_iso_budget"
            continue
        if node.depth >= max_rounds:
            node.status = "completed"
            continue
        if len(tree.nodes) > guard:
            node.status = "frontier_guard"
            continue
        if not targets:
            n = node.state.regime.n_data()
            if n >= max_data:
                node.status = "terminal_data_bound"
                continue
            token = f"g{n}"
            grown = node.history + (Supply(token), AdmitDatum(token))
            child_state = ts_replay(grown)
            info: dict[str, object] = {
                "demands_after_growth": len(demands(child_state)),
                "data_before": n,
            }
            _attach(tree, key_map, queue, node, grown, "grow", "grow", (), 1, 1, (0, 0), 1, info)
            node.status = "expanded"
            continue
        gathered: list[tuple[tuple[str, Pair], Minima]] = []
        refused = False
        for target in targets:
            mr = min_responses(node.state, target, measure, bounds)
            if mr is None:
                tree.refusals.append(
                    {
                        "node": nid,
                        "kind": target[0],
                        "target": list(target[1]),
                        "data": node.state.regime.n_data(),
                        "open_demands": len(demands(node.state)),
                        "single_item_candidates": sum(
                            1 for _ in iter_full_deltas(node.state.regime, 1, bounds)
                        ),
                    }
                )
                refused = True
                break
            gathered.append((target, mr))
        if refused:
            node.status = "terminal_no_response"
            continue
        for target, mr in gathered:
            classes = _quotient(node.state, target, mr)
            for rep, size in classes:
                assert response_valid(node.state, target, rep)
                history2 = (
                    node.history
                    + (Answer(target[0], target[1][0], target[1][1]),)
                    + tuple(delta_events(node.state.regime, rep))
                )
                cost = mr.cost if measure == "mu2" else (mr.cost[0], -1)
                info = diagnostics(node.state, target, rep)
                info["valid_at_cost"] = mr.valid_at_cost
                _attach(
                    tree, key_map, queue, node, history2,
                    f"{target[0]}{target[1]}", delta_label(node.state.regime, rep),
                    rep, len(classes), size, cost, len(targets), info,
                )
        node.status = "expanded"
    return tree


def _quotient(s: TState, target: tuple[str, Pair], mr: Minima) -> list[tuple[Delta, int]]:
    grouped: dict[TStateKey, list[Delta]] = {}
    for delta in mr.deltas:
        child = TState(apply_delta(s.regime, delta), s.commitment)
        grouped.setdefault(key_of(child), []).append(delta)
    return [(members[0], len(members)) for _, members in sorted(grouped.items())]


def _attach(
    tree: TTree,
    key_map: dict[TStateKey, int],
    queue: "deque[int]",
    parent: TNode,
    history: tuple[TSEvent, ...],
    challenge: str,
    label: str,
    response: Delta,
    tie_classes: int,
    class_size: int,
    cost: tuple[int, int],
    target_count: int,
    info: dict[str, object],
) -> None:
    state = ts_replay(history)
    key = key_of(state)
    if key in key_map:
        child_id = key_map[key]
        kind = "merge"
        tree.nodes[child_id].merged_count += 1
    else:
        child_id = len(tree.nodes)
        kind = "creation"
        child = TNode(child_id, history, state, parent.depth + 1, key)
        child.certified = certify(child.history, child.state)
        child.grown_from = challenge == "grow"
        tree.nodes.append(child)
        key_map[key] = child_id
        queue.append(child_id)
    tree.edges.append(
        TEdge(
            parent.node_id, child_id, parent.depth + 1, challenge, label, response,
            tie_classes, class_size, cost, target_count, kind, info,
        )
    )


# ---------------------------------------------------------------------------
# Path statistics
# ---------------------------------------------------------------------------


def paths(tree: TTree) -> list[list[int]]:
    out_edges: dict[int, list[int]] = {}
    for idx, e in enumerate(tree.edges):
        out_edges.setdefault(e.parent, []).append(idx)
    result: list[list[int]] = []

    def walk(node: int, acc: list[int]) -> None:
        nexts = out_edges.get(node, [])
        if not nexts:
            result.append(list(acc))
            return
        for idx in nexts:
            acc.append(idx)
            walk(tree.edges[idx].child, acc)
            acc.pop()

    walk(0, [])
    return result


def growth_epochs(tree: TTree) -> list[dict[str, object]]:
    """For every growth edge on every path: the data count before growth,
    the demands it produced, and the number of response rounds until the
    next demand-free node (or the leaf, if the branch never gets there)."""
    out: list[dict[str, object]] = []
    for path in paths(tree):
        for pos, idx in enumerate(path):
            e = tree.edges[idx]
            if e.challenge != "grow":
                continue
            rounds = 0
            closed = False
            for later in path[pos + 1:]:
                e2 = tree.edges[later]
                if e2.challenge == "grow":
                    closed = True
                    break
                rounds += 1
            leaf_status = tree.nodes[tree.edges[path[-1]].child].status
            if not closed and leaf_status in ("terminal_data_bound",):
                closed = True
            out.append(
                {
                    "data_before": int(str(e.info.get("data_before"))),
                    "demands_after_growth": int(str(e.info.get("demands_after_growth"))),
                    "rounds_to_next_demand_free": rounds,
                    "reached_demand_free": closed,
                    "leaf_status": leaf_status,
                }
            )
    return out


def pre_growth_nodes(tree: TTree) -> list[int]:
    """Nodes reachable from the root without crossing a growth edge."""
    out_edges: dict[int, list[TEdge]] = {}
    for e in tree.edges:
        out_edges.setdefault(e.parent, []).append(e)
    seen: set[int] = set()
    stack = [0]
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        for e in out_edges.get(nid, []):
            if e.challenge != "grow":
                stack.append(e.child)
    return sorted(seen)


def sealed_closed_counts(reading: Reading, measure: str, bounds: Bounds) -> tuple[int, int]:
    """(nodes, terminal nodes) of the sealed closed baseline."""
    t = build_tree(reading, measure, bounds, supply=False)
    return (len(t.nodes), sum(1 for n in t.nodes if n.status == "terminal_all_separated"))


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------


def event_json(e: TSEvent) -> dict[str, object]:
    from derivation.export import event_json as sealed_event_json

    if isinstance(e, Declare):
        return {"kind": "declare", "commitment": e.commitment}
    if isinstance(e, Answer):
        return {"kind": "answer", "demand": e.kind, "i": e.i, "j": e.j}
    return dict(sealed_event_json(e))


def node_json(n: TNode) -> dict[str, object]:
    ds = demands(n.state)
    return {
        "id": n.node_id,
        "depth": n.depth,
        "status": n.status,
        "merged_count": n.merged_count,
        "certified": n.certified,
        "regime": regime_json(n.state.regime),
        "demands": [[k, list(p)] for (k, p) in ds],
        "history_length": len(n.history),
    }


def edge_json(e: TEdge) -> dict[str, object]:
    return {
        "parent": e.parent,
        "child": e.child,
        "round": e.round_no,
        "challenge": e.challenge,
        "label": e.label,
        "response": delta_json(e.response),
        "tie_classes": e.tie_classes,
        "class_size": e.class_size,
        "cost": list(e.cost),
        "target_count": e.target_count,
        "kind": e.kind,
        "info": dict(e.info),
    }


def has_fresh_datum(delta: Delta) -> bool:
    return any(isinstance(it, NewDatum) for it in delta)


def sealed_readings() -> tuple[Reading, ...]:
    return READINGS


def replay_regime(history: tuple[TSEvent, ...]) -> Regime:
    sealed = tuple(e for e in history if not isinstance(e, (Declare, Answer)))
    return replay(sealed)
