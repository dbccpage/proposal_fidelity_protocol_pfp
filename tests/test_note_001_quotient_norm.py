"""
Executable verification for Derivations ATL-N001-001 and ATL-N001-003 (Note 001).

Derivations:
- AUDIT-N001-001: Finite Lp quotient norm infimum attainment on C^1 / im d_0
- AUDIT-N001-003: Phi_p quotient norm axioms on Q^1 under strictly positive weights

Tests:
1. Kernel triviality on the gauge-fixed subspace F (df = 0 and f in F implies f = 0).
2. Explicit positive coercivity constant c_{p, w} > 0 on F for p in {1, 2, inf}.
3. Compact sublevel set bound: all candidates with cost <= ||c|| lie within a compact box.
4. Exact Lp quotient infimum attainment for p=1, p=2, and p=inf on cycle and graph instances.
5. Well-definedness of Phi_p on quotient equivalence classes ([c] = [c + dg]).
6. Absolute homogeneity Phi_p([lambda c]) = |lambda| * Phi_p([c]).
7. Subadditivity (triangle inequality) Phi_p([c1 + c2]) <= Phi_p([c1]) + Phi_p([c2]).
8. Positive definiteness under positive weights (Phi_p([c]) = 0 iff c in im d_0).
9. Negative control / boundary: Zero-weight refusal counterexample showing failure of
   positive definiteness when a zero weight is permitted.
"""

from fractions import Fraction
import math
import pytest


# ---------------------------------------------------------------------------
# Exact Discrete Graph Model and Operators
# ---------------------------------------------------------------------------

class DiscreteGraph:
    """Exact discrete graph structure with rational weights and coboundary operator."""

    def __init__(self, num_vertices, edges, weights=None):
        self.num_vertices = num_vertices
        self.edges = edges  # list of (u, v) tuples
        if weights is None:
            self.weights = [Fraction(1) for _ in edges]
        else:
            self.weights = [Fraction(w) for w in weights]
        if any(w <= 0 for w in self.weights):
            raise ValueError("Edge weights must be strictly positive")

    def d0(self, potential):
        """Evaluate coboundary df on each oriented edge (u, v)."""
        return [potential[v] - potential[u] for (u, v) in self.edges]

    def residual(self, cochain, potential):
        """Evaluate residual r = c - df."""
        df = self.d0(potential)
        return [cochain[i] - df[i] for i in range(len(self.edges))]

    def norm_1(self, cochain):
        """Weighted L1 norm."""
        return sum(self.weights[i] * abs(cochain[i]) for i in range(len(self.edges)))

    def norm_2_sq(self, cochain):
        """Weighted squared L2 norm."""
        return sum(self.weights[i] * (cochain[i] ** 2) for i in range(len(self.edges)))

    def norm_inf(self, cochain):
        """Weighted Linf norm."""
        return max(self.weights[i] * abs(cochain[i]) for i in range(len(self.edges)))


# ---------------------------------------------------------------------------
# Test Cases for AUDIT-N001-001 (Attainment & Coercivity)
# ---------------------------------------------------------------------------

def test_kernel_triviality_on_gauge_fixed_subspace():
    """Verify d0|_F is strictly injective on connected graphs (f0 = 0 and df = 0 implies f = 0)."""
    # 3-cycle: vertices 0, 1, 2; edges (0, 1), (1, 2), (0, 2)
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])

    # Search gauge-fixed potentials (f0 = 0)
    for f1 in range(-6, 7):
        for f2 in range(-6, 7):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            df = graph.d0(f)
            if all(e == 0 for e in df):
                assert f1 == 0 and f2 == 0, f"Non-trivial kernel element found: {f}"


