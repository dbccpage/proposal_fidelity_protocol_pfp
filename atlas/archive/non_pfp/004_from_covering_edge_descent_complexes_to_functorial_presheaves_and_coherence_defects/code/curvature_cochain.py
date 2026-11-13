"""Curvature cochain K, Theorem 3.2 closure identity d_1 d_0 = K, and Theorem 3.4 d_2 K boundary for PO-001.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from exact import (
    ExactInput,
    as_rational,
    exact_equal,
    exact_matrix_from_matrix,
    l1_norm,
)
from exactsym import Basic, Matrix, simplify

from covering_edge_poset import FinitePoset, NodeId
from restriction_system import RestrictionSystem
from cochain_complex import Cochain1, Cochain2, Section0Cochain, coboundary_d0, coboundary_d1


@dataclass(frozen=True)
class CurvatureOperator:
    """The curvature operator K_{c, b, a}: F(c) -> F(a) along a <= b <= c.
    
    Defined as K_{c, b, a} = r_{b, a} * r_{c, b} - r_{c, a}.
    """

    bottom: NodeId  # a
    middle: NodeId  # b
    top: NodeId     # c
    matrix: Matrix  # shape: (dim F(a), dim F(c))

    def __post_init__(self) -> None:
        object.__setattr__(self, "matrix", exact_matrix_from_matrix(self.matrix))

    def __call__(self, vector: Matrix) -> Matrix:
        """Apply curvature operator to section value s(c) in F(c)."""
        return self.matrix * vector

    def is_zero(self) -> bool:
        """Check if curvature operator is identically zero."""
        return exact_equal(self.matrix, Matrix.zeros(*self.matrix.shape))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CurvatureOperator):
            return False
        return (
            self.bottom == other.bottom
            and self.middle == other.middle
            and self.top == other.top
            and exact_equal(self.matrix, other.matrix)
        )


def compute_curvature_operator(
    system: RestrictionSystem,
    a: NodeId,
    b: NodeId,
    c: NodeId,
) -> CurvatureOperator:
    """Compute K_{c, b, a} = r_{b, a} * r_{c, b} - r_{c, a} for a <= b <= c."""
    poset = system.poset
    if not (poset.is_le(a, b) and poset.is_le(b, c)):
        raise ValueError(f"nodes ({a}, {b}, {c}) do not satisfy a <= b <= c")

    r_ba = system.get_restriction(target=a, source=b)
    r_cb = system.get_restriction(target=b, source=c)
    r_ca = system.get_restriction(target=a, source=c)

    comp = r_ba.matrix * r_cb.matrix
    k_mat = comp - r_ca.matrix
    return CurvatureOperator(bottom=a, middle=b, top=c, matrix=k_mat)


def compute_all_curvature_operators(system: RestrictionSystem) -> dict[tuple[NodeId, NodeId, NodeId], CurvatureOperator]:
    """Compute K_{c, b, a} for all triples a <= b <= c in the poset."""
    poset = system.poset
    operators: dict[tuple[NodeId, NodeId, NodeId], CurvatureOperator] = {}

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                operators[(a, b, c)] = compute_curvature_operator(system, a, b, c)

    return operators


def is_flat_system(system: RestrictionSystem) -> bool:
    """Check if restriction system is flat (K_{c, b, a} == 0 for all a <= b <= c)."""
    operators = compute_all_curvature_operators(system)
    return all(op.is_zero() for op in operators.values())


def verify_theorem_3_2_pointwise(
    system: RestrictionSystem,
    s: Section0Cochain,
    a: NodeId,
    b: NodeId,
    c: NodeId,
) -> tuple[bool, Matrix, Matrix]:
    """Verify Theorem 3.2 pointwise for triple a <= b <= c:
    
    (d_1 (d_0 s))(a, b, c) == K_{c, b, a}(s(c)).
    Returns (matches, d1_d0_val, k_val).
    """
    g = coboundary_d0(system, s)
    h = coboundary_d1(system, g)
    d1_d0_val = h(a, b, c)

    k_op = compute_curvature_operator(system, a, b, c)
    k_val = k_op(s(c))

    matches = exact_equal(d1_d0_val, k_val)
    return matches, d1_d0_val, k_val


def verify_theorem_3_2_all_triples(
    system: RestrictionSystem,
    s: Section0Cochain,
) -> bool:
    """Verify Theorem 3.2 across all comparable triples in the poset."""
    poset = system.poset
    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                matches, _, _ = verify_theorem_3_2_pointwise(system, s, a, b, c)
                if not matches:
                    return False
    return True


def evaluate_d2_boundary(
    system: RestrictionSystem,
    a: NodeId,
    b: NodeId,
    c: NodeId,
    d: NodeId,
    s_d: Matrix,
    s_c: Matrix,
) -> tuple[Matrix, Matrix]:
    """Evaluate degree-3 boundary formula (Theorem 3.4) on quadruple a <= b <= c <= d:
    
    d_2(K_{d, c, b}(s_d), K_{d, c, a}(s_d), K_{d, b, a}(s_d), K_{c, b, a}(s_c))
    = r_{b, a}(K_{d, c, b}(s_d)) - K_{d, c, a}(s_d) + K_{d, b, a}(s_d) - K_{c, b, a}(s_c).
    
    Theorem 3.4 proves this equals:
    K_{c, b, a}(r_{d, c}(s_d)) - K_{c, b, a}(s_c).
    
    Returns (d2_result, lower_curvature_difference).
    """
    poset = system.poset
    if not (poset.is_le(a, b) and poset.is_le(b, c) and poset.is_le(c, d)):
        raise ValueError(f"nodes ({a}, {b}, {c}, {d}) do not satisfy a <= b <= c <= d")

    k_dcb = compute_curvature_operator(system, b, c, d)
    k_dca = compute_curvature_operator(system, a, c, d)
    k_dba = compute_curvature_operator(system, a, b, d)
    k_cba = compute_curvature_operator(system, a, b, c)

    r_ba = system.get_restriction(target=a, source=b)
    r_dc = system.get_restriction(target=c, source=d)

    h_dcb = k_dcb(s_d)
    h_dca = k_dca(s_d)
    h_dba = k_dba(s_d)
    h_cba = k_cba(s_c)

    d2_val = r_ba(h_dcb) - h_dca + h_dba - h_cba
    lower_diff = k_cba(r_dc(s_d)) - k_cba(s_c)

    return d2_val, lower_diff
