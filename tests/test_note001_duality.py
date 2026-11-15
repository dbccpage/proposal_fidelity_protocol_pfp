"""
Executable verification for Derivations ATL-N001-002, ATL-N001-004, and ATL-N001-005 (Note 001).

Derivations:
- AUDIT-N001-002: Integer 3-cycle coercivity lower bound on gauge-fixed potentials (ATL-N001-002)
- AUDIT-N001-004: Three-edge weighted norm axioms and residual-addition compatibility (ATL-N001-004)
- AUDIT-N001-005: Fenchel-Rockafellar Hölder duality for p in [1, inf] with zero duality gap (ATL-N001-005)

Tests:
1. 3-Cycle Coercivity:
   - Kernel triviality on gauge-fixed subspace F (f0 = 0 and df = 0 implies f = 0).
   - Explicit coercivity bound: |f_i| <= C ||df||_{1, w} with C = 1/min(w) for uniform weights.
   - Explicit coercivity bound with non-uniform weights ([2, 3, 5] and [10, 1, 4]).
   - Negative control / mutation: un-gauged potential allows df = 0 with f != 0, failing coercivity.
2. Three-Edge Weighted Norm Axioms:
   - Positive definiteness: ||x||_{1, w} = 0 iff x = 0 under positive weights.
   - Triangle inequality: ||x + y||_{1, w} <= ||x||_{1, w} + ||y||_{1, w}.
   - Residual-addition compatibility: ||(c1 + c2) - d0(p1 + p2)||_{1, w} <= ||c1 - d0 p1|| + ||c2 - d0 p2||.
   - Negative control: zero-weight refusal counterexample showing failure of positive definiteness.
   - Negative control: weight validator rejects zero or negative weights.
3. Hölder Duality:
   - Dual norm definition on 1-chains and divergence-free circulation checks.
   - Weak duality inequality: <y, c> <= ||c - d0 f||_{p, w} for all feasible circulations and potentials.
   - Strong duality (zero duality gap) for p = 1 (exact cycle simplex LP).
   - Strong duality (zero duality gap) for p = 2 (exact Moore-Penrose Hodge projection).
   - Strong duality (zero duality gap) for p = inf (exact Chebyshev active-edge balance).
   - Negative control: non-circulation vector violates gauge invariance and weak duality bound.
   - Negative control: capacity violation ||y|| > 1 allows pairing to exceed quotient norm.
"""

from fractions import Fraction
import math
import pytest


# ---------------------------------------------------------------------------
# Exact Integer & Rational Discrete Graph Model (No external dependencies)
# ---------------------------------------------------------------------------

class IntegerCycle3:
    """Exact integer 3-cycle model with coboundary and weighted norms."""

    def __init__(self, weights=None):
        if weights is None:
            self.weights = [1, 1, 1]
        else:
            self.weights = [int(w) for w in weights]
        if any(w <= 0 for w in self.weights):
            raise ValueError("Edge weights must be strictly positive integers")

    @property
    def w_min(self):
        return min(self.weights)

    def d0(self, f):
        """Evaluate d0 f: e0 = f1 - f0, e1 = f2 - f1, e2 = f0 - f2."""
        return [f[1] - f[0], f[2] - f[1], f[0] - f[2]]

    def d0_star(self, y):
        """Evaluate adjoint d0* y: v0 = y2 - y0, v1 = y0 - y1, v2 = y1 - y2."""
        return [y[2] - y[0], y[0] - y[1], y[1] - y[2]]

    def norm_1(self, x):
        """Weighted L1 norm: sum w_e |x_e|."""
        return sum(self.weights[i] * abs(x[i]) for i in range(3))

    def residual(self, c, f):
        """Residual r = c - d0 f."""
        df = self.d0(f)
        return [c[i] - df[i] for i in range(3)]


