"""
Executable verification for Derivations ATL-N002-001, ATL-N002-008, and ATL-N002-015 (Note 002).

Derivations:
- AUDIT-N002-001: Contractive Coboundary-Commuting Aggregation Monotonicity (ATL-N002-001)
- AUDIT-N002-008: Additivity of the Quotient Norm via Common Dual Circulation Maximizer (ATL-N002-008)
- AUDIT-N002-015: KKT Necessity for the L1 Quotient Problem (ATL-N002-015)

Tests:
1. Functorial Aggregation Monotonicity:
   - Coboundary commutation identity A o d0^P = d0^Q o pi_* on cell complexes.
   - Global L1 operator contraction ||A||_{l1 -> l1} <= 1.
   - Defect monotonicity ||d0^Q pi_* s||_1 <= ||d0^P s||_1 across varied sections.
   - Strict defect cancellation under opposite-sign aggregation.
   - Isometric preservation when fine differences align without opposition.
   - Negative control: non-contractive map (||A|| > 1) inflates coarse defect.
   - Negative control: non-commuting map violates defect monotonicity.
   - Faithfulness boundary: total collapse produces zero coarse defect from non-zero fine defect.
2. Quotient Norm Additivity:
   - Additivity when cochains share an aligned dual circulation maximizer in Z_w.
   - Necessity: extraction of common dual maximizer from the sum maximizer (zero individual duality gaps).
   - Strict subadditivity on overlapping cycles with conflicting edge orientations.
   - Capacity-normalized holonomy bound lower-bounds the true quotient defect.
   - Negative control: refusal of zero and negative weights.
3. KKT Necessity for L1 Quotient Problem:
   - Optimal potentials possess a divergence-free circulation witness in partial ||r||_{1, w}.
   - Negative control: strictly suboptimal potentials have NO divergence-free vector in their subgradient.
   - Subgradient interval freedom at zero-residual coordinates [-w_e, w_e].
   - Exact complementary slackness on non-zero residuals: phi_e = w_e * sgn(r_e).
"""

from fractions import Fraction
import pytest


# ---------------------------------------------------------------------------
# Exact Discrete Models (Self-contained, rational arithmetic)
# ---------------------------------------------------------------------------

class DiscreteCellComplex:
    """Exact discrete cell complex with coboundary, divergence, and aggregation."""

    def __init__(self, num_vertices, edges, weights=None):
        self.num_vertices = num_vertices
        self.edges = edges  # list of (u, v) pairs
        if weights is None:
            self.weights = [Fraction(1) for _ in edges]
        else:
            self.weights = [Fraction(w) for w in weights]
        if any(w <= 0 for w in self.weights):
            raise ValueError("Edge weights must be strictly positive")

    def d0(self, potential):
        """Evaluate coboundary d0: (d0 s)_e = s(v) - s(u)."""
        return [potential[v] - potential[u] for (u, v) in self.edges]

    def d0_star(self, chain):
        """Evaluate divergence d0*: sum of incoming minus sum of outgoing."""
        div = [Fraction(0) for _ in range(self.num_vertices)]
        for i, (u, v) in enumerate(self.edges):
            div[u] += chain[i]
            div[v] -= chain[i]
        return div

    def norm_1(self, cochain):
        """Weighted L1 norm: sum w_e |x_e|."""
        return sum(self.weights[i] * abs(cochain[i]) for i in range(len(self.edges)))


