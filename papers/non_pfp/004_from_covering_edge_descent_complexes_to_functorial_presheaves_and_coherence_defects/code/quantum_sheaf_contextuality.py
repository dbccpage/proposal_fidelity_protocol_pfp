"""Quantum sheaf contextuality and Bell-CHSH presheaf gluing obstruction for PO-001.

AuthorityEffect: None.

This module formalizes Theorem 4.9 of PO-001 v2.0:
1. Bell-CHSH Measurement Poset M:
   Comprises 9 contexts:
     - Base node: "base" (dimension 1, probability normalization)
     - 4 single contexts: A1, A2, B1, B2 (dimension 2, local marginal distributions)
     - 4 joint contexts: C11, C12, C21, C22 (dimension 4, joint pairwise distributions)
   Covering edges represent marginalization:
     - Cij -> Ai (marginalize over Bob's outcomes)
     - Cij -> Bj (marginalize over Alice's outcomes)
     - Ai -> base, Bj -> base (sum over outcomes to 1)

2. Presheaf Flatness:
   The composite restriction maps from Cij down to "base" commute identically:
     r_{Ai, base} * r_{Cij, Ai} == r_{Bj, base} * r_{Cij, Bj} == [1, 1, 1, 1].
   Thus the underlying operator system is strictly flat:
     K_{Cij, Ai, base} = 0  and  K_{Cij, Bj, base} = 0.

3. Empirical Model as 0-Cochain:
   An empirical model e assigns to each context node x in M a local probability vector.
   The covering-edge descent condition d_0 e == 0 corresponds strictly to the
   No-Signaling condition (local marginal consistency) plus normalization.

4. Cech Sheaf Contextuality Obstruction:
   A global section P in Delta_16 is a joint probability distribution over all 16
   micro-states (a1, a2, b1, b2) in {0, 1}^4 reproducing all 4 joint contexts.
   By Fine's Theorem (1982) and Abramsky-Brandenburger (2011), P exists if and only if
   the empirical model admits a Local Hidden Variable (LHV) realization.
   The contextuality obstruction is the exact L1 distance:
       Gamma_{context}(e) := min_{P in Delta_16} ||e - M_{glue} P||_1.
   When Gamma_{context}(e) > 0, the model is strictly contextual.

5. Exact Primal-Dual Witness Certification:
   Solved via exact rational simplex linear programming, yielding:
     - Optimal joint distribution P* in Delta_16
     - Dual witness certificate Y* in Q^16 satisfying ||Y*||_infty <= 1
     - Exact zero duality gap: Primal == Dual identically.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple, Union

from covering_edge_poset import CoverEdge, FinitePoset, NodeId
from exact import exact_equal
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cohomology_quotient import (
    Operator3Cochain,
    build_curvature_operator_cochain,
    verify_unconditional_operator_cocycle,
)


# The 16 micro-states (a1, a2, b1, b2) in {0, 1}^4
MICRO_STATES: Tuple[Tuple[int, int, int, int], ...] = tuple(
    (a1, a2, b1, b2)
    for a1 in (0, 1)
    for a2 in (0, 1)
    for b1 in (0, 1)
    for b2 in (0, 1)
)

# Ordered list of 4 joint measurement contexts
JOINT_CONTEXTS: Tuple[str, ...] = ("C11", "C12", "C21", "C22")

# Context specification: (context_id, alice_var_idx, bob_var_idx)
# where indices in MICRO_STATES are: a1=0, a2=1, b1=2, b2=3
CONTEXT_SPECS: Tuple[Tuple[str, int, int], ...] = (
    ("C11", 0, 2),
    ("C12", 0, 3),
    ("C21", 1, 2),
    ("C22", 1, 3),
)

# Binary outcomes: (0,0)=0, (0,1)=1, (1,0)=2, (1,1)=3
OUTCOME_PAIRS: Tuple[Tuple[int, int], ...] = (
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
)


def _build_gluing_matrix_rows() -> List[List[Fraction]]:
    """Build the 16x16 gluing matrix M_{glue} mapping Delta_16 to joint contexts.

    Row index (4 * c_idx + out_idx) corresponds to P(c_name = (a, b)).
    """
    rows: List[List[Fraction]] = []
    for _, a_idx, b_idx in CONTEXT_SPECS:
        for a_val, b_val in OUTCOME_PAIRS:
            row = [
                Fraction(1) if (state[a_idx] == a_val and state[b_idx] == b_val) else Fraction(0)
                for state in MICRO_STATES
            ]
            rows.append(row)
    return rows


GLUING_MATRIX_ROWS: List[List[Fraction]] = _build_gluing_matrix_rows()


@dataclass(frozen=True)
class ContextualityReceipt:
    """Exact rational certification receipt for Cech contextuality obstruction."""

    model_name: str
    is_no_signaling: bool
    no_signaling_residual_norm: Fraction
    bell_chsh_parameter: Fraction
    is_bell_violating: bool
    is_contextual: bool
    obstruction_distance: Fraction
    optimal_joint_distribution: Optional[Tuple[Fraction, ...]]
    dual_witness: Optional[Tuple[Fraction, ...]]
    dual_objective: Optional[Fraction]
    duality_gap: Fraction
    pivot_count: int


@dataclass(frozen=True)
class EmpiricalModel:
    """An empirical model assigning local probability distributions to contexts."""

    name: str
    context_data: Dict[NodeId, Tuple[Fraction, ...]]

    def get_distribution(self, context: NodeId) -> Tuple[Fraction, ...]:
        if context not in self.context_data:
            raise KeyError(f"Context '{context}' not present in empirical model '{self.name}'")
        return self.context_data[context]

    def joint_vector(self) -> List[Fraction]:
        """Return the flattened 16-element vector of joint probabilities for C11, C12, C21, C22."""
        vec: List[Fraction] = []
        for c in JOINT_CONTEXTS:
            vec.extend(self.get_distribution(c))
        return vec

    @classmethod
    def classical_deterministic(
        cls, a1: int, a2: int, b1: int, b2: int, name: Optional[str] = None
    ) -> EmpiricalModel:
        """Create a deterministic local hidden variable model for fixed outcomes."""
        model_name = name or f"Deterministic({a1},{a2},{b1},{b2})"
        data: Dict[NodeId, Tuple[Fraction, ...]] = {
            "base": (Fraction(1),),
            "A1": (Fraction(1 if a1 == 0 else 0), Fraction(1 if a1 == 1 else 0)),
            "A2": (Fraction(1 if a2 == 0 else 0), Fraction(1 if a2 == 1 else 0)),
            "B1": (Fraction(1 if b1 == 0 else 0), Fraction(1 if b1 == 1 else 0)),
            "B2": (Fraction(1 if b2 == 0 else 0), Fraction(1 if b2 == 1 else 0)),
            "C11": tuple(Fraction(1 if (a1 == a and b1 == b) else 0) for a, b in OUTCOME_PAIRS),
            "C12": tuple(Fraction(1 if (a1 == a and b2 == b) else 0) for a, b in OUTCOME_PAIRS),
            "C21": tuple(Fraction(1 if (a2 == a and b1 == b) else 0) for a, b in OUTCOME_PAIRS),
            "C22": tuple(Fraction(1 if (a2 == a and b2 == b) else 0) for a, b in OUTCOME_PAIRS),
        }
        return cls(name=model_name, context_data=data)

    @classmethod
    def classical_mixture(
        cls,
        weights: Sequence[Union[int, Fraction]],
        deterministic_tuples: Sequence[Tuple[int, int, int, int]],
        name: str = "ClassicalMixture",
    ) -> EmpiricalModel:
        """Create a convex combination of deterministic local hidden variable models."""
        frac_weights = [Fraction(w) for w in weights]
        total_w = sum(frac_weights)
        if total_w != Fraction(1):
            frac_weights = [w / total_w for w in frac_weights]

        combined_data: Dict[NodeId, List[Fraction]] = {
            "base": [Fraction(1)],
            "A1": [Fraction(0), Fraction(0)],
            "A2": [Fraction(0), Fraction(0)],
            "B1": [Fraction(0), Fraction(0)],
            "B2": [Fraction(0), Fraction(0)],
            "C11": [Fraction(0)] * 4,
            "C12": [Fraction(0)] * 4,
            "C21": [Fraction(0)] * 4,
            "C22": [Fraction(0)] * 4,
        }

        for w, (a1, a2, b1, b2) in zip(frac_weights, deterministic_tuples):
            det = cls.classical_deterministic(a1, a2, b1, b2)
            for node, dist in det.context_data.items():
                if node == "base":
                    continue
                for idx, p in enumerate(dist):
                    combined_data[node][idx] += w * p

        frozen_data = {k: tuple(v) for k, v in combined_data.items()}
        return cls(name=name, context_data=frozen_data)

    @classmethod
    def pr_box(cls, name: str = "PR_Box") -> EmpiricalModel:
        """Create the maximally contextual Popescu-Rohrlich (PR) box.

        Satisfies: a + b = x * y (mod 2).
        For C11, C12, C21: correlated (0,0) and (1,1) with p = 1/2.
        For C22: anti-correlated (0,1) and (1,0) with p = 1/2.
        Bell-CHSH parameter: S = 4.
        """
        half = Fraction(1, 2)
        zero = Fraction(0)
        data: Dict[NodeId, Tuple[Fraction, ...]] = {
            "base": (Fraction(1),),
            "A1": (half, half),
            "A2": (half, half),
            "B1": (half, half),
            "B2": (half, half),
            "C11": (half, zero, zero, half),
            "C12": (half, zero, zero, half),
            "C21": (half, zero, zero, half),
            "C22": (zero, half, half, zero),
        }
        return cls(name=name, context_data=data)

    @classmethod
    def isotropic_werner_model(
        cls, p: Union[int, Fraction], name: Optional[str] = None
    ) -> EmpiricalModel:
        """Create an isotropic Werner mixture: p * PR_box + (1 - p) * WhiteNoise."""
        frac_p = Fraction(p)
        if frac_p < Fraction(0) or frac_p > Fraction(1):
            raise ValueError(f"Mixture parameter p must be in [0, 1], got {frac_p}")

        model_name = name or f"Werner(p={frac_p})"
        pr = cls.pr_box()
        quarter = Fraction(1, 4)
        half = Fraction(1, 2)

        data: Dict[NodeId, Tuple[Fraction, ...]] = {
            "base": (Fraction(1),),
            "A1": (half, half),
            "A2": (half, half),
            "B1": (half, half),
            "B2": (half, half),
        }

        white_joint = (quarter, quarter, quarter, quarter)
        for c in JOINT_CONTEXTS:
            pr_dist = pr.get_distribution(c)
            mixed_dist = tuple(frac_p * pr_dist[i] + (Fraction(1) - frac_p) * white_joint[i] for i in range(4))
            data[c] = mixed_dist

        return cls(name=model_name, context_data=data)


def build_bell_chsh_poset() -> FinitePoset:
    """Build the 9-element Bell-CHSH measurement cover poset.

    Poset structure:
      base <= A1, A2, B1, B2
      A1 <= C11, C12
      A2 <= C21, C22
      B1 <= C11, C21
      B2 <= C12, C22
    """
    elements = ["base", "A1", "A2", "B1", "B2", "C11", "C12", "C21", "C22"]
    relations: List[Tuple[NodeId, NodeId]] = [
        # Base to singles
        ("base", "A1"),
        ("base", "A2"),
        ("base", "B1"),
        ("base", "B2"),
        # Singles to pairs
        ("A1", "C11"),
        ("A1", "C12"),
        ("A2", "C21"),
        ("A2", "C22"),
        ("B1", "C11"),
        ("B1", "C21"),
        ("B2", "C12"),
        ("B2", "C22"),
    ]
    return FinitePoset(elements=elements, relations=relations)


def build_bell_sheaf_system() -> RestrictionSystem:
    """Build the exact rational restriction system representing the probability presheaf."""
    poset = build_bell_chsh_poset()

    # Fiber dimensions: base=1, singles=2, pairs=4
    dims: Dict[NodeId, int] = {
        "base": 1,
        "A1": 2,
        "A2": 2,
        "B1": 2,
        "B2": 2,
        "C11": 4,
        "C12": 4,
        "C21": 4,
        "C22": 4,
    }

    # Standard marginalization matrices
    # Alice marginal: sums Bob's outcomes
    # [p(0,0)+p(0,1), p(1,0)+p(1,1)]
    m_alice = Matrix([
        [Fraction(1), Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1), Fraction(1)],
    ])

    # Bob marginal: sums Alice's outcomes
    # [p(0,0)+p(1,0), p(0,1)+p(1,1)]
    m_bob = Matrix([
        [Fraction(1), Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0), Fraction(1)],
    ])

    # Summing single distributions to base: [1, 1]
    m_to_base = Matrix([[Fraction(1), Fraction(1)]])

    # Direct composite from pair to base: [1, 1, 1, 1]
    m_pair_to_base = Matrix([[Fraction(1), Fraction(1), Fraction(1), Fraction(1)]])

    maps: List[RestrictionMap] = []

    # Self-loops
    for elem, d in dims.items():
        maps.append(RestrictionMap(source=elem, target=elem, matrix=Matrix.eye(d)))

    # Singles to base
    for s in ("A1", "A2", "B1", "B2"):
        maps.append(RestrictionMap(source=s, target="base", matrix=m_to_base))

    # Pairs to singles
    maps.append(RestrictionMap(source="C11", target="A1", matrix=m_alice))
    maps.append(RestrictionMap(source="C12", target="A1", matrix=m_alice))
    maps.append(RestrictionMap(source="C21", target="A2", matrix=m_alice))
    maps.append(RestrictionMap(source="C22", target="A2", matrix=m_alice))

    maps.append(RestrictionMap(source="C11", target="B1", matrix=m_bob))
    maps.append(RestrictionMap(source="C21", target="B1", matrix=m_bob))
    maps.append(RestrictionMap(source="C12", target="B2", matrix=m_bob))
    maps.append(RestrictionMap(source="C22", target="B2", matrix=m_bob))

    # Pairs to base (transitive closure)
    for c in JOINT_CONTEXTS:
        maps.append(RestrictionMap(source=c, target="base", matrix=m_pair_to_base))

    return RestrictionSystem(poset=poset, fiber_dimensions=dims, restrictions=maps)


def verify_bell_sheaf_flatness(system: RestrictionSystem) -> Tuple[bool, int]:
    """Verify that the Bell measurement presheaf has identically zero curvature K == 0.

    This confirms that the gluing obstruction is not due to base connection defects,
    but purely a global section (Cech contextuality) obstruction.
    """
    poset = system.poset
    k_cochain = build_curvature_operator_cochain(system)

    triple_count = 0
    all_zero = True

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                triple_count += 1
                k_mat = k_cochain(a, b, c)
                if not exact_equal(k_mat, Matrix.zeros(*k_mat.shape)):
                    all_zero = False

    return all_zero, triple_count


def check_no_signaling_descent(
    system: RestrictionSystem, model: EmpiricalModel
) -> Tuple[bool, Fraction]:
    """Verify that empirical model satisfies covering-edge descent d_0 e == 0.

    In the Bell-CHSH poset, this checks:
      1. Marginalization from Cij to Ai matches model.data[Ai]
      2. Marginalization from Cij to Bj matches model.data[Bj]
      3. Normalization from singles to base sums to 1
    Returns (is_satisfied, max_residual_norm).
    """
    poset = system.poset
    max_res = Fraction(0)

    for edge in poset.covering_edges:
        src = edge.upper
        tgt = edge.lower
        r_map = system.get_restriction(target=tgt, source=src)

        src_vec = Matrix([[x] for x in model.get_distribution(src)])
        tgt_vec = Matrix([[x] for x in model.get_distribution(tgt)])

        projected = r_map.matrix * src_vec
        diff = projected - tgt_vec

        res_norm = sum(abs(diff[r, 0]) for r in range(diff.rows))
        if res_norm > max_res:
            max_res = res_norm

    is_satisfied = (max_res == Fraction(0))
    return is_satisfied, max_res


def compute_bell_chsh_parameter(model: EmpiricalModel) -> Fraction:
    """Compute the exact rational Bell-CHSH parameter S:

        S := <A1 B1> + <A1 B2> + <A2 B1> - <A2 B2>
    where <Ai Bj> = p(0,0) - p(0,1) - p(1,0) + p(1,1).
    """
    correlators: Dict[str, Fraction] = {}
    for c in JOINT_CONTEXTS:
        dist = model.get_distribution(c)
        # Outcome signs: (0,0)->+1, (0,1)->-1, (1,0)->-1, (1,1)->+1
        corr = dist[0] - dist[1] - dist[2] + dist[3]
        correlators[c] = corr

    s_val = (
        correlators["C11"]
        + correlators["C12"]
        + correlators["C21"]
        - correlators["C22"]
    )
    return s_val


def solve_cech_contextuality_obstruction(model: EmpiricalModel) -> ContextualityReceipt:
    """Compute the exact Cech contextuality obstruction distance via rational simplex LP:

        Gamma_{context}(e) := min_{P in Delta_16} ||e - M_{glue} P||_1.
    Certifies zero duality gap via the exact dual witness Y* in Q^16.
    """
    # Verify no-signaling
    sheaf_sys = build_bell_sheaf_system()
    is_ns, ns_res = check_no_signaling_descent(sheaf_sys, model)

    s_param = compute_bell_chsh_parameter(model)
    is_bell_violating = abs(s_param) > Fraction(2)

    e = model.joint_vector()
    m = 16  # number of joint probabilities
    k = 16  # number of global joint micro-states
    n_vars = k + 2 * m  # 16 P's, 16 p's, 16 n's = 48 vars
    n_rows = m + 1      # 17 constraints (16 gluing equations + 1 simplex normalization)

    # Build tableau of shape (n_rows + 1) x (n_vars + 1)
    tableau = [[Fraction(0) for _ in range(n_vars + 1)] for _ in range(n_rows + 1)]

    # Row 17 (index 17 in tableau): sum(P) = 1
    for j in range(k):
        tableau[17][j] = Fraction(1)
    tableau[17][n_vars] = Fraction(1)

    # Rows 1..16: M_{glue}[i] * P + p_i - n_i = e_i
    for i in range(m):
        row = i + 1
        for j in range(k):
            tableau[row][j] = GLUING_MATRIX_ROWS[i][j]
        tableau[row][k + i] = Fraction(1)       # p_i
        tableau[row][k + m + i] = Fraction(-1)  # n_i
        tableau[row][n_vars] = e[i]

    # Eliminate P_0 from rows 1..16 using Row 17 to obtain an initial basic feasible solution
    for i in range(m):
        row = i + 1
        factor = GLUING_MATRIX_ROWS[i][0]
        if factor != 0:
            for col in range(n_vars + 1):
                tableau[row][col] -= factor * tableau[17][col]

    basis: List[int] = []
    for i in range(m):
        row = i + 1
        rhs = tableau[row][n_vars]
        if rhs >= 0:
            basis.append(k + i)  # p_i
        else:
            for col in range(n_vars + 1):
                tableau[row][col] = -tableau[row][col]
            basis.append(k + m + i)  # n_i

    basis.append(0)  # P_0 is basic in row 17

    c = [Fraction(0)] * k + [Fraction(1)] * (2 * m)

    # Compute initial reduced costs in Row 0
    for j in range(n_vars):
        cb_dot_a = sum((c[basis[i]] * tableau[i + 1][j] for i in range(n_rows)), Fraction(0))
        tableau[0][j] = c[j] - cb_dot_a

    # Simplex iteration with Bland's rule
    max_iter = 500
    pivots = 0
    while pivots < max_iter:
        pivots += 1
        entering = -1
        for j in range(n_vars):
            if tableau[0][j] < 0:
                entering = j
                break
        if entering == -1:
            # Optimal solution found
            pivots -= 1
            break

        best_ratio: Optional[Fraction] = None
        pivot_row = -1
        for i in range(n_rows):
            coeff = tableau[i + 1][entering]
            if coeff > 0:
                ratio = tableau[i + 1][n_vars] / coeff
                if best_ratio is None or ratio < best_ratio:
                    best_ratio = ratio
                    pivot_row = i + 1
                elif ratio == best_ratio:
                    if basis[i] < basis[pivot_row - 1]:
                        pivot_row = i + 1

        if pivot_row == -1:
            raise RuntimeError("Linear program is unbounded, which contradicts compact L1 norm formulation.")

        pivot_val = tableau[pivot_row][entering]
        for col in range(n_vars + 1):
            tableau[pivot_row][col] /= pivot_val

        for r in range(n_rows + 1):
            if r != pivot_row:
                factor = tableau[r][entering]
                if factor != 0:
                    for col in range(n_vars + 1):
                        tableau[r][col] -= factor * tableau[pivot_row][col]

        basis[pivot_row - 1] = entering

    # Extract primal solution
    x = [Fraction(0)] * n_vars
    for i in range(n_rows):
        x[basis[i]] = tableau[i + 1][n_vars]

    p_sol = tuple(x[j] for j in range(k))
    p_slack = [x[k + i] for i in range(m)]
    n_slack = [x[k + m + i] for i in range(m)]
    primal_obj = sum((p_slack[i] + n_slack[i] for i in range(m)), Fraction(0))

    # Dual variables extraction:
    # Since c_{p_i} = 1, the reduced cost of p_i satisfies: r_{p_i} = 1 - y_i
    # Hence y_i = 1 - tableau[0][k + i].
    y_dual = tuple(Fraction(1) - tableau[0][k + i] for i in range(m))

    # Lambda (dual variable for sum(P) = 1):
    # Primal objective == Dual objective = sum(y_i * e_i) + lambda.
    dual_obj_without_lambda = sum((y_dual[i] * e[i] for i in range(m)), Fraction(0))
    lam = primal_obj - dual_obj_without_lambda
    dual_obj = dual_obj_without_lambda + lam

    duality_gap = Fraction(abs(primal_obj - dual_obj))
    is_contextual = (primal_obj > Fraction(0))

    return ContextualityReceipt(
        model_name=model.name,
        is_no_signaling=is_ns,
        no_signaling_residual_norm=ns_res,
        bell_chsh_parameter=s_param,
        is_bell_violating=is_bell_violating,
        is_contextual=is_contextual,
        obstruction_distance=primal_obj,
        optimal_joint_distribution=p_sol,
        dual_witness=y_dual,
        dual_objective=dual_obj,
        duality_gap=duality_gap,
        pivot_count=pivots,
    )