def test_coercivity_constants_positive():
    """Verify explicit coercivity constant c_{p, w} > 0 on gauge-fixed space for p in {1, 2, inf}."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)], weights=[Fraction(1), Fraction(1), Fraction(1)])

    min_ratio_1 = float("inf")
    min_ratio_2 = float("inf")
    min_ratio_inf = float("inf")

    for f1 in range(-5, 6):
        for f2 in range(-5, 6):
            if f1 == 0 and f2 == 0:
                continue
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            df = graph.d0(f)
            norm_inf_f = max(abs(f1), abs(f2))

            r1 = float(graph.norm_1(df)) / norm_inf_f
            r2 = math.sqrt(float(graph.norm_2_sq(df))) / norm_inf_f
            r_inf = float(graph.norm_inf(df)) / norm_inf_f

            min_ratio_1 = min(min_ratio_1, r1)
            min_ratio_2 = min(min_ratio_2, r2)
            min_ratio_inf = min(min_ratio_inf, r_inf)

    # Coercivity constants are strictly positive
    assert min_ratio_1 >= 2.0, f"Expected c_1 >= 2.0, got {min_ratio_1}"
    assert min_ratio_2 >= 1.2, f"Expected c_2 >= 1.2, got {min_ratio_2}"
    assert min_ratio_inf >= 1.0, f"Expected c_inf >= 1.0, got {min_ratio_inf}"


def test_sublevel_set_boundedness():
    """Verify that all potentials satisfying ||c - df|| <= ||c|| lie within a compact ball."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])
    c = [Fraction(1), Fraction(1), Fraction(-1)]
    cost_origin = graph.norm_1(c)  # 3

    # Coercivity constant c_1 = 2
    c1 = Fraction(2)
    radius_bound = (cost_origin + cost_origin) / c1  # 2 * ||c|| / c_1 = 3

    # Every potential outside the radius bound must have cost > cost_origin
    for f1 in range(-8, 9):
        for f2 in range(-8, 9):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            if max(abs(f1), abs(f2)) > radius_bound:
                cost = graph.norm_1(graph.residual(c, f))
                assert cost > cost_origin, f"Potential {f} outside radius has cost {cost} <= {cost_origin}"


def test_lp_attainment_triangle():
    """Verify exact quotient infimum attainment for p=1, p=2, and p=inf."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])
    c = [Fraction(1), Fraction(1), Fraction(-1)]

    # 1. Attainment for p = 1: cycle flux is c0 + c1 - c2 = 3.
    # Triangle inequality enforces ||c - df||_1 >= 3 for every f.
    # Attainment at f* = (0, 0, 0) achieving value exactly 3.
    min_1 = float("inf")
    best_f_1 = None
    for f1 in range(-4, 5):
        for f2 in range(-4, 5):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            cost = graph.norm_1(graph.residual(c, f))
            if cost < min_1:
                min_1 = cost
                best_f_1 = f

    assert min_1 == Fraction(3)
    assert best_f_1 is not None

    # 2. Attainment for p = 2: normal equations L f = d0^T W c.
    # Here c is orthogonal to im d0, so f* = (0, 0, 0) is the unique optimal gauge-fixed potential.
    min_2 = graph.norm_2_sq(c)  # 3
    for f1 in range(-4, 5):
        for f2 in range(-4, 5):
            f = [Fraction(0), Fraction(f1, 2), Fraction(f2, 2)]
            cost = graph.norm_2_sq(graph.residual(c, f))
            assert cost >= min_2
            if f1 != 0 or f2 != 0:
                assert cost > min_2

    # 3. Attainment for p = inf: Chebyshev active-edge balance achieves 1.
    min_inf = float("inf")
    best_f_inf = None
    for f1 in range(-4, 5):
        for f2 in range(-4, 5):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            cost = graph.norm_inf(graph.residual(c, f))
            if cost < min_inf:
                min_inf = cost
                best_f_inf = f

    assert min_inf == Fraction(1)
    assert best_f_inf is not None


# ---------------------------------------------------------------------------
# Test Cases for AUDIT-N001-003 (Quotient Norm Axioms)
# ---------------------------------------------------------------------------

def _compute_phi_1(graph, cochain, search_radius=5):
    """Compute exact Phi_1([c]) by minimization over the compact gauge-fixed region."""
    min_cost = float("inf")
    for f1 in range(-search_radius, search_radius + 1):
        for f2 in range(-search_radius, search_radius + 1):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            cost = graph.norm_1(graph.residual(cochain, f))
            if cost < min_cost:
                min_cost = cost
    return min_cost


def test_quotient_norm_well_definedness():
    """Verify Phi_1([c]) = Phi_1([c + dg]) for any potential g."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])
    c = [Fraction(1), Fraction(1), Fraction(-1)]
    g = [Fraction(0), Fraction(2), Fraction(-1)]
    dg = graph.d0(g)

    c_shifted = [c[i] + dg[i] for i in range(3)]
    assert _compute_phi_1(graph, c) == _compute_phi_1(graph, c_shifted) == Fraction(3)


