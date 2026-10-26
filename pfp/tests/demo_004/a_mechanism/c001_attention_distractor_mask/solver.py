"""
solver.py — Fast exact integer potential propagation solver for Challenge C001.

Implements:
1. Strict Zero-Float Law: exact integers (int) only, no floats.
2. O(|V| + |E|) BFS potential propagation deciding Phi_1(c) = 0.
3. For contradictory systems, extracts minimal directed cycle sigma with nonzero
   signed claim sum ((d_1 omega)(sigma) != 0, certifying Gamma_2 > 0).
4. Single-edge repair solver: systematically checks edge substitutions yielding Phi_1 = 0.
5. Witness audit: checks candidate potential against all relations, returning ACCEPT
   or REJECT with the violated edge.
6. Certificate verification engine: verifies solutions and kills invalid checker mutations.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

_CANONICAL_INT_RE = re.compile(r"^(0|-?[1-9][0-9]*)\Z")


def is_canonical_int_str(val: Any) -> bool:
    """Returns True iff val is a string representation of an integer in canonical decimal form.

    Rejects:
    - floats ("0.5", "1.0")
    - non-integer rationals ("1/1", "3/4")
    - non-canonical leading zeros ("007", "-0", "+5")
    - booleans, floats, non-numeric strings
    """
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return True
    if not isinstance(val, str):
        return False
    return bool(_CANONICAL_INT_RE.match(val))


def format_int(val: int) -> str:
    """Formats an exact integer as a canonical decimal string without leading zeros."""
    if not isinstance(val, int) or isinstance(val, bool):
        raise TypeError(f"format_int requires exact int, got {type(val)}: {val}")
    return str(val)


def parse_int_exact(val: Any, field_name: str = "value") -> int:
    """Parses val into an exact int, rejecting floats, fractions, or non-canonical strings."""
    if isinstance(val, bool):
        raise ValueError(f"Boolean not allowed for integer field {field_name}: {val}")
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        if not is_canonical_int_str(val):
            raise ValueError(f"Non-canonical integer string for {field_name}: {val!r}")
        return int(val)
    raise TypeError(f"Invalid type for integer field {field_name}: {type(val)} ({val!r})")


@dataclass
class ConstraintSystem:
    """Represents an integer rank-difference system."""

    items: List[str]
    edges: List[Tuple[str, str, int]]  # (u, v, weight)
    claims: Dict[Tuple[str, str], int]  # (u, v) -> claim c_e

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConstraintSystem:
        """Parses and validates a ConstraintSystem from dictionary data."""
        if not isinstance(data, dict):
            raise ValueError("case data must be a dictionary")

        items_raw = data.get("items")
        if not isinstance(items_raw, list) or not items_raw:
            raise ValueError("items must be a non-empty list of vertex identifiers")
        for x in items_raw:
            if isinstance(x, bool):
                raise ValueError(f"Boolean not permitted as vertex identifier: {x}")
        items = [str(x) for x in items_raw]
        if len(set(items)) != len(items):
            raise ValueError("items must be distinct vertex identifiers")

        items_set = set(items)
        edges_raw = data.get("edges")
        if not isinstance(edges_raw, list):
            raise ValueError("edges must be a list of relations")

        edges: List[Tuple[str, str, int]] = []
        seen_pairs: Set[Tuple[str, str]] = set()
        for i, edge in enumerate(edges_raw):
            if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                raise ValueError(f"edge at index {i} must have at least 2 endpoints: {edge}")
            if isinstance(edge[0], bool) or isinstance(edge[1], bool):
                raise ValueError(f"Boolean endpoint not permitted in edge at index {i}: {edge}")
            u = str(edge[0])
            v = str(edge[1])
            if u not in items_set:
                raise ValueError(f"edge at index {i} references undeclared endpoint u: {u}")
            if v not in items_set:
                raise ValueError(f"edge at index {i} references undeclared endpoint v: {v}")
            if u == v:
                raise ValueError(f"self-loop not permitted at vertex: {u}")
            if (u, v) in seen_pairs:
                raise ValueError(f"duplicate relation edge not permitted: ({u}, {v})")
            if (v, u) in seen_pairs:
                raise ValueError(
                    f"opposed relation edge not permitted: ({u}, {v}) opposes existing ({v}, {u})"
                )
            seen_pairs.add((u, v))
            weight = 1
            if len(edge) >= 3:
                w_val = edge[2]
                if isinstance(w_val, bool) or not isinstance(w_val, int) or w_val <= 0:
                    raise ValueError(f"edge at index {i} has invalid weight: {w_val}")
                weight = w_val
            edges.append((u, v, weight))

        claims_raw = data.get("claims")
        if not isinstance(claims_raw, dict):
            raise ValueError("claims must be a dictionary mapping edges to integer claims")

        claims: Dict[Tuple[str, str], int] = {}
        for k, v in claims_raw.items():
            if isinstance(k, tuple) and len(k) == 2:
                edge_pair = (str(k[0]), str(k[1]))
            elif isinstance(k, str):
                if "->" in k:
                    parts = k.split("->", 1)
                    edge_pair = (parts[0].strip(), parts[1].strip())
                elif "," in k:
                    cleaned = k.strip("()[] ")
                    parts = cleaned.split(",", 1)
                    edge_pair = (parts[0].strip(" '\""), parts[1].strip(" '\""))
                else:
                    raise ValueError(f"unparseable edge key format: {k!r}")
            else:
                raise ValueError(f"unsupported claim key type: {type(k)} ({k!r})")

            c_val = parse_int_exact(v, field_name=f"claims[{edge_pair}]")
            claims[edge_pair] = c_val

        declared_edge_pairs = {(u, v) for u, v, _w in edges}
        if set(claims.keys()) != declared_edge_pairs:
            raise ValueError(
                f"claims keys mismatch declared edges. Declared: {declared_edge_pairs}, Claims: {set(claims.keys())}"
            )

        return cls(items=items, edges=edges, claims=claims)


class PotentialSolver:
    """Exact integer solver for rank-difference systems."""

    def __init__(self, system: ConstraintSystem):
        self.system = system
        self.items = system.items
        self.edges = system.edges
        self.claims = system.claims

        # Build adjacency graph
        # For relation (u, v) with claim c:
        # u -> v: delta = +c (phi(v) = phi(u) + c)
        # v -> u: delta = -c (phi(u) = phi(v) - c)
        self.adj: Dict[str, List[Tuple[str, int, Tuple[str, str], int]]] = {
            item: [] for item in self.items
        }
        for u, v, _w in self.edges:
            c = self.claims[(u, v)]
            self.adj[u].append((v, c, (u, v), +1))
            self.adj[v].append((u, -c, (u, v), -1))

    def solve_verdict(self) -> Tuple[str, Dict[str, int] | List[str]]:
        """Solves consistency of the system in O(|V| + |E|).

        Returns:
            ("CONSISTENT", potentials_dict) if system is consistent (Phi_1 = 0).
            ("CONTRADICTION", cycle_vertices) if contradictory (Gamma_2 > 0).
        """
        potentials: Dict[str, int] = {}
        parent: Dict[str, Optional[Tuple[str, Tuple[str, str], int]]] = {}
        depth: Dict[str, int] = {}

        for root in self.items:
            if root in potentials:
                continue
            potentials[root] = 0
            parent[root] = None
            depth[root] = 0
            queue: deque[str] = deque([root])

            while queue:
                u = queue.popleft()
                u_pot = potentials[u]

                for v, delta, edge_tuple, direction in self.adj[u]:
                    # Skip the immediate parent edge that brought us to u
                    if parent[u] is not None:
                        p_node, p_edge, _p_dir = parent[u]
                        if v == p_node and edge_tuple == p_edge:
                            continue

                    expected_v = u_pot + delta
                    if v not in potentials:
                        potentials[v] = expected_v
                        parent[v] = (u, edge_tuple, direction)
                        depth[v] = depth[u] + 1
                        queue.append(v)
                    elif potentials[v] != expected_v:
                        # Contradiction detected!
                        # Extract the minimal cycle formed by tree paths from LCA(u, v)
                        cycle = self._extract_cycle(u, v, parent, depth)
                        return "CONTRADICTION", cycle

        return "CONSISTENT", potentials

    def _extract_cycle(
        self,
        u: str,
        v: str,
        parent: Dict[str, Optional[Tuple[str, Tuple[str, str], int]]],
        depth: Dict[str, int],
    ) -> List[str]:
        """Extracts the simple directed cycle formed by LCA(u, v) and the cross/back edge u -> v."""
        # Find LCA of u and v in the BFS tree
        curr_u = u
        curr_v = v
        path_u: List[str] = []
        path_v: List[str] = []

        # Equalize depths
        while depth[curr_u] > depth[curr_v]:
            path_u.append(curr_u)
            p = parent[curr_u]
            assert p is not None
            curr_u = p[0]

        while depth[curr_v] > depth[curr_u]:
            path_v.append(curr_v)
            p = parent[curr_v]
            assert p is not None
            curr_v = p[0]

        # Step up together until common ancestor is reached
        while curr_u != curr_v:
            path_u.append(curr_u)
            path_v.append(curr_v)
            p_u = parent[curr_u]
            p_v = parent[curr_v]
            assert p_u is not None and p_v is not None
            curr_u = p_u[0]
            curr_v = p_v[0]

        lca = curr_u

        # The cycle path is: lca -> path_u (reversed) -> u -> v -> path_v -> lca
        # Or starting from u: u -> (up to LCA) -> (down to v) -> u
        # Cycle format in C001 contract: ["A", "C", "F", "A"] (starts and ends at same vertex)
        # Let's order the cycle: [lca] + reversed(path_u) -> edge(u, v) -> path_v + [lca]
        # path_u goes u -> parent -> ... -> child_of_lca
        # So reversed(path_u) goes child_of_lca -> ... -> u
        cycle = [lca] + list(reversed(path_u)) + path_v + [lca]

        # Verify the cycle is closed and valid
        return cycle


def host_verdict(system: ConstraintSystem) -> Tuple[str, Dict[str, int] | List[str]]:
    """Host evaluation returning ("CONSISTENT", potentials) or ("CONTRADICTION", cycle)."""
    solver = PotentialSolver(system)
    return solver.solve_verdict()


def extract_contradiction_cycle(system: ConstraintSystem) -> Optional[List[str]]:
    """Extracts a contradiction cycle if one exists, else None."""
    status, result = host_verdict(system)
    if status == "CONTRADICTION" and isinstance(result, list):
        return result
    return None


def solve_single_repair(system: ConstraintSystem) -> Dict[str, Any]:
    """Finds a single-edge repair (edge, new_value) such that substituting edge makes Phi_1 = 0.

    Returns:
        {"status": "SOLVED", "kind": "repair", "edge": [u, v], "value": format_int(new_val)}
    """
    for u, v, weight in system.edges:
        # Form system without edge (u, v)
        remaining_edges = [(x, y, w) for x, y, w in system.edges if not (x == u and y == v)]
        remaining_claims = {
            (x, y): c for (x, y), c in system.claims.items() if not (x == u and y == v)
        }
        sub_system = ConstraintSystem(
            items=list(system.items),
            edges=remaining_edges,
            claims=remaining_claims,
        )
        sub_solver = PotentialSolver(sub_system)
        status, sub_potentials = sub_solver.solve_verdict()

        if status == "CONSISTENT" and isinstance(sub_potentials, dict):
            # Check if u and v are connected in sub_system
            if u in sub_potentials and v in sub_potentials:
                # The consistent claim must satisfy phi(v) - phi(u) = c'
                # Note: sub_potentials assigns independent components with arbitrary root=0,
                # so we must verify that u and v are in the same component of sub_system!
                # To check if u and v are in the same component of sub_system:
                comp_u = _get_component(sub_solver, u)
                if v in comp_u:
                    repaired_c = sub_potentials[v] - sub_potentials[u]
                    original_c = system.claims[(u, v)]
                    if repaired_c != original_c:
                        return {
                            "status": "SOLVED",
                            "kind": "repair",
                            "edge": [u, v],
                            "value": format_int(repaired_c),
                        }

    return {"status": "UNKNOWN", "refusal": "NO_SINGLE_REPAIR_FOUND"}


def _get_component(solver: PotentialSolver, start_node: str) -> Set[str]:
    """Returns the set of vertices in the connected component of start_node."""
    visited: Set[str] = set()
    queue = deque([start_node])
    visited.add(start_node)
    while queue:
        curr = queue.popleft()
        for nxt, _d, _e, _dir in solver.adj[curr]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


def audit_witness(
    system: ConstraintSystem,
    claimed_potential: Dict[str, Any],
) -> Dict[str, Any]:
    """Audits a claimed potential against all relations.

    Returns:
        {"status": "SOLVED", "kind": "audit", "answer": "ACCEPT"}
        or
        {"status": "SOLVED", "kind": "audit", "answer": "REJECT", "violated": [u, v]}
    """
    if not isinstance(claimed_potential, dict):
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "claimed_potential", "reason": "MUST_BE_DICT"},
        }

    # Check that all items exist in claimed_potential and parse as exact int
    parsed_potential: Dict[str, int] = {}
    for item in system.items:
        if item not in claimed_potential:
            return {
                "status": "OUT_OF_SCOPE",
                "witness": {"field": f"claimed_potential[{item}]", "reason": "UNKNOWN_ENDPOINT"},
            }
        val = claimed_potential[item]
        if not is_canonical_int_str(val):
            return {
                "status": "OUT_OF_SCOPE",
                "witness": {"field": f"claimed_potential[{item}]", "reason": "NON_INTEGER_VALUE"},
            }
        parsed_potential[item] = parse_int_exact(val, field_name=f"claimed_potential[{item}]")

    # Verify each edge in order
    for u, v, _w in system.edges:
        claimed_delta = system.claims[(u, v)]
        actual_delta = parsed_potential[v] - parsed_potential[u]
        if actual_delta != claimed_delta:
            return {
                "status": "SOLVED",
                "kind": "audit",
                "answer": "REJECT",
                "violated": [u, v],
            }

    return {"status": "SOLVED", "kind": "audit", "answer": "ACCEPT"}


def verify_protocol_envelope(solution: Dict[str, Any]) -> Tuple[bool, str]:
    """Checks whether a response dictionary conforms to the C001 wire protocol envelope.

    Validates protocol envelope syntax for:
    - SOLVED (requires valid kind in ('verdict', 'repair', 'audit'))
    - OUT_OF_SCOPE (requires witness dict with non-empty 'field' and 'reason')
    - UNKNOWN (requires non-empty 'refusal' string)
    """
    if not isinstance(solution, dict):
        return False, "Solution must be a dictionary"
    status = solution.get("status")
    if status == "OUT_OF_SCOPE":
        witness = solution.get("witness")
        if isinstance(witness, dict) and "field" in witness and "reason" in witness:
            if (
                isinstance(witness["field"], str)
                and witness["field"]
                and isinstance(witness["reason"], str)
                and witness["reason"]
            ):
                return True, "Valid OUT_OF_SCOPE protocol envelope"
        return False, "OUT_OF_SCOPE missing valid witness field and reason"
    if status == "UNKNOWN":
        refusal = solution.get("refusal")
        if isinstance(refusal, str) and refusal.strip():
            return True, "Valid UNKNOWN protocol envelope"
        return False, "UNKNOWN missing refusal reason"
    if status == "SOLVED":
        kind = solution.get("kind")
        if kind in ("verdict", "repair", "audit"):
            return True, f"Valid SOLVED {kind} protocol envelope"
        return False, f"SOLVED status has unknown kind: {kind!r}"
    return False, f"Unrecognized protocol status: {status!r}"


def verify_certificate(case_dict: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent checker that verifies whether a solution is a complete, sound certificate.

    Per C001 Specification Section 4:
    - Only a verified correct solution scores as correct.
    - UNKNOWN or OUT_OF_SCOPE refusals score as incorrect (not as false acceptance, but not as correct).

    Kills checker mutations:
    - Potential off-by-one at a single vertex
    - Unclosed cycle
    - Undeclared edge in cycle
    - Repair modifying two edges or failing Phi_1 = 0
    - Non-canonical integer strings ("1/1", "0.5", "007")
    - False REJECT naming a satisfied edge
    - False ACCEPT on an invalid potential
    - Counting UNKNOWN refusal or OUT_OF_SCOPE as a correct solution
    """
    if not isinstance(solution, dict):
        return False, "Solution must be a dictionary"

    status = solution.get("status")
    if status == "OUT_OF_SCOPE":
        return False, "OUT_OF_SCOPE is a refusal, not a verified correct solution"

    if status == "UNKNOWN":
        refusal = solution.get("refusal", "UNSPECIFIED")
        return False, f"UNKNOWN refusal ({refusal}) is not a verified correct solution"

    if status != "SOLVED":
        return False, f"Invalid status: {status!r} (expected 'SOLVED')"

    # Parse case
    try:
        system = ConstraintSystem.from_dict(case_dict)
    except Exception as exc:
        return False, f"Invalid case dict: {exc}"

    kind = solution.get("kind")
    if kind not in ("verdict", "repair", "audit"):
        return False, f"Unknown kind: {kind!r}"
    case_kind = case_dict.get("kind")
    if case_kind not in ("verdict", "repair", "audit"):
        return False, f"Invalid case kind: {case_kind!r}"
    if kind != case_kind:
        return False, f"Solution kind {kind!r} does not match requested case kind {case_kind!r}"

    if kind == "verdict":
        answer = solution.get("answer")
        if answer == "CONSISTENT":
            pot = solution.get("potential")
            if not isinstance(pot, dict):
                return False, "CONSISTENT verdict requires potential dictionary"
            for item in system.items:
                if item not in pot:
                    return False, f"Potential missing item {item}"
                if not is_canonical_int_str(pot[item]):
                    return (
                        False,
                        f"Potential value for {item} is not a canonical int string: {pot[item]!r}",
                    )
            # Check every edge
            for u, v, _w in system.edges:
                p_u = int(pot[u])
                p_v = int(pot[v])
                if p_v - p_u != system.claims[(u, v)]:
                    return False, f"Potential violates relation ({u}, {v})"
            return True, "Consistent potential verified"

        elif answer == "CONTRADICTION":
            cycle = solution.get("cycle")
            if not isinstance(cycle, list) or len(cycle) < 4:
                return False, "CONTRADICTION requires cycle of at least 3 vertices (len >= 4)"
            if any(not isinstance(vertex, str) for vertex in cycle):
                return False, "Cycle vertices must be string identifiers"
            if cycle[0] != cycle[-1]:
                return False, f"Cycle is not closed: starts at {cycle[0]}, ends at {cycle[-1]}"

            # Check that each step is a declared relation and compute signed sum
            edge_pairs = set(system.claims.keys())
            signed_sum = 0
            for i in range(len(cycle) - 1):
                u, v = cycle[i], cycle[i + 1]
                if (u, v) in edge_pairs:
                    signed_sum += system.claims[(u, v)]
                elif (v, u) in edge_pairs:
                    signed_sum -= system.claims[(v, u)]
                else:
                    return False, f"Cycle traverses undeclared relation ({u}, {v})"

            if signed_sum == 0:
                return False, f"Contradiction cycle has zero signed claim sum: {signed_sum}"
            return True, "Contradiction cycle verified with nonzero signed sum"
        else:
            return False, f"Unknown verdict answer: {answer!r}"

    elif kind == "repair":
        edge = solution.get("edge")
        val_str = solution.get("value")
        if not isinstance(edge, list) or len(edge) != 2:
            return False, f"Repair requires exactly one 2-element edge list, got {edge!r}"
        u, v = str(edge[0]), str(edge[1])
        if (u, v) not in system.claims:
            return False, f"Repair edge ({u}, {v}) is not a declared edge"
        if not is_canonical_int_str(val_str):
            return False, f"Repair value is not a canonical integer string: {val_str!r}"
        new_val = parse_int_exact(val_str, field_name="repair.value")

        # Check that substituting (u, v) -> new_val yields Phi_1 = 0
        new_claims = dict(system.claims)
        new_claims[(u, v)] = new_val
        repaired_system = ConstraintSystem(
            items=list(system.items),
            edges=list(system.edges),
            claims=new_claims,
        )
        verdict_status, _ = host_verdict(repaired_system)
        if verdict_status != "CONSISTENT":
            return False, f"Repair substituting ({u}, {v}) -> {new_val} does not yield Phi_1 = 0"
        return True, "Repair verified"

    elif kind == "audit":
        answer = solution.get("answer")
        claimed_potential = case_dict.get("claimed_potential")
        if not isinstance(claimed_potential, dict):
            return False, "Case missing claimed_potential for audit kind"

        # Check ground truth audit
        ground_truth_audit = audit_witness(system, claimed_potential)
        if ground_truth_audit.get("status") != "SOLVED":
            return (
                False,
                f"Case claimed_potential is out of scope: {ground_truth_audit.get('witness')}",
            )

        expected_answer = ground_truth_audit.get("answer")

        if answer == "ACCEPT":
            if expected_answer != "ACCEPT":
                return False, "False ACCEPT on an invalid claimed potential"
            return True, "ACCEPT audit verified"

        elif answer == "REJECT":
            if expected_answer != "REJECT":
                return (
                    False,
                    "False REJECT on an acceptable claimed potential (relations are actually satisfied)",
                )
            violated = solution.get("violated")
            if not isinstance(violated, list) or len(violated) != 2:
                return False, f"REJECT requires 2-element violated edge list, got {violated!r}"
            u, v = str(violated[0]), str(violated[1])
            if (u, v) not in system.claims:
                return False, f"Violated edge ({u}, {v}) is not a declared relation"
            # Verify that claimed_potential actually violates (u, v)
            if u not in claimed_potential or v not in claimed_potential:
                return False, f"Endpoints of violated edge ({u}, {v}) not in claimed_potential"
            try:
                p_u = parse_int_exact(claimed_potential[u])
                p_v = parse_int_exact(claimed_potential[v])
            except ValueError as exc:
                return False, f"Non-canonical endpoint in claimed_potential: {exc}"
            if p_v - p_u == system.claims[(u, v)]:
                return False, f"Violated edge ({u}, {v}) is actually satisfied by claimed potential"
            return True, "REJECT audit verified with genuine violated relation"
        else:
            return False, f"Unknown audit answer: {answer!r}"

    return False, f"Unknown kind: {kind!r}"
