"""Higher-Order Simplicial Complexes, 1-Cochains, and Exact Rational Gradient Solvers.

Provides exact rational simplicial complex representations, spanning tree decomposition,
fundamental cycle basis extraction, and discrete cochain gradient computation over Q
for higher-order simplicial complexes (N >= 6, cycle rank b_1 >= 10).

Governing Invariant: Zero Python Math Re-invention & Sovereign Rust Delegation.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
Governing Invariant: Strict Descent on (Gamma_2, Phi_1, defect_count).

The quantity this module computes is the cycle holonomy sum
sum_k |r_k| over one chosen fundamental cycle basis. It is zero exactly when
every cycle in that basis closes, but its positive values depend on the basis,
so it is not Phi_1 (the L1 distance to the coboundaries, which
omega_functional computes). Nothing here reports it as Phi_1.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence

# =============================================================================
# 1. Simplicial Complex (N >= 6)
# =============================================================================

@dataclass(frozen=True)
class CochainCarrier:
    """Finite abstract simplicial complex with exact combinatorial structure.

    Supports complete complexes K_N (for N >= 6), triangulated 2-manifolds,
    and arbitrary finite simplicial complexes with verified boundary operators.
    """

    complex_id: str
    vertices: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    faces: tuple[tuple[str, str, str], ...]  # 2-simplices (triangles)

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError("Simplicial complex must contain at least 3 vertices.")
        # Ensure vertices are uniquely named
        if len(set(self.vertices)) != len(self.vertices):
            raise ValueError("Vertices must have distinct identifiers.")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.complex_id == other.complex_id
            and self.vertices == other.vertices
            and self.edges == other.edges
            and self.faces == other.faces
        )

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def face_count(self) -> int:
        return len(self.faces)

    @property
    def cycle_rank(self) -> int:
        """First Betti number b_1 = |E| - |V| + 1 for connected 1-skeleton."""
        return self.edge_count - self.vertex_count + 1

    @classmethod
    def make_complete_complex(cls, n: int, prefix: str = "v") -> "CochainCarrier":
        """Generates canonical complete simplicial complex K_n.

        For n=6: |V|=6, |E|=15, |F|=20, b_1 = 15 - 6 + 1 = 10 fundamental cycles.
        For n=7: |V|=7, |E|=21, |F|=35, b_1 = 21 - 7 + 1 = 15 fundamental cycles.
        """
        if n < 3:
            raise ValueError(f"Complete complex K_n requires n >= 3, got n={n}")
        verts = tuple(f"{prefix}{i}" for i in range(n))
        edges = tuple(
            (verts[i], verts[j])
            for i in range(n)
            for j in range(i + 1, n)
        )
        faces = tuple(
            (verts[i], verts[j], verts[k])
            for i in range(n)
            for j in range(i + 1, n)
            for k in range(j + 1, n)
        )
        return cls(
            complex_id=f"K_{n}",
            vertices=verts,
            edges=edges,
            faces=faces,
        )

    @classmethod
    def make_octahedral_complex(cls) -> "CochainCarrier":
        """Generates the regular octahedral triangulated complex (boundary of 3-cross-polytope).

        6 vertices, 12 edges, 8 faces, cycle rank b_1 = 12 - 6 + 1 = 7.
        Homology: H_0 = Z, H_1 = 0 (as hollow 2-sphere), 1-skeleton b_1 = 7.
        """
        verts = ("x_pos", "x_neg", "y_pos", "y_neg", "z_pos", "z_neg")
        # Edges connect vertices that are not antipodal
        antipodal = {
            ("x_pos", "x_neg"), ("x_neg", "x_pos"),
            ("y_pos", "y_neg"), ("y_neg", "y_pos"),
            ("z_pos", "z_neg"), ("z_neg", "z_pos"),
        }
        edges_list: list[tuple[str, str]] = []
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                if (verts[i], verts[j]) not in antipodal:
                    edges_list.append((verts[i], verts[j]))
        edges = tuple(edges_list)

        # 8 triangular faces
        faces = (
            ("x_pos", "y_pos", "z_pos"),
            ("x_pos", "y_pos", "z_neg"),
            ("x_pos", "y_neg", "z_pos"),
            ("x_pos", "y_neg", "z_neg"),
            ("x_neg", "y_pos", "z_pos"),
            ("x_neg", "y_pos", "z_neg"),
            ("x_neg", "y_neg", "z_pos"),
            ("x_neg", "y_neg", "z_neg"),
        )
        return cls(
            complex_id="octahedron_S2",
            vertices=verts,
            edges=edges,
            faces=faces,
        )

    def to_faces_boundary_spec(self) -> tuple[tuple[tuple[int, int, int], ...], ...]:
        """Convert 2-simplices (faces) to boundary terms (tail, head, sign) for exact homology."""
        v_idx = {v: i for i, v in enumerate(self.vertices)}
        spec: list[tuple[tuple[int, int, int], ...]] = []
        for u, v, w in self.faces:
            u_i, v_i, w_i = v_idx[u], v_idx[v], v_idx[w]
            face_terms = ((u_i, v_i, 1), (v_i, w_i, 1), (w_i, u_i, 1))
            spec.append(face_terms)
        return tuple(spec)

    def to_simplices_spec(self) -> tuple[tuple[int, ...], ...]:
        """Convert complex faces into simplex index tuples for simplicial boundary law verification."""
        v_idx = {v: i for i, v in enumerate(self.vertices)}
        return tuple(tuple(v_idx[v] for v in face) for face in self.faces)

    def verify_boundary_closed(self, hom_port: Any = None) -> bool:
        """Verify boundary closedness via sovereign Rust homology action exact_verify_boundary_closed."""
        if hom_port is None:
            try:
                from .kinds import get_homology_port

                hom_port = get_homology_port()
            except Exception:
                pass
        if hom_port is not None and getattr(hom_port, "__class__", None).__name__ != "_UnboundHomologyPort":
            return bool(hom_port.verify_boundary_closed(self.to_faces_boundary_spec()))
        raise RuntimeError("ExactHomologyPort unavailable for boundary closedness verification")

    def verify_simplicial_boundary_law(self, hom_port: Any = None) -> Mapping[str, Any]:
        """Verify simplicial boundary law d_1 o d_2 = 0 via sovereign Rust homology action."""
        if hom_port is None:
            try:
                from .kinds import get_homology_port

                hom_port = get_homology_port()
            except Exception:
                pass
        if hom_port is not None and getattr(hom_port, "__class__", None).__name__ != "_UnboundHomologyPort":
            return hom_port.verify_simplicial_boundary_law(self.to_simplices_spec())
        raise RuntimeError("ExactHomologyPort unavailable for simplicial boundary law verification")

    def find_spanning_tree(
        self, root: str | None = None
    ) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
        """Constructs a deterministic spanning tree T and chord set C = E \\ T via BFS.

        Returns (tree_edges, chord_edges).
        """
        if root is None:
            root = self.vertices[0]

        adj: dict[str, list[tuple[str, tuple[str, str]]]] = {v: [] for v in self.vertices}
        for u, v in self.edges:
            adj[u].append((v, (u, v)))
            adj[v].append((u, (u, v)))

        visited: set[str] = {root}
        tree_edges: list[tuple[str, str]] = []
        used_edges: set[tuple[str, str]] = set()

        queue = deque([root])
        while queue:
            curr = queue.popleft()
            for neighbor, original_edge in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    tree_edges.append(original_edge)
                    used_edges.add(original_edge)
                    queue.append(neighbor)

        if len(visited) != len(self.vertices):
            raise ValueError("1-skeleton is not connected; spanning tree cannot cover all vertices.")

        chord_edges = [e for e in self.edges if e not in used_edges]
        return tuple(tree_edges), tuple(chord_edges)

    def find_fundamental_cycles(
        self,
        tree_edges: Sequence[tuple[str, str]],
        chord_edges: Sequence[tuple[str, str]],
    ) -> tuple[tuple[tuple[str, str, int], ...], ...]:
        """Derives the fundamental cycle basis induced by spanning tree T and chords C.

        For each chord e_k = (u, v) in C, finds the unique path P_T(v, u) in T
        and forms cycle C_k = ((u, v, +1), ...path edges...).
        Each chord appears in EXACTLY one cycle in this basis (triangular/decoupled basis).
        """
        tree_adj: dict[str, list[tuple[str, tuple[str, str], int]]] = {
            v: [] for v in self.vertices
        }
        for u, v in tree_edges:
            tree_adj[u].append((v, (u, v), +1))   # forward: u -> v
            tree_adj[v].append((u, (u, v), -1))   # backward: v -> u

        cycles: list[tuple[tuple[str, str, int], ...]] = []

        for chord_u, chord_v in chord_edges:
            # BFS path in tree from chord_v to chord_u
            parent: dict[str, tuple[str, tuple[str, str], int] | None] = {chord_v: None}
            q = deque([chord_v])
            found = False

            while q and not found:
                curr = q.popleft()
                if curr == chord_u:
                    found = True
                    break
                for nxt, edge, sign in tree_adj[curr]:
                    if nxt not in parent:
                        parent[nxt] = (curr, edge, sign)
                        q.append(nxt)

            if not found:
                raise ValueError(f"Disconnected tree: no path between {chord_v} and {chord_u}")

            # Reconstruct tree path from chord_v to chord_u
            path: list[tuple[str, str, int]] = []
            curr = chord_u
            while curr != chord_v:
                prev_info = parent[curr]
                assert prev_info is not None
                p_node, p_edge, p_sign = prev_info
                path.append((p_edge[0], p_edge[1], p_sign))
                curr = p_node

            path.reverse()
            # Cycle starts with chord traversed forward (+1), followed by tree path back to chord_u
            full_cycle = ((chord_u, chord_v, +1), *path)
            cycles.append(full_cycle)

        return tuple(cycles)


# =============================================================================
# 2. Simplicial 1-Cochain (Exact Rational Values)
# =============================================================================

@dataclass(frozen=True)
class Simplicial1Cochain:
    """Exact rational 1-cochain c: C_1 -> Q assigning values to oriented edges.

    Satisfies anti-symmetry c(v, u) = -c(u, v). Zero float tolerance.
    """

    claims: dict[tuple[str, str], Fraction]

    def __post_init__(self) -> None:
        # Enforce exact rational Fraction types
        for k, v in self.claims.items():
            if not isinstance(v, Fraction):
                raise TypeError(f"Cochain values must be exact Fraction, got {type(v)} for edge {k}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.claims == other.claims

    def get(self, u: str, v: str) -> Fraction:
        """Returns the cochain evaluation c(u -> v) with anti-symmetry."""
        if (u, v) in self.claims:
            return self.claims[(u, v)]
        if (v, u) in self.claims:
            return -self.claims[(v, u)]
        return Fraction(0)

    def with_update(self, u: str, v: str, val: Fraction) -> "Simplicial1Cochain":
        """Returns a new 1-cochain with an updated edge claim."""
        new_claims = dict(self.claims)
        if (v, u) in new_claims and (u, v) not in new_claims:
            new_claims[(v, u)] = -val
        else:
            new_claims[(u, v)] = val
        return Simplicial1Cochain(new_claims)

    def evaluate_cycle_holonomy(self, cycle: Sequence[tuple[str, str, int]]) -> Fraction:
        """Evaluates holonomy residual r = sum_e sign * c(e) around an oriented cycle."""
        tot = Fraction(0)
        for u, v, sign in cycle:
            edge_val = self.get(u, v)
            tot += Fraction(sign) * edge_val
        return tot

    def cycle_holonomy_sum(
        self,
        cycles: Sequence[Sequence[tuple[str, str, int]]],
    ) -> Fraction:
        """Sum of |holonomy| over the given cycles: sum_k |r_k|.

        Zero exactly when every listed cycle closes. For a fundamental cycle
        basis that means the cochain is a coboundary on the 1-skeleton. A
        positive value depends on which basis was chosen (a cycle and its sum
        with another give different sums for the same cochain), so it is not
        Phi_1 and is not comparable across bases.
        """
        tot = Fraction(0)
        for cyc in cycles:
            r = self.evaluate_cycle_holonomy(cyc)
            tot += abs(r)
        return tot


# =============================================================================
# 3. Cochain Gradient Result Value Object
# =============================================================================

@dataclass(frozen=True)
class CochainGradientResult:
    """Exact rational solution and decoupling guidance for a simplicial complex.

    Enforces Value Object Exact-Type Equality Invariant.
    """

    complex_id: str
    vertex_count: int
    edge_count: int
    cycle_rank: int
    tree_edges: tuple[tuple[str, str], ...]
    chord_edges: tuple[tuple[str, str], ...]
    vertex_potentials: dict[str, Fraction]
    cycle_holonomies: tuple[tuple[str, Fraction], ...]
    chord_gradient_deltas: dict[tuple[str, str], Fraction]
    repaired_cochain: dict[tuple[str, str], Fraction]
    holonomy_sum_before: Fraction
    holonomy_sum_after: Fraction
    is_exact_coboundary: bool
    hint_payload: dict[str, Any]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.complex_id == other.complex_id
            and self.vertex_count == other.vertex_count
            and self.edge_count == other.edge_count
            and self.cycle_rank == other.cycle_rank
            and self.tree_edges == other.tree_edges
            and self.chord_edges == other.chord_edges
            and self.vertex_potentials == other.vertex_potentials
            and self.cycle_holonomies == other.cycle_holonomies
            and self.chord_gradient_deltas == other.chord_gradient_deltas
            and self.repaired_cochain == other.repaired_cochain
            and self.holonomy_sum_before == other.holonomy_sum_before
            and self.holonomy_sum_after == other.holonomy_sum_after
            and self.is_exact_coboundary == other.is_exact_coboundary
            and self.hint_payload == other.hint_payload
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "complex_id": self.complex_id,
            "vertex_count": self.vertex_count,
            "edge_count": self.edge_count,
            "cycle_rank": self.cycle_rank,
            "tree_edges": [list(e) for e in self.tree_edges],
            "chord_edges": [list(e) for e in self.chord_edges],
            "vertex_potentials": {
                k: int(v) if v.denominator == 1 else str(v)
                for k, v in self.vertex_potentials.items()
            },
            "cycle_holonomies": [
                [c, int(v) if v.denominator == 1 else str(v)]
                for c, v in self.cycle_holonomies
            ],
            "chord_gradient_deltas": {
                f"{u}->{v}": int(d) if d.denominator == 1 else str(d)
                for (u, v), d in self.chord_gradient_deltas.items()
            },
            "repaired_cochain": {
                f"{u}->{v}": int(c) if c.denominator == 1 else str(c)
                for (u, v), c in self.repaired_cochain.items()
            },
            "holonomy_sum_before": (
                int(self.holonomy_sum_before)
                if self.holonomy_sum_before.denominator == 1
                else str(self.holonomy_sum_before)
            ),
            "holonomy_sum_after": (
                int(self.holonomy_sum_after)
                if self.holonomy_sum_after.denominator == 1
                else str(self.holonomy_sum_after)
            ),
            "is_exact_coboundary": self.is_exact_coboundary,
            "hint_payload": self.hint_payload,
        }


# =============================================================================
# 4. Exact Rational Cochain Gradient Solver
# =============================================================================

class SimplicialCochainGradientSolver:
    """Computes exact rational cochain gradients, vertex potentials, and chord repairs."""

    @classmethod
    def compute_vertex_potentials(
        cls,
        complex_obj: CochainCarrier,
        tree_edges: Sequence[tuple[str, str]],
        cochain: Simplicial1Cochain,
        root: str | None = None,
    ) -> dict[str, Fraction]:
        """Integrates 1-cochain along tree edges to find 0-cochain vertex potentials f_T: V -> Q."""
        if root is None:
            root = complex_obj.vertices[0]

        potentials: dict[str, Fraction] = {root: Fraction(0)}

        tree_adj: dict[str, list[tuple[str, Fraction, bool]]] = {
            v: [] for v in complex_obj.vertices
        }
        for u, v in tree_edges:
            val = cochain.get(u, v)
            tree_adj[u].append((v, val, True))   # forward: f(v) = f(u) + val
            tree_adj[v].append((u, val, False))  # backward: f(u) = f(v) - val => f(v) = f(u) - val

        queue = deque([root])
        visited: set[str] = {root}

        while queue:
            curr = queue.popleft()
            curr_pot = potentials[curr]
            for nxt, val, is_forward in tree_adj[curr]:
                if nxt not in visited:
                    visited.add(nxt)
                    if is_forward:
                        potentials[nxt] = curr_pot + val
                    else:
                        potentials[nxt] = curr_pot - val
                    queue.append(nxt)

        return potentials

    @classmethod
    def solve_gradient(
        cls,
        complex_obj: CochainCarrier,
        cochain: Simplicial1Cochain,
    ) -> CochainGradientResult:
        """Calculates the discrete cochain gradient and decoupled chord repairs over Q."""
        tree_edges, chord_edges = complex_obj.find_spanning_tree()
        cycles = complex_obj.find_fundamental_cycles(tree_edges, chord_edges)
        potentials = cls.compute_vertex_potentials(complex_obj, tree_edges, cochain)

        # 1. Compute initial cycle holonomies
        cycle_holonomies_list: list[tuple[str, Fraction]] = []
        for idx, cyc in enumerate(cycles):
            r = cochain.evaluate_cycle_holonomy(cyc)
            chord = chord_edges[idx]
            name = f"C_{chord[0]}->{chord[1]}"
            cycle_holonomies_list.append((name, r))

        holonomy_sum_before = sum((abs(r) for _, r in cycle_holonomies_list), Fraction(0))

        # 2. Derive exact coboundary chord claims and deltas
        chord_gradient_deltas: dict[tuple[str, str], Fraction] = {}
        repaired_claims: dict[tuple[str, str], Fraction] = dict(cochain.claims)

        for u, v in chord_edges:
            # Coboundary formula: c*(u -> v) = f_T(v) - f_T(u)
            target_val = potentials[v] - potentials[u]
            curr_val = cochain.get(u, v)
            delta = target_val - curr_val
            chord_gradient_deltas[(u, v)] = delta

            if (u, v) in repaired_claims:
                repaired_claims[(u, v)] = target_val
            elif (v, u) in repaired_claims:
                repaired_claims[(v, u)] = -target_val
            else:
                repaired_claims[(u, v)] = target_val

        # 3. Verify all cycle holonomies vanish identically on repaired claims
        repaired_cochain_obj = Simplicial1Cochain(repaired_claims)
        holonomy_sum_after = repaired_cochain_obj.cycle_holonomy_sum(cycles)
        is_exact = (holonomy_sum_after == Fraction(0))

        # 4. Build prompt / candidate guidance hint payload
        proposed_dict: dict[str, int | str] = {}
        for (u, v), val in repaired_claims.items():
            k = f"{u}->{v}"
            proposed_dict[k] = int(val) if val.denominator == 1 else str(val)

        hint_payload = {
            "move_type": "CUT",
            "complex_id": complex_obj.complex_id,
            "cycle_rank": complex_obj.cycle_rank,
            "spanning_tree_edges": [f"{u}->{v}" for u, v in tree_edges],
            "chord_edges": [f"{u}->{v}" for u, v in chord_edges],
            "chord_repairs": {
                f"{u}->{v}": {
                    "current": int(cochain.get(u, v)) if cochain.get(u, v).denominator == 1 else str(cochain.get(u, v)),
                    "target": int(potentials[v] - potentials[u]) if (potentials[v] - potentials[u]).denominator == 1 else str(potentials[v] - potentials[u]),
                    "delta": int(chord_gradient_deltas[(u, v)]) if chord_gradient_deltas[(u, v)].denominator == 1 else str(chord_gradient_deltas[(u, v)]),
                }
                for u, v in chord_edges
            },
            "suggested_cut_claims": proposed_dict,
        }

        return CochainGradientResult(
            complex_id=complex_obj.complex_id,
            vertex_count=complex_obj.vertex_count,
            edge_count=complex_obj.edge_count,
            cycle_rank=complex_obj.cycle_rank,
            tree_edges=tree_edges,
            chord_edges=chord_edges,
            vertex_potentials=potentials,
            cycle_holonomies=tuple(cycle_holonomies_list),
            chord_gradient_deltas=chord_gradient_deltas,
            repaired_cochain=repaired_claims,
            holonomy_sum_before=holonomy_sum_before,
            holonomy_sum_after=holonomy_sum_after,
            is_exact_coboundary=is_exact,
            hint_payload=hint_payload,
        )


__all__ = [
    "CochainGradientResult",
    "Simplicial1Cochain",
    "SimplicialCochainGradientSolver",
    "CochainCarrier",
]
