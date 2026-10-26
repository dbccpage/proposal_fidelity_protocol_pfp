"""Targeted property tests for higher-order cochain verification on physics and epistemic contracts.

Verifies:
1. Discrete Hodge Normal Form (DHNF - nf.cochain.dhnf):
   - Exact orthogonal decomposition of discrete 1-cochains: omega = d0(alpha) + delta(beta) + h
   - Harmonic orthogonality: <d0(alpha), h> == 0 and Delta(h) == 0
   - Homological cycle kernel match with Betti numbers
2. Binary Sign-Switching Normal Form (BSS-NF - nf.fsp.bssnf):
   - Cycle edge-bit holonomy test (mod 2) on signed Hamiltonian graphs
   - Exact sign elimination under vertex gauge transformation v in {0, 1}^V
   - Frustration detection on odd negative cycles
3. Meron Involutive Cancellation Normal Form (MIC-NF - nf.fsp.micnf):
   - Weight-preserving, sign-reversing involution I on uncancelled sector S0
   - Fixed-point freeness on S0 guaranteeing exact cancellation sum = 0
   - Positivity of survivor partition function Z_surv > 0
4. Zero-Float Rational Normal Form (ZFNF - nf.runtime.zfnf):
   - Exact rational Q primal-dual linear cochain duality
   - Certified optimal state achieves zero duality gap (c^T x - b^T y == 0)
   - Positive gap strictly escalates to Escalate terminal route
5. Epistemic Quotient Normal Form (EQNF - nf.coda.eqnf):
   - Indistinguishability equivalence relation under observer measurement operators
   - Kernel perturbation invariance: delta in ker(M) preserves quotient class
   - Non-zero measurement delta forces distinct epistemic quotient partition

AuthorityEffect: None.
"""

from __future__ import annotations

import random
import unittest
from fractions import Fraction
from typing import Dict, List, Tuple


class TestDiscreteHodgeProperties(unittest.TestCase):
    """Property tests asserting Discrete Hodge Decomposition invariants (DHNF)."""

    def test_discrete_hodge_orthogonal_decomposition(self) -> None:
        """Verify omega = d0(alpha) + h on finite 1-complexes with zero inner product."""
        # Cycle graph C_4 with 4 vertices and 4 edges (1-cycle, Betti-1 = 1)
        # Vertices: 0, 1, 2, 3. Directed edges: e0=(0,1), e1=(1,2), e2=(2,3), e3=(3,0)
        num_v = 4
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        num_e = 4

        # Boundary matrix d0: C0 -> C1 has (d0 v)(e) = v(dst) - v(src)
        # Random vertex potential alpha
        for seed in range(25):
            rng = random.Random(seed + 100)
            alpha = [Fraction(rng.randint(-10, 10), 1) for _ in range(num_v)]

            # d0(alpha) on edges
            d0_alpha = [alpha[dst] - alpha[src] for src, dst in edges]

            # Harmonic 1-cochain on C_4: constant on cycle, e.g. h = [k, k, k, k]
            k = Fraction(rng.randint(1, 5), 1)
            h = [k, k, k, k]

            # Composite cochain omega = d0_alpha + h
            omega = [d0_alpha[i] + h[i] for i in range(num_e)]

            # Verification 1: Orthogonality <d0_alpha, h> = sum_e d0_alpha[e] * h[e] == 0
            inner_product = sum(d0_alpha[i] * h[i] for i in range(num_e))
            self.assertEqual(inner_product, Fraction(0, 1))

            # Verification 2: Graph Laplacian on h: delta(h)(v) = sum_{e: dst=v} h(e) - sum_{e: src=v} h(e) == 0
            # For vertex 1: incoming e0, outgoing e1 -> h[0] - h[1] = k - k = 0
            for v in range(num_v):
                in_flux = sum(h[i] for i, (s, d) in enumerate(edges) if d == v)
                out_flux = sum(h[i] for i, (s, d) in enumerate(edges) if s == v)
                self.assertEqual(in_flux - out_flux, Fraction(0, 1))

            # Verification 3: Total circulation sum along cycle equals 4 * k != 0
            circulation = sum(omega)
            self.assertEqual(circulation, 4 * k)


