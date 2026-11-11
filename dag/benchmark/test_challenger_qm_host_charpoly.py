"""Independent Empirical Challenger & Adversarial Stress Harness for Milestone 2.

Authored by Independent Checker / Attack Reviewer to rigorously test:
1. Exact rational arithmetic, Leibniz vs Laplace engine equivalence, and theoretical identity.
2. Degree bounds and Schwartz-Zippel grid uniqueness (no non-zero degree <= 4 polynomial vanishes on grid).
3. Adversarial mutations and boundary conditions (single coefficient alterations, malformed rationals,
   whitespace variations in injection/contradiction payloads).
4. Strict false-acceptance prevention across native sidecar grid evaluation (witness generation).
5. Strict false-refusal prevention on authentic host-derived polynomials.
6. Absolute intermediate vs final contradiction firewall.
"""
from __future__ import annotations

import json
import random
import unittest
from copy import deepcopy
from fractions import Fraction
from itertools import product

import qm_host_charpoly as host


def build_raw_candidate(coefficients: list[list[dict]], extra_keys: dict | None = None) -> str:
    payload = {"coefficients": coefficients}
    if extra_keys:
        payload.update(extra_keys)
    return json.dumps(payload, separators=(",", ":"))


class TestChallengerExactAlgebraAndEngines(unittest.TestCase):
    """Rigorous verification of algebraic determinant engines and theoretical polynomial identity."""

    def test_theoretical_factorization_identity(self):
        """Verify det(lambda*I - H) == (lambda - K)^2 * ((lambda + K)^2 - 4J^2 - 4Delta^2) symbolically."""
        derived = host.derive_host_charpoly()
        poly = derived["polynomial"]

        # Theoretical coefficients in lambda^m * J^j * Delta^d * K^k:
        # lambda^4: 1
        # lambda^2: -2 K^2 - 4 J^2 - 4 Delta^2
        # lambda^1: 8 J^2 K + 8 Delta^2 K
        # lambda^0: K^4 - 4 J^2 K^2 - 4 Delta^2 K^2
        expected_poly = {
            (4, 0, 0, 0): Fraction(1),
            (2, 0, 0, 2): Fraction(-2),
            (2, 2, 0, 0): Fraction(-4),
            (2, 0, 2, 0): Fraction(-4),
            (1, 2, 0, 1): Fraction(8),
            (1, 0, 2, 1): Fraction(8),
            (0, 0, 0, 4): Fraction(1),
            (0, 2, 0, 2): Fraction(-4),
            (0, 0, 2, 2): Fraction(-4),
        }
        self.assertEqual(poly, expected_poly)

    def test_random_rational_evaluations_against_theoretical_formula(self):
        """Stress-test off-grid rational points against closed-form factorization."""
        derived = host.derive_host_charpoly()
        poly = derived["polynomial"]

        rng = random.Random(42)  # noqa: S311
        for _ in range(200):
            lam = Fraction(rng.randint(-50, 50), rng.randint(1, 20))
            j = Fraction(rng.randint(-50, 50), rng.randint(1, 20))
            delta = Fraction(rng.randint(-50, 50), rng.randint(1, 20))
            k = Fraction(rng.randint(-50, 50), rng.randint(1, 20))

            # Closed form: (lambda - K)^2 * ((lambda + K)^2 - 4*J^2 - 4*Delta^2)
            factor1 = (lam - k) ** 2
            factor2 = (lam + k) ** 2 - 4 * (j ** 2) - 4 * (delta ** 2)
            expected_val = factor1 * factor2

            # Polynomial evaluation
            poly_val = Fraction(0)
            for exp, coeff in poly.items():
                poly_val += (
                    coeff
                    * (lam ** exp[0])
                    * (j ** exp[1])
                    * (delta ** exp[2])
                    * (k ** exp[3])
                )

            self.assertEqual(poly_val, expected_val)

    def test_dual_engine_equivalence_on_random_matrices(self):
        """Verify that Leibniz and Laplace engines produce identical results on random 4x4 polynomial matrices."""
        rng = random.Random(1337)  # noqa: S311
        for _ in range(10):
            matrix: list[list[host.Polynomial]] = []
            for _r in range(4):
                row: list[host.Polynomial] = []
                for _c in range(4):
                    # sparse polynomial with 1 or 2 monomials
                    entry: host.Polynomial = {}
                    num_terms = rng.randint(0, 2)
                    for _t in range(num_terms):
                        exp = (
                            rng.randint(0, 1),
                            rng.randint(0, 1),
                            rng.randint(0, 1),
                            rng.randint(0, 1),
                        )
                        entry[exp] = Fraction(rng.randint(-5, 5), rng.randint(1, 4))
                    row.append({k: v for k, v in entry.items() if v != 0})
                matrix.append(row)

            det_l = host.det_leibniz(matrix)
            det_lp = host.det_laplace(matrix)
            self.assertEqual(det_l, det_lp)