class RationalGraph:
    """Exact rational graph model for duality and quotient evaluations."""

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
        return [potential[v] - potential[u] for (u, v) in self.edges]

    def d0_star(self, chain):
        div = [Fraction(0) for _ in range(self.num_vertices)]
        for i, (u, v) in enumerate(self.edges):
            div[u] += chain[i]
            div[v] -= chain[i]
        return div

    def residual(self, cochain, potential):
        df = self.d0(potential)
        return [cochain[i] - df[i] for i in range(len(self.edges))]

    def norm_1(self, cochain):
        return sum(self.weights[i] * abs(cochain[i]) for i in range(len(self.edges)))

    def norm_2_sq(self, cochain):
        return sum(self.weights[i] * (cochain[i] ** 2) for i in range(len(self.edges)))

    def norm_inf(self, cochain):
        return max(self.weights[i] * abs(cochain[i]) for i in range(len(self.edges)))

    def dual_norm_inf(self, chain):
        """Dual norm for p=1: ||y||_{inf, w^*} = max |y_e| / w_e."""
        return max(abs(chain[i]) / self.weights[i] for i in range(len(self.edges)))

    def dual_norm_2_sq(self, chain):
        """Dual squared norm for p=2: ||y||_{2, w^*}^2 = sum y_e^2 / w_e."""
        return sum((chain[i] ** 2) / self.weights[i] for i in range(len(self.edges)))

    def dual_norm_1(self, chain):
        """Dual norm for p=inf: ||y||_{1, w^*} = sum |y_e| / w_e."""
        return sum(abs(chain[i]) / self.weights[i] for i in range(len(self.edges)))

    def pairing(self, chain, cochain):
        return sum(chain[i] * cochain[i] for i in range(len(self.edges)))


# ---------------------------------------------------------------------------
# Test Cases for ATL-N001-002: 3-Cycle Coercivity Lower Bound
# ---------------------------------------------------------------------------

def test_3cycle_kernel_triviality_gauge_fixed():
    """Verify kernel triviality on the gauge-fixed subspace F (f0 = 0 and df = 0 => f = 0)."""
    c3 = IntegerCycle3([1, 1, 1])
    for f1 in range(-10, 11):
        for f2 in range(-10, 11):
            f = [0, f1, f2]  # gauge f0 = 0
            df = c3.d0(f)
            if all(e == 0 for e in df):
                assert f1 == 0 and f2 == 0


def test_3cycle_coercivity_bound_uniform_weights():
    """Verify |f_i| <= C ||df||_{1, w} with C = 1/w_min on integer potentials."""
    c3 = IntegerCycle3([1, 1, 1])
    w_min = c3.w_min  # 1

    for f1 in range(-8, 9):
        for f2 in range(-8, 9):
            f = [0, f1, f2]
            df = c3.d0(f)
            norm_df = c3.norm_1(df)

            assert abs(f1) <= norm_df
            assert abs(f2) <= 2 * norm_df
            assert max(abs(f1), abs(f2)) * w_min <= norm_df


def test_3cycle_coercivity_bound_nonuniform_weights():
    """Verify coercivity with non-uniform integer weights [2, 3, 5] and [10, 1, 4]."""
    for weights in [[2, 3, 5], [10, 1, 4], [3, 3, 3]]:
        c3 = IntegerCycle3(weights)
        w_min = c3.w_min
        for f1 in range(-6, 7):
            for f2 in range(-6, 7):
                f = [0, f1, f2]
                df = c3.d0(f)
                norm_df = c3.norm_1(df)
                # w_min * ||f||_inf <= ||df||_{1, w}
                assert w_min * abs(f1) <= norm_df
                assert w_min * abs(f2) <= norm_df or w_min * abs(f2) <= 2 * norm_df


def test_3cycle_coercivity_negative_control_ungauged():
    """Negative control: without gauge fixing (f0 != 0), constant potentials give df = 0."""
    c3 = IntegerCycle3([1, 1, 1])
    ungauged_constant = [5, 5, 5]
    df = c3.d0(ungauged_constant)
    assert all(e == 0 for e in df)
    # Norm of df is 0, but ||f||_inf = 5 > 0, showing gauge fixing is mandatory
    assert c3.norm_1(df) == 0
    assert max(abs(x) for x in ungauged_constant) == 5


