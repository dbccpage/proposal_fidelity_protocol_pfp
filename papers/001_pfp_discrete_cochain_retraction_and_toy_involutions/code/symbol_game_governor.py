"""
Paper-local reference governor and certificate builder for finite graph repair.

Implements exact rational calculations on small finite constraint graphs:
  - Exact rational arithmetic via fractions.Fraction (no floating point).
  - Difference operator: (B f)(u -> v) = f(v) - f(u).
  - Proposal cost: D(s) = sum_{e=(u,v)} w_e * |c(e) - (s(v) - s(u))|.
  - Quotient minimum: Phi_1([c]) = min_f D(f) for the fixed reports c.
  - LP duality: Phi_1([c]) = max { sum_e c(e) x_e : x a circulation, |x_e| <= w_e }.
  - Certificates: a primal potential s* and a feasible circulation x* with equal
    objectives, checked independently by verify_phi_1_certificate.
  - The admitted CUT rule requires strict decrease of D(s); Phi_1([c]) does not
    change under CUT because the reports are fixed.
  - Deterministic JSON hashing and an append-only event record.
  - Value object exact-type equality guard: type(self) is type(other).

Spanning-tree enumeration is exponential in graph size and is capped at
MAX_SPANNING_TREES per connected component; exceeding the cap raises
SpanningTreeLimitExceeded instead of returning a partial minimum.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

MAX_SPANNING_TREES = 100_000


class SpanningTreeLimitExceeded(RuntimeError):
    """Raised when exhaustive tree enumeration would exceed MAX_SPANNING_TREES."""


def _is_exact(value: object) -> bool:
    return type(value) in (int, Fraction)


def _proposal_rational(value: object) -> Fraction:
    """Exact in-process values or integer/fraction strings at the proposal wire."""
    if _is_exact(value):
        return Fraction(value)
    if type(value) is str and re.fullmatch(r"[+-]?[0-9]+(?:/[+-]?[0-9]+)?", value):
        return Fraction(value)
    raise ValueError("proposal numbers require int, Fraction, or integer/fraction strings")


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 JSON; rational values use numerator/denominator strings.

    This archive encoding is intentionally not an RFC 8785 implementation.
    """
    def normalize(value):
        if isinstance(value, Fraction):
            return f"{value.numerator}/{value.denominator}"
        if isinstance(value, dict):
            if any(not isinstance(k, str) for k in value):
                raise TypeError("JSON object keys must be strings")
            return {k: normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [normalize(v) for v in value]
        return value
    return json.dumps(normalize(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


class MoveType(str, Enum):
    INVALID = "INVALID"  # Receipt tag for unsupported input; never an admitted move.
    ASSERT = "ASSERT"
    CUT = "CUT"
    VERIFY = "VERIFY"
    RETRACT = "RETRACT"
    LIFT_REQUEST = "LIFT_REQUEST"


class StepVerdict(str, Enum):
    ASSERTED = "ASSERTED"
    DESCENT = "DESCENT"
    EXACT = "EXACT"
    HOLD = "HOLD"
    REFUSAL = "REFUSAL"
    FAIL = "FAIL"


@dataclass(frozen=True)
class Edge:
    """Directed edge in a constraint graph: u -> v with integer weight >= 1."""

    u: str
    v: str
    weight: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.u, str) or not self.u.strip():
            raise ValueError("u must be a non-empty string")
        if not isinstance(self.v, str) or not self.v.strip():
            raise ValueError("v must be a non-empty string")
        if self.u == self.v:
            raise ValueError(f"Self-loop {self.u} -> {self.v} violates irreflexivity.")
        if type(self.weight) is not int or self.weight <= 0:
            raise ValueError(f"Edge weight must be positive integer, got {self.weight}.")

    @property
    def key(self) -> Tuple[str, str]:
        return (self.u, self.v)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.u == other.u and self.v == other.v and self.weight == other.weight

    def __hash__(self) -> int:
        return hash((type(self), self.u, self.v, self.weight))


@dataclass(frozen=True)
class ConstraintGraph:
    """Finite constraint graph with carrier vertices and directed edges."""

    vertices: Tuple[str, ...]
    edges: Tuple[Edge, ...]

    def __post_init__(self) -> None:
        v_set = set(self.vertices)
        if len(v_set) != len(self.vertices) or any(not isinstance(v, str) or not v.strip() for v in self.vertices):
            raise ValueError("Vertices must be unique non-empty strings")
        if len({e.key for e in self.edges}) != len(self.edges):
            raise ValueError("Duplicate directed edges are not supported")
        for e in self.edges:
            if e.u not in v_set:
                raise ValueError(f"Edge source '{e.u}' not in declared vertices.")
            if e.v not in v_set:
                raise ValueError(f"Edge target '{e.v}' not in declared vertices.")

    def edge_by_pair(self, u: str, v: str) -> Optional[Edge]:
        for e in self.edges:
            if e.u == u and e.v == v:
                return e
        return None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.vertices == other.vertices and self.edges == other.edges

    def __hash__(self) -> int:
        return hash((type(self), self.vertices, self.edges))


@dataclass(frozen=True)
class Phi1Certificate:
    """
    Exact primal-dual certificate for Phi_1 cochain boundary defect.
    Primal upper bound: D(s*) = sum w_e |c(e) - (s*(v) - s*(u))|.
    Dual lower bound: sum c(e) x*(e) over a circulation x* with -w_e <= x*(e) <= w_e.
    Zero duality gap certifies global optimality of the obstruction.
    """

    phi_1: Fraction
    primal_potentials: Mapping[str, Fraction]
    dual_circulations: Mapping[Tuple[str, str], Fraction]
    duality_gap: Fraction

    def __post_init__(self) -> None:
        # Exact integers are widened to Fraction; floats and booleans are
        # refused rather than silently converted into exact values.
        for name in ("phi_1", "duality_gap"):
            value = getattr(self, name)
            if not _is_exact(value):
                raise TypeError(f"{name} must be an exact int or Fraction, got {type(value).__name__}")
            object.__setattr__(self, name, Fraction(value))
        # Snapshot the payload so later caller mutation cannot alter a
        # certificate after it has been verified.
        object.__setattr__(self, "primal_potentials", MappingProxyType(dict(self.primal_potentials)))
        object.__setattr__(self, "dual_circulations", MappingProxyType(dict(self.dual_circulations)))

    def verify(self, vertices, edges, claims) -> bool:
        """Certification requires the source problem, not just a reported gap."""
        return verify_phi_1_certificate(vertices, edges, claims, self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.phi_1 == other.phi_1
            and self.primal_potentials == other.primal_potentials
            and self.dual_circulations == other.dual_circulations
            and self.duality_gap == other.duality_gap
        )


    def __hash__(self) -> int:
        return hash((
            type(self),
            self.phi_1,
            tuple(sorted(self.primal_potentials.items())),
            tuple(sorted(self.dual_circulations.items())),
            self.duality_gap,
        ))


ObstructionScore = Phi1Certificate


@dataclass(frozen=True)
class GovernorStepOutcome:
    """Outcome of one retraction step under the Symbol Game Governor."""

    turn: int
    move_type: MoveType
    verdict: StepVerdict
    defect: Fraction
    phi_1: Fraction
    admitted: bool
    feedback: str
    evidence_sha256: str
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.turn == other.turn
            and self.move_type == other.move_type
            and self.verdict == other.verdict
            and self.defect == other.defect
            and self.phi_1 == other.phi_1
            and self.admitted == other.admitted
            and self.feedback == other.feedback
            and self.evidence_sha256 == other.evidence_sha256
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.turn,
            self.move_type,
            self.verdict,
            self.defect,
            self.phi_1,
            self.admitted,
            self.feedback,
            self.evidence_sha256,
            self.authority_effect,
        ))