class TestChallengerGridUniquenessAndDegreeAliasing(unittest.TestCase):
    """Verify Schwartz-Zippel / polynomial identity bounds and degree aliasing defenses."""

    def test_no_nonzero_poly_of_per_variable_degree_4_vanishes_on_125_grid(self):
        """Empirically test that random non-zero polynomials with deg <= 4 NEVER vanish on all 125 grid points."""
        rng = random.Random(999)  # noqa: S311
        grid_nodes = host.GRID_NODES

        for _ in range(50):
            # Generate a non-zero parameter polynomial with per-variable degree <= 4
            num_monomials = rng.randint(1, 5)
            poly: dict[tuple[int, int, int], Fraction] = {}
            for _ in range(num_monomials):
                exp = (rng.randint(0, 4), rng.randint(0, 4), rng.randint(0, 4))
                coeff = Fraction(rng.randint(-10, 10), rng.randint(1, 5))
                if coeff != 0:
                    poly[exp] = coeff

            if not poly:
                continue

            # Evaluate on all 125 grid points
            vanished_on_all = True
            for j, d, k in product(grid_nodes, repeat=3):
                val = sum(c * (j ** e[0]) * (d ** e[1]) * (k ** e[2]) for e, c in poly.items())
                if val != 0:
                    vanished_on_all = False
                    break

            # Under the Polynomial Identity Theorem, it is mathematically impossible to vanish on all 125 points
            self.assertFalse(vanished_on_all, f"Found non-zero poly vanishing on 125 grid: {poly}")

    def test_degree_aliasing_attack_variants_rejected(self):
        """Test variations of grid-vanishing polynomial (J^5 - 5J^3 + 4J) attached to different lambda powers."""
        base_coeffs = deepcopy(host.derive_host_charpoly()["normalized_coefficients"])

        # Try adding aliasing polynomial to lambda^2, lambda^1, and lambda^0
        for lam_pow in [0, 1, 2]:
            mutated = deepcopy(base_coeffs)
            mutated[lam_pow].append({"powers": [5, 0, 0], "q": "1"})
            mutated[lam_pow].append({"powers": [3, 0, 0], "q": "-5"})
            mutated[lam_pow].append({"powers": [1, 0, 0], "q": "4"})

            receipt = host.verify_candidate_charpoly(build_raw_candidate(mutated))
            self.assertFalse(receipt["accepted"])
            self.assertIn(
                receipt["refusal_code"],
                {"JSON_INTEGER_OUT_OF_PROFILE", "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED", "DEGREE_LIMIT_EXCEEDED"},
            )


