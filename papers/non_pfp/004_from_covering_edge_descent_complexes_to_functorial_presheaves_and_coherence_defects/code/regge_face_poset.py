"""Finite simplicial face-poset fixtures for the operator cocycle identity.

Comparable-face maps define K = r_ba*r_cb-r_ca, and delta_2 K is zero by
associativity. Rational fixtures need not be orthogonal and contain no metric
edge lengths or dihedral angles. Regge terminology is a model interpretation;
this module does not prove equality with geometric deficit angles or identify
the comparable-triple K with an independently declared loop defect W-I.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Set, Tuple

from covering_edge_poset import CoverEdge, FinitePoset, NodeId
from exact import exact_equal, exact_matrix_from_matrix
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cohomology_quotient import (
    Operator3Cochain,
    build_curvature_operator_cochain,
    verify_unconditional_operator_cocycle,
)


@dataclass(frozen=True)
class Simplex:
    """An abstract simplex represented by a sorted tuple of vertex integers."""

    vertices: Tuple[int, ...]
    dim: int
    id: str

    def __init__(self, vertices: Sequence[int]) -> None:
        sorted_v = tuple(sorted(set(vertices)))
        dim = len(sorted_v) - 1
        prefix = {0: "v", 1: "e", 2: "f", 3: "t", 4: "s4"}.get(dim, f"d{dim}")
        s_id = f"{prefix}_{'_'.join(str(v) for v in sorted_v)}"
        object.__setattr__(self, "vertices", sorted_v)
        object.__setattr__(self, "dim", dim)
        object.__setattr__(self, "id", s_id)

    def faces(self) -> List[Simplex]:
        """Return all codimension-1 sub-simplices."""
        if self.dim == 0:
            return []
        res: List[Simplex] = []
        for i in range(len(self.vertices)):
            sub_v = self.vertices[:i] + self.vertices[i + 1:]
            res.append(Simplex(sub_v))
        return res

    def is_face_of(self, other: Simplex) -> bool:
        """Check if self is a face of other."""
        return set(self.vertices).issubset(set(other.vertices))


@dataclass(frozen=True)
class ReggeHinge:
    """A codimension-2 simplicial hinge h with incident top-dimensional simplices."""

    hinge: Simplex
    incident_simplices: Tuple[Simplex, ...]
    dual_loop_hops: Tuple[Tuple[NodeId, NodeId], ...]


class SimplicialComplex:
    """A collection of simplices closed under taking faces."""

    def __init__(self, top_simplices: Sequence[Sequence[int]]) -> None:
        discovered: Set[Simplex] = set()

        def _add_recursive(s: Simplex) -> None:
            if s in discovered:
                return
            discovered.add(s)
            for f in s.faces():
                _add_recursive(f)

        for v_seq in top_simplices:
            _add_recursive(Simplex(v_seq))

        self.simplices: Tuple[Simplex, ...] = tuple(sorted(discovered, key=lambda s: (s.dim, s.vertices)))
        self.dim: int = max(s.dim for s in self.simplices) if self.simplices else 0

        by_dim: Dict[int, List[Simplex]] = {d: [] for d in range(self.dim + 1)}
        for s in self.simplices:
            by_dim[s.dim].append(s)
        self.simplices_by_dim: Dict[int, Tuple[Simplex, ...]] = {d: tuple(by_dim[d]) for d in by_dim}

    @classmethod
    def triangle_2d(cls) -> SimplicialComplex:
        """Single 2D triangle (0, 1, 2)."""
        return cls([(0, 1, 2)])

    @classmethod
    def tetrahedron_boundary_2d(cls) -> SimplicialComplex:
        """Boundary 2-sphere of standard 3-simplex (4 triangles, 6 edges, 4 vertices)."""
        return cls([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])

    @classmethod
    def equilateral_fan_2d(cls, n_fans: int = 5) -> SimplicialComplex:
        """Disk fan of n triangles sharing central vertex 0 and perimeter vertices 1..n."""
        triangles: List[Tuple[int, int, int]] = []
        for i in range(1, n_fans):
            triangles.append((0, i, i + 1))
        triangles.append((0, n_fans, 1))
        return cls(triangles)

    @classmethod
    def four_simplex_boundary_3d(cls) -> SimplicialComplex:
        """Boundary 3-sphere of standard 4-simplex (5 tetrahedra, 10 triangles, 10 edges, 5 vertices)."""
        # All 5 subsets of 4 vertices from {0, 1, 2, 3, 4}
        all_v = [0, 1, 2, 3, 4]
        tets: List[Tuple[int, ...]] = []
        for i in range(5):
            tets.append(tuple(all_v[:i] + all_v[i + 1:]))
        return cls(tets)

    @classmethod
    def triangulated_hinge_star_4d(cls) -> SimplicialComplex:
        """Star of three 4-simplices meeting around a 2D triangle hinge (0, 1, 2)."""
        # Simplices: (0, 1, 2, 3, 4), (0, 1, 2, 4, 5), (0, 1, 2, 5, 3)
        return cls([
            (0, 1, 2, 3, 4),
            (0, 1, 2, 4, 5),
            (0, 1, 2, 5, 3),
        ])


def build_simplicial_face_poset(complex_data: SimplicialComplex) -> FinitePoset:
    """Build the face poset P(T) where sigma <= tau iff sigma is a sub-simplex of tau.

    Covering edges correspond strictly to codimension-1 attachments: dim(tau) = dim(sigma) + 1.
    """
    elements = [s.id for s in complex_data.simplices]
    relations: List[Tuple[NodeId, NodeId]] = []

    # Codimension-1 face inclusions generate the covering relations
    for s in complex_data.simplices:
        for f in s.faces():
            relations.append((f.id, s.id))

    return FinitePoset(elements=elements, relations=relations)


def build_regge_restriction_system(
    complex_data: SimplicialComplex,
    fiber_dim: int = 3,
    curvature_scale: Optional[Fraction] = None,
) -> RestrictionSystem:
    """Build an exact rational restriction system representing simplicial geometry.

    If curvature_scale is None or 0:
        Produces a flat connection (K = 0 identically).
    If curvature_scale != 0:
        Produces a curved Regge geometry where deficit angles around hinges yield non-zero K.
    """
    poset = build_simplicial_face_poset(complex_data)
    eye = Matrix.eye(fiber_dim)

    # Base identity restrictions for self-loops
    maps: List[RestrictionMap] = [
        RestrictionMap(source=elem, target=elem, matrix=eye) for elem in poset.elements
    ]

    # For each comparable pair lower <= upper
    pairs = poset.comparable_pairs()
    scale = curvature_scale if curvature_scale is not None else Fraction(0)

    for pair in pairs:
        a = pair.lower
        b = pair.upper
        if a == b:
            continue

        # In a flat connection, r_{b, a} = eye
        if scale == Fraction(0):
            mat = Matrix.eye(fiber_dim)
        else:
            # Add a systematic rational rotation/skew proportional to simplex dimension difference
            # ensuring non-zero deficit angles while keeping exact rational entries
            dim_diff = Fraction(abs(len(a) - len(b)), 1)
            mat_data = [
                [
                    Fraction(1) if r == c else (scale * dim_diff if r < c else -scale * dim_diff)
                    for c in range(fiber_dim)
                ]
                for r in range(fiber_dim)
            ]
            mat = Matrix(mat_data)

        maps.append(RestrictionMap(source=b, target=a, matrix=mat))

    fiber_dims = {elem: fiber_dim for elem in poset.elements}
    return RestrictionSystem(poset=poset, fiber_dimensions=fiber_dims, restrictions=maps)


def verify_regge_bianchi_identity(system: RestrictionSystem) -> Tuple[bool, int]:
    """Verify that delta_2(K) == 0 holds identically on all quadruples in the simplicial poset.

    In Regge calculus, this is the discrete Bianchi identity:
        delta_2(K) = 0  <=>  vec_prod_{h in boundary(v^*)} R(h) = I.
    """
    is_zero, _ = verify_unconditional_operator_cocycle(system)

    # Count how many quadruples were checked
    quad_count = 0
    poset = system.poset
    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                for d in poset.elements:
                    if poset.is_le(c, d):
                        quad_count += 1

    return is_zero, quad_count


def compute_hinge_holonomy_product(
    system: RestrictionSystem,
    dual_loop_hops: Sequence[Tuple[NodeId, NodeId]],
) -> Matrix:
    """Compute the ordered product of transports along a closed dual loop circling a hinge:

        R(h) = r_{k, 0} * ... * r_{2, 1} * r_{1, 0}.
    """
    if not dual_loop_hops:
        raise ValueError("dual_loop_hops cannot be empty")

    dim = system.fiber_dimensions[dual_loop_hops[0][0]]
    prod = Matrix.eye(dim)

    for src, tgt in dual_loop_hops:
        r_map = system.get_restriction(target=tgt, source=src)
        prod = r_map.matrix * prod

    return prod