def test_quotient_norm_homogeneity():
    """Verify Phi_1([lambda * c]) = |lambda| * Phi_1([c])."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])
    c = [Fraction(1), Fraction(1), Fraction(-1)]
    base_val = _compute_phi_1(graph, c)  # 3

    for scale in [-2, 0, 1, 2]:
        c_scaled = [Fraction(scale) * x for x in c]
        expected = abs(scale) * base_val
        actual = _compute_phi_1(graph, c_scaled, search_radius=5 * (abs(scale) + 1))
        assert actual == expected, f"Homogeneity failed for scale {scale}: expected {expected}, got {actual}"


def test_quotient_norm_subadditivity():
    """Verify Phi_1([c1 + c2]) <= Phi_1([c1]) + Phi_1([c2])."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])
    # Non-trivial independent classes
    c1 = [Fraction(1), Fraction(1), Fraction(-1)]   # cycle flux 3 -> Phi_1 = 3
    c2 = [Fraction(-1), Fraction(0), Fraction(1)]   # cycle flux -2 -> Phi_1 = 2
    c12 = [c1[i] + c2[i] for i in range(3)]         # cycle flux 1 -> Phi_1 = 1

    phi_c1 = _compute_phi_1(graph, c1)
    phi_c2 = _compute_phi_1(graph, c2)
    phi_c12 = _compute_phi_1(graph, c12)

    assert phi_c12 <= phi_c1 + phi_c2
    assert phi_c12 == Fraction(1)
    assert phi_c1 + phi_c2 == Fraction(5)


def test_quotient_norm_positive_definiteness():
    """Verify Phi_1([c]) == 0 if and only if c in im d0."""
    graph = DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)])

    # Exact cochain c_exact in im d0
    f_sample = [Fraction(0), Fraction(3), Fraction(-2)]
    c_exact = graph.d0(f_sample)
    assert _compute_phi_1(graph, c_exact) == Fraction(0)

    # Non-exact cochain c_flux not in im d0
    c_non_exact = [Fraction(1), Fraction(1), Fraction(-1)]
    assert _compute_phi_1(graph, c_non_exact) > Fraction(0)


def test_zero_weight_refusal_counterexample():
    """Negative control: zero weight on an edge allows non-exact cochain to have norm 0."""
    # Weight on edge 2 set to 0
    w_bad = [Fraction(1), Fraction(1), Fraction(0)]
    c_non_exact = [Fraction(0), Fraction(0), Fraction(1)]

    # Cochain is non-exact (cycle flux c0 + c1 - c2 = -1 != 0)
    cycle_flux = c_non_exact[0] + c_non_exact[1] - c_non_exact[2]
    assert cycle_flux != 0

    # At f = (0, 0, 0), weighted norm evaluates to 0
    res_norm = sum(w_bad[i] * abs(c_non_exact[i]) for i in range(3))
    assert res_norm == Fraction(0), "Expected zero-weight counterexample to produce norm 0"

    # DiscreteGraph rejects non-positive weights on initialization
    with pytest.raises(ValueError, match="Edge weights must be strictly positive"):
        DiscreteGraph(3, [(0, 1), (1, 2), (0, 2)], weights=w_bad)
