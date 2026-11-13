"""Challenges 0-3, the autonomous challenge generator, and the branch tree.

Classification:

* Challenges 0-3 are externally imposed challenges (transcribed from the
  seed); their analyses are deterministic computations.
* The two *readings* record a proved underdetermination of the challenge
  text: whether an inscription is admitted at genesis / on bare supply.
  Reading L admits only on explicit retention ("supplies and retains");
  reading F additionally admits the initial inscription at genesis
  ("the only initial object-language inscription is").  Both are carried.
* The challenge source splits into two declared components.  No
  object-language endogenous demand generator was derived; both components
  are declared metatheory:

  - the *declared pair-separation closure policy*
    (``closure_challenge_orbits``): reissue the admitted requirement
    pattern (separation) on the collapsed pairs of admitted data, one
    challenge branch per automorphism orbit of collapsed pairs.  A
    collapsed pair is not an active obstruction by itself; this policy is
    what makes it one.  The policy reads only profile equality and the
    automorphism structure; it never inspects presentation-token glyphs,
    never supplies data, and never imports a new goal kind.  It reaches a
    fixpoint once every pair is separated (pair-separation closure
    terminates).  Orbit selection — unlike raw least-pair selection — is
    isomorphism-equivariant, so the quotiented transition is well defined
    (regression: ``test_least_pair_selection_is_not_equivariant``).
  - the *external continuation policy* (supply): the supply-and-admission
    of one fresh opaque token.  This is an explicitly declared external
    policy, not a derived transition; runs with ``supply=False`` are the
    closed-system baseline.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .candidates import (
    Bounds,
    Delta,
    MinResponses,
    NewDatum,
    NewForm,
    NewInst,
    NewRuleAll,
    delta_events,
    min_responses,
    response_valid_naive,
)
from .iso import CanonKey, canonical, find_iso, pair_orbits
from .model import (
    AdmitDatum,
    Event,
    Impose,
    Pair,
    Regime,
    Supply,
    replay,
)
from .observe import collapsed_pairs, profiles, separable, witness

GENESIS_L: tuple[Event, ...] = (
    Supply("<>"),
    Supply("<a>"),
    Supply("<a>"),
    Supply("<ab>"),
    AdmitDatum("<a>"),
    AdmitDatum("<ab>"),
)

GENESIS_F: tuple[Event, ...] = (
    Supply("<>"),
    AdmitDatum("<>"),
    Supply("<a>"),
    Supply("<a>"),
    Supply("<ab>"),
    AdmitDatum("<a>"),
    AdmitDatum("<ab>"),
)


@dataclass(frozen=True)
class Reading:
    name: str
    description: str
    genesis: tuple[Event, ...]
    target: Pair


READING_L = Reading(
    "L",
    "strict admission: only explicit retention admits; the initial "
    "inscription is presented but never retained",
    GENESIS_L,
    (0, 1),
)

READING_F = Reading(
    "F",
    "possession admission: the initial inscription is admitted at genesis; "
    "supplied inscriptions are admitted on retention",
    GENESIS_F,
    (1, 2),
)

READINGS: tuple[Reading, ...] = (READING_L, READING_F)


def delta_label(base: Regime, delta: Delta) -> str:
    """Deterministic neutral label for a response delta."""
    parts: list[str] = []
    n0 = base.n_data()
    for it in delta:
        if isinstance(it, NewDatum):
            parts.append("datum")
        elif isinstance(it, NewForm):
            parts.append(f"form{it.arity}")
        elif isinstance(it, NewRuleAll):
            parts.append(f"rule@{it.form}")
        else:
            shape = "diag" if len(set(it.args)) == 1 and len(it.args) > 1 else ""
            fresh = "+fresh" if any(a >= n0 for a in it.args) else ""
            parts.append(f"inst{len(it.args)}{shape}{fresh}")
    return "+".join(parts) if parts else "empty"


# ---------------------------------------------------------------------------
# Challenge analyses
# ---------------------------------------------------------------------------


def challenge0_report() -> dict[str, object]:
    """Initial inscription, no object-language operation or transition rule.

    Facts (each a deterministic computation; theorem-level versions are in
    the Lean development):

    * supply alone does not change the admitted state;
    * with nothing admitted there are no contexts, no derivable judgment
      instances, and no internally observable anything;
    * no successor is internally forced: the admitted state has no rules,
      and every state change in the model factors through an external
      admission event.
    """
    from .model import EMPTY, step
    from .observe import contexts

    after_supply = step(EMPTY, Supply("<>"))
    return {
        "challenge": 0,
        "supplied": ["<>"],
        "supply_changes_state": after_supply != EMPTY,
        "admitted_data": list(after_supply.data),
        "context_count": len(contexts(after_supply)),
        "derivable_instances": sorted(after_supply.insts),
        "internally_forced_successor": None,
        "readings": {
            "L": "nothing admitted at genesis",
            "F": "the initial inscription is admitted at genesis "
            "(possession reading); still no forms, no instances, "
            "no internal observables",
        },
    }


def challenge1_report() -> dict[str, object]:
    """Supply of <a>: separate supply, admission, observation.

    The sub-reading (admit <a> at supply time or not) provably converges at
    Challenge 2 close because admission dedups on presentation identity;
    the convergence is computed here.
    """
    h_bare: tuple[Event, ...] = (Supply("<>"), Supply("<a>"))
    h_admit: tuple[Event, ...] = h_bare + (AdmitDatum("<a>"),)
    c2_tail: tuple[Event, ...] = (
        Supply("<a>"),
        Supply("<ab>"),
        AdmitDatum("<a>"),
        AdmitDatum("<ab>"),
    )
    r_bare, r_admit = replay(h_bare), replay(h_admit)
    conv = replay(h_bare + c2_tail) == replay(h_admit + c2_tail)
    return {
        "challenge": 1,
        "new_external_presentation": True,
        "admitted_without_admission_event": False,
        "sub_readings": {
            "bare_supply_data": list(r_bare.data),
            "supply_plus_admission_data": list(r_admit.data),
        },
        "sub_readings_converge_at_challenge2": conv,
        "internal_observable_distinction": False,
        "reason": "no admitted judgment forms, hence no contexts and no "
        "internal observation in any sub-reading",
    }


def challenge2_report() -> dict[str, object]:
    """Both wholes supplied and retained.  What changed by admission and
    what remains internally unavailable."""
    out: dict[str, object] = {"challenge": 2, "readings": {}}
    readings: dict[str, object] = {}
    for rd in READINGS:
        r = replay(rd.genesis)
        profs = profiles(r)
        classes = len(set(profs)) if profs else 0
        readings[rd.name] = {
            "admitted_data": list(r.data),
            "externally_distinct_tokens": len(set(r.data)) == len(r.data),
            "collapsed_pairs": list(collapsed_pairs(r)),
            "observational_classes": classes,
            "expressive_increase_over_challenge0": classes > 1,
            "internally_unavailable": [
                "glyph identity",
                "component count",
                "order",
                "concatenation",
                "multiplicity",
                "substring structure",
                "matching",
                "string equality",
            ],
        }
    out["readings"] = readings
    return out


def challenge3_report(
    reading: Reading, bounds: Bounds
) -> dict[str, object]:
    """Required separation of <a> and <ab>.

    Declared meaning of internal separability: behavioral separation by
    positive derivability -- there is a context whose plugging is derivable
    for one datum and not the other (profiles differ)."""
    base = replay(reading.genesis)
    i, j = reading.target
    report: dict[str, object] = {
        "challenge": 3,
        "reading": reading.name,
        "declared_separability": "profiles differ (behavioral separation "
        "by positive derivability)",
        "current_regime_satisfies": separable(base, i, j),
        "witness": witness(base, i, j),
    }
    uniqueness_scope = {
        "mu1": "not unique: the listed classes are tied minima within the "
        "declared bounds; the impossibility below two items is absolute "
        "over the item grammar (Lean); across unbounded arity the tie "
        "class is infinite (Lean arity family), so the enumeration is "
        "complete only within max_arity",
        "mu2": "unique up to the implemented isomorphism among two-item "
        "deltas with new-form arity sum <= 1 over the full item grammar "
        "(Lean, reading L); within the declared bounds the engine finds "
        "exactly one class in both readings",
    }
    for measure in ("mu1", "mu2"):
        mr = min_responses(base, (i, j), measure, bounds)
        assert mr is not None, "progress lemma violated"
        classes = _quotient(base, (i, j), mr)
        report[measure] = {
            "cost_measure": (
                "item count" if measure == "mu1"
                else "(item count, new-form arity sum), lexicographic"
            ),
            "candidate_bounds": {
                "max_items": bounds.max_items,
                "max_arity": bounds.max_arity,
            },
            "uniqueness_scope": uniqueness_scope[measure],
            "minimum_cost": list(mr.cost),
            "valid_deltas_at_minimum": len(mr.deltas),
            "iso_classes": [
                {
                    "label": delta_label(base, rep),
                    "representative": delta_json_items(rep),
                    "class_size": size,
                    "capabilities": _capabilities(rep),
                }
                for rep, size in classes
            ],
            "cost_below_minimum_all_fail": True,
        }
    return report


def _capabilities(delta: Delta) -> dict[str, int]:
    return {
        "new_data": sum(1 for it in delta if isinstance(it, NewDatum)),
        "new_forms": sum(1 for it in delta if isinstance(it, NewForm)),
        "new_form_arity_sum": sum(
            it.arity for it in delta if isinstance(it, NewForm)
        ),
        "new_instances": sum(1 for it in delta if isinstance(it, NewInst)),
        "new_rules": sum(1 for it in delta if isinstance(it, NewRuleAll)),
    }


def delta_json_items(delta: Delta) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for it in delta:
        if isinstance(it, NewDatum):
            out.append({"kind": "datum"})
        elif isinstance(it, NewForm):
            out.append({"kind": "form", "arity": it.arity})
        elif isinstance(it, NewRuleAll):
            out.append({"kind": "rule_all", "form": it.form})
        else:
            out.append(
                {"kind": "inst", "form": it.form, "args": list(it.args)}
            )
    return out


def _quotient(
    base: Regime, target: Pair, mr: MinResponses
) -> list[tuple[Delta, int]]:
    """Group minimum deltas by isomorphism class of the resulting regime;
    return (representative, class size) in deterministic order."""
    grouped: dict[CanonKey, list[Delta]] = {}
    for delta in mr.deltas:
        child = replay(
            (Impose(target[0], target[1]),) + delta_events(base, delta),
            base,
        )
        grouped.setdefault(canonical(child), []).append(delta)
    return [
        (members[0], len(members))
        for _, members in sorted(grouped.items())
    ]


def closure_challenge_orbits(r: Regime) -> tuple[Pair, ...]:
    """The declared pair-separation closure policy: one representative
    (least member) per automorphism orbit of the collapsed pairs, or the
    empty tuple at the fixpoint (every pair separated).

    Token-blind by construction: the computation never reads ``r.data``
    entries, only structural indices (verified by test against renaming).
    Equivariant by construction: renaming the regime by any bijection maps
    the challenge set onto the corresponding challenge set, so isomorphic
    regimes expand to isomorphic child sets."""
    orbits = pair_orbits(r, collapsed_pairs(r))
    return tuple(orbit[0] for orbit in orbits)


# ---------------------------------------------------------------------------
# Branch tree
# ---------------------------------------------------------------------------


@dataclass
class Node:
    node_id: int
    history: tuple[Event, ...]
    regime: Regime
    depth: int
    canon: CanonKey
    status: str = "open"
    merged_count: int = 1
    certified: bool = False


@dataclass
class Edge:
    parent: int
    child: int
    round_no: int
    challenge: str
    response_label: str
    response: Delta
    tie_classes: int
    class_size: int
    cost: tuple[int, int]
    orbits: int = 1
    kind: str = "creation"
    merge_dmap: Optional[tuple[int, ...]] = None
    merge_fmap: Optional[tuple[int, ...]] = None


@dataclass
class Tree:
    reading: str
    measure: str
    bounds: Bounds
    max_rounds: int
    pre_expansion_node_guard: int
    supply: bool
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def stats(self) -> dict[str, object]:
        by_status: dict[str, int] = {}
        for n in self.nodes:
            by_status[n.status] = by_status.get(n.status, 0) + 1
        roles: dict[str, int] = {}
        for e in self.edges:
            role = _role(e)
            roles[role] = roles.get(role, 0) + 1
        tie_expansions = len(
            {
                (e.parent, e.challenge)
                for e in self.edges
                if e.tie_classes > 1
            }
        )
        multi_orbit = len(
            {e.parent for e in self.edges if e.orbits > 1}
        )
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "by_status": by_status,
            "roles": roles,
            "expansions_with_ties": tie_expansions,
            "expansions_with_multiple_orbits": multi_orbit,
            "max_depth": max((n.depth for n in self.nodes), default=0),
            "all_certified": all(n.certified for n in self.nodes),
        }


def _role(e: Edge) -> str:
    """Recurring transition roles, derived from the accepted responses."""
    if e.challenge == "supply":
        return "supply"
    kinds = sorted(
        (
            "datum"
            if isinstance(it, NewDatum)
            else "form"
            if isinstance(it, NewForm)
            else "rule"
            if isinstance(it, NewRuleAll)
            else "inst"
        )
        for it in e.response
    )
    if kinds == ["inst"]:
        return "discrimination"
    if kinds == ["form", "inst"]:
        return "innovation"
    if kinds == ["datum", "inst"]:
        return "auxiliary_witness"
    if kinds == ["inst", "inst"]:
        return "double_discrimination"
    return "+".join(kinds)  # pragma: no cover - no other accepted shape


def build_tree(
    reading: Reading,
    measure: str,
    bounds: Bounds,
    max_rounds: int = 15,
    pre_expansion_node_guard: int = 250,
    supply: bool = True,
) -> Tree:
    """Breadth-first expansion of the branch tree from the Challenge 3
    situation, quotiented by the implemented isomorphism relation
    (isomorphic regimes at any depth merge into one node).

    Round 1 responds to the externally imposed Challenge 3 requirement;
    later rounds respond to the autonomous generator.  With ``supply``
    False the generator's supply move is disabled (termination variant).
    """
    tree = Tree(
        reading.name, measure, bounds, max_rounds, pre_expansion_node_guard, supply
    )
    base = replay(reading.genesis)
    root = Node(0, reading.genesis, base, 0, canonical(base))
    root.certified = replay(root.history) == root.regime
    tree.nodes.append(root)
    canon_map: dict[CanonKey, int] = {root.canon: 0}
    queue: deque[int] = deque([0])
    while queue:
        nid = queue.popleft()
        node = tree.nodes[nid]
        targets: tuple[Pair, ...]
        if nid == 0:
            targets = (reading.target,)
        else:
            assert not (
                set(collapsed_pairs(node.regime)) & set(node.regime.reqs)
            )
            targets = closure_challenge_orbits(node.regime)
        if not targets and not supply:
            # Pair-separation closure fixpoint: every pair separated, and
            # the external continuation policy is disabled.  Genuine
            # termination, regardless of the round budget.
            node.status = "terminal_all_separated"
            continue
        if node.depth >= max_rounds:
            node.status = "completed"
            continue
        if len(tree.nodes) > pre_expansion_node_guard:
            node.status = "frontier_guard"
            continue
        if not targets:
            token = f"g{node.regime.n_data()}"
            history = node.history + (Supply(token), AdmitDatum(token))
            _attach(
                tree,
                canon_map,
                queue,
                node,
                history,
                challenge="supply",
                label="supply",
                response=(),
                tie_classes=1,
                class_size=1,
                cost=(0, 0),
                orbits=1,
            )
            node.status = "expanded"
            continue
        gathered: list[tuple[Pair, MinResponses]] = []
        no_response = False
        for target in targets:
            mr = min_responses(node.regime, target, measure, bounds)
            if mr is None:
                no_response = True
                break
            gathered.append((target, mr))
        if no_response:
            node.status = "terminal_no_response"
            continue
        for target, mr in gathered:
            classes = _quotient(node.regime, target, mr)
            for rep, size in classes:
                assert response_valid_naive(node.regime, target, rep)
                history = (
                    node.history
                    + (Impose(target[0], target[1]),)
                    + delta_events(node.regime, rep)
                )
                cost = (
                    (mr.cost[0], mr.cost[1])
                    if measure == "mu2"
                    else (mr.cost[0], -1)
                )
                _attach(
                    tree,
                    canon_map,
                    queue,
                    node,
                    history,
                    challenge=f"separate{target}",
                    label=delta_label(node.regime, rep),
                    response=rep,
                    tie_classes=len(classes),
                    class_size=size,
                    cost=cost,
                    orbits=len(targets),
                )
        node.status = "expanded"
    return tree


def _attach(
    tree: Tree,
    canon_map: dict[CanonKey, int],
    queue: "deque[int]",
    parent: Node,
    history: tuple[Event, ...],
    challenge: str,
    label: str,
    response: Delta,
    tie_classes: int,
    class_size: int,
    cost: tuple[int, int],
    orbits: int,
) -> None:
    regime = replay(history)
    canon = canonical(regime)
    merge_dmap: Optional[tuple[int, ...]] = None
    merge_fmap: Optional[tuple[int, ...]] = None
    if canon in canon_map:
        # Merge edge: certify it with an explicit isomorphism carrying
        # the replayed result onto the stored child representative.
        child_id = canon_map[canon]
        kind = "merge"
        iso = find_iso(regime, tree.nodes[child_id].regime)
        assert iso is not None, "merge edge without isomorphism"
        merge_dmap, merge_fmap = iso
        tree.nodes[child_id].merged_count += 1
    else:
        child_id = len(tree.nodes)
        kind = "creation"
        child = Node(
            child_id, history, regime, parent.depth + 1, canon
        )
        child.certified = replay(child.history) == child.regime
        tree.nodes.append(child)
        canon_map[canon] = child_id
        queue.append(child_id)
    tree.edges.append(
        Edge(
            parent.node_id,
            child_id,
            parent.depth + 1,
            challenge,
            label,
            response,
            tie_classes,
            class_size,
            cost,
            orbits,
            kind,
            merge_dmap,
            merge_fmap,
        )
    )
