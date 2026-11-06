"""Graph Cohomology and Exact Rational Minimum-L1 Coboundary Repair.

Provides:
- Exact canonical rational parsing and formatting (RFC 8785 compliant).
- Graph representation, connected component analysis, spanning tree and cycle basis extraction.
- Exact rational Simplex solver for the dual circulation LP.
- Primal potential reconstruction and complementary slackness certification.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Any


def parse_canonical_rational(val: Any) -> Fraction:
    """Parses a value into an exact Fraction according to strict canonical rules.

    Rejects floats, decimals, and non-canonical representations (e.g. '1/1', '2/4').
    """
    if isinstance(val, bool):
        raise TypeError("Booleans are forbidden as numeric values")
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, (list, tuple)):
        if len(val) != 2:
            raise ValueError(f"Rational list/tuple must have length 2: {val!r}")
        num, den = val[0], val[1]
        if (
            isinstance(num, bool)
            or isinstance(den, bool)
            or not isinstance(num, int)
            or not isinstance(den, int)
        ):
            raise TypeError(f"Rational components must be exact ints: {val!r}")
        if den <= 0:
            raise ValueError(f"Rational denominator must be strictly positive: {val!r}")
        return Fraction(num, den)
    if isinstance(val, str):
        val = val.strip()
        if "." in val or "e" in val.lower():
            raise ValueError(f"Decimals and floats forbidden in canonical rationals: {val!r}")
        if "/" in val:
            parts = val.split("/")
            if len(parts) != 2:
                raise ValueError(f"Malformed fraction string: {val!r}")
            num_str, den_str = parts[0].strip(), parts[1].strip()
            num = int(num_str)
            den = int(den_str)
            if den <= 0:
                raise ValueError(f"Denominator must be strictly positive: {val!r}")
            if den == 1:
                raise ValueError(
                    f"Fractions with denominator 1 forbidden (must be integer string): {val!r}"
                )
            f = Fraction(num, den)
            if f.numerator != num or f.denominator != den:
                raise ValueError(f"Unreduced fraction forbidden: {val!r}")
            return f
        return Fraction(int(val), 1)
    raise TypeError(f"Unsupported rational type: {type(val)}: {val!r}")


def format_canonical_rational(val: Fraction | int) -> str:
    """Formats an exact Fraction or int to a canonical string.

    Never outputs '1/1' or decimals.
    """
    if isinstance(val, int):
        return str(val)
    f = Fraction(val)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


@dataclass(frozen=True)
class Edge:
    id: str
    u: str
    v: str
    claim: Fraction
    weight: Fraction


@dataclass
class Graph:
    vertices: list[str]
    edges: list[Edge]

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def num_edges(self) -> int:
        return len(self.edges)


def extract_components(graph: Graph) -> list[Graph]:
    """Partitions a graph into connected components (undirected connectivity)."""
    adj: dict[str, list[Edge]] = {v: [] for v in graph.vertices}
    for e in graph.edges:
        adj[e.u].append(e)
        adj[e.v].append(e)

    visited: set[str] = set()
    components: list[Graph] = []

    for v in graph.vertices:
        if v in visited:
            continue
        comp_verts: list[str] = []
        comp_edges_set: set[str] = set()
        comp_edges: list[Edge] = []
        queue = deque([v])
        visited.add(v)

        while queue:
            curr = queue.popleft()
            comp_verts.append(curr)
            for edge in adj[curr]:
                if edge.id not in comp_edges_set:
                    comp_edges_set.add(edge.id)
                    comp_edges.append(edge)
                neighbor = edge.v if edge.u == curr else edge.u
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        components.append(Graph(vertices=comp_verts, edges=comp_edges))

    return components


def compute_cycle_rank(graph: Graph) -> int:
    """Computes cycle rank b1 = |E| - |V| + (number of connected components)."""
    comps = extract_components(graph)
    return len(graph.edges) - len(graph.vertices) + len(comps)


def find_spanning_tree_and_cycles(
    graph: Graph,
) -> tuple[list[Edge], list[Edge], list[dict[str, int]]]:
    """Finds a spanning tree and fundamental cycles for a connected graph.

    Returns:
    - tree_edges: list of edges in spanning tree
    - chord_edges: list of chord edges not in tree
    - cycles: list of cycle vectors, where each cycle is a dict {edge_id: orientation (+1 or -1)}
    """
    if not graph.vertices:
        return [], [], []

    tree_edges: list[Edge] = []
    tree_edge_ids: set[str] = set()
    chord_edges: list[Edge] = []

    # BFS spanning tree
    visited: set[str] = {graph.vertices[0]}
    # Track parent edge for path reconstruction: child -> (parent, edge, direction: +1 if u->v else -1)
    tree_adj: dict[str, list[tuple[str, Edge, int]]] = {v: [] for v in graph.vertices}

    queue = deque([graph.vertices[0]])
    while queue:
        curr = queue.popleft()
        for edge in graph.edges:
            if edge.id in tree_edge_ids:
                continue
            if edge.u == curr and edge.v not in visited:
                visited.add(edge.v)
                tree_edges.append(edge)
                tree_edge_ids.add(edge.id)
                tree_adj[curr].append((edge.v, edge, 1))
                tree_adj[edge.v].append((curr, edge, -1))
                queue.append(edge.v)
            elif edge.v == curr and edge.u not in visited:
                visited.add(edge.u)
                tree_edges.append(edge)
                tree_edge_ids.add(edge.id)
                tree_adj[curr].append((edge.u, edge, -1))
                tree_adj[edge.u].append((curr, edge, 1))
                queue.append(edge.u)

    for edge in graph.edges:
        if edge.id not in tree_edge_ids:
            chord_edges.append(edge)

    # For each chord edge e = (u, v):
    # Find simple path in tree from v to u.
    # The cycle is +1 on chord edge, and follows the path from v to u.
    cycles: list[dict[str, int]] = []
    for chord in chord_edges:
        # BFS in tree from chord.v to chord.u
        pred: dict[str, tuple[str, Edge, int]] = {}
        q = deque([chord.v])
        seen = {chord.v}
        found = False
        while q:
            c = q.popleft()
            if c == chord.u:
                found = True
                break
            for nxt, t_edge, direction in tree_adj[c]:
                if nxt not in seen:
                    seen.add(nxt)
                    pred[nxt] = (c, t_edge, direction)
                    q.append(nxt)

        assert found, f"Tree disconnected between {chord.v} and {chord.u}"

        cycle: dict[str, int] = {chord.id: 1}
        curr = chord.u
        while curr != chord.v:
            p, t_edge, direction = pred[curr]
            cycle[t_edge.id] = direction
            curr = p

        cycles.append(cycle)

    return tree_edges, chord_edges, cycles


class ExactSimplexSolver:
    """Exact rational Simplex algorithm using pure Python Fraction arithmetic.

    Solves:
    Maximize gamma^T (alpha^+ - alpha^-)
    Subject to:
    A (alpha^+ - alpha^-) + s^+ = w
    -A (alpha^+ - alpha^-) + s^- = w
    alpha^+, alpha^-, s^+, s^- >= 0
    where w > 0.
    """

    def __init__(
        self,
        gamma: list[Fraction],
        a_matrix: list[list[int]],
        capacities: list[Fraction],
        edge_ids: list[str],
    ) -> None:
        self.k = len(gamma)  # number of cycle variables
        self.m = len(capacities)  # number of edges
        self.gamma = gamma
        self.a_matrix = a_matrix  # m rows, k cols
        self.capacities = capacities
        self.edge_ids = edge_ids

    def solve(self) -> tuple[dict[str, Fraction], dict[str, Fraction], Fraction]:
        """Runs exact Simplex and returns (dual_circulation_y, repair_r, phi1)."""
        k = self.k
        m = self.m
        if k == 0:
            # Cycle rank 0 -> zero dual circulation, zero repair, zero phi1
            return (
                {eid: Fraction(0) for eid in self.edge_ids},
                {eid: Fraction(0) for eid in self.edge_ids},
                Fraction(0),
            )

        # Variables ordering:
        # 0 .. k-1: alpha^+
        # k .. 2k-1: alpha^-
        # 2k .. 2k+m-1: s^+ (slacks for +A alpha <= w)
        # 2k+m .. 2k+2m-1: s^- (slacks for -A alpha <= w)
        num_vars = 2 * k + 2 * m
        num_rows = 2 * m

        # Tableau representation:
        # rows 0 .. 2m-1: constraint rows
        # row 2m: objective row (Z row)
        # Each row has length num_vars + 1 (last column is RHS)
        tableau: list[list[Fraction]] = [
            [Fraction(0) for _ in range(num_vars + 1)] for _ in range(num_rows + 1)
        ]

        # Initial basic variables:
        # s_e^+ is basic for row e (col 2k + e)
        # s_e^- is basic for row m + e (col 2k + m + e)
        basis = [2 * k + e for e in range(m)] + [2 * k + m + e for e in range(m)]

        # Fill constraint rows:
        # Row e: +A alpha^+ - A alpha^- + s_e^+ = w_e
        for e in range(m):
            for j in range(k):
                val = Fraction(self.a_matrix[e][j])
                tableau[e][j] = val  # alpha^+
                tableau[e][k + j] = -val  # alpha^-
            tableau[e][2 * k + e] = Fraction(1)  # s_e^+
            tableau[e][num_vars] = self.capacities[e]  # RHS w_e

        # Row m + e: -A alpha^+ + A alpha^- + s_e^- = w_e
        for e in range(m):
            row = m + e
            for j in range(k):
                val = Fraction(self.a_matrix[e][j])
                tableau[row][j] = -val  # alpha^+
                tableau[row][k + j] = val  # alpha^-
            tableau[row][2 * k + m + e] = Fraction(1)  # s_e^-
            tableau[row][num_vars] = self.capacities[e]  # RHS w_e

        # Objective row: Maximize sum_j gamma_j (alpha_j^+ - alpha_j^-)
        # Standard form: Z - sum_j gamma_j alpha_j^+ + sum_j gamma_j alpha_j^- = 0
        # In tableau, coefficient of x_j in obj row is -c_j.
        for j in range(k):
            tableau[num_rows][j] = -self.gamma[j]
            tableau[num_rows][k + j] = self.gamma[j]

        # Simplex loop
        max_pivots = 500 + 50 * (k + m)
        pivots = 0

        while pivots < max_pivots:
            pivots += 1

            # Find entering variable: column with smallest negative reduced cost (or Bland's rule)
            entering_col = -1
            min_rc = Fraction(0)
            for j in range(num_vars):
                rc = tableau[num_rows][j]
                if rc < min_rc:
                    min_rc = rc
                    entering_col = j

            if entering_col == -1:
                # Optimal solution reached!
                break

            # Minimum ratio test
            leaving_row = -1
            min_ratio: Fraction | None = None

            for i in range(num_rows):
                coeff = tableau[i][entering_col]
                if coeff > Fraction(0):
                    ratio = tableau[i][num_vars] / coeff
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        leaving_row = i
                    elif ratio == min_ratio and leaving_row != -1:
                        # Tie-breaking by smallest basic variable index (Bland's rule)
                        if basis[i] < basis[leaving_row]:
                            leaving_row = i

            if leaving_row == -1:
                raise ValueError("LP is unbounded (unexpected for bounded circulation LP)")

            # Pivot on (leaving_row, entering_col)
            pivot_val = tableau[leaving_row][entering_col]
            for j in range(num_vars + 1):
                tableau[leaving_row][j] /= pivot_val

            for i in range(num_rows + 1):
                if i != leaving_row:
                    factor = tableau[i][entering_col]
                    if factor != Fraction(0):
                        for j in range(num_vars + 1):
                            tableau[i][j] -= factor * tableau[leaving_row][j]

            basis[leaving_row] = entering_col

        # Extract variable values
        var_values = [Fraction(0)] * num_vars
        for i in range(num_rows):
            var_values[basis[i]] = tableau[i][num_vars]

        alpha = [var_values[j] - var_values[k + j] for j in range(k)]

        # Compute dual circulation y_e = sum_j A_{e, j} alpha_j
        y: dict[str, Fraction] = {}
        for e, eid in enumerate(self.edge_ids):
            val = Fraction(0)
            for j in range(k):
                val += Fraction(self.a_matrix[e][j]) * alpha[j]
            y[eid] = val

        # Extract shadow prices (dual variables of this LP -> primal repairs r_e)
        # The dual variables are the reduced costs in the objective row for the slack variables!
        repair: dict[str, Fraction] = {}
        for e, eid in enumerate(self.edge_ids):
            # Slack s_e^+ is column 2k + e
            # Slack s_e^- is column 2k + m + e
            lambda_plus = tableau[num_rows][2 * k + e]
            lambda_minus = tableau[num_rows][2 * k + m + e]
            r_val = lambda_plus - lambda_minus
            repair[eid] = r_val

        phi1 = tableau[num_rows][num_vars]
        return y, repair, phi1


def solve_component(
    comp: Graph,
) -> tuple[dict[str, Fraction], dict[str, Fraction], dict[str, Fraction], Fraction]:
    """Solves minimum-L1 repair on a single connected component.

    Returns:
    - potential: dict {vertex_id: Fraction}
    - repair: dict {edge_id: Fraction}
    - dual: dict {edge_id: Fraction}
    - phi1: Fraction
    """
    if comp.num_vertices == 0:
        return {}, {}, {}, Fraction(0)

    if comp.num_edges == 0:
        # Only isolated vertices
        return {v: Fraction(0) for v in comp.vertices}, {}, {}, Fraction(0)

    tree_edges, chord_edges, cycles = find_spanning_tree_and_cycles(comp)
    k = len(cycles)

    if k == 0:
        # Cycle rank is 0 -> Graph is a tree! Exact without any repair.
        # Pick comp.vertices[0] as root, set phi(root) = 0.
        potential: dict[str, Fraction] = {comp.vertices[0]: Fraction(0)}
        adj: dict[str, list[tuple[str, Edge, int]]] = {v: [] for v in comp.vertices}
        for e in comp.edges:
            adj[e.u].append((e.v, e, 1))
            adj[e.v].append((e.u, e, -1))

        queue = deque([comp.vertices[0]])
        while queue:
            curr = queue.popleft()
            curr_phi = potential[curr]
            for nxt, edge, direction in adj[curr]:
                if nxt not in potential:
                    # direction: +1 if edge is curr -> nxt (head=nxt, tail=curr)
                    # phi(head) - phi(tail) = claim => phi(nxt) = curr_phi + claim
                    # direction: -1 if edge is nxt -> curr (head=curr, tail=nxt)
                    # phi(head) - phi(tail) = claim => curr_phi - phi(nxt) = claim => phi(nxt) = curr_phi - claim
                    if direction == 1:
                        potential[nxt] = curr_phi + edge.claim
                    else:
                        potential[nxt] = curr_phi - edge.claim
                    queue.append(nxt)

        return (
            potential,
            {e.id: Fraction(0) for e in comp.edges},
            {e.id: Fraction(0) for e in comp.edges},
            Fraction(0),
        )

    # k > 0: Construct LP
    edge_ids = [e.id for e in comp.edges]
    edge_map = {e.id: e for e in comp.edges}
    capacities = [e.weight for e in comp.edges]

    # Cycle claims gamma_j = sum_{e in C_j} c_e * orientation
    gamma: list[Fraction] = []
    a_matrix: list[list[int]] = [[0 for _ in range(k)] for _ in range(len(comp.edges))]

    for j, cycle in enumerate(cycles):
        c_sum = Fraction(0)
        for eid, orient in cycle.items():
            c_sum += edge_map[eid].claim * Fraction(orient)
        gamma.append(c_sum)

        for e_idx, e in enumerate(comp.edges):
            if e.id in cycle:
                a_matrix[e_idx][j] = cycle[e.id]

    solver = ExactSimplexSolver(gamma, a_matrix, capacities, edge_ids)
    dual_y, repair_r, phi1 = solver.solve()

    # Now reconstruct potential phi such that phi(v) - phi(u) = c_e - r_e
    repaired_claims = {e.id: e.claim - repair_r[e.id] for e in comp.edges}

    potential = {comp.vertices[0]: Fraction(0)}
    adj = {v: [] for v in comp.vertices}
    for e in comp.edges:
        adj[e.u].append((e.v, e, 1))
        adj[e.v].append((e.u, e, -1))

    queue = deque([comp.vertices[0]])
    while queue:
        curr = queue.popleft()
        curr_phi = potential[curr]
        for nxt, edge, direction in adj[curr]:
            if nxt not in potential:
                rep_c = repaired_claims[edge.id]
                if direction == 1:
                    potential[nxt] = curr_phi + rep_c
                else:
                    potential[nxt] = curr_phi - rep_c
                queue.append(nxt)

    return potential, repair_r, dual_y, phi1


def solve_minimum_l1_repair(
    graph: Graph,
) -> tuple[dict[str, Fraction], dict[str, Fraction], dict[str, Fraction], Fraction]:
    """Solves minimum-L1 repair for the entire graph across all connected components."""
    components = extract_components(graph)
    total_potential: dict[str, Fraction] = {}
    total_repair: dict[str, Fraction] = {}
    total_dual: dict[str, Fraction] = {}
    total_phi1 = Fraction(0)

    for comp in components:
        pot, rep, dual, phi1 = solve_component(comp)
        total_potential.update(pot)
        total_repair.update(rep)
        total_dual.update(dual)
        total_phi1 += phi1

    return total_potential, total_repair, total_dual, total_phi1
