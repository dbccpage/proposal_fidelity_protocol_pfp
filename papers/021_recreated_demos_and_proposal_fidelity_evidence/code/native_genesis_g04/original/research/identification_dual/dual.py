"""The sealed machine run under the other demand.

Classification (assumption discipline):

* Everything here is metatheory apparatus layered on the sealed kernel,
  which is imported read-only and pinned in ``SOURCE_MANIFEST.json``.
* ``RequireSame`` is an EXTERNALLY IMPOSED CHALLENGE: two admitted data
  that are internally separable in the sealed declared sense (profiles
  differ) must become internally indistinguishable in that same sense
  (equal profiles).  Nothing in the object language asks for it.
* ``Retract`` and ``Switch`` are DECLARED METATHEORY: a retraction discards
  every standing requirement of both kinds; a switch retracts and flips the
  demand kind.  Neither is derived, and each is recorded in the history as
  one event so that every state replays from the sealed genesis.
* The candidate grammar, bounds, and both cost measures are the sealed ones.
  The sealed pruning lemmas are NOT used: they were proved for separation
  demands, and this tree assumes nothing about which items matter for the
  other demand.  Enumeration is the sealed unpruned one.
* The isomorphism relation is the sealed serialization, minimised by brute
  force over every bijection pair, extended to the two requirement stores
  and the demand mode.  Brute force is exact and is what the sealed tests
  use as their reference; the states here are small enough for it.
"""

from __future__ import annotations