def _solve_tree_flows(
    component_vertices: List[str],
    tree_edges: List[Tuple[str, str, int]],
    non_tree_flows: Dict[Tuple[str, str], Fraction],
) -> Dict[Tuple[str, str], Fraction]:
    """Solves exact flow conservation on spanning tree edges via Gaussian elimination over Q."""
    if not tree_edges:
        return dict(non_tree_flows)

    independent_vertices = component_vertices[1:]
    n_vars = len(tree_edges)

    A = [[Fraction(0)] * n_vars for _ in independent_vertices]
    b = [Fraction(0) for _ in independent_vertices]
    tree_map = {(u, v): i for i, (u, v, w) in enumerate(tree_edges)}

    for row_idx, v in enumerate(independent_vertices):
        for (edge_u, edge_v, w) in tree_edges:
            col_idx = tree_map[(edge_u, edge_v)]
            if edge_u == v:
                A[row_idx][col_idx] += Fraction(1)
            elif edge_v == v:
                A[row_idx][col_idx] -= Fraction(1)
        rhs = Fraction(0)
        for (edge_u, edge_v), flow in non_tree_flows.items():
            if edge_u == v:
                rhs -= flow
            elif edge_v == v:
                rhs += flow
        b[row_idx] = rhs

    for col in range(n_vars):
        pivot_row = None
        for row in range(col, n_vars):
            if A[row][col] != 0:
                pivot_row = row
                break
        if pivot_row is None:
            continue
        A[col], A[pivot_row] = A[pivot_row], A[col]
        b[col], b[pivot_row] = b[pivot_row], b[col]
        pivot_val = A[col][col]
        for c in range(col, n_vars):
            A[col][c] /= pivot_val
        b[col] /= pivot_val
        for r in range(n_vars):
            if r != col and A[r][col] != 0:
                factor = A[r][col]
                for c in range(col, n_vars):
                    A[r][c] -= factor * A[col][c]
                b[r] -= factor * b[col]

    res = dict(non_tree_flows)
    for i, (u, v, w) in enumerate(tree_edges):
        res[(u, v)] = b[i]
    return res