class TestChallengerMutationMatrix(unittest.TestCase):
    """Stress-test single-coefficient mutations against native sidecar verification (False Acceptance Gate)."""

    @classmethod
    def setUpClass(cls):
        cls.base_coeffs = deepcopy(host.derive_host_charpoly()["normalized_coefficients"])

    def test_perturb_every_nonzero_monomial_coefficient(self):
        """Perturb every single non-zero monomial in the characteristic polynomial.

        Every single perturbation MUST be rejected, and if wire-valid, MUST be refuted on native grid
        with a concrete witness showing claimed != native.
        """
        for lam_idx, terms in enumerate(self.base_coeffs):
            if lam_idx == 4:
                continue  # Leading monic tested separately
            for term_idx, term in enumerate(terms):
                original_q = Fraction(term["q"])
                for delta_q in [Fraction(1), Fraction(-1), Fraction(1, 2)]:
                    mutated = deepcopy(self.base_coeffs)
                    new_q = original_q + delta_q
                    if new_q == 0:
                        continue
                    mutated[lam_idx][term_idx]["q"] = str(new_q)

                    raw = build_raw_candidate(mutated)
                    receipt = host.verify_candidate_charpoly(raw)

                    self.assertFalse(
                        receipt["accepted"],
                        f"False acceptance on lambda^{lam_idx} term {term['powers']} perturbed to {new_q}",
                    )
                    self.assertEqual(receipt["status"], "REFUTED_IDENTITY")
                    self.assertIsNotNone(receipt["witness"])
                    self.assertNotEqual(receipt["witness"]["claimed"], receipt["witness"]["native"])

    def test_monic_leading_coefficient_mutations(self):
        """Verify that any tampering with leading lambda^4 coefficient is rejected."""
        for bad_lead in ["0", "-1", "2", "1/2", "3/4", "999"]:
            mutated = deepcopy(self.base_coeffs)
            mutated[4] = [{"powers": [0, 0, 0], "q": bad_lead}]
            receipt = host.verify_candidate_charpoly(build_raw_candidate(mutated))
            self.assertFalse(receipt["accepted"])
            self.assertEqual(receipt["refusal_code"], "NONMONIC_LEADING_COEFFICIENT")

    def test_leading_lambda_with_nonzero_parameter_powers(self):
        """Verify that lambda^4 with non-zero parameter powers is rejected."""
        for bad_powers in [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]:
            mutated = deepcopy(self.base_coeffs)
            mutated[4] = [{"powers": bad_powers, "q": "1"}]
            receipt = host.verify_candidate_charpoly(build_raw_candidate(mutated))
            self.assertFalse(receipt["accepted"])
            self.assertEqual(receipt["refusal_code"], "NONMONIC_LEADING_COEFFICIENT")


class TestChallengerIntermediateFinalFirewall(unittest.TestCase):
    """Stress-test intermediate vs final contradiction detection and prompt injection."""

    def test_whitespace_variations_in_contradiction_payload(self):
        """Verify that tabs, newlines, and varied whitespace in final_answer_certified are rejected."""
        base_coeffs = deepcopy(host.derive_host_charpoly()["normalized_coefficients"])

        whitespace_cases = [
            '{"coefficients": ' + json.dumps(base_coeffs) + ', "final_answer_certified":\n true}',
            '{"coefficients": ' + json.dumps(base_coeffs) + ', "final_answer_certified":\t true}',
            '{"coefficients": ' + json.dumps(base_coeffs) + ', "final_answer_certified":\r\n true}',
            '{"coefficients": ' + json.dumps(base_coeffs) + ', "final_answer_certified": true }',
        ]
        for payload in whitespace_cases:
            receipt = host.verify_candidate_charpoly(payload)
            self.assertFalse(receipt["accepted"])
            # Either preflight catches it or wire refuses closed coefficients object
            self.assertIn(
                receipt["refusal_code"],
                {"CONTRADICTION_FINAL_ANSWER_CLAIM", "CLOSED_COEFFICIENTS_OBJECT_REQUIRED"},
            )

    def test_validate_certified_context_strict_type_enforcement(self):
        """Verify that validate_certified_context rejects non-boolean or non-False values."""
        context = host.build_certified_context()

        for bad_val in [True, 1, 0, "False", "true", None, []]:
            bad_ctx = deepcopy(context)
            bad_ctx["limitations"]["final_answer_certified"] = bad_val
            with self.assertRaises(host.HostCharpolyRefusalError) as err:
                host.validate_certified_context(bad_ctx)
            self.assertEqual(err.exception.code, "CONTRADICTION_FINAL_ANSWER_CLAIM")

    def test_uncertified_obligations_subset_checking(self):
        """Verify that omitting even a single uncertified obligation is refused."""
        context = host.build_certified_context()

        for omitted_obligation in host.UNCERTIFIED_OBLIGATIONS:
            bad_ctx = deepcopy(context)
            obligations = [o for o in host.UNCERTIFIED_OBLIGATIONS if o != omitted_obligation]
            bad_ctx["limitations"]["uncertified_obligations"] = obligations
            with self.assertRaises(host.HostCharpolyRefusalError) as err:
                host.validate_certified_context(bad_ctx)
            self.assertEqual(err.exception.code, "CONTRADICTION_FINAL_ANSWER_CLAIM")


