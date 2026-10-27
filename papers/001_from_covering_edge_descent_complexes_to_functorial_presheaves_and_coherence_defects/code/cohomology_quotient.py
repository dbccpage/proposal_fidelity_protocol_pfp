"""Typed operator-cochain diagnostics for PO-001.

The historical filename is retained for deposit compatibility.  This module:
1. Graded operator-cochain sequence C^*(P, Hom):
   - C^1(P, Hom): T_{b, a}: F(b) -> F(a) for a <= b
   - C^2(P, Hom): H_{c, b, a}: F(c) -> F(a) for a <= b <= c
   - C^3(P, Hom): Omega_{d, c, b, a}: F(d) -> F(a) for a <= b <= c <= d
2. Operator differentials:
   - (delta_1 T)_{c, b, a} = r_{b, a} * T_{c, b} - T_{c, a} + T_{b, a} * r_{c, b}
   - (delta_2 H)_{d, c, b, a} = r_{b, a} * H_{d, c, b} - H_{d, c, a} + H_{d, b, a} - H_{c, b, a} * r_{d, c}
3. Exact cocycle identity:
   - delta_2(K) == 0 holds identically and unconditionally for all quadruples a <= b <= c <= d
     without requiring edge compatibility on sections.
4. Exact image-membership diagnostics for im(delta_1).

For a non-flat restriction system, delta_2(delta_1(T)) need not vanish, so
im(delta_1) is not generally contained in ker(delta_2).  Accordingly, the
generic H^2 quotient and gauge-rectification claims remain open.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from covering_edge_poset import FinitePoset, NodeId
from curvature_cochain import CurvatureOperator, compute_curvature_operator
from exact import exact_equal, exact_matrix_from_matrix
from exactsym import Matrix
from restriction_system import RestrictionSystem


@dataclass(frozen=True)
class Operator1Cochain:
    """An operator 1-cochain T assigning T_{b, a}: F(b) -> F(a) to each comparable pair a <= b."""

    poset: FinitePoset
    operators: Dict[Tuple[NodeId, NodeId], Matrix]

    def __post_init__(self) -> None:
        cleaned = {k: exact_matrix_from_matrix(v) for k, v in self.operators.items()}
        object.__setattr__(self, "operators", cleaned)

    def __call__(self, a: NodeId, b: NodeId) -> Matrix:
        if not self.poset.is_le(a, b):
            raise ValueError(f"pair ({a}, {b}) not comparable with a <= b")
        return self.operators[(a, b)]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Operator1Cochain):
            return False
        if self.poset != other.poset:
            return False
        if set(self.operators.keys()) != set(other.operators.keys()):
            return False
        return all(exact_equal(self.operators[k], other.operators[k]) for k in self.operators)


@dataclass(frozen=True)
class Operator2Cochain:
    """An operator 2-cochain H assigning H_{c, b, a}: F(c) -> F(a) to each triple a <= b <= c."""

    poset: FinitePoset
    operators: Dict[Tuple[NodeId, NodeId, NodeId], Matrix]

    def __post_init__(self) -> None:
        cleaned = {k: exact_matrix_from_matrix(v) for k, v in self.operators.items()}
        object.__setattr__(self, "operators", cleaned)

    def __call__(self, a: NodeId, b: NodeId, c: NodeId) -> Matrix:
        if not (self.poset.is_le(a, b) and self.poset.is_le(b, c)):
            raise ValueError(f"triple ({a}, {b}, {c}) not comparable")
        return self.operators[(a, b, c)]

    def is_zero(self) -> bool:
        return all(exact_equal(m, Matrix.zeros(*m.shape)) for m in self.operators.values())

    def __add__(self, other: Operator2Cochain) -> Operator2Cochain:
        if type(self) is not type(other) or self.poset != other.poset:
            raise TypeError("Cannot add incompatible Operator2Cochains")
        res = {k: self.operators[k] + other.operators[k] for k in self.operators}
        return Operator2Cochain(poset=self.poset, operators=res)

    def __sub__(self, other: Operator2Cochain) -> Operator2Cochain:
        if type(self) is not type(other) or self.poset != other.poset:
            raise TypeError("Cannot subtract incompatible Operator2Cochains")
        res = {k: self.operators[k] - other.operators[k] for k in self.operators}
        return Operator2Cochain(poset=self.poset, operators=res)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Operator2Cochain):
            return False
        if self.poset != other.poset:
            return False
        if set(self.operators.keys()) != set(other.operators.keys()):
            return False
        return all(exact_equal(self.operators[k], other.operators[k]) for k in self.operators)


@dataclass(frozen=True)
class Operator3Cochain:
    """An operator 3-cochain Omega assigning Omega_{d, c, b, a}: F(d) -> F(a) to each quadruple a <= b <= c <= d."""

    poset: FinitePoset
    operators: Dict[Tuple[NodeId, NodeId, NodeId, NodeId], Matrix]

    def __post_init__(self) -> None:
        cleaned = {k: exact_matrix_from_matrix(v) for k, v in self.operators.items()}
        object.__setattr__(self, "operators", cleaned)

    def __call__(self, a: NodeId, b: NodeId, c: NodeId, d: NodeId) -> Matrix:
        if not (self.poset.is_le(a, b) and self.poset.is_le(b, c) and self.poset.is_le(c, d)):
            raise ValueError(f"quadruple ({a}, {b}, {c}, {d}) not comparable")
        return self.operators[(a, b, c, d)]

    def is_zero(self) -> bool:
        return all(exact_equal(m, Matrix.zeros(*m.shape)) for m in self.operators.values())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Operator3Cochain):
            return False
        if self.poset != other.poset:
            return False
        if set(self.operators.keys()) != set(other.operators.keys()):
            return False
        return all(exact_equal(self.operators[k], other.operators[k]) for k in self.operators)


def operator_coboundary_delta1(
    system: RestrictionSystem,
    t: Operator1Cochain,
) -> Operator2Cochain:
    """Compute operator coboundary delta_1: C^1(P, Hom) -> C^2(P, Hom).
    
    (delta_1 T)_{c, b, a} = r_{b, a} * T_{c, b} - T_{c, a} + T_{b, a} * r_{c, b}.
    """
    poset = system.poset
    res: Dict[Tuple[NodeId, NodeId, NodeId], Matrix] = {}

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                r_ba = system.get_restriction(target=a, source=b).matrix
                r_cb = system.get_restriction(target=b, source=c).matrix
                t_cb = t(b, c)
                t_ca = t(a, c)
                t_ba = t(a, b)
                delta1_val = r_ba * t_cb - t_ca + t_ba * r_cb
                res[(a, b, c)] = delta1_val

    return Operator2Cochain(poset=poset, operators=res)


def operator_coboundary_delta2(
    system: RestrictionSystem,
    h: Operator2Cochain,
) -> Operator3Cochain:
    """Compute operator coboundary delta_2: C^2(P, Hom) -> C^3(P, Hom).
    
    (delta_2 H)_{d, c, b, a} = r_{b, a} * H_{d, c, b} - H_{d, c, a} + H_{d, b, a} - H_{c, b, a} * r_{d, c}.
    """
    poset = system.poset
    res: Dict[Tuple[NodeId, NodeId, NodeId, NodeId], Matrix] = {}

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                for d in poset.elements:
                    if not poset.is_le(c, d):
                        continue
                    r_ba = system.get_restriction(target=a, source=b).matrix
                    r_dc = system.get_restriction(target=c, source=d).matrix
                    h_dcb = h(b, c, d)
                    h_dca = h(a, c, d)
                    h_dba = h(a, b, d)
                    h_cba = h(a, b, c)

                    delta2_val = r_ba * h_dcb - h_dca + h_dba - h_cba * r_dc
                    res[(a, b, c, d)] = delta2_val

    return Operator3Cochain(poset=poset, operators=res)


def build_curvature_operator_cochain(system: RestrictionSystem) -> Operator2Cochain:
    """Build the curvature cochain K as an Operator2Cochain."""
    poset = system.poset
    ops: Dict[Tuple[NodeId, NodeId, NodeId], Matrix] = {}

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                cop = compute_curvature_operator(system, a, b, c)
                ops[(a, b, c)] = cop.matrix

    return Operator2Cochain(poset=poset, operators=ops)


def verify_unconditional_operator_cocycle(system: RestrictionSystem) -> Tuple[bool, Operator3Cochain]:
    """Verify Theorem 3.6: delta_2(K) == 0 identically on all quadruples a <= b <= c <= d.
    
    Returns (is_zero, delta2_k).
    """
    k = build_curvature_operator_cochain(system)
    delta2_k = operator_coboundary_delta2(system, k)
    return delta2_k.is_zero(), delta2_k


class OperatorCochainImageDiagnostic:
    """Exact rational diagnostics for the image of delta_1.

    This class does not construct a cohomology quotient.  On a non-flat
    restriction system the declared operators form a curved sequence because
    delta_2 composed with delta_1 may be nonzero.
    """

    def __init__(self, system: RestrictionSystem) -> None:
        self.system = system
        self.poset = system.poset

        # Enumerate basis indices for C^1, C^2, C^3
        self.pairs: List[Tuple[NodeId, NodeId]] = []
        for a in self.poset.elements:
            for b in self.poset.elements:
                if self.poset.is_le(a, b):
                    self.pairs.append((a, b))

        self.triples: List[Tuple[NodeId, NodeId, NodeId]] = []
        for a in self.poset.elements:
            for b in self.poset.elements:
                if not self.poset.is_le(a, b):
                    continue
                for c in self.poset.elements:
                    if self.poset.is_le(b, c):
                        self.triples.append((a, b, c))

        self.quads: List[Tuple[NodeId, NodeId, NodeId, NodeId]] = []
        for a in self.poset.elements:
            for b in self.poset.elements:
                if not self.poset.is_le(a, b):
                    continue
                for c in self.poset.elements:
                    if not self.poset.is_le(b, c):
                        continue
                    for d in self.poset.elements:
                        if self.poset.is_le(c, d):
                            self.quads.append((a, b, c, d))

        # Flatten dimensions
        self.c1_dim = sum(self.system.fiber_dimensions[a] * self.system.fiber_dimensions[b] for a, b in self.pairs)
        self.c2_dim = sum(self.system.fiber_dimensions[a] * self.system.fiber_dimensions[c] for a, b, c in self.triples)
        self.c3_dim = sum(self.system.fiber_dimensions[a] * self.system.fiber_dimensions[d] for a, b, c, d in self.quads)

    def cochain2_to_vector(self, h: Operator2Cochain) -> List[Fraction]:
        """Flatten an Operator2Cochain into a 1D rational vector."""
        vec: List[Fraction] = []
        for a, b, c in self.triples:
            mat = h(a, b, c)
            for r in range(mat.rows):
                for col in range(mat.cols):
                    vec.append(Fraction(mat[r, col]))
        return vec

    def vector_to_cochain2(self, vec: List[Fraction]) -> Operator2Cochain:
        """Unflatten a 1D rational vector back into an Operator2Cochain."""
        idx = 0
        ops: Dict[Tuple[NodeId, NodeId, NodeId], Matrix] = {}
        for a, b, c in self.triples:
            rows = self.system.fiber_dimensions[a]
            cols = self.system.fiber_dimensions[c]
            data = []
            for _ in range(rows):
                row = []
                for _ in range(cols):
                    row.append(vec[idx])
                    idx += 1
                data.append(row)
            ops[(a, b, c)] = Matrix(data)
        return Operator2Cochain(poset=self.poset, operators=ops)

    def compute_coboundary_matrix_delta1(self) -> Matrix:
        """Construct the matrix of delta_1: C^1 -> C^2 over Q."""
        cols: List[List[Fraction]] = []

        for a_p, b_p in self.pairs:
            dim_a = self.system.fiber_dimensions[a_p]
            dim_b = self.system.fiber_dimensions[b_p]
            for r_p in range(dim_a):
                for c_p in range(dim_b):
                    ops: Dict[Tuple[NodeId, NodeId], Matrix] = {}
                    for a, b in self.pairs:
                        if a == a_p and b == b_p:
                            m_data = [[Fraction(1) if i == r_p and j == c_p else Fraction(0)
                                      for j in range(self.system.fiber_dimensions[b])]
                                      for i in range(self.system.fiber_dimensions[a])]
                            ops[(a, b)] = Matrix(m_data)
                        else:
                            ops[(a, b)] = Matrix.zeros(self.system.fiber_dimensions[a], self.system.fiber_dimensions[b])

                    t = Operator1Cochain(poset=self.poset, operators=ops)
                    d1_t = operator_coboundary_delta1(self.system, t)
                    cols.append(self.cochain2_to_vector(d1_t))

        if not cols:
            return Matrix.zeros(self.c2_dim, 0)

        rows: List[List[Fraction]] = []
        for r in range(self.c2_dim):
            rows.append([cols[c][r] for c in range(len(cols))])
        return Matrix(rows)

    def is_coboundary(self, h: Operator2Cochain) -> Tuple[bool, Optional[Operator1Cochain]]:
        """Check if an Operator2Cochain h lies in B^2 = im(delta_1).
        
        Solves delta_1(T) == h over Q via Gaussian elimination.
        Returns (is_in_im, witness_T).
        """
        a_mat = self.compute_coboundary_matrix_delta1()
        b_vec = self.cochain2_to_vector(h)

        sol = _solve_linear_system_exact(a_mat, b_vec)
        if sol is None:
            return False, None

        idx = 0
        t_ops: Dict[Tuple[NodeId, NodeId], Matrix] = {}
        for a, b in self.pairs:
            rows = self.system.fiber_dimensions[a]
            cols = self.system.fiber_dimensions[b]
            data = []
            for _ in range(rows):
                row = []
                for _ in range(cols):
                    row.append(sol[idx])
                    idx += 1
                data.append(row)
            t_ops[(a, b)] = Matrix(data)

        witness = Operator1Cochain(poset=self.poset, operators=t_ops)
        return True, witness

    def is_curvature_trivial(self) -> Tuple[bool, Optional[Operator1Cochain]]:
        """Check whether K lies in im(delta_1); no quotient claim is implied."""
        k = build_curvature_operator_cochain(self.system)
        return self.is_coboundary(k)


def _solve_linear_system_exact(a: Matrix, b: List[Fraction]) -> Optional[List[Fraction]]:
    """Exact Gaussian elimination solving A * x = b over Fraction."""
    rows = a.rows
    cols = a.cols
    if len(b) != rows:
        raise ValueError("dimension mismatch in linear system")

    aug: List[List[Fraction]] = []
    for r in range(rows):
        aug.append([Fraction(a[r, c]) for c in range(cols)] + [Fraction(b[r])])

    lead = 0
    pivots: List[Tuple[int, int]] = []

    for r in range(rows):
        while lead < cols:
            i = r
            while i < rows and aug[i][lead] == 0:
                i += 1
            if i < rows:
                break
            lead += 1
        if lead >= cols:
            break

        aug[r], aug[i] = aug[i], aug[r]
        pivot_val = aug[r][lead]

        for c in range(cols + 1):
            aug[r][c] = aug[r][c] / pivot_val

        for i_row in range(rows):
            if i_row != r:
                factor = aug[i_row][lead]
                if factor != 0:
                    for c in range(cols + 1):
                        aug[i_row][c] = aug[i_row][c] - factor * aug[r][c]

        pivots.append((r, lead))
        lead += 1

    for r in range(rows):
        if all(aug[r][c] == 0 for c in range(cols)):
            if aug[r][cols] != 0:
                return None

    x = [Fraction(0) for _ in range(cols)]
    for r, c in pivots:
        x[c] = aug[r][cols]

    return x