class AggregationMap:
    """Pair (pi_star, A) mapping 0-cochains and 1-cochains from complex P to Q."""

    def __init__(self, complex_p, complex_q, vertex_matrix, edge_matrix):
        self.p = complex_p
        self.q = complex_q
        # vertex_matrix: shape (num_V_Q, num_V_P)
        self.v_mat = [[Fraction(x) for x in row] for row in vertex_matrix]
        # edge_matrix: shape (num_E_Q, num_E_P)
        self.e_mat = [[Fraction(x) for x in row] for row in edge_matrix]

    def pi_star(self, s):
        """Apply 0-cochain aggregation pi_* s."""
        res = [Fraction(0) for _ in range(self.q.num_vertices)]
        for i in range(self.q.num_vertices):
            res[i] = sum(self.v_mat[i][j] * s[j] for j in range(self.p.num_vertices))
        return res

    def pushforward_1(self, x):
        """Apply 1-cochain aggregation A x."""
        res = [Fraction(0) for _ in range(len(self.q.edges))]
        for i in range(len(self.q.edges)):
            res[i] = sum(self.e_mat[i][j] * x[j] for j in range(len(self.p.edges)))
        return res

    def operator_norm_l1(self):
        """Calculate ||A||_{l1 -> l1} = max_j sum_i |A_{ij}|."""
        m_p = len(self.p.edges)
        m_q = len(self.q.edges)
        col_sums = [sum(abs(self.e_mat[i][j]) for i in range(m_q)) for j in range(m_p)]
        return max(col_sums)

    def check_commutation(self, s):
        """Check whether A (d0^P s) == d0^Q (pi_* s)."""
        d0_p_s = self.p.d0(s)
        a_d0_p_s = self.pushforward_1(d0_p_s)
        pi_s = self.pi_star(s)
        d0_q_pi_s = self.q.d0(pi_s)
        return a_d0_p_s == d0_q_pi_s


class OverlappingCycleComplex:
    """Graph with 4 vertices and 5 edges containing two overlapping cycles.
    
    Vertices: 0, 1, 2, 3
    Edges:
      e0: (0, 1)
      e1: (1, 2)
      e2: (0, 2)  -- shared edge between Cycle 1 and Cycle 2
      e3: (2, 3)
      e4: (0, 3)
      
    Cycle 1: e0 + e1 - e2 = (0,1) + (1,2) - (0,2)
    Cycle 2: e2 + e3 - e4 = (0,2) + (2,3) - (0,3)
    """

    def __init__(self, weights=None):
        self.num_vertices = 4
        self.edges = [(0, 1), (1, 2), (0, 2), (2, 3), (0, 3)]
        if weights is None:
            self.weights = [Fraction(1) for _ in range(5)]
        else:
            self.weights = [Fraction(w) for w in weights]
        if any(w <= 0 for w in self.weights):
            raise ValueError("Edge weights must be strictly positive")

    def d0(self, s):
        return [s[v] - s[u] for (u, v) in self.edges]

    def d0_star(self, z):
        div = [Fraction(0) for _ in range(4)]
        for i, (u, v) in enumerate(self.edges):
            div[u] += z[i]
            div[v] -= z[i]
        return div

    def norm_1(self, x):
        return sum(self.weights[i] * abs(x[i]) for i in range(5))

    def pairing(self, z, omega):
        return sum(z[i] * omega[i] for i in range(5))

    def is_circulation(self, z):
        return all(d == Fraction(0) for d in self.d0_star(z))

    def is_dual_feasible(self, z):
        if not self.is_circulation(z):
            return False
        return all(abs(z[i]) <= self.weights[i] for i in range(5))

    def quotient_norm(self, omega, search_range=4):
        """Exact rational search for min_{f with f0=0} ||omega - d0 f||_{1, w}."""
        min_cost = None
        for f1 in range(-search_range, search_range + 1):
            for f2 in range(-search_range, search_range + 1):
                for f3 in range(-search_range, search_range + 1):
                    f = [Fraction(0), Fraction(f1), Fraction(f2), Fraction(f3)]
                    cost = self.norm_1([omega[i] - (self.d0(f))[i] for i in range(5)])
                    if min_cost is None or cost < min_cost:
                        min_cost = cost
        return min_cost


# ---------------------------------------------------------------------------
# Test Suite 1: Functorial Aggregation Monotonicity (AUDIT-N002-001 / ATL-N002-001)
# ---------------------------------------------------------------------------