class TestChallengerLagrangeAndCompactContext(unittest.TestCase):
    """Challenger tests for Milestone 2: tensor Lagrange exactness and compact context limits."""

    def test_challenger_lagrange_basis_random_rational_interpolation(self):
        """Verify that any degree <= 4 rational polynomial is reconstructed exactly from 5 nodes."""
        rng = random.Random(999)
        nodes = list(host.GRID_NODES)
        # Random polynomial of degree <= 4
        poly_coeffs = [Fraction(rng.randint(-20, 20), rng.randint(1, 10)) for _ in range(5)]
        eval_at = lambda x: sum(c * (Fraction(x) ** d) for d, c in enumerate(poly_coeffs))

        # Sample at the 5 nodes
        node_vals = [eval_at(x) for x in nodes]

        # Reconstruct via 1D Lagrange basis
        reconstructed_coeffs = [Fraction(0)] * 5
        for i, val in enumerate(node_vals):
            basis_i = host.lagrange_basis_1d(nodes, i)
            for deg, coeff in basis_i.items():
                reconstructed_coeffs[deg] += val * coeff

        self.assertEqual(reconstructed_coeffs, poly_coeffs)

    def test_challenger_trivariate_lagrange_against_closed_form(self):
        """Verify trivariate Lagrange reconstruction matches closed-form factorization for various K."""
        matrices = host.admit_public_matrices(host.SUPPORTED_SEED_SHA256)
        rng = random.Random(2026)

        for k_int in [-3, -1, 0, 1, 3]:
            k_val = Fraction(k_int)
            poly_tri = host.interpolate_trivariate_charpoly(matrices, host.GRID_NODES, K_val=k_val)

            # Test 20 off-grid evaluation points
            for _ in range(20):
                lam = Fraction(rng.randint(-15, 15), rng.randint(1, 5))
                g1 = Fraction(rng.randint(-15, 15), rng.randint(1, 5))
                g2 = Fraction(rng.randint(-15, 15), rng.randint(1, 5))

                # Theoretical closed form: (lambda - K)^2 * ((lambda + K)^2 - 4*g1^2 - 4*g2^2)
                expected = ((lam - k_val) ** 2) * (((lam + k_val) ** 2) - 4 * (g1 ** 2) - 4 * (g2 ** 2))

                actual = sum(
                    coeff * (lam ** exp[0]) * (g1 ** exp[1]) * (g2 ** exp[2])
                    for exp, coeff in poly_tri.items()
                )
                self.assertEqual(actual, expected)

    def test_challenger_compact_context_budget_and_absence_of_internal_tokens(self):
        """Verify strict character count <= 1,200 and zero internal error token leakage."""
        compact = host.build_compact_certificate()
        serialized = json.dumps(compact, sort_keys=True, separators=(",", ":"))

        # Budget ceiling
        self.assertLessEqual(len(serialized), 1200)

        # Zero failure state names or descriptions
        for err_code, err_desc in host.FAILURE_STATES.items():
            self.assertNotIn(err_code, serialized)
            self.assertNotIn(err_desc, serialized)

        # Disclaiming notice must be present
        self.assertIn("limitations", compact)
        self.assertFalse(compact["limitations"]["final_answer_certified"])
        self.assertIn("notice", compact["limitations"])

    def test_challenger_trivariate_lagrange_125_node_uniqueness_under_perturbation(self):
        """Verify that perturbing any single scalar evaluation across all 125 grid nodes alters the polynomial."""
        nodes = host.GRID_NODES
        n_nodes = len(nodes)
        basis = [host.lagrange_basis_1d(nodes, idx) for idx in range(n_nodes)]

        perturbed_count = 0
        for i, j, k in product(range(n_nodes), repeat=3):
            # Delta polynomial contributed by perturbing node (i, j, k) by delta = 1:
            delta_poly: dict[tuple[int, int, int], Fraction] = {}
            for d_lam, c_lam in basis[k].items():
                for d_g1, c_g1 in basis[i].items():
                    for d_g2, c_g2 in basis[j].items():
                        c = Fraction(1) * c_lam * c_g1 * c_g2
                        key = (d_lam, d_g1, d_g2)
                        delta_poly[key] = delta_poly.get(key, Fraction(0)) + c
            delta_poly = {k: v for k, v in delta_poly.items() if v != 0}
            if len(delta_poly) > 0:
                perturbed_count += 1

        self.assertEqual(perturbed_count, 125, "Every node perturbation must produce a distinct polynomial")

    def test_challenger_full_grid_4var_lagrange_625_perturbation_uniqueness(self):
        """Verify that perturbing any single scalar determinant evaluation at any of 625 points alters 4-var poly."""
        nodes = host.GRID_NODES
        n_nodes = len(nodes)
        basis = [host.lagrange_basis_1d(nodes, idx) for idx in range(n_nodes)]

        perturbed_count = 0
        for param_idx in range(125):
            for lam_idx in range(5):
                i = param_idx // 25
                j = (param_idx % 25) // 5
                k = param_idx % 5
                delta_poly: dict[tuple[int, int, int, int], Fraction] = {}
                for d_lam, c_lam in basis[lam_idx].items():
                    for d_j, c_j in basis[i].items():
                        for d_d, c_d in basis[j].items():
                            for d_k, c_k in basis[k].items():
                                c = Fraction(1) * c_lam * c_j * c_d * c_k
                                exp = (d_lam, d_j, d_d, d_k)
                                delta_poly[exp] = delta_poly.get(exp, Fraction(0)) + c
                delta_poly = {k: v for k, v in delta_poly.items() if v != 0}
                if len(delta_poly) > 0:
                    perturbed_count += 1

        self.assertEqual(perturbed_count, 625, "All 625 point perturbations must change 4-var polynomial")

    def test_challenger_lagrange_arbitrary_rational_nodes_and_partition_of_unity(self):
        """Verify Kronecker delta and partition of unity on arbitrary non-integer rational nodes."""
        frac_nodes = [Fraction(1, 3), Fraction(-2, 5), Fraction(7, 11), Fraction(4, 7), Fraction(-5, 2)]
        frac_bases = [host.lagrange_basis_1d(frac_nodes, idx) for idx in range(5)]

        # Kronecker delta
        for i, xi in enumerate(frac_nodes):
            for j, xj in enumerate(frac_nodes):
                val = sum(c * (xj ** d) for d, c in frac_bases[i].items())
                self.assertEqual(val, Fraction(1) if i == j else Fraction(0))

        # Partition of unity off-grid
        rng = random.Random(12345)
        for _ in range(30):
            x_test = Fraction(rng.randint(-100, 100), rng.randint(1, 50))
            sum_val = sum(sum(c * (x_test ** d) for d, c in b.items()) for b in frac_bases)
            self.assertEqual(sum_val, Fraction(1))

    def test_challenger_trivariate_lagrange_fractional_nodes_and_rational_k(self):
        """Verify trivariate Lagrange reconstruction with half-integer grid nodes and rational coupling K."""
        matrices = host.admit_public_matrices()
        half_nodes = [Fraction(-3, 2), Fraction(-1, 2), Fraction(0), Fraction(1, 2), Fraction(3, 2)]
        k_val = Fraction(3, 7)
        poly_half = host.interpolate_trivariate_charpoly(matrices, half_nodes, K_val=k_val)

        # Off-grid evaluation against closed-form factorization
        rng = random.Random(54321)
        for _ in range(25):
            lam = Fraction(rng.randint(-10, 10), rng.randint(1, 5))
            g1 = Fraction(rng.randint(-10, 10), rng.randint(1, 5))
            g2 = Fraction(rng.randint(-10, 10), rng.randint(1, 5))
            expected = ((lam - k_val) ** 2) * (((lam + k_val) ** 2) - 4 * (g1 ** 2) - 4 * (g2 ** 2))
            actual = sum(coeff * (lam ** exp[0]) * (g1 ** exp[1]) * (g2 ** exp[2]) for exp, coeff in poly_half.items())
            self.assertEqual(actual, expected)

    def test_challenger_large_rational_stability_50_digits(self):
        """Stress-test scalar determinant engine stability with 50-digit rational matrix entries."""
        rng = random.Random(9999)
        mat = []
        for _r in range(4):
            row = []
            for _c in range(4):
                num = rng.randint(10**40, 10**45) * rng.choice([1, -1])
                den = rng.randint(10**30, 10**35)
                row.append(Fraction(num, den))
            mat.append(row)
        det = host.eval_scalar_det_4x4(mat)
        self.assertIsInstance(det, Fraction)

    def test_challenger_degree_bounds_parameter_and_total_degree_rejection(self):
        """Verify direct rejection of monomials exceeding per-variable or total parameter degree bounds."""
        base_coeffs = deepcopy(host.derive_host_charpoly()["normalized_coefficients"])

        # Exponent 5 in single variable J
        mut_deg = deepcopy(base_coeffs)
        mut_deg[0].append({"powers": [5, 0, 0], "q": "1"})
        code, _ = host._check_parsed_coefficient_degrees(mut_deg)
        self.assertEqual(code, "DEGREE_LIMIT_EXCEEDED")

        # Total degree 5 (J^2 * Delta^2 * K^1)
        mut_tot = deepcopy(base_coeffs)
        mut_tot[0].append({"powers": [2, 2, 1], "q": "1"})
        code, _ = host._check_parsed_coefficient_degrees(mut_tot)
        self.assertEqual(code, "DEGREE_LIMIT_EXCEEDED")

    def test_challenger_compact_context_tampering_vulnerabilities_observed(self):
        """Verify that validate_certified_context strictly refuses tampered certificate fields."""
        compact = host.build_compact_certificate()

        # 1. Altered polynomial standard_form
        bad_poly = deepcopy(compact)
        bad_poly["polynomial"]["standard_form"] = "lambda^4 - 999*lambda^2"
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_poly)
        self.assertEqual(ctx.exception.code, "CONTRADICTION_FINAL_ANSWER_CLAIM")

        # 2. Altered degree bounds
        bad_deg = deepcopy(compact)
        bad_deg["carrier"]["degree_bounds"]["lambda"] = 99
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_deg)
        self.assertEqual(ctx.exception.code, "DEGREE_LIMIT_EXCEEDED")

        # 3. Altered domain
        bad_dom = deepcopy(compact)
        bad_dom["carrier"]["domain"] = "Complex"
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_dom)
        self.assertEqual(ctx.exception.code, "FORGED_CERTIFICATE")

        # 4. Altered limitation notice claiming full solution
        bad_not = deepcopy(compact)
        bad_not["limitations"]["notice"] = "This is a certified full QM solution!"
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_not)
        self.assertEqual(ctx.exception.code, "CONTRADICTION_FINAL_ANSWER_CLAIM")

        # 5. Altered native verification status
        bad_nat = deepcopy(compact)
        bad_nat["native_verification"]["status"] = "FORGED"
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_nat)
        self.assertEqual(ctx.exception.code, "FORGED_CERTIFICATE")

        # 6. Altered public Hamiltonian matrix
        bad_mat = deepcopy(compact)
        bad_mat["public_hamiltonian"]["matrix"][0][0] = "999*K"
        with self.assertRaises(host.HostCharpolyRefusalError) as ctx:
            host.validate_certified_context(bad_mat)
        self.assertEqual(ctx.exception.code, "PUBLIC_INPUT_MISMATCH")

    def test_challenger_tampered_compact_certificate_rejection_expected(self):
        """validate_certified_context MUST refuse tampered polynomial strings, bounds, and notices.

        Integrity remediated: verifies strict refusal on altered polynomial strings,
        degree bounds, and limitation notices.
        """
        compact = host.build_compact_certificate()

        bad_poly = deepcopy(compact)
        bad_poly["polynomial"]["standard_form"] = "lambda^4 - 999*lambda^2"
        with self.assertRaises(host.HostCharpolyRefusalError):
            host.validate_certified_context(bad_poly)

        bad_deg = deepcopy(compact)
        bad_deg["carrier"]["degree_bounds"]["lambda"] = 99
        with self.assertRaises(host.HostCharpolyRefusalError):
            host.validate_certified_context(bad_deg)

        bad_not = deepcopy(compact)
        bad_not["limitations"]["notice"] = "This is a certified full QM solution!"
        with self.assertRaises(host.HostCharpolyRefusalError):
            host.validate_certified_context(bad_not)



if __name__ == "__main__":
    unittest.main(verbosity=2)