import pathlib
import sys
from collections import deque
from dataclasses import dataclass, field
from itertools import permutations
from typing import Optional, Union

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
_CODE = str(REPO / "code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

from derivation.candidates import (  # noqa: E402
    Bounds,
    Delta,
    NewDatum,
    NewForm,
    NewInst,
    NewRuleAll,
    apply_delta,
    delta_events,
    item_key,
    iter_full_deltas,
    mu2,
)
from derivation.engine import READINGS, Node, build_tree, delta_label  # noqa: E402
from derivation.iso import CanonKey, serialize  # noqa: E402
from derivation.model import (  # noqa: E402
    EMPTY,
    AdmissionError,
    AdmitDatum,
    Event,
    Pair,
    Regime,
    replay,
    step,
)
from derivation.observe import collapsed_pairs, profiles  # noqa: E402

IDENTIFY = "identify"
SEPARATE = "separate"
PERM_BUDGET = 100_000


# ---------------------------------------------------------------------------
# Declared events and the dual state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RequireSame:
    """External requirement: data ``i`` and ``j`` must be internally
    indistinguishable (equal profiles).  Persistent, like the sealed
    separation requirement."""

    i: int
    j: int


@dataclass(frozen=True)
class Retract:
    """Declared retraction of every standing requirement of both kinds."""


@dataclass(frozen=True)
class Switch:
    """Declared switch: retract everything and flip the demand kind."""


DualEvent = Union[Event, RequireSame, Retract, Switch]


@dataclass(frozen=True)
class State:
    """A sealed regime, the store of identification requirements, and the
    current demand kind.  The sealed regime keeps its own separation store
    in ``regime.reqs``."""

    regime: Regime
    same: frozenset[Pair]
    mode: str


GENESIS_STATE = State(EMPTY, frozenset(), IDENTIFY)


def _flip(mode: str) -> str:
    return SEPARATE if mode == IDENTIFY else IDENTIFY


def dual_step(s: State, e: DualEvent) -> State:
    """Apply one event.  Sealed events go through the sealed ``step``."""
    if isinstance(e, RequireSame):
        if not (0 <= e.i < e.j < s.regime.n_data()):
            raise AdmissionError(f"identification out of range: ({e.i}, {e.j})")
        return State(s.regime, s.same | {(e.i, e.j)}, s.mode)
    if isinstance(e, Retract):
        r = s.regime
        return State(
            Regime(r.data, r.forms, r.insts, r.rules, frozenset()),
            frozenset(),
            s.mode,
        )
    if isinstance(e, Switch):
        r = s.regime
        return State(
            Regime(r.data, r.forms, r.insts, r.rules, frozenset()),
            frozenset(),
            _flip(s.mode),
        )
    return State(step(s.regime, e), s.same, s.mode)


def dual_replay(history: tuple[DualEvent, ...], base: State = GENESIS_STATE) -> State:
    s = base
    for e in history:
        s = dual_step(s, e)
    return s


def certify(history: tuple[DualEvent, ...], claimed: State) -> bool:
    return dual_replay(history) == claimed


# ---------------------------------------------------------------------------
# Observation helpers
# ---------------------------------------------------------------------------


def separated_pairs(r: Regime) -> tuple[Pair, ...]:
    """All pairs ``i < j`` with different profiles, lexicographically."""
    profs = profiles(r)
    n = r.n_data()
    return tuple(
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if profs[i] != profs[j]
    )


def class_count(r: Regime) -> int:
    profs = profiles(r)
    return len(set(profs)) if profs else 0


def demanded_pairs(s: State) -> tuple[Pair, ...]:
    """The pairs the declared closure policy reads in the current mode."""
    if s.mode == IDENTIFY:
        return separated_pairs(s.regime)
    return collapsed_pairs(s.regime)


# ---------------------------------------------------------------------------
# Validity and minima (unpruned)
# ---------------------------------------------------------------------------


def wanted_stores(s: State, target: Pair) -> tuple[frozenset[Pair], frozenset[Pair]]:
    """(pairs that must be collapsed, pairs that must be separated) after
    a response to ``target`` in the current mode."""
    if s.mode == IDENTIFY:
        return (s.same | {target}, s.regime.reqs)
    return (s.same, s.regime.reqs | {target})


def response_valid(s: State, target: Pair, delta: Delta) -> bool:
    """Full recomputation by replay: the augmented regime collapses every
    identification requirement (with the target in identify mode) and
    separates every separation requirement (with the target in separate
    mode).  Raises nothing; an ill-formed delta is simply not valid."""
    try:
        r2 = apply_delta(s.regime, delta)
    except AdmissionError:
        return False
    want_same, want_sep = wanted_stores(s, target)
    profs = profiles(r2)
    if any(profs[i] != profs[j] for (i, j) in sorted(want_same)):
        return False
    return all(profs[i] != profs[j] for (i, j) in sorted(want_sep))


def _has_noop_item(base: Regime, delta: Delta) -> bool:
    """A rule item on a form already carrying the rule changes nothing."""
    return any(
        isinstance(it, NewRuleAll) and it.form in base.rules for it in delta
    )


def _delta_key(delta: Delta) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    return tuple(item_key(it) for it in delta)


@dataclass(frozen=True)
class Minima:
    measure: str
    cost: tuple[int, int]
    deltas: tuple[Delta, ...]
    valid_at_cost: int


def min_responses(
    s: State, target: Pair, measure: str, bounds: Bounds
) -> Optional[Minima]:
    """Minimum valid responses within the declared bounds, over the sealed
    UNPRUNED enumeration, or ``None`` when no valid delta of at most
    ``max_items`` items exists."""
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
            return Minima(
                "mu1", (cost, -1), tuple(sorted(valid, key=_delta_key)), len(valid)
            )
        best = min(mu2(d) for d in valid)
        chosen = tuple(sorted((d for d in valid if mu2(d) == best), key=_delta_key))
        return Minima("mu2", best, chosen, len(valid))
    return None


# ---------------------------------------------------------------------------
# Isomorphism of states: brute force over every bijection pair
# ---------------------------------------------------------------------------

StateKey = tuple[CanonKey, tuple[Pair, ...], str]


def _map_pairs(pairs: frozenset[Pair], pi: tuple[int, ...]) -> tuple[Pair, ...]:
    return tuple(
        sorted((min(pi[i], pi[j]), max(pi[i], pi[j])) for (i, j) in pairs)
    )


def _form_perms(r: Regime) -> list[tuple[int, ...]]:
    """Every form-label bijection.

    The serialized arity table and rule set decide whether a bijection
    preserves those structures when two keys are compared.  Restricting a
    permutation to the positions that already have the same arity and rule
    status would only enumerate automorphisms of this particular labeling;
    it would miss an isomorphism that relabels two differently coloured
    forms.  The declared states are small enough for the exact factorial
    search, guarded by ``PERM_BUDGET`` below.
    """
    return list(permutations(range(len(r.forms))))


def _budget(n: int, form_perms: int) -> None:
    total = form_perms
    for k in range(2, n + 1):
        total *= k
    if total > PERM_BUDGET:
        raise RuntimeError(
            f"{total} bijection pairs exceed the declared budget {PERM_BUDGET}"
        )


def state_key(s: State) -> StateKey:
    """Canonical key: the minimum over every datum and form bijection of
    the sealed serialization (which carries arities, the rule set, and the
    separation store), paired with the mapped identification store and
    tagged with the mode.  Equal keys hold exactly for isomorphic states."""
    r = s.regime
    n = r.n_data()
    phis = _form_perms(r)
    _budget(n, len(phis))
    best: Optional[tuple[CanonKey, tuple[Pair, ...]]] = None
    for pi in permutations(range(n)):
        for phi in phis:
            cand = (serialize(r, pi, phi), _map_pairs(s.same, pi))
            if best is None or cand < best:
                best = cand
    assert best is not None
    return (best[0], best[1], s.mode)


def automorphisms(s: State) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """Bijection pairs fixing the regime (sealed serialization) and the
    identification store."""
    r = s.regime
    n = r.n_data()
    phis = _form_perms(r)
    _budget(n, len(phis))
    ident_d, ident_f = tuple(range(n)), tuple(range(len(r.forms)))
    key = serialize(r, ident_d, ident_f)
    same = tuple(sorted(s.same))
    return [
        (pi, phi)
        for pi in permutations(range(n))
        for phi in phis
        if serialize(r, pi, phi) == key and _map_pairs(s.same, pi) == same
    ]


def pair_orbits(s: State, pairs: tuple[Pair, ...]) -> tuple[tuple[Pair, ...], ...]:
    autos = automorphisms(s)
    remaining = set(pairs)
    orbits: list[tuple[Pair, ...]] = []
    for pair in sorted(pairs):
        if pair not in remaining:
            continue
        orbit = {
            (min(pi[pair[0]], pi[pair[1]]), max(pi[pair[0]], pi[pair[1]]))
            for (pi, _) in autos
        }
        orbit &= remaining
        remaining -= orbit
        orbits.append(tuple(sorted(orbit)))
    return tuple(orbits)


def closure_targets(s: State) -> tuple[Pair, ...]:
    """The declared closure policy: one representative (least member) per
    automorphism orbit of the demanded pairs in the current mode, or the
    empty tuple at the fixpoint."""
    return tuple(orbit[0] for orbit in pair_orbits(s, demanded_pairs(s)))


# ---------------------------------------------------------------------------
# Diagnostics of an accepted response
# ---------------------------------------------------------------------------


def item_kinds(delta: Delta) -> list[str]:
    out: list[str] = []
    for it in delta:
        if isinstance(it, NewDatum):
            out.append("datum")
        elif isinstance(it, NewForm):
            out.append("form")
        elif isinstance(it, NewRuleAll):
            out.append("rule")
        else:
            out.append("inst")
    return sorted(out)


def diagnostics(base: Regime, target: Pair, delta: Delta) -> dict[str, object]:
    """What the response did beyond the target pair."""
    after = apply_delta(base, delta)
    before_p = profiles(base)
    after_p = profiles(after)
    n0 = base.n_data()
    third = [
        d for d in range(n0) if d not in target and before_p[d] != after_p[d]
    ]
    before_sep = set(separated_pairs(base))
    after_sep = set(separated_pairs(after))
    others = {
        (i, j) for i in range(n0) for j in range(i + 1, n0) if (i, j) != target
    }
    flipped = sorted(p for p in others if (p in before_sep) != (p in after_sep))
    kinds = item_kinds(delta)
    return {
        "kinds": kinds,
        "contains_rule": "rule" in kinds,
        "fresh_form": "form" in kinds,
        "fresh_datum": "datum" in kinds,
        "instantiates_ruled_form": any(
            isinstance(it, NewInst) and it.form in base.rules for it in delta
        ),
        "third_party_changed": third,
        "other_pairs_flipped": [list(p) for p in flipped],
        "ruled_forms_after": len(after.rules),
        "classes_after": class_count(after),
    }


# ---------------------------------------------------------------------------
# Genesis: the sealed all-separated fixpoints
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Genesis:
    genesis_id: str
    reading: str
    sealed_measures: tuple[str, ...]
    depth: int
    history: tuple[Event, ...]
    regime: Regime
    key: CanonKey


def sealed_fixpoints(bounds: Bounds) -> tuple[Genesis, ...]:
    """Terminal nodes of the sealed closed-system baselines, for both
    readings and both sealed measures, quotiented by the sealed canonical
    key.  Ordered by (reading, key)."""
    found: dict[tuple[str, CanonKey], tuple[Node, set[str]]] = {}
    for rd in READINGS:
        for measure in ("mu1", "mu2"):
            tree = build_tree(rd, measure, bounds, supply=False)
            for node in tree.nodes:
                if node.status != "terminal_all_separated":
                    continue
                slot = (rd.name, node.canon)
                if slot in found:
                    found[slot][1].add(measure)
                else:
                    found[slot] = (node, {measure})
    out: list[Genesis] = []
    for index, (slot, (node, measures)) in enumerate(sorted(found.items())):
        assert replay(node.history) == node.regime
        out.append(
            Genesis(
                f"g{index:02d}",
                slot[0],
                tuple(sorted(measures)),
                node.depth,
                node.history,
                node.regime,
                node.canon,
            )
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# The tree
# ---------------------------------------------------------------------------


@dataclass
class DNode:
    node_id: int
    history: tuple[DualEvent, ...]
    state: State
    depth: int
    key: StateKey
    status: str = "open"
    merged_count: int = 1
    certified: bool = False


@dataclass
class DEdge:
    parent: int
    child: int
    round_no: int
    challenge: str
    label: str
    response: Delta
    tie_classes: int
    class_size: int
    cost: tuple[int, int]
    orbits: int
    kind: str
    info: dict[str, object] = field(default_factory=dict)


@dataclass
class DTree:
    genesis_id: str
    reading: str
    measure: str
    alternate: bool
    bounds: Bounds
    max_rounds: int
    guard: int
    nodes: list[DNode] = field(default_factory=list)
    edges: list[DEdge] = field(default_factory=list)
    refusals: list[dict[str, object]] = field(default_factory=list)

    def stats(self) -> dict[str, object]:
        by_status: dict[str, int] = {}
        for n in self.nodes:
            by_status[n.status] = by_status.get(n.status, 0) + 1
        roles: dict[str, int] = {}
        for e in self.edges:
            raw = e.info.get("kinds")
            kinds = [str(k) for k in raw] if isinstance(raw, list) else []
            role = "switch" if e.challenge == "switch" else "+".join(kinds)
            roles[role] = roles.get(role, 0) + 1
        tie_expansions = len(
            {(e.parent, e.challenge) for e in self.edges if e.tie_classes > 1}
        )
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "by_status": by_status,
            "roles": roles,
            "expansions_with_ties": tie_expansions,
            "max_depth": max((n.depth for n in self.nodes), default=0),
            "all_certified": all(n.certified for n in self.nodes),
            "max_ruled_forms": max(
                (len(n.state.regime.rules) for n in self.nodes), default=0
            ),
            "max_forms": max((len(n.state.regime.forms) for n in self.nodes), default=0),
            "max_data": max((n.state.regime.n_data() for n in self.nodes), default=0),
        }


def genesis_history(g: Genesis, reading: str) -> tuple[DualEvent, ...]:
    """Reading P keeps the sealed separations; reading R retracts them."""
    history: tuple[DualEvent, ...] = tuple(g.history)
    if reading == "R":
        history = history + (Retract(),)
    return history


def build_dual_tree(
    g: Genesis,
    reading: str,
    measure: str,
    bounds: Bounds,
    alternate: bool = False,
    max_rounds: int = 15,
    guard: int = 250,
) -> DTree:
    """Breadth-first expansion under the declared closure policy, quotiented
    by the state isomorphism.  Every node is replay-certified from the
    sealed genesis."""
    if reading not in ("P", "R"):
        raise ValueError(f"unknown reading: {reading}")
    tree = DTree(g.genesis_id, reading, measure, alternate, bounds, max_rounds, guard)
    history = genesis_history(g, reading)
    root_state = dual_replay(history)
    root = DNode(0, history, root_state, 0, state_key(root_state))
    root.certified = certify(root.history, root.state)
    tree.nodes.append(root)
    key_map: dict[StateKey, int] = {root.key: 0}
    queue: deque[int] = deque([0])
    while queue:
        nid = queue.popleft()
        node = tree.nodes[nid]
        targets = closure_targets(node.state)
        if not targets and not alternate:
            node.status = (
                "terminal_all_collapsed"
                if node.state.mode == IDENTIFY
                else "terminal_all_separated"
            )
            continue
        if node.depth >= max_rounds:
            node.status = "completed"
            continue
        if len(tree.nodes) > guard:
            node.status = "frontier_guard"
            continue
        if not targets:
            _attach(
                tree, key_map, queue, node, node.history + (Switch(),),
                challenge="switch", label="switch", response=(),
                tie_classes=1, class_size=1, cost=(0, 0), orbits=1, info={},
            )
            node.status = "expanded"
            continue
        gathered: list[tuple[Pair, Minima]] = []
        no_response = False
        for target in targets:
            mr = min_responses(node.state, target, measure, bounds)
            if mr is None:
                tree.refusals.append(
                    {
                        "node": nid,
                        "mode": node.state.mode,
                        "target": list(target),
                        "target_is_required_separation": target in node.state.regime.reqs,
                    }
                )
                no_response = True
                break
            gathered.append((target, mr))
        if no_response:
            node.status = "terminal_no_response"
            continue
        for target, mr in gathered:
            classes = _quotient(node.state, target, mr)
            for rep, size in classes:
                assert response_valid(node.state, target, rep)
                demand: DualEvent = (
                    RequireSame(target[0], target[1])
                    if node.state.mode == IDENTIFY
                    else _impose(target)
                )
                history2 = node.history + (demand,) + tuple(
                    delta_events(node.state.regime, rep)
                )
                cost = mr.cost if measure == "mu2" else (mr.cost[0], -1)
                info = diagnostics(node.state.regime, target, rep)
                info["valid_at_cost"] = mr.valid_at_cost
                _attach(
                    tree, key_map, queue, node, history2,
                    challenge=f"{node.state.mode}{target}",
                    label=delta_label(node.state.regime, rep),
                    response=rep, tie_classes=len(classes), class_size=size,
                    cost=cost, orbits=len(targets), info=info,
                )
        node.status = "expanded"
    return tree


def _impose(target: Pair) -> Event:
    from derivation.model import Impose

    return Impose(target[0], target[1])


def _quotient(s: State, target: Pair, mr: Minima) -> list[tuple[Delta, int]]:
    grouped: dict[StateKey, list[Delta]] = {}
    demand: DualEvent = (
        RequireSame(target[0], target[1]) if s.mode == IDENTIFY else _impose(target)
    )
    for delta in mr.deltas:
        child = dual_replay((demand,) + tuple(delta_events(s.regime, delta)), s)
        grouped.setdefault(state_key(child), []).append(delta)
    return [(members[0], len(members)) for _, members in sorted(grouped.items())]


def _attach(
    tree: DTree,
    key_map: dict[StateKey, int],
    queue: "deque[int]",
    parent: DNode,
    history: tuple[DualEvent, ...],
    challenge: str,
    label: str,
    response: Delta,
    tie_classes: int,
    class_size: int,
    cost: tuple[int, int],
    orbits: int,
    info: dict[str, object],
) -> None:
    state = dual_replay(history)
    key = state_key(state)
    if key in key_map:
        child_id = key_map[key]
        kind = "merge"
        tree.nodes[child_id].merged_count += 1
    else:
        child_id = len(tree.nodes)
        kind = "creation"
        child = DNode(child_id, history, state, parent.depth + 1, key)
        child.certified = certify(child.history, child.state)
        tree.nodes.append(child)
        key_map[key] = child_id
        queue.append(child_id)
    tree.edges.append(
        DEdge(
            parent.node_id, child_id, parent.depth + 1, challenge, label,
            response, tie_classes, class_size, cost, orbits, kind, info,
        )
    )


# ---------------------------------------------------------------------------
# Path statistics over the DAG
# ---------------------------------------------------------------------------


def paths(tree: DTree) -> list[list[int]]:
    """Every root-to-leaf edge path (edge indices).  The DAG is finite and
    acyclic: every response edge strictly grows the regime and a switch
    edge changes the mode without touching the regime."""
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


def branch_report(tree: DTree) -> list[dict[str, object]]:
    """Per maximal branch: rounds spent in each mode before each fixpoint,
    the ruled-form count at each identify fixpoint, and admitted data."""
    reports: list[dict[str, object]] = []
    for path in paths(tree):
        identify_rounds = 0
        separate_rounds = 0
        fixpoint_ruled: list[int] = []
        segments: list[dict[str, object]] = []
        for idx in path:
            e = tree.edges[idx]
            if e.challenge == "switch":
                parent = tree.nodes[e.parent]
                mode = parent.state.mode
                segments.append(
                    {
                        "mode": mode,
                        "rounds": identify_rounds if mode == IDENTIFY else separate_rounds,
                        "ruled_forms_at_fixpoint": len(parent.state.regime.rules),
                        "forms_at_fixpoint": len(parent.state.regime.forms),
                    }
                )
                if mode == IDENTIFY:
                    fixpoint_ruled.append(len(parent.state.regime.rules))
                identify_rounds = 0
                separate_rounds = 0
            elif e.challenge.startswith(IDENTIFY):
                identify_rounds += 1
            else:
                separate_rounds += 1
        leaf = tree.nodes[tree.edges[path[-1]].child] if path else tree.nodes[0]
        if leaf.status == "terminal_all_collapsed":
            fixpoint_ruled.append(len(leaf.state.regime.rules))
        reports.append(
            {
                "leaf": leaf.node_id,
                "leaf_status": leaf.status,
                "identify_rounds_in_final_segment": identify_rounds,
                "separate_rounds_in_final_segment": separate_rounds,
                "segments": segments,
                "identify_fixpoint_ruled_forms": fixpoint_ruled,
                "data_at_leaf": leaf.state.regime.n_data(),
                "forms_at_leaf": len(leaf.state.regime.forms),
                "ruled_forms_at_leaf": len(leaf.state.regime.rules),
            }
        )
    return reports


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def pair_probe(s: State, measure: str, bounds: Bounds) -> list[dict[str, object]]:
    """Every separated pair of the state, demanded on its own."""
    out: list[dict[str, object]] = []
    for pair in separated_pairs(s.regime):
        mr = min_responses(s, pair, measure, bounds)
        entry: dict[str, object] = {
            "pair": list(pair),
            "required_separation": pair in s.regime.reqs,
            "identifiable_within_bounds": mr is not None,
        }
        if mr is not None:
            classes = _quotient(s, pair, mr)
            entry["min_cost"] = list(mr.cost)
            entry["valid_at_cost"] = mr.valid_at_cost
            entry["iso_classes"] = len(classes)
            entry["class_kinds"] = [item_kinds(rep) for rep, _ in classes]
        out.append(entry)
    return out


def reversal_probe(s: State, measure: str, bounds: Bounds) -> list[dict[str, object]]:
    """At an all-collapsed state: switch to separate mode and price the
    re-separation of every collapsed-pair orbit."""
    switched = dual_step(s, Switch())
    out: list[dict[str, object]] = []
    for target in closure_targets(switched):
        mr = min_responses(switched, target, measure, bounds)
        entry: dict[str, object] = {"pair": list(target), "answerable": mr is not None}
        if mr is not None:
            classes = _quotient(switched, target, mr)
            entry["min_cost"] = list(mr.cost)
            entry["iso_classes"] = len(classes)
            entry["class_diagnostics"] = [
                diagnostics(switched.regime, target, rep) for rep, _ in classes
            ]
        out.append(entry)
    return out


# ---------------------------------------------------------------------------
# JSON encoders (deterministic, no environment data)
# ---------------------------------------------------------------------------


def event_json(e: DualEvent) -> dict[str, object]:
    from derivation.export import event_json as sealed_event_json

    if isinstance(e, RequireSame):
        return {"kind": "require_same", "i": e.i, "j": e.j}
    if isinstance(e, Retract):
        return {"kind": "retract"}
    if isinstance(e, Switch):
        return {"kind": "switch"}
    return dict(sealed_event_json(e))


def regime_json(r: Regime) -> dict[str, object]:
    return {
        "data": list(r.data),
        "forms": list(r.forms),
        "insts": [[f, list(a)] for (f, a) in sorted(r.insts)],
        "rules": sorted(r.rules),
        "reqs": [list(p) for p in sorted(r.reqs)],
    }


def delta_json(delta: Delta) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for it in delta:
        if isinstance(it, NewDatum):
            out.append({"kind": "datum"})
        elif isinstance(it, NewForm):
            out.append({"kind": "form", "arity": it.arity})
        elif isinstance(it, NewRuleAll):
            out.append({"kind": "rule_all", "form": it.form})
        else:
            out.append({"kind": "inst", "form": it.form, "args": list(it.args)})
    return out


def node_json(n: DNode) -> dict[str, object]:
    return {
        "id": n.node_id,
        "depth": n.depth,
        "status": n.status,
        "mode": n.state.mode,
        "merged_count": n.merged_count,
        "certified": n.certified,
        "regime": regime_json(n.state.regime),
        "same": [list(p) for p in sorted(n.state.same)],
        "classes": class_count(n.state.regime),
        "history_length": len(n.history),
    }


def edge_json(e: DEdge) -> dict[str, object]:
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
        "orbits": e.orbits,
        "kind": e.kind,
        "info": dict(e.info),
    }


def admitted_fresh_data(tree: DTree) -> int:
    """Fresh data admitted by responses (never by genesis)."""
    root_n = tree.nodes[0].state.regime.n_data()
    return max(n.state.regime.n_data() for n in tree.nodes) - root_n


def events_json(history: tuple[DualEvent, ...]) -> list[dict[str, object]]:
    return [event_json(e) for e in history]


def is_admit_datum(e: DualEvent) -> bool:
    return isinstance(e, AdmitDatum)