def _problem_is_well_formed(vertices, edges, claims) -> bool:
    """Exact types, positive penalties, declared endpoints, no duplicate edges."""
    vertex_set = set(vertices)
    if len(vertex_set) != len(vertices):
        return False
    keys = set()
    for edge in edges:
        if len(edge) != 3:
            return False
        u, v, w = edge
        if u == v or u not in vertex_set or v not in vertex_set:
            return False
        if not _is_exact(w) or w <= 0:
            return False
        if (u, v) in keys:
            return False
        keys.add((u, v))
    if set(claims) - keys:
        return False
    return all(_is_exact(value) for value in claims.values())


def verify_phi_1_certificate(vertices, edges, claims, certificate) -> bool:
    """Check the problem data, coverage, dual feasibility, and both objectives.

    Every scalar must already be an exact int or Fraction; nothing is coerced.
    Objective equality alone is never accepted: the circulation must balance at
    every vertex and respect every capacity.
    """
    if not _problem_is_well_formed(vertices, edges, claims):
        return False
    if set(certificate.primal_potentials) != set(vertices):
        return False
    if set(certificate.dual_circulations) != {(u, v) for u, v, _ in edges}:
        return False
    values = [
        certificate.phi_1,
        certificate.duality_gap,
        *certificate.primal_potentials.values(),
        *certificate.dual_circulations.values(),
    ]
    if any(not _is_exact(value) for value in values):
        return False
    divergence = {v: Fraction(0) for v in vertices}
    primal = dual = Fraction(0)
    for u, v, w in edges:
        x = certificate.dual_circulations[u, v]
        if abs(x) > w:
            return False
        divergence[u] += x
        divergence[v] -= x
        c = claims.get((u, v), Fraction(0))
        primal += w * abs(c - (certificate.primal_potentials[v] - certificate.primal_potentials[u]))
        dual += c * x
    return (
        all(x == 0 for x in divergence.values())
        and primal == dual == certificate.phi_1
        and certificate.duality_gap == 0
    )