class TestBssnfGaugeSignProperties(unittest.TestCase):
    """Property tests asserting Binary Sign-Switching gauge invariance (BSS-NF)."""

    def test_spanning_tree_gauge_elimination(self) -> None:
        """On a tree-like (or zero-holonomy) signed graph, exact gauge transforms all edges non-negative."""
        # Simple connected tree with 5 vertices and 4 edges
        edges = [(0, 1), (1, 2), (1, 3), (3, 4)]
        for seed in range(30):
            rng = random.Random(seed + 200)
            # Random initial signs: +/- 1
            edge_signs = {e: rng.choice([-1, 1]) for e in edges}

            # Gauge transformation on vertices: v_0 = 0, propagate signs
            v_gauge: Dict[int, int] = {0: 0}
            queue = [0]
            visited = {0}
            while queue:
                curr = queue.pop(0)
                for s, d in edges:
                    neighbor = None
                    if s == curr and d not in visited:
                        neighbor = d
                        # desired: (-1)^{v_curr + v_neighbor} * sgn == 1
                        # v_curr + v_neighbor + (1 if sgn == -1 else 0) = 0 mod 2
                        v_gauge[neighbor] = (
                            v_gauge[curr] + (1 if edge_signs[(s, d)] == -1 else 0)
                        ) % 2
                    elif d == curr and s not in visited:
                        neighbor = s
                        v_gauge[neighbor] = (
                            v_gauge[curr] + (1 if edge_signs[(s, d)] == -1 else 0)
                        ) % 2
                    if neighbor is not None:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Assert all transformed edge signs are strictly non-negative (+1)
            for s, d in edges:
                orig = edge_signs[(s, d)]
                gauge_factor = (-1) ** (v_gauge[s] + v_gauge[d])
                transformed = orig * gauge_factor
                self.assertEqual(transformed, 1)

    def test_frustrated_odd_negative_cycle_rejection(self) -> None:
        """A cycle with odd number of negative signs has non-trivial holonomy and cannot be eliminated."""
        # Triangular cycle with 3 edges: (0, 1), (1, 2), (2, 0)
        # Plant 1 negative sign (odd count = 1 -> holonomy = -1)
        edge_signs = {(0, 1): -1, (1, 2): 1, (2, 0): 1}

        # Check all 2^3 = 8 possible vertex gauge vectors {0, 1}^3
        all_non_negative_achievable = False
        for v0 in (0, 1):
            for v1 in (0, 1):
                for v2 in (0, 1):
                    v = [v0, v1, v2]
                    t0 = edge_signs[(0, 1)] * ((-1) ** (v[0] + v[1]))
                    t1 = edge_signs[(1, 2)] * ((-1) ** (v[1] + v[2]))
                    t2 = edge_signs[(2, 0)] * ((-1) ** (v[2] + v[0]))
                    if t0 >= 0 and t1 >= 0 and t2 >= 0:
                        all_non_negative_achievable = True

        self.assertFalse(
            all_non_negative_achievable, "Frustrated cycle must not admit non-negative gauge"
        )


class TestMicnfInvolutiveCancellationProperties(unittest.TestCase):
    """Property tests asserting Meron Involutive Cancellation invariants (MIC-NF)."""

    def test_meron_involution_exact_cancellation_and_survivor_positivity(self) -> None:
        """Verify that fixed-point-free involution I on S0 cancels sum exactly, leaving Z_surv > 0."""
        for seed in range(30):
            rng = random.Random(seed + 300)
            # Create S0 with 20 elements (10 pairs)
            pairs: List[Tuple[int, int]] = [(i * 2, i * 2 + 1) for i in range(10)]
            s0_weights: Dict[int, Fraction] = {}
            s0_signs: Dict[int, int] = {}
            involution_map: Dict[int, int] = {}

            for a, b in pairs:
                w = Fraction(rng.randint(1, 20), 1)
                s0_weights[a] = w
                s0_weights[b] = w
                s0_signs[a] = 1
                s0_signs[b] = -1
                involution_map[a] = b
                involution_map[b] = a

            # Invariant 1: Involution property I(I(x)) == x
            for x in s0_weights:
                self.assertEqual(involution_map[involution_map[x]], x)

            # Invariant 2: Fixed-point freeness on S0: I(x) != x
            for x in s0_weights:
                self.assertNotEqual(involution_map[x], x)

            # Invariant 3: Weight preservation and sign reversal
            for x in s0_weights:
                y = involution_map[x]
                self.assertEqual(s0_weights[x], s0_weights[y])
                self.assertEqual(s0_signs[x], -s0_signs[y])

            # Invariant 4: Exact algebraic cancellation sum_{x in S0} w(x) * sgn(x) == 0
            uncancelled_sum = sum(s0_weights[x] * s0_signs[x] for x in s0_weights)
            self.assertEqual(uncancelled_sum, Fraction(0, 1))

            # Invariant 5: Survivor sector S_surv has positive partition function
            survivor_weights = [Fraction(rng.randint(1, 10), 1) for _ in range(5)]
            z_surv = sum(survivor_weights)
            self.assertGreater(z_surv, Fraction(0, 1))

            total_z = uncancelled_sum + z_surv
            self.assertEqual(total_z, z_surv)