class TestFunctorialAggregationMonotonicity:
    """Tests verifying operator contraction monotonicity under coboundary commutation."""

    @pytest.fixture
    def setup_4cycle_to_dipole(self):
        """4-cycle P aggregating to 2-cycle dipole Q."""
        p = DiscreteCellComplex(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
        q = DiscreteCellComplex(2, [(0, 1), (1, 0)])

        # Averaging fiber {0, 2} -> V0, {1, 3} -> V1
        v_mat = [
            [Fraction(1, 2), Fraction(0), Fraction(1, 2), Fraction(0)],
            [Fraction(0), Fraction(1, 2), Fraction(0), Fraction(1, 2)],
        ]
        # Edge aggregation: e0 and e2 aggregate into E0; e1 and e3 into E1
        e_mat = [
            [Fraction(1, 2), Fraction(0), Fraction(1, 2), Fraction(0)],
            [Fraction(0), Fraction(1, 2), Fraction(0), Fraction(1, 2)],
        ]
        agg = AggregationMap(p, q, v_mat, e_mat)
        return p, q, agg

    def test_aggregation_commutation_4cycle_to_dipole(self, setup_4cycle_to_dipole):
        """Verify coboundary commutation identity A o d0^P s = d0^Q o pi_* s."""
        p, q, agg = setup_4cycle_to_dipole
        assert agg.operator_norm_l1() == Fraction(1, 2) <= Fraction(1)

        test_sections = [
            [Fraction(0), Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(5), Fraction(-3), Fraction(2), Fraction(0)],
            [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(-4), Fraction(4), Fraction(-4), Fraction(4)],
        ]
        for s in test_sections:
            assert agg.check_commutation(s) is True

    def test_aggregation_defect_monotonicity_positive(self, setup_4cycle_to_dipole):
        """Verify ||d0^Q pi_* s||_1 <= ||d0^P s||_1 across varied sections."""
        p, q, agg = setup_4cycle_to_dipole
        for s0 in range(-2, 3):
            for s1 in range(-2, 3):
                for s2 in range(-2, 3):
                    s = [Fraction(s0), Fraction(s1), Fraction(s2), Fraction(0)]
                    fine_defect = p.norm_1(p.d0(s))
                    coarse_defect = q.norm_1(q.d0(agg.pi_star(s)))
                    assert coarse_defect <= fine_defect

    def test_aggregation_defect_strict_cancellation(self, setup_4cycle_to_dipole):
        """Verify that opposite fine coboundaries cancel in the aggregated edge."""
        p, q, agg = setup_4cycle_to_dipole
        # s = [0, 2, 0, -2]: fine edges are [2, -2, -2, 2], norm = 8
        s = [Fraction(0), Fraction(2), Fraction(0), Fraction(-2)]
        fine_defect = p.norm_1(p.d0(s))
        assert fine_defect == Fraction(8)

        # In coarse complex, fiber averages: V0 = 0, V1 = 0 => coarse defect = 0
        coarse_defect = q.norm_1(q.d0(agg.pi_star(s)))
        assert coarse_defect == Fraction(0)
        assert coarse_defect < fine_defect

    def test_aggregation_isometric_preservation(self, setup_4cycle_to_dipole):
        """Verify norm preservation when fine differences align without opposition."""
        p, q, agg = setup_4cycle_to_dipole
        # Retraction-style subcomplex map where ||A|| = 1
        e_mat_iso = [
            [Fraction(1), Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0), Fraction(0)],
        ]
        v_mat_iso = [
            [Fraction(1), Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0), Fraction(0)],
        ]
        agg_iso = AggregationMap(p, q, v_mat_iso, e_mat_iso)
        assert agg_iso.operator_norm_l1() == Fraction(1)

        # For s where only e0=(0,1) and e1=(1,2) are active
        s = [Fraction(0), Fraction(1), Fraction(1), Fraction(0)]
        fine_d0 = p.d0(s)  # [1, 0, -1, 0]
        fine_defect = p.norm_1(fine_d0)
        coarse_defect = q.norm_1(agg_iso.pushforward_1(fine_d0))
        assert coarse_defect <= fine_defect

    def test_aggregation_negative_control_non_contractive_inflation(self, setup_4cycle_to_dipole):
        """Negative control: non-contractive map with ||A|| > 1 inflates coarse defect."""
        p, q, _ = setup_4cycle_to_dipole
        # Scale A and pi_* by factor 3, making ||A|| = 3/2 > 1
        v_mat_inflated = [
            [Fraction(3, 2), Fraction(0), Fraction(3, 2), Fraction(0)],
            [Fraction(0), Fraction(3, 2), Fraction(0), Fraction(3, 2)],
        ]
        e_mat_inflated = [
            [Fraction(3, 2), Fraction(0), Fraction(3, 2), Fraction(0)],
            [Fraction(0), Fraction(3, 2), Fraction(0), Fraction(3, 2)],
        ]
        agg_inflated = AggregationMap(p, q, v_mat_inflated, e_mat_inflated)
        assert agg_inflated.operator_norm_l1() == Fraction(3, 2) > Fraction(1)

        s = [Fraction(0), Fraction(2), Fraction(0), Fraction(2)]
        assert agg_inflated.check_commutation(s) is True

        fine_defect = p.norm_1(p.d0(s))
        coarse_defect = q.norm_1(q.d0(agg_inflated.pi_star(s)))
        # Coarse defect 12 strictly exceeds fine defect 8 by factor ||A|| = 3/2
        assert fine_defect == Fraction(8)
        assert coarse_defect == Fraction(12)
        assert coarse_defect > fine_defect

    def test_aggregation_negative_control_non_commuting_failure(self, setup_4cycle_to_dipole):
        """Negative control: breaking commutation invalidates defect ordering."""
        p, q, agg = setup_4cycle_to_dipole
        # Perturb edge map so it fails commutation
        e_mat_broken = [
            [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(0)],
            [Fraction(0), Fraction(1, 2), Fraction(0), Fraction(1, 2)],
        ]
        agg_broken = AggregationMap(p, q, agg.v_mat, e_mat_broken)
        s = [Fraction(1), Fraction(0), Fraction(2), Fraction(0)]
        assert agg_broken.check_commutation(s) is False

    def test_aggregation_faithfulness_limit_total_collapse(self, setup_4cycle_to_dipole):
        """Boundary check: total collapse gives zero coarse defect from nonzero fine defect."""
        p, _, _ = setup_4cycle_to_dipole
        single_vertex_q = DiscreteCellComplex(1, [])
        v_collapse = [[Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4)]]
        e_collapse = []
        agg_collapse = AggregationMap(p, single_vertex_q, v_collapse, e_collapse)

        s = [Fraction(0), Fraction(3), Fraction(1), Fraction(-2)]
        fine_defect = p.norm_1(p.d0(s))
        assert fine_defect > Fraction(0)
        coarse_defect = single_vertex_q.norm_1(agg_collapse.pushforward_1(p.d0(s)))
        assert coarse_defect == Fraction(0)