def _spanning_trees(
    component: Sequence[str],
    component_edges: Sequence[Tuple[str, str, Any]],
    limit: int,
) -> List[Tuple[Tuple[str, str, Any], ...]]:
    """Enumerate spanning trees in lexicographic edge-index order.

    Include/exclude recursion with union-find pruning visits only forests, so
    the work is proportional to the number of trees, which is capped at limit.
    """
    index = {vertex: position for position, vertex in enumerate(component)}
    target = len(component) - 1
    trees: List[Tuple[Tuple[str, str, Any], ...]] = []

    def root(parent: List[int], node: int) -> int:
        while parent[node] != node:
            node = parent[node]
        return node

    def recurse(position: int, parent: List[int], chosen: List[Tuple[str, str, Any]]) -> None:
        if len(chosen) == target:
            if len(trees) == limit:
                raise SpanningTreeLimitExceeded(
                    f"more than {limit} spanning trees in a component of {len(component)} vertices"
                )
            trees.append(tuple(chosen))
            return
        if position >= len(component_edges) or len(chosen) + len(component_edges) - position < target:
            return
        u, v, _ = component_edges[position]
        a, b = root(parent, index[u]), root(parent, index[v])
        if a != b:
            joined = list(parent)
            joined[a] = b
            chosen.append(component_edges[position])
            recurse(position + 1, joined, chosen)
            chosen.pop()
        recurse(position + 1, parent, chosen)

    recurse(0, list(range(len(component))), [])
    return trees


def _tree_potential(component: Sequence[str], tree, claims) -> Dict[str, Fraction]:
    """Potential with zero residual on every tree edge, pinned to 0 at component[0]."""
    potential: Dict[str, Fraction] = {component[0]: Fraction(0)}
    changed = True
    while changed:
        changed = False
        for u, v, _ in tree:
            report = Fraction(claims.get((u, v), 0))
            if u in potential and v not in potential:
                potential[v] = potential[u] + report
                changed = True
            elif v in potential and u not in potential:
                potential[u] = potential[v] - report
                changed = True
    return potential