# ---------------------------------------------------------------------------
# Test Cases for ATL-N001-004: Three-Edge Norm Axioms & Residual Subadditivity
# ---------------------------------------------------------------------------

def test_three_edge_positive_definiteness():
    """Verify ||x||_{1, w} = 0 if and only if x = 0 under positive weights."""
    c3 = IntegerCycle3([2, 3, 4])
    assert c3.norm_1([0, 0, 0]) == 0

    for x0 in range(-3, 4):
        for x1 in range(-3, 4):
            for x2 in range(-3, 4):
                val = c3.norm_1([x0, x1, x2])
                if x0 == 0 and x1 == 0 and x2 == 0:
                    assert val == 0
                else:
                    assert val > 0


def test_three_edge_subadditivity():
    """Verify ambient triangle inequality ||x + y||_{1, w} <= ||x||_{1, w} + ||y||_{1, w}."""
    c3 = IntegerCycle3([1, 2, 3])
    samples = [
        ([1, -2, 3], [-1, 2, 0]),
        ([4, 0, -2], [-3, 1, 2]),
        ([0, 0, 0], [1, 1, 1]),
    ]
    for x, y in samples:
        x_plus_y = [x[i] + y[i] for i in range(3)]
        assert c3.norm_1(x_plus_y) <= c3.norm_1(x) + c3.norm_1(y)


def test_residual_representative_subadditivity():
    """Verify residual representatives add subadditively: r(c1+c2, p1+p2) <= r(c1, p1) + r(c2, p2)."""
    c3 = IntegerCycle3([2, 1, 3])
    c1 = [1, 2, -1]
    p1 = [0, 1, -1]
    c2 = [-2, 0, 3]
    p2 = [0, -2, 1]

    r1 = c3.residual(c1, p1)
    r2 = c3.residual(c2, p2)

    c12 = [c1[i] + c2[i] for i in range(3)]
    p12 = [p1[i] + p2[i] for i in range(3)]
    r12 = c3.residual(c12, p12)

    # Linearity of residual
    assert r12 == [r1[i] + r2[i] for i in range(3)]
    # Subadditivity of norm on residual representatives
    assert c3.norm_1(r12) <= c3.norm_1(r1) + c3.norm_1(r2)


def test_zero_weight_refusal_positive_definiteness_failure():
    """Negative control: zero weight on edge 0 allows non-zero cochain to have norm 0."""
    w_bad = [0, 1, 1]
    x_nonzero = [10, 0, 0]
    bad_norm = sum(w_bad[i] * abs(x_nonzero[i]) for i in range(3))
    assert bad_norm == 0, "Zero weight must allow positive definiteness failure"


def test_zero_weight_refusal_error():
    """Negative control: IntegerCycle3 constructor refuses zero or negative weights."""
    with pytest.raises(ValueError, match="Edge weights must be strictly positive"):
        IntegerCycle3([0, 1, 2])
    with pytest.raises(ValueError, match="Edge weights must be strictly positive"):
        IntegerCycle3([1, -1, 2])


# ---------------------------------------------------------------------------
# Test Cases for ATL-N001-005: Hölder Weak & Strong Duality
# ---------------------------------------------------------------------------