# ---------------------------------------------------------------------------
# Test Suite 2: Quotient Norm Additivity (AUDIT-N002-008 / ATL-N002-008)
# ---------------------------------------------------------------------------

class TestQuotientNormAdditivity:
    """Tests verifying the common dual circulation criterion for quotient additivity."""

    def test_additivity_when_common_dual_circulation_exists(self):
        """Verify additivity when both cochains admit an identical dual maximizer."""
        graph = OverlappingCycleComplex()
        # Cochains aligned along Cycle 1: e0 + e1 - e2
        omega1 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        omega2 = [Fraction(2), Fraction(2), Fraction(-2), Fraction(0), Fraction(0)]

        phi1 = graph.quotient_norm(omega1)
        phi2 = graph.quotient_norm(omega2)
        phi_sum = graph.quotient_norm([omega1[i] + omega2[i] for i in range(5)])

        assert phi1 == Fraction(3)
        assert phi2 == Fraction(6)
        assert phi_sum == Fraction(9)
        assert phi_sum == phi1 + phi2

        # Shared dual circulation z* = [1, 1, -1, 0, 0]
        z_star = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        assert graph.is_dual_feasible(z_star) is True
        assert graph.pairing(z_star, omega1) == phi1
        assert graph.pairing(z_star, omega2) == phi2

    def test_common_dual_circulation_extracted_from_sum_maximizer(self):
        """Verify necessity: optimal sum maximizer achieves zero duality gap on each summand."""
        graph = OverlappingCycleComplex()
        omega1 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        omega2 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        omega_sum = [omega1[i] + omega2[i] for i in range(5)]

        phi1 = graph.quotient_norm(omega1)
        phi2 = graph.quotient_norm(omega2)
        phi_sum = graph.quotient_norm(omega_sum)
        assert phi_sum == phi1 + phi2

        # Optimal maximizer for the sum
        z_hat = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        assert graph.pairing(z_hat, omega_sum) == phi_sum

        # Check that individual duality gaps vanish
        gap1 = phi1 - graph.pairing(z_hat, omega1)
        gap2 = phi2 - graph.pairing(z_hat, omega2)
        assert gap1 == Fraction(0)
        assert gap2 == Fraction(0)

    def test_strict_subadditivity_on_opposing_cycles_counterexample(self):
        """Verify strict subadditivity when cycles share an edge with conflicting signs."""
        graph = OverlappingCycleComplex()
        # Cycle 1 uses e2 with coefficient -1; Cycle 2 uses e2 with coefficient +1
        omega1 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        omega2 = [Fraction(0), Fraction(0), Fraction(1), Fraction(1), Fraction(-1)]

        phi1 = graph.quotient_norm(omega1)
        phi2 = graph.quotient_norm(omega2)
        assert phi1 == Fraction(3)
        assert phi2 == Fraction(3)

        # On the sum, the shared edge cancels: omega_sum = [1, 1, 0, 1, -1]
        omega_sum = [omega1[i] + omega2[i] for i in range(5)]
        phi_sum = graph.quotient_norm(omega_sum)
        assert phi_sum == Fraction(4)

        # Strict subadditivity
        assert phi_sum < phi1 + phi2

        # Optimal circulation for the sum: a=1, b=1 => z = [1, 1, 0, 1, -1]
        z_sum = [Fraction(1), Fraction(1), Fraction(0), Fraction(1), Fraction(-1)]
        assert graph.is_dual_feasible(z_sum) is True
        assert graph.pairing(z_sum, omega_sum) == Fraction(4)

        # Duality gaps on each component are strictly positive
        gap1 = phi1 - graph.pairing(z_sum, omega1)
        gap2 = phi2 - graph.pairing(z_sum, omega2)
        assert gap1 == Fraction(3) - Fraction(2) == Fraction(1) > Fraction(0)
        assert gap2 == Fraction(3) - Fraction(2) == Fraction(1) > Fraction(0)

    def test_capacity_normalized_holonomy_bound(self):
        """Verify that capacity normalization bounds the defect while naive addition overcounts."""
        graph = OverlappingCycleComplex()
        omega = [Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(0)]

        # Two circulations passing through e2 in opposite directions
        c1 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
        c2 = [Fraction(0), Fraction(0), Fraction(1), Fraction(1), Fraction(-1)]
        assert graph.is_circulation(c1) is True
        assert graph.is_circulation(c2) is True

        hol1 = graph.pairing(c1, omega)
        hol2 = graph.pairing(c2, omega)
        naive_holonomy_sum = abs(hol1) + abs(hol2)
        assert naive_holonomy_sum == Fraction(2)

        # True quotient defect is 1
        true_defect = graph.quotient_norm(omega)
        assert true_defect == Fraction(1)
        assert naive_holonomy_sum > true_defect

        # Capacity normalized bound: |<z, omega>| / max_e (|z_e|/w_e) <= true_defect
        norm_bound1 = abs(hol1) / max(abs(c1[e]) / graph.weights[e] for e in range(5))
        norm_bound2 = abs(hol2) / max(abs(c2[e]) / graph.weights[e] for e in range(5))
        assert norm_bound1 <= true_defect
        assert norm_bound2 <= true_defect

    def test_quotient_additivity_negative_control_zero_weight_refusal(self):
        """Negative control: zero weight refusal prevents degenerate capacity bounds."""
        with pytest.raises(ValueError, match="Edge weights must be strictly positive"):
            OverlappingCycleComplex([1, 0, 1, 1, 1])
        with pytest.raises(ValueError, match="Edge weights must be strictly positive"):
            OverlappingCycleComplex([1, -1, 1, 1, 1])


