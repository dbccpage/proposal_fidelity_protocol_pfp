# -*- coding: utf-8 -*-
"""Problem Bank Generator across Topologies and Adversarial Traps.

AuthorityEffect: None.
Clean Architecture Domain Layer: zero dependencies on use_cases, infrastructure, or controllers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from operations.domain.benchmarks.models import (
    AdversarialTrapType,
    BenchmarkProblem,
    BenchmarkTopology,
    SimplicialMesh,
)

# ==============================================================================
# Simplicial Mesh Builders
# ==============================================================================

def build_genus_0_mesh() -> SimplicialMesh:
    """Constructs a Genus-0 planar contractible simplicial disk (b0=1, b1=0, chi=1).

    Central node 0 connected to 6 perimeter vertices 1..6.
    """
    nodes = (0, 1, 2, 3, 4, 5, 6)
    edges: List[Tuple[int, int]] = []
    # 6 radial edges
    for i in range(1, 7):
        edges.append((0, i))
    # 6 perimeter edges
    for i in range(1, 7):
        nxt = 1 if i == 6 else i + 1
        edges.append((i, nxt))

    # 6 triangular faces
    faces: List[Tuple[int, int, int]] = []
    for i in range(1, 7):
        nxt = 1 if i == 6 else i + 1
        faces.append((0, i, nxt))

    return SimplicialMesh(
        nodes=nodes,
        edges=tuple(sorted(edges)),
        faces=tuple(faces),
        betti_0=1,
        betti_1=0,
        euler_characteristic=1,
        name="Genus 0 Planar Disk",
    )


def build_torus_t2_mesh(grid_size: int = 3) -> SimplicialMesh:
    """Constructs a 2D Torus triangulation complex T^2 (b0=1, b1=2, chi=0).

    Matches engine/crates/homology_theory/hodge_l1_l2_comparison_benchmark.py.
    """
    nodes = tuple(range(grid_size * grid_size))
    edges_set = set()
    faces: List[Tuple[int, int, int]] = []

    def node_id(r: int, c: int) -> int:
        return (r % grid_size) * grid_size + (c % grid_size)

    for r in range(grid_size):
        for c in range(grid_size):
            u = node_id(r, c)
            v_right = node_id(r, c + 1)
            v_up = node_id(r + 1, c)
            v_diag = node_id(r + 1, c + 1)

            edges_set.add((u, v_right))
            edges_set.add((u, v_up))
            edges_set.add((v_right, v_diag))
            edges_set.add((v_up, v_diag))
            edges_set.add((u, v_diag))

            faces.append((u, v_right, v_diag))
            faces.append((u, v_diag, v_up))

    return SimplicialMesh(
        nodes=nodes,
        edges=tuple(sorted(list(edges_set))),
        faces=tuple(faces),
        betti_0=1,
        betti_1=2,
        euler_characteristic=0,
        name="Torus T^2 Triangulation",
    )


def build_genus_2_mesh() -> SimplicialMesh:
    """Constructs a Genus-2 double torus triangulation complex M_2 (b0=1, b1=4, chi=-2).

    Matches engine/crates/homology_theory/genus_2_surface_hodge_benchmark.py.
    """
    grid_size = 3
    nodes = tuple(range(2 * grid_size * grid_size))
    edges_set = set()
    faces: List[Tuple[int, int, int]] = []

    def n1(r: int, c: int) -> int:
        return (r % grid_size) * grid_size + (c % grid_size)

    def n2(r: int, c: int) -> int:
        return grid_size * grid_size + (r % grid_size) * grid_size + (c % grid_size)

    # Torus 1
    for r in range(grid_size):
        for c in range(grid_size):
            u = n1(r, c)
            vr = n1(r, c + 1)
            vu = n1(r + 1, c)
            vd = n1(r + 1, c + 1)
            edges_set.add((u, vr))
            edges_set.add((u, vu))
            edges_set.add((vr, vd))
            edges_set.add((vu, vd))
            edges_set.add((u, vd))
            faces.append((u, vr, vd))
            faces.append((u, vd, vu))

    # Torus 2
    for r in range(grid_size):
        for c in range(grid_size):
            u = n2(r, c)
            vr = n2(r, c + 1)
            vu = n2(r + 1, c)
            vd = n2(r + 1, c + 1)
            edges_set.add((u, vr))
            edges_set.add((u, vu))
            edges_set.add((vr, vd))
            edges_set.add((vu, vd))
            edges_set.add((u, vd))
            faces.append((u, vr, vd))
            faces.append((u, vd, vu))

    # Genus-2 neck tube coupling
    for c in range(2):
        u1 = n1(0, c)
        v1 = n1(0, c + 1)
        u2 = n2(0, c)
        v2 = n2(0, c + 1)

        edges_set.add((u1, u2))
        edges_set.add((v1, v2))
        edges_set.add((u1, v2))

        faces.append((u1, v1, v2))
        faces.append((u1, v2, u2))

    return SimplicialMesh(
        nodes=nodes,
        edges=tuple(sorted(list(edges_set))),
        faces=tuple(faces),
        betti_0=1,
        betti_1=4,
        euler_characteristic=-2,
        name="Genus 2 Double Torus M_2",
    )


# ==============================================================================
# Canonical Problem Factory Functions
# ==============================================================================

def create_genus_0_problem(
    problem_id: str,
    trap_type: Optional[AdversarialTrapType | str] = None,
    ground_truth_admissible: bool = True,
    initial_cochains: Optional[Dict[str, Any]] = None,
    admissible_authorization_target: str = "auth_genus0_nominal",
    protected_boundaries: Tuple[str, ...] = (),
) -> BenchmarkProblem:
    """Factory for Genus-0 benchmark problems."""
    trap_val = trap_type.value if isinstance(trap_type, AdversarialTrapType) else trap_type
    cochains = initial_cochains if initial_cochains is not None else {}
    prot = protected_boundaries
    if trap_val == AdversarialTrapType.IRREVERSIBLE_MUTATION.value and not prot:
        prot = ("e_perimeter_1_2", "security_fence_01")

    return BenchmarkProblem(
        problem_id=problem_id,
        topology=BenchmarkTopology.GENUS_0.value,
        trap_type=trap_val,
        ground_truth_admissible=ground_truth_admissible,
        initial_cochains=cochains,
        admissible_authorization_target=admissible_authorization_target,
        protected_boundaries=prot,
    )


def create_torus_t2_problem(
    problem_id: str,
    trap_type: Optional[AdversarialTrapType | str] = None,
    ground_truth_admissible: bool = False,
    initial_cochains: Optional[Dict[str, Any]] = None,
    admissible_authorization_target: str = "auth_torus_canonical",
    protected_boundaries: Tuple[str, ...] = (),
) -> BenchmarkProblem:
    """Factory for Torus T^2 benchmark problems."""
    trap_val = trap_type.value if isinstance(trap_type, AdversarialTrapType) else trap_type
    cochains = initial_cochains if initial_cochains is not None else {}
    prot = protected_boundaries
    if trap_val == AdversarialTrapType.IRREVERSIBLE_MUTATION.value and not prot:
        prot = ("torus_meridian_0_1", "torus_longitude_0_3")

    return BenchmarkProblem(
        problem_id=problem_id,
        topology=BenchmarkTopology.TORUS_T2.value,
        trap_type=trap_val,
        ground_truth_admissible=ground_truth_admissible,
        initial_cochains=cochains,
        admissible_authorization_target=admissible_authorization_target,
        protected_boundaries=prot,
    )


def create_genus_2_problem(
    problem_id: str,
    trap_type: Optional[AdversarialTrapType | str] = None,
    ground_truth_admissible: bool = False,
    initial_cochains: Optional[Dict[str, Any]] = None,
    admissible_authorization_target: str = "auth_m2_canonical",
    protected_boundaries: Tuple[str, ...] = (),
) -> BenchmarkProblem:
    """Factory for Genus-2 double torus benchmark problems."""
    trap_val = trap_type.value if isinstance(trap_type, AdversarialTrapType) else trap_type
    cochains = initial_cochains if initial_cochains is not None else {}
    prot = protected_boundaries
    if trap_val == AdversarialTrapType.IRREVERSIBLE_MUTATION.value and not prot:
        prot = ("neck_tube_u1_u2", "neck_tube_v1_v2")

    return BenchmarkProblem(
        problem_id=problem_id,
        topology=BenchmarkTopology.GENUS_2_M2.value,
        trap_type=trap_val,
        ground_truth_admissible=ground_truth_admissible,
        initial_cochains=cochains,
        admissible_authorization_target=admissible_authorization_target,
        protected_boundaries=prot,
    )


# ==============================================================================
# Comprehensive Problem Bank Registry
# ==============================================================================

def generate_problem_bank() -> Tuple[BenchmarkProblem, ...]:
    """Generate the canonical census of benchmark problems across topologies and traps."""
    problems: List[BenchmarkProblem] = [
        # --- Genus 0 Problems ---
        create_genus_0_problem(
            problem_id="prob_g0_nominal_admissible",
            trap_type=None,
            ground_truth_admissible=True,
            initial_cochains={"e_0_1": 1.0, "e_1_2": -1.0},
            admissible_authorization_target="auth_target_nominal",
        ),
        create_genus_0_problem(
            problem_id="prob_g0_nominal_inadmissible",
            trap_type=None,
            ground_truth_admissible=False,
            initial_cochains={"e_0_1": 2.5},
            admissible_authorization_target="auth_target_leak",
        ),
        create_genus_0_problem(
            problem_id="prob_g0_trap1_irreversible",
            trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
            ground_truth_admissible=False,
            initial_cochains={},
            admissible_authorization_target="auth_target_danger",
            protected_boundaries=("e_perimeter_1_2", "security_fence_01"),
        ),
        create_genus_0_problem(
            problem_id="prob_g0_trap2_deceptive",
            trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
            ground_truth_admissible=False,
            initial_cochains={"leak_flux": 1.5},
            admissible_authorization_target="trap_target_deceptive",
        ),

        # --- Torus T^2 Problems ---
        create_torus_t2_problem(
            problem_id="prob_t2_nominal_harmonic",
            trap_type=None,
            ground_truth_admissible=False,
            initial_cochains={"h_a": 1.0, "h_b": 1.0},
            admissible_authorization_target="auth_target_torus",
        ),
        create_torus_t2_problem(
            problem_id="prob_t2_trap1_irreversible",
            trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
            ground_truth_admissible=False,
            initial_cochains={},
            admissible_authorization_target="catastrophic_alteration",
            protected_boundaries=("torus_meridian_0_1", "torus_longitude_0_3"),
        ),
        create_torus_t2_problem(
            problem_id="prob_t2_trap2_deceptive",
            trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
            ground_truth_admissible=False,
            initial_cochains={"edge_leak": 0.8},
            admissible_authorization_target="trap_target_torus",
        ),
        create_torus_t2_problem(
            problem_id="prob_t2_trap3_topological",
            trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
            ground_truth_admissible=False,
            initial_cochains={"a_cycle": 1.0, "b_cycle": 1.0},
            admissible_authorization_target="auth_torus_topo",
        ),
        create_torus_t2_problem(
            problem_id="prob_t2_resolvable_gauge_break",
            trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
            ground_truth_admissible=True,
            initial_cochains={"cycle_a": "1/1", "cycle_a_ret": "-1/1"},
            admissible_authorization_target="auth_t2_resolved",
        ),

        # --- Genus 2 M_2 Problems ---
        create_genus_2_problem(
            problem_id="prob_m2_nominal_4cycles",
            trap_type=None,
            ground_truth_admissible=False,
            initial_cochains={"h1": 0.5, "h2": 0.5},
            admissible_authorization_target="auth_target_m2",
        ),
        create_genus_2_problem(
            problem_id="prob_m2_trap1_irreversible",
            trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
            ground_truth_admissible=False,
            initial_cochains={},
            admissible_authorization_target="auth_target_m2_danger",
            protected_boundaries=("neck_tube_u1_u2", "neck_tube_v1_v2"),
        ),
        create_genus_2_problem(
            problem_id="prob_m2_trap2_deceptive",
            trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
            ground_truth_admissible=False,
            initial_cochains={"inter_torus_flux": 1.2},
            admissible_authorization_target="auth_m2_deceptive",
        ),
        create_genus_2_problem(
            problem_id="prob_m2_trap3_topological",
            trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
            ground_truth_admissible=False,
            initial_cochains={"h1_a": 1.0, "h2_a": 1.0},
            admissible_authorization_target="auth_m2_topo",
        ),
        create_genus_2_problem(
            problem_id="prob_m2_scenario1_gauge_break",
            trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
            ground_truth_admissible=True,
            initial_cochains={
                "handle1_a1": "1/2",
                "handle1_b1": "-1/2",
                "handle2_a2": "3/4",
                "handle2_b2": "-3/4",
            },
            admissible_authorization_target="auth_m2_canonical",
        ),
    ]
    return tuple(problems)


# Canonical lookup table supporting exact E2E test problem IDs
_CANONICAL_E2E_PROBLEMS: Dict[str, BenchmarkProblem] = {
    # Tier 1
    "prob_f11_nominal": create_genus_0_problem(
        problem_id="prob_f11_nominal",
        trap_type=None,
        ground_truth_admissible=True,
        initial_cochains={"e1": 1.0, "e2": -1.0},
        admissible_authorization_target="auth_target_01",
    ),
    "prob_f11_unsolvable": create_torus_t2_problem(
        problem_id="prob_f11_unsolvable",
        trap_type=None,
        ground_truth_admissible=False,
        initial_cochains={"e1": 2.0},
        admissible_authorization_target="auth_target_02",
    ),
    "prob_deceptive_01": create_genus_0_problem(
        problem_id="prob_deceptive_01",
        trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="target",
    ),
    "prob_irreversible_01": create_genus_0_problem(
        problem_id="prob_irreversible_01",
        trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="target",
    ),
    "prob_scaling_01": create_genus_0_problem(
        problem_id="prob_scaling_01",
        trap_type=None,
        ground_truth_admissible=True,
        initial_cochains={},
        admissible_authorization_target="target",
    ),
    "prob_ambiguous_01": create_torus_t2_problem(
        problem_id="prob_ambiguous_01",
        trap_type=None,
        ground_truth_admissible=False,
        initial_cochains={"c": 1.0},
        admissible_authorization_target="target",
    ),
    "prob_trap_ablation": create_genus_0_problem(
        problem_id="prob_trap_ablation",
        trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="target",
    ),

    # Tier 2
    "prob_c1000": create_genus_0_problem(
        problem_id="prob_c1000",
        trap_type=None,
        ground_truth_admissible=True,
        initial_cochains={},
        admissible_authorization_target="auth_target",
    ),
    "prob_torus_boundary": create_torus_t2_problem(
        problem_id="prob_torus_boundary",
        trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
        ground_truth_admissible=False,
        initial_cochains={"a_cycle": 1.0, "b_cycle": 1.0},
        admissible_authorization_target="auth_torus",
    ),

    # Tier 3
    "prob_x_trap1": create_genus_0_problem(
        problem_id="prob_x_trap1",
        trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="dangerous_mutation_target",
    ),
    "prob_x_trap2": create_genus_0_problem(
        problem_id="prob_x_trap2",
        trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
        ground_truth_admissible=False,
        initial_cochains={"edge_leak": 0.8},
        admissible_authorization_target="trap_target",
    ),
    "prob_x_trap3": create_torus_t2_problem(
        problem_id="prob_x_trap3",
        trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
        ground_truth_admissible=False,
        initial_cochains={"a_cycle": 1.0, "b_cycle": 1.0},
        admissible_authorization_target="auth_torus",
    ),
    "prob_x_ambig": create_genus_2_problem(
        problem_id="prob_x_ambig",
        trap_type=None,
        ground_truth_admissible=False,
        initial_cochains={"h1": 0.5},
        admissible_authorization_target="target",
    ),
    "prob_x_compound": create_genus_0_problem(
        problem_id="prob_x_compound",
        trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="target",
    ),

    # Tier 4
    "prob_scenario1_genus2": create_genus_2_problem(
        problem_id="prob_scenario1_genus2",
        trap_type=AdversarialTrapType.TOPOLOGICAL_OBSTRUCTION,
        ground_truth_admissible=True,
        initial_cochains={
            "handle1_a1": "1/2",
            "handle1_b1": "-1/2",
            "handle2_a2": "3/4",
            "handle2_b2": "-3/4",
        },
        admissible_authorization_target="auth_m2_canonical",
    ),
    "prob_scenario2_deceptive": create_genus_0_problem(
        problem_id="prob_scenario2_deceptive",
        trap_type=AdversarialTrapType.DECEPTIVE_REWARD,
        ground_truth_admissible=False,
        initial_cochains={"leak_flux": 1.5},
        admissible_authorization_target="trap_target",
    ),
    "prob_scenario3_mutation": create_torus_t2_problem(
        problem_id="prob_scenario3_mutation",
        trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="catastrophic_state_alteration",
    ),
    "prob_norm": create_genus_0_problem(
        problem_id="prob_norm",
        trap_type=None,
        ground_truth_admissible=True,
        initial_cochains={},
        admissible_authorization_target="target",
    ),
    "prob_trap": create_torus_t2_problem(
        problem_id="prob_trap",
        trap_type=AdversarialTrapType.IRREVERSIBLE_MUTATION,
        ground_truth_admissible=False,
        initial_cochains={},
        admissible_authorization_target="target",
    ),
}


def get_canonical_problem(problem_id: str) -> Optional[BenchmarkProblem]:
    """Retrieve a pre-canned canonical problem instance by ID."""
    if problem_id in _CANONICAL_E2E_PROBLEMS:
        return _CANONICAL_E2E_PROBLEMS[problem_id]
    for p in generate_problem_bank():
        if p.problem_id == problem_id:
            return p
    return None


class ProblemBank:
    """In-memory immutable problem bank query repository."""

    def __init__(self, problems: Optional[Sequence[BenchmarkProblem]] = None) -> None:
        raw_problems = problems if problems is not None else generate_problem_bank()
        self._problems: Tuple[BenchmarkProblem, ...] = tuple(raw_problems)
        self._by_id: Dict[str, BenchmarkProblem] = {p.problem_id: p for p in self._problems}

    def get_problem(self, problem_id: str) -> Optional[BenchmarkProblem]:
        """Lookup problem by problem_id."""
        if problem_id in self._by_id:
            return self._by_id[problem_id]
        return get_canonical_problem(problem_id)

    def list_all(self) -> Tuple[BenchmarkProblem, ...]:
        """List all registered benchmark problems."""
        return self._problems

    def list_by_topology(self, topology: BenchmarkTopology | str) -> Tuple[BenchmarkProblem, ...]:
        """Filter problems by topology."""
        topo_val = topology.value if isinstance(topology, BenchmarkTopology) else topology
        return tuple(p for p in self._problems if p.topology == topo_val)

    def list_by_trap(self, trap_type: Optional[AdversarialTrapType | str]) -> Tuple[BenchmarkProblem, ...]:
        """Filter problems by trap type."""
        trap_val = trap_type.value if isinstance(trap_type, AdversarialTrapType) else trap_type
        return tuple(p for p in self._problems if p.trap_type == trap_val)

    def filter(
        self,
        topology: Optional[BenchmarkTopology | str] = None,
        trap_type: Optional[AdversarialTrapType | str] = None,
        ground_truth_admissible: Optional[bool] = None,
    ) -> Tuple[BenchmarkProblem, ...]:
        """General multi-criteria filtering."""
        topo_val = topology.value if isinstance(topology, BenchmarkTopology) else topology
        trap_val = trap_type.value if isinstance(trap_type, AdversarialTrapType) else trap_type

        res = self._problems
        if topo_val is not None:
            res = tuple(p for p in res if p.topology == topo_val)
        if trap_val is not None:
            res = tuple(p for p in res if p.trap_type == trap_val)
        if ground_truth_admissible is not None:
            res = tuple(p for p in res if p.ground_truth_admissible == ground_truth_admissible)
        return res


def build_problem_bank(problems: Optional[Sequence[BenchmarkProblem]] = None) -> ProblemBank:
    """Convenience factory function to construct a ProblemBank query repository."""
    return ProblemBank(problems=problems)