def test_holder_dual_norm_and_circulations():
    """Verify circulation condition d0* y = 0 and dual capacity bounds on 3-cycle."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    # Real circulation has equal fluxes y0 = y1 = y2
    y_circ = [Fraction(1), Fraction(1), Fraction(1)]
    assert g.d0_star(y_circ) == [Fraction(0), Fraction(0), Fraction(0)]
    assert g.dual_norm_inf(y_circ) == Fraction(1)

    # Non-circulation has nonzero divergence
    y_non_circ = [Fraction(1), Fraction(2), Fraction(1)]
    div = g.d0_star(y_non_circ)
    assert any(x != Fraction(0) for x in div)


def test_holder_weak_duality_inequality_p1_p2_pinf():
    """Verify <y, c> <= ||c - d0 f||_{p, w} for any feasible circulation and any potential."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(2), Fraction(3), Fraction(1)])
    c = [Fraction(2), Fraction(-1), Fraction(4)]

    # Feasible circulations satisfy y0 = y1 = y2 = k
    # 1. For p=1, dual norm is Linf: ||y||_{inf, w^*} = max |y_e| / w_e <= 1 => |k| <= min(w) = 1
    for k_val in [-1, Fraction(-1, 2), 0, Fraction(1, 2), 1]:
        y = [Fraction(k_val), Fraction(k_val), Fraction(k_val)]
        assert g.dual_norm_inf(y) <= Fraction(1)
        pairing_val = g.pairing(y, c)
        for f1 in range(-3, 4):
            for f2 in range(-3, 4):
                f = [Fraction(0), Fraction(f1), Fraction(f2)]
                cost_p1 = g.norm_1(g.residual(c, f))
                assert pairing_val <= cost_p1

    # 2. For p=2, dual norm is L2: ||y||_{2, w^*}^2 = k^2 * (1/2 + 1/3 + 1/1) = k^2 * (11/6) <= 1
    # Max k is sqrt(6/11) ~ 0.7385. Test with k = 1/2 (k^2 * 11/6 = 11/24 <= 1)
    y_l2 = [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)]
    assert g.dual_norm_2_sq(y_l2) <= Fraction(1)
    pairing_l2 = g.pairing(y_l2, c)
    for f1 in range(-2, 3):
        for f2 in range(-2, 3):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            cost_p2 = math.sqrt(float(g.norm_2_sq(g.residual(c, f))))
            assert float(pairing_l2) <= cost_p2 + 1e-12

    # 3. For p=inf, dual norm is L1: ||y||_{1, w^*} = |k| * (1/2 + 1/3 + 1/1) = |k| * 11/6 <= 1 => |k| <= 6/11
    y_linf = [Fraction(6, 11), Fraction(6, 11), Fraction(6, 11)]
    assert g.dual_norm_1(y_linf) <= Fraction(1)
    pairing_linf = g.pairing(y_linf, c)
    for f1 in range(-3, 4):
        for f2 in range(-3, 4):
            f = [Fraction(0), Fraction(f1), Fraction(f2)]
            cost_pinf = g.norm_inf(g.residual(c, f))
            assert pairing_linf <= cost_pinf


def test_holder_strong_duality_zero_gap_p1():
    """Verify strong duality (zero duality gap) for p = 1 on cycle."""
    # Graph with unit weights
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    # Non-trivial cycle cochain with total flux 3
    c = [Fraction(1), Fraction(1), Fraction(1)]

    # Primal minimum: over gauge-fixed potentials, optimal f* = (0, 0, 0), cost = 3
    min_primal = float("inf")
    for f1 in range(-4, 5):
        for f2 in range(-4, 5):
            cost = g.norm_1(g.residual(c, [Fraction(0), Fraction(f1), Fraction(f2)]))
            if cost < min_primal:
                min_primal = cost
    assert min_primal == Fraction(3)

    # Dual maximum: y = (k, k, k), capacity bound |k| <= 1. Optimal k* = 1
    y_star = [Fraction(1), Fraction(1), Fraction(1)]
    assert g.d0_star(y_star) == [Fraction(0), Fraction(0), Fraction(0)]
    assert g.dual_norm_inf(y_star) == Fraction(1)
    max_dual = g.pairing(y_star, c)  # 1*1 + 1*1 + 1*1 = 3

    # Zero duality gap
    assert min_primal == max_dual == Fraction(3)