def compute_exact_phi_1(
    vertices: Sequence[str],
    edges: Sequence[Tuple[str, str, int | Fraction]],
    claims: Mapping[Tuple[str, str], int | Fraction],
) -> Phi1Certificate:
    """
    Computes exact Phi_1([c]) = min_{f in C^0} sum w_e |c(e) - (f(v) - f(u))|
    and constructs a matching dual circulation certificate x* in Z_1(G) satisfying:
      sum_{e=(v,w)} x_e - sum_{e=(u,v)} x_e = 0  (flow conservation)
      -w_e <= x_e <= w_e                         (capacity bounds)
      sum_e c(e) x_e == Phi_1([c])               (zero duality gap).

    For each connected component, every spanning tree defines a potential with
    zero residual on its edges; an optimum is attained by one of them. Among
    optimal trees, a non-tree edge with nonzero residual r_e carries
    x_e = w_e * sign(r_e). A non-tree edge with zero residual may carry any value
    in [-w_e, w_e]; the builder tries 0 first and then both bounds, which is
    complete because the bounded-variable network simplex method terminates at
    an optimal tree whose non-tree flows sit at +w_e or -w_e. Tree flows then
    follow from balance. The result is checked by verify_phi_1_certificate.
    """
    vert_list = list(vertices)
    if len(set(vert_list)) != len(vert_list) or any(not isinstance(v, str) for v in vert_list):
        raise ValueError("vertices must be distinct strings")
    for edge in edges:
        if len(edge) != 3:
            raise ValueError("edges must be (u, v, weight) triples")
        u, v, w = edge
        if u == v or u not in vert_list or v not in vert_list:
            raise ValueError("edges must join distinct declared vertices")
        if not _is_exact(w):
            raise TypeError("edge weights must be exact int or Fraction, not float or bool")
        if w <= 0:
            raise ValueError("edge weights must be positive")
    edge_keys = [(u, v) for u, v, _ in edges]
    if len(set(edge_keys)) != len(edge_keys):
        raise ValueError("duplicate directed edge")
    if set(claims) - set(edge_keys):
        raise ValueError("claim edge absent from declared carrier")
    if any(not _is_exact(value) for value in claims.values()):
        raise TypeError("claims must be exact int or Fraction, not float or bool")

    if not vert_list:
        return Phi1Certificate(Fraction(0), {}, {}, Fraction(0))

    if not edges:
        return Phi1Certificate(Fraction(0), {v: Fraction(0) for v in vert_list}, {}, Fraction(0))

    adj_undirected: Dict[str, List[str]] = {v: [] for v in vert_list}
    for u, v, _ in edges:
        adj_undirected[u].append(v)
        adj_undirected[v].append(u)

    visited = set()
    components: List[List[str]] = []
    for v in vert_list:
        if v not in visited:
            comp: List[str] = []
            queue = [v]
            visited.add(v)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for nbr in adj_undirected[curr]:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
            components.append(comp)

    total_phi1 = Fraction(0)
    full_primal: Dict[str, Fraction] = {}
    full_dual: Dict[Tuple[str, str], Fraction] = {}

    for comp in components:
        comp_set = set(comp)
        comp_edges = [(u, v, w) for u, v, w in edges if u in comp_set and v in comp_set]

        if len(comp) == 1:
            full_primal[comp[0]] = Fraction(0)
            continue

        tree_evals = []
        best_comp_defect: Optional[Fraction] = None
        for tree in _spanning_trees(comp, comp_edges, MAX_SPANNING_TREES):
            pot = _tree_potential(comp, tree, claims)
            defect = sum(
                (Fraction(w) * abs(Fraction(claims.get((u, v), 0)) - (pot[v] - pot[u])) for u, v, w in comp_edges),
                Fraction(0),
            )
            if best_comp_defect is None or defect < best_comp_defect:
                best_comp_defect = defect
            tree_evals.append((tree, pot, defect))
        if best_comp_defect is None:
            raise ArithmeticError("connected component without a spanning tree")

        chosen_pot: Optional[Dict[str, Fraction]] = None
        chosen_flows: Optional[Dict[Tuple[str, str], Fraction]] = None
        for tree, pot, defect in tree_evals:
            if defect != best_comp_defect:
                continue
            tree_set = {(u, v) for u, v, _ in tree}
            forced: Dict[Tuple[str, str], Fraction] = {}
            free: List[Tuple[Tuple[str, str], Fraction]] = []
            for u, v, w in comp_edges:
                if (u, v) in tree_set:
                    continue
                residual = Fraction(claims.get((u, v), 0)) - (pot[v] - pot[u])
                if residual > 0:
                    forced[(u, v)] = Fraction(w)
                elif residual < 0:
                    forced[(u, v)] = -Fraction(w)
                else:
                    free.append(((u, v), Fraction(w)))
            choices = itertools.chain(
                [tuple(Fraction(0) for _ in free)],
                itertools.product(*[(capacity, -capacity) for _, capacity in free]),
            )
            for choice in choices:
                non_tree_flows = dict(forced)
                non_tree_flows.update({key: value for (key, _), value in zip(free, choice)})
                comp_flows = _solve_tree_flows(comp, list(tree), non_tree_flows)
                if all(abs(comp_flows[(u, v)]) <= Fraction(w) for u, v, w in comp_edges):
                    chosen_pot, chosen_flows = pot, comp_flows
                    break
            if chosen_flows is not None:
                break

        if chosen_pot is None or chosen_flows is None:
            raise ArithmeticError("no capacity-feasible dual circulation found among optimal spanning trees")

        total_phi1 += best_comp_defect
        full_primal.update(chosen_pot)
        full_dual.update(chosen_flows)

    dual_value = sum((Fraction(claims.get(e, 0)) * x_val for e, x_val in full_dual.items()), Fraction(0))
    gap = total_phi1 - dual_value

    certificate = Phi1Certificate(
        phi_1=total_phi1,
        primal_potentials=full_primal,
        dual_circulations=full_dual,
        duality_gap=gap,
    )
    if not verify_phi_1_certificate(vertices, edges, claims, certificate):
        raise ArithmeticError("Primal-dual certificate failed independent verification")
    return certificate