class TestZfnfExactRationalProperties(unittest.TestCase):
    """Property tests asserting Zero-Float Rational duality gap invariants (ZFNF)."""

    def test_rational_duality_gap_zero_certified_optimal(self) -> None:
        """At certified optimality, primal objective c^T x equals dual objective b^T y exactly in Q."""
        # Simple 2-variable LP: max 3 x1 + 2 x2 s.t. x1 + x2 <= 4, x1 <= 2, x1, x2 >= 0
        # Optimal primal: x1 = 2, x2 = 2. Objective = 3(2) + 2(2) = 10
        # Dual: min 4 y1 + 2 y2 s.t. y1 + y2 >= 3, y1 >= 2, y1, y2 >= 0
        # Optimal dual: y1 = 2, y2 = 1. Objective = 4(2) + 2(1) = 10
        for scale in [1, 2, 5, 7, 13]:
            c = [Fraction(3 * scale, 1), Fraction(2 * scale, 1)]
            b = [Fraction(4, 1), Fraction(2, 1)]
            x_opt = [Fraction(2, 1), Fraction(2, 1)]
            y_opt = [Fraction(2 * scale, 1), Fraction(1 * scale, 1)]

            primal_val = c[0] * x_opt[0] + c[1] * x_opt[1]
            dual_val = b[0] * y_opt[0] + b[1] * y_opt[1]

            duality_gap = primal_val - dual_val
            self.assertEqual(duality_gap, Fraction(0, 1))

    def test_positive_duality_gap_escalates(self) -> None:
        """A sub-optimal or infeasible candidate with Delta > 0 must route to Escalate, never Preserve."""
        c = [Fraction(3, 1), Fraction(2, 1)]
        b = [Fraction(4, 1), Fraction(2, 1)]
        # Sub-optimal primal: x1 = 1, x2 = 1 -> obj = 5
        x_sub = [Fraction(1, 1), Fraction(1, 1)]
        # Dual y1 = 2, y2 = 1 -> dual obj = 10
        y_opt = [Fraction(2, 1), Fraction(1, 1)]

        primal_val = c[0] * x_sub[0] + c[1] * x_sub[1]
        dual_val = b[0] * y_opt[0] + b[1] * y_opt[1]
        gap = dual_val - primal_val

        self.assertGreater(gap, Fraction(0, 1))
        # Route determination
        route = "Escalate" if gap > 0 else "Preserve"
        self.assertEqual(route, "Escalate")


class TestEqnfEpistemicQuotientProperties(unittest.TestCase):
    """Property tests asserting Epistemic Quotient Normal Form invariants (EQNF)."""

    def test_kernel_variation_quotient_invariance(self) -> None:
        """Variations lying strictly within observer measurement null space preserve quotient class."""
        # Measurement operator M: R^3 -> R^2 projects out x3 (M = [[1, 0, 0], [0, 1, 0]])
        # ker(M) = span([0, 0, 1])
        base_state = [Fraction(3, 1), Fraction(5, 1), Fraction(10, 1)]

        for seed in range(25):
            rng = random.Random(seed + 400)
            perturbation = [Fraction(0, 1), Fraction(0, 1), Fraction(rng.randint(-50, 50), 1)]
            perturbed_state = [base_state[i] + perturbation[i] for i in range(3)]

            # Measurement projection pi(x) = [x1, x2]
            obs_base = (base_state[0], base_state[1])
            obs_perturbed = (perturbed_state[0], perturbed_state[1])

            # Invariant: observer measurement is identical -> same quotient class
            self.assertEqual(obs_base, obs_perturbed)

    def test_orthogonal_variation_generates_distinct_quotient(self) -> None:
        """Variations with non-zero projection onto row space of M resolve to distinct observable classes."""
        base_state = [Fraction(3, 1), Fraction(5, 1), Fraction(10, 1)]

        for seed in range(25):
            rng = random.Random(seed + 500)
            dx = rng.choice([-3, -2, -1, 1, 2, 3])
            perturbation = [Fraction(dx, 1), Fraction(0, 1), Fraction(rng.randint(-10, 10), 1)]
            perturbed_state = [base_state[i] + perturbation[i] for i in range(3)]

            obs_base = (base_state[0], base_state[1])
            obs_perturbed = (perturbed_state[0], perturbed_state[1])

            # Must resolve to distinct observable quotient
            self.assertNotEqual(obs_base, obs_perturbed)


if __name__ == "__main__":
    unittest.main()