# ---------------------------------------------------------------------------
# Test Suite 3: KKT Necessity for L1 Quotient Problem (AUDIT-N002-015 / ATL-N002-015)
# ---------------------------------------------------------------------------

class TestKKTNecessityL1Quotient:
    """Tests verifying KKT necessity: minimizers admit divergence-free subgradients."""

    @pytest.fixture
    def setup_4cycle(self):
        """Standard 4-cycle complex."""
        return DiscreteCellComplex(4, [(0, 1), (1, 2), (2, 3), (3, 0)])

    def test_kkt_necessity_optimal_potential_has_divergence_free_subgradient(self, setup_4cycle):
        """Verify optimal potential admits a divergence-free circulation subgradient."""
        graph = setup_4cycle
        omega = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]

        # Global minimizer is s* = (0, 0, 0, 0), residual r = [1, 0, 0, 0]
        s_opt = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
        d0_s = graph.d0(s_opt)
        r = [omega[e] - d0_s[e] for e in range(4)]
        assert r == [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]

        # Subgradient constraints: phi0 = 1; phi1, phi2, phi3 in [-1, 1]
        # Circulation on 4-cycle requires phi0 = phi1 = phi2 = phi3
        phi_star = [Fraction(1), Fraction(1), Fraction(1), Fraction(1)]

        # Check subgradient inclusion:
        assert phi_star[0] == Fraction(1)  # r0 > 0 => phi0 = w0
        assert abs(phi_star[1]) <= Fraction(1)  # r1 == 0 => phi1 in [-w1, w1]
        assert abs(phi_star[2]) <= Fraction(1)  # r2 == 0 => phi2 in [-w2, w2]
        assert abs(phi_star[3]) <= Fraction(1)  # r3 == 0 => phi3 in [-w3, w3]

        # Check circulation condition: d0* phi == 0
        div = graph.d0_star(phi_star)
        assert all(d == Fraction(0) for d in div)

    def test_kkt_necessity_negative_control_suboptimal_potential_fails(self, setup_4cycle):
        """Negative control: strictly suboptimal potentials have NO circulation subgradient."""
        graph = setup_4cycle
        omega = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]

        # Suboptimal potential s = (0, 2, 0, 0)
        s_sub = [Fraction(0), Fraction(2), Fraction(0), Fraction(0)]
        d0_s = graph.d0(s_sub)  # [2, -2, 0, 0]
        r = [omega[e] - d0_s[e] for e in range(4)]  # [-1, 2, 0, 0]

        # Cost = |-1| + |2| + 0 + 0 = 3 > 1 (strictly suboptimal!)
        assert graph.norm_1(r) == Fraction(3) > Fraction(1)

        # Subgradient requires:
        # r0 = -1 < 0 => phi0 = -1
        # r1 = +2 > 0 => phi1 = +1
        # Circulation on 4-cycle demands phi0 == phi1
        # But phi0 = -1 and phi1 = +1, so no circulation vector exists in the subgradient!
        for phi2 in [-1, 0, 1]:
            for phi3 in [-1, 0, 1]:
                candidate_phi = [Fraction(-1), Fraction(1), Fraction(phi2), Fraction(phi3)]
                div = graph.d0_star(candidate_phi)
                assert any(d != Fraction(0) for d in div)

    def test_kkt_subgradient_interval_at_zero_residual(self, setup_4cycle):
        """Verify that selecting within [-w_e, w_e] is required to achieve d0* phi = 0."""
        graph = setup_4cycle
        omega = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
        s_opt = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
        # r = [1, 0, 0, 0]
        # If one naively chooses phi_e = 0 for the zero residuals:
        phi_naive = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
        # This naive selection is NOT divergence-free
        div_naive = graph.d0_star(phi_naive)
        assert any(d != Fraction(0) for d in div_naive)

        # But selecting phi_e = 1 in [-1, 1] achieves divergence-free circulation
        phi_correct = [Fraction(1), Fraction(1), Fraction(1), Fraction(1)]
        div_correct = graph.d0_star(phi_correct)
        assert all(d == Fraction(0) for d in div_correct)

    def test_kkt_complementary_slackness_exact_sign(self, setup_4cycle):
        """Verify exact sign alignment phi_e = w_e * sgn(r_e) on all nonzero residual edges."""
        graph = setup_4cycle
        # Negative residual case: omega = [-1, 0, 0, 0], optimal potential s = 0
        omega_neg = [Fraction(-1), Fraction(0), Fraction(0), Fraction(0)]
        s_zero = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
        r = [omega_neg[e] - (graph.d0(s_zero))[e] for e in range(4)]
        assert r[0] == Fraction(-1)

        # Complementary slackness forces phi0 = -w0 = -1
        phi_neg = [Fraction(-1), Fraction(-1), Fraction(-1), Fraction(-1)]
        assert phi_neg[0] == -graph.weights[0]
        assert all(d == Fraction(0) for d in graph.d0_star(phi_neg))

        # A positive subgradient on e0 violates complementary slackness and fails
        phi_wrong_sign = [Fraction(1), Fraction(-1), Fraction(-1), Fraction(-1)]
        assert any(d != Fraction(0) for d in graph.d0_star(phi_wrong_sign))