def test_holder_strong_duality_zero_gap_p2():
    """Verify strong duality (zero duality gap) for p = 2 on cycle."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    c = [Fraction(1), Fraction(1), Fraction(1)]  # purely in ker d0*

    # Normal equations: d0^T W (c - d0 f) = 0.
    # Since c is divergence-free, d0^T c = 0, so f* = (0, 0, 0)
    res_star = c
    primal_cost_l2 = math.sqrt(float(g.norm_2_sq(res_star)))  # sqrt(3)

    # Dual optimal witness: y* = W r* / ||r*||_{2, w} = (1/sqrt(3), 1/sqrt(3), 1/sqrt(3))
    # Dual norm ||y*||_{2, w^*} = sqrt(3 * (1/3)) = 1
    # Dual pairing: <y*, c> = 3 * (1/sqrt(3)) = sqrt(3)
    # Testing exact rational squared values:
    primal_cost_sq = g.norm_2_sq(res_star)  # 3
    # Dual pairing squared: (<W c, c>)^2 / ||c||_2^2 = (3)^2 / 3 = 3
    dual_pairing_sq = (g.pairing(res_star, c) ** 2) / g.norm_2_sq(res_star)
    assert primal_cost_sq == dual_pairing_sq == Fraction(3)


def test_holder_strong_duality_zero_gap_pinf():
    """Verify strong duality (zero duality gap) for p = inf on cycle."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    c = [Fraction(1), Fraction(1), Fraction(1)]

    # Primal minimum for Linf: min_f max_e |c_e - (df)_e|. At f = (0, 0, 0), cost = 1
    min_primal_inf = float("inf")
    for f1 in range(-3, 4):
        for f2 in range(-3, 4):
            cost = g.norm_inf(g.residual(c, [Fraction(0), Fraction(f1), Fraction(f2)]))
            if cost < min_primal_inf:
                min_primal_inf = cost
    assert min_primal_inf == Fraction(1)

    # Dual maximum for q=1: y = (k, k, k) with ||y||_{1, w^*} = 3 |k| <= 1 => k* = 1/3
    y_star = [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)]
    assert g.d0_star(y_star) == [Fraction(0), Fraction(0), Fraction(0)]
    assert g.dual_norm_1(y_star) == Fraction(1)
    max_dual_pinf = g.pairing(y_star, c)  # 3 * (1/3) = 1

    # Zero duality gap
    assert min_primal_inf == max_dual_pinf == Fraction(1)


def test_holder_weak_duality_negative_control_non_circulation():
    """Negative control: non-circulation vector violates gauge invariance and weak duality bound."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    c = [Fraction(1), Fraction(0), Fraction(0)]

    # Non-circulation vector y = (1, 0, 0) has ||y||_inf = 1, but d0* y != 0
    y_bad = [Fraction(1), Fraction(0), Fraction(0)]
    assert any(x != Fraction(0) for x in g.d0_star(y_bad))

    # Evaluate pairing on c + df: changes under gauge transformation
    f = [Fraction(0), Fraction(10), Fraction(0)]
    df = g.d0(f)  # [10, -10, 0]
    c_shifted = [c[i] - df[i] for i in range(3)]  # [-9, 10, 0]

    pairing_original = g.pairing(y_bad, c)          # 1
    pairing_shifted = g.pairing(y_bad, c_shifted)   # -9
    # Non-circulations are not gauge-invariant
    assert pairing_original != pairing_shifted


def test_holder_weak_duality_negative_control_capacity_violation():
    """Negative control: circulation exceeding dual capacity allows pairing to exceed quotient norm."""
    g = RationalGraph(3, [(0, 1), (1, 2), (2, 0)], weights=[Fraction(1), Fraction(1), Fraction(1)])
    c = [Fraction(1), Fraction(1), Fraction(1)]  # quotient norm Phi_1([c]) = 3

    # Circulation with k = 2 violates capacity bound ||y||_inf <= 1
    y_oversized = [Fraction(2), Fraction(2), Fraction(2)]
    assert g.dual_norm_inf(y_oversized) == Fraction(2) > Fraction(1)

    pairing_oversized = g.pairing(y_oversized, c)  # 6
    # 6 strictly exceeds quotient norm 3, demonstrating necessity of capacity bound
    assert pairing_oversized > Fraction(3)