class SymbolGameGovernor:
    """
    Discrete Manifold Governor enforcing strict defect descent and obstruction evaluation.

    State:
      - graph: ConstraintGraph carrier.
      - claims: Active asserted 1-cochains (c: E -> Q).
      - section: Current potential 0-cochain (s: V -> Q).
      - history: Sequence of verified GovernorStepOutcome turns.
      - hash_chain: Tamper-evident deterministic JSON SHA-256 state chain.

    Fundamental Invariant:
      D(s) >= Phi_1([c]) at every step.
      CUT modifies s, descending D(s) toward Phi_1([c]); Phi_1([c]) is invariant under CUT.
    """

    def __init__(
        self,
        graph: ConstraintGraph,
        initial_claims: Optional[Dict[Tuple[str, str], Fraction | int]] = None,
    ) -> None:
        self.graph = graph
        self.claims: Dict[Tuple[str, str], Fraction] = {}
        if initial_claims:
            for k, v in initial_claims.items():
                if not _is_exact(v):
                    raise TypeError("initial claims must be exact int or Fraction, not float or bool")
                self.claims[k] = Fraction(v)

        if not set(self.claims) <= {e.key for e in graph.edges}:
            raise ValueError("Claims must belong to the declared carrier")

        self.section: Dict[str, Fraction] = {v: Fraction(0) for v in graph.vertices}
        self.turn = 0
        self.history: List[GovernorStepOutcome] = []
        self.events: List[Dict[str, Any]] = []
        self._snapshots = {0: (dict(self.claims), dict(self.section))}
        self.genesis = {"vertices": graph.vertices, "edges": [(e.u, e.v, e.weight) for e in graph.edges],
                        "claims": [(u, v, c) for (u, v), c in sorted(self.claims.items())]}
        self._hash_chain = hashlib.sha256(canonical_json_bytes(self.genesis)).hexdigest()

    def _record_outcome(self, outcome, record):
        record = copy.deepcopy(record)
        record["result"] = {"verdict": outcome.verdict.value, "admitted": outcome.admitted,
                            "defect": outcome.defect, "phi_1": outcome.phi_1, "feedback": outcome.feedback}
        record["claims"] = [(u, v, c) for (u, v), c in sorted(self.claims.items())]
        record["section"] = dict(self.section)
        digest = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
        outcome = replace(outcome, evidence_sha256=digest)
        self._hash_chain = digest
        self.events.append(record)
        self.history.append(outcome)
        self._snapshots[self.turn] = (dict(self.claims), dict(self.section))
        return outcome

    def compute_section_defect(self, s: Dict[str, Fraction]) -> Fraction:
        """Computes section defect norm D(s) = sum_{e=(u,v)} w_e * |c(e) - (s(v) - s(u))|."""
        total = Fraction(0)
        for e in self.graph.edges:
            c_val = self.claims.get(e.key, Fraction(0))
            diff = s.get(e.v, Fraction(0)) - s.get(e.u, Fraction(0))
            res = abs(c_val - diff)
            total += Fraction(e.weight) * res
        return total

    def compute_phi_1(self) -> Tuple[Fraction, Dict[str, Fraction]]:
        """Computes exact Phi_1([c]) and returns (phi_1, primal_potentials)."""
        edges_tuple = tuple((e.u, e.v, e.weight) for e in self.graph.edges)
        cert = compute_exact_phi_1(self.graph.vertices, edges_tuple, self.claims)
        return cert.phi_1, cert.primal_potentials

    def get_phi_1_certificate(self) -> Phi1Certificate:
        """Returns the full exact primal-dual Phi_1 certificate with matching circulation lower bound."""
        edges_tuple = tuple((e.u, e.v, e.weight) for e in self.graph.edges)
        return compute_exact_phi_1(self.graph.vertices, edges_tuple, self.claims)

    def execute_move(self, move_type: MoveType | str, payload: Dict[str, Any]) -> GovernorStepOutcome:
        """
        Executes a discrete move in the Symbol Game:
          - ASSERT: Asserts/updates an edge claim c(e).
          - CUT: Proposes a potential adjustment s_{t+1}, strictly descending D(s).
          - VERIFY: Asserts carrier completeness and checks D(s) == 0 or D(s) == Phi_1([c]).
          - RETRACT: Steps backward to a prior state in history.
          - LIFT_REQUEST: Requests carrier expansion upon verified obstruction.
        """
        self.turn += 1
        if isinstance(move_type, MoveType):
            mt = move_type
        else:
            raw_name = str(move_type).split(".")[-1].upper()
            try:
                mt = MoveType(raw_name)
            except ValueError:
                mt = MoveType.INVALID

        current_defect = self.compute_section_defect(self.section)
        current_phi1, _ = self.compute_phi_1()
        if current_defect < current_phi1:
            raise ArithmeticError(f"Invariant violated: D(s)={current_defect} < Phi_1={current_phi1}")

        step_record = {
            "turn": self.turn,
            "move": mt.value,
            "payload": payload,
            "requested_move": str(move_type),
            "prior_hash": self._hash_chain,
        }
        sha = ""  # Filled only after the outcome and resulting state are bound.
        invalid_reason = None
        if not isinstance(payload, dict):
            invalid_reason = "Proposal payload must be a dictionary"
        elif mt == MoveType.ASSERT:
            try:
                if isinstance(payload.get("value"), bool):
                    raise ValueError("Boolean is not a rational claim")
                _proposal_rational(payload.get("value"))
                if not isinstance(payload.get("u"), str) or not isinstance(payload.get("v"), str):
                    raise ValueError("Edge endpoints must be strings")
            except (TypeError, ValueError, ZeroDivisionError, OverflowError):
                invalid_reason = "ASSERT requires valid endpoints and a finite rational value"
        elif mt == MoveType.CUT:
            potentials = payload.get("potentials")
            try:
                if not isinstance(potentials, dict) or not set(potentials) <= set(self.graph.vertices):
                    raise ValueError("Potential outside carrier")
                if any(isinstance(v, bool) for v in potentials.values()):
                    raise ValueError("Boolean potential")
                for value in potentials.values():
                    _proposal_rational(value)
            except (TypeError, ValueError, ZeroDivisionError, OverflowError):
                invalid_reason = "CUT requires finite rational potentials on declared vertices"
        try:
            canonical_json_bytes(step_record)
        except (TypeError, ValueError, OverflowError):
            # Non-JSON inputs cannot enter the JSON audit protocol. Record their
            # diagnostic representation as rejected input without mutating state.
            step_record["payload"] = {"invalid_payload_repr": repr(payload)}
            invalid_reason = "Proposal payload is not serializable finite JSON"
        if invalid_reason:
            return self._record_outcome(GovernorStepOutcome(
                self.turn, mt, StepVerdict.REFUSAL, current_defect, current_phi1,
                False, "Refused: MalformedProposal. " + invalid_reason, sha), step_record)

        if mt == MoveType.ASSERT:
            u = payload.get("u")
            v = payload.get("v")
            val = payload.get("value")
            if not u or not v or val is None:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback="ASSERT requires non-empty 'u', 'v', and 'value'.",
                    evidence_sha256=sha,
                )
                return self._record_outcome(outcome, step_record)

            edge = self.graph.edge_by_pair(u, v)
            if not edge:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback=f"Edge {u} -> {v} does not exist in carrier graph.",
                    evidence_sha256=sha,
                )
                return self._record_outcome(outcome, step_record)

            self.claims[(u, v)] = _proposal_rational(val)
            new_defect = self.compute_section_defect(self.section)
            new_phi1, _ = self.compute_phi_1()

            outcome = GovernorStepOutcome(
                turn=self.turn,
                move_type=mt,
                verdict=StepVerdict.ASSERTED,
                defect=new_defect,
                phi_1=new_phi1,
                admitted=True,
                feedback=f"Admitted ASSERT edge {u}->{v} with claim {val}. Current D(s)={new_defect}, Phi_1([c])={new_phi1}.",
                evidence_sha256=sha,
            )
            return self._record_outcome(outcome, step_record)

        elif mt == MoveType.CUT:
            potentials = payload.get("potentials", {})
            test_section = dict(self.section)
            for v_name, p_val in potentials.items():
                if v_name in test_section:
                    test_section[v_name] = _proposal_rational(p_val)

            proposed_defect = self.compute_section_defect(test_section)

            if proposed_defect > current_defect:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback=(
                        f"Refused: DefectIncrease. Proposed defect {proposed_defect} "
                        f"exceeds current defect {current_defect}."
                    ),
                    evidence_sha256=sha,
                )
                return self._record_outcome(outcome, step_record)
            elif proposed_defect == current_defect:
                if test_section == self.section:
                    feedback = "Refused: IdempotentStationaryLoop. CUT proposes no state change."
                else:
                    feedback = f"Refused: NonDecreasingCut. Proposed defect {proposed_defect} does not strictly decrease current defect {current_defect}."
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback=feedback,
                    evidence_sha256=sha,
                )
                return self._record_outcome(outcome, step_record)

            self.section = test_section
            verdict = (StepVerdict.EXACT if proposed_defect == 0 else
                       StepVerdict.HOLD if proposed_defect == current_phi1 else StepVerdict.DESCENT)
            outcome = GovernorStepOutcome(
                turn=self.turn,
                move_type=mt,
                verdict=verdict,
                defect=proposed_defect,
                phi_1=current_phi1,  # Phi_1([c]) invariant under CUT
                admitted=True,
                feedback=f"Admitted CUT. Section defect descended from {current_defect} to {proposed_defect}. Phi_1([c])={current_phi1}.",
                evidence_sha256=sha,
            )
            return self._record_outcome(outcome, step_record)

        elif mt == MoveType.VERIFY:
            if set(self.claims) != {e.key for e in self.graph.edges}:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback=f"Refused: IncompleteCarrier. Declared {len(self.claims)}/{len(self.graph.edges)} edges.",
                    evidence_sha256=sha,
                )
                return self._record_outcome(outcome, step_record)

            if current_defect == 0:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.EXACT,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=True,
                    feedback="Verified: ZERO_OBSTRUCTION confirmed. D(s)=0 and Phi_1=0 on declared section.",
                    evidence_sha256=sha,
                )
            elif current_defect == current_phi1:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.HOLD,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=True,
                    feedback=f"Verified: MINIMAL_OBSTRUCTION confirmed. Section defect D(s)={current_defect} matches exact obstruction Phi_1([c])={current_phi1}.",
                    evidence_sha256=sha,
                )
            else:
                outcome = GovernorStepOutcome(
                    turn=self.turn,
                    move_type=mt,
                    verdict=StepVerdict.REFUSAL,
                    defect=current_defect,
                    phi_1=current_phi1,
                    admitted=False,
                    feedback=f"Refused: SuboptimalSection. Current defect D(s)={current_defect} > Phi_1([c])={current_phi1}. Further CUT descent required.",
                    evidence_sha256=sha,
                )
            return self._record_outcome(outcome, step_record)

        elif mt == MoveType.RETRACT:
            target_turn = payload.get("target_turn")
            valid = type(target_turn) is int and target_turn in self._snapshots
            if valid:
                claims, section = self._snapshots[target_turn]
                self.claims, self.section = dict(claims), dict(section)
                current_defect = self.compute_section_defect(self.section)
                current_phi1, _ = self.compute_phi_1()
            outcome = GovernorStepOutcome(
                turn=self.turn, move_type=mt,
                verdict=StepVerdict.HOLD if valid else StepVerdict.REFUSAL,
                defect=current_defect, phi_1=current_phi1, admitted=valid,
                feedback=f"Retracted to turn {target_turn}." if valid else "Refused: UnknownTargetTurn.",
                evidence_sha256=sha,
            )
            return self._record_outcome(outcome, step_record)

        elif mt == MoveType.LIFT_REQUEST:
            reason = payload.get("reason", "Local gauge insufficient; requesting carrier lift.")
            outcome = GovernorStepOutcome(
                turn=self.turn,
                move_type=mt,
                verdict=StepVerdict.HOLD,
                defect=current_defect,
                phi_1=current_phi1,
                admitted=True,
                feedback=f"Lift request admitted: {reason}",
                evidence_sha256=sha,
            )
            return self._record_outcome(outcome, step_record)

        else:
            outcome = GovernorStepOutcome(
                turn=self.turn,
                move_type=mt,
                verdict=StepVerdict.REFUSAL,
                defect=current_defect,
                phi_1=current_phi1,
                admitted=False,
                feedback=f"Unsupported move: {mt}",
                evidence_sha256=sha,
            )
            return self._record_outcome(outcome, step_record)


# Backwards-compatible alias
L1SymbolGameGovernor = SymbolGameGovernor
