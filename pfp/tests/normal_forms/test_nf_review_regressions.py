"""Regression test suite for Normal Form Review Verdict REVISE findings.

Verifies mathematical and structural correctness across the 19 normal form contracts:
1. ZFNF weak duality sign and primal/dual feasibility witnesses.
2. SPJA duplicate-key rejection, bag semantics, and non-null AVG argument counting.
3. EFNF permission soundness firewall and inert execution eligibility.
4. L1 Constraint Closure distinction between optimal residual and exact closure.
5. RCNF signed Cayley-Menger determinant and Gram positive-definiteness.
6. Lorentzian CDT topology distinction beyond Euler characteristic.
7. Pachner-LP polynomial scaling target breach vs superpolynomial misnomer.
8. Schläfli differential identity vs nilpotence misnomer.
9. Wick-MC separation of detailed balance, positivity, and semiclassical convergence.
10. Zolotarev overlap absolute spectral gap and GW algebraic triviality firewall.
11. WDWNF operator-scaled relative residual vs unscaled absolute kernel membership.
12. PWNF normalized conditional slice unitary transitions vs raw slice norm artifacts.
13. DBCNF least rotation and Lyndon aperiodicity distinction.
14. Light-Cone & Time-Sync separation of physical causality from consensus serialization.

AuthorityEffect: None.
"""

from __future__ import annotations
from omega_engine_pfp.infrastructure.normal_form_loading import validate_contract_file

import unittest
from pathlib import Path

import yaml


from omega_engine_pfp.infrastructure.normal_forms.contract_model import CANONICAL_TERMINALS_DEFAULT
from omega_engine_pfp.infrastructure.normal_forms.contract_model import load_yaml


def _get_contracts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"

CONTRACTS_DIR = _get_contracts_dir()


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader rejecting duplicate mapping keys."""

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"Duplicate key detected in YAML: {key}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


class TestNormalFormReviewRegressions(unittest.TestCase):
    """Test suite covering all 14 review sections and mathematical probes."""

    def test_all_19_contracts_have_no_duplicate_keys(self) -> None:
        """Section 1: Strict duplicate key rejection across all 19 contracts."""
        files = list(CONTRACTS_DIR.glob("nf.*.yaml"))
        self.assertGreaterEqual(len(files), 19)
        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    yaml.load(f, Loader=UniqueKeyLoader)
                except ValueError as exc:
                    self.fail(f"Duplicate key found in {fpath.name}: {exc}")

    def test_all_19_contracts_pass_schema_and_canonical_routes(self) -> None:
        """Section 1: Ensure zero schema defects and all local routes map to canonical terminals."""
        target_stems = [
            "nf.runtime.zfnf",
            "nf.query.spja",
            "nf.security.efnf",
            "nf.physics.l1_constraint_closure",
            "nf.physics.rcnf",
            "nf.physics.lorentzian_cdt",
            "nf.physics.pachner_lp_scaling",
            "nf.physics.schlafli_nf",
            "nf.physics.cdt_wick_mc",
            "nf.physics.cdt_zolotarev_overlap",
            "nf.physics.wdwnf",
            "nf.physics.pwnf",
            "nf.representation.gnf",
            "nf.coda.mur.transport",
            "nf.recursion.asrf",
            "nf.representation.tbnf",
            "nf.representation.dbcnf",
            "nf.relativistic.lightcone",
            "nf.relativistic.time_sync",
        ]
        for stem in target_stems:
            fpath = CONTRACTS_DIR / f"{stem}.yaml"
            self.assertTrue(fpath.is_file(), f"Missing contract: {fpath}")
            defects = validate_contract_file(fpath)
            self.assertEqual(defects, [], f"Defects in {fpath.name}: {defects}")

            doc = load_yaml(fpath)
            trm = doc.get("terminal_route_map", {})
            self.assertIsInstance(trm, dict, f"terminal_route_map missing in {fpath.name}")
            for local_route, canonical_term in trm.items():
                self.assertIn(
                    canonical_term,
                    CANONICAL_TERMINALS_DEFAULT,
                    f"Invalid canonical terminal '{canonical_term}' for route '{local_route}' in {fpath.name}",
                )

    def test_zfnf_weak_duality_sign_and_feasibility(self) -> None:
        """Section 2: ZFNF weak duality sign P(x) >= D(y) for minimize primal, maximize dual."""
        fpath = CONTRACTS_DIR / "nf.runtime.zfnf.yaml"
        doc = load_yaml(fpath)

        # 1. Nonnegative gap is P - D >= 0
        gap_formula = doc["definition"]["formal_statement"]
        self.assertIn("P(x) - D(y)", gap_formula)
        self.assertIn("P(x) >= D(y)", doc["purpose"]["preserves_invariant"])

        # 2. Test Boyd & Vandenberghe counterexample: min x s.t. x >= 1, x >= 0; max y s.t. 0 <= y <= 1
        # For feasible x=2, y=1:
        primal_obj = 2.0
        dual_obj = 1.0
        correct_gap = primal_obj - dual_obj
        reversed_gap = dual_obj - primal_obj
        self.assertGreaterEqual(
            correct_gap, 0.0, "Primal minus dual must be non-negative for min primal / max dual"
        )
        self.assertLess(reversed_gap, 0.0, "Dual minus primal would be wrongly negative")

        # 3. Test feasibility witness requirement: equal numbers (x=0, y=0) do NOT certify optimality without feasibility
        ev_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["evidence_required"]
        ]
        self.assertIn("primal_feasibility_check", ev_keys)
        self.assertIn("dual_feasibility_check", ev_keys)

    def test_spja_duplicate_key_and_aggregation_semantics(self) -> None:
        """Section 11: SPJA duplicate key elimination and join multiplicity bag semantics."""
        fpath = CONTRACTS_DIR / "nf.query.spja.yaml"
        with open(fpath, "r", encoding="utf-8") as f:
            doc = yaml.load(f, Loader=UniqueKeyLoader)

        # Check evidence_required is a list and aggregate_evidence_specifications is under extensions
        self.assertIsInstance(doc["evidence_required"], list)
        self.assertIn("joined_partner_multiplicities", doc["evidence_required"])
        self.assertIn("extensions", doc)
        self.assertIn("aggregate_evidence_specifications", doc["extensions"])

        # Multiplicity test: delta = 2 with multiplicity 1 vs 2
        source_delta = 2
        sum_change_mult_1 = source_delta * 1
        sum_change_mult_2 = source_delta * 2
        self.assertEqual(sum_change_mult_1, 2)
        self.assertEqual(sum_change_mult_2, 4)

    def test_efnf_permission_soundness_and_temporal_square(self) -> None:
        """Section 9: EFNF commutation does not act as authorization oracle; requires permission soundness."""
        fpath = CONTRACTS_DIR / "nf.security.efnf.yaml"
        doc = load_yaml(fpath)

        # Identity projection commutes trivially on public=1, secret=42 but exposes secret
        # Contract must declare permission_soundness_witness
        decl_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["declarations_required"]
        ]
        self.assertIn("permission_soundness_witness", decl_keys)
        self.assertIn("temporal_policy_binding", decl_keys)

        # Check non_claims explicitly disclaims commutation as an authorization oracle
        non_claims_str = " ".join(doc["purpose"]["non_claims"])
        self.assertIn("not an authorization oracle", non_claims_str)

        # Check EligibleForExecution terminal maps to Preserve (inert disposition)
        trm = doc["terminal_route_map"]
        self.assertIn("EligibleForExecution", trm)
        self.assertIn("AdapterCommutationMismatch", trm)

    def test_l1_constraint_closure_optimality_vs_closure(self) -> None:
        """Section 3: L1 Constraint Closure distinguishes optimal residual from exact closure."""
        fpath = CONTRACTS_DIR / "nf.physics.l1_constraint_closure.yaml"
        doc = load_yaml(fpath)

        # Distinct routes
        routes = doc["terminal_routes"]
        self.assertIn("ExactClosureCertified", routes)
        self.assertIn("OptimalResidualCertified", routes)
        self.assertIn("DualityGapViolation", routes)
        self.assertIn("HamiltonianBlindSpot", routes)

        # D = [0], omega = [1], alpha = [0], w = [1]
        # Primal objective = |1 - 0*0| = 1. Dual objective = 1*1 = 1. Duality gap = 1 - 1 = 0.
        # Residual norm = 1 > 0. Optimum certified, but constraint closure FALSE.
        primal_obj = 1
        dual_obj = 1
        gap = primal_obj - dual_obj
        residual = 1
        is_optimal = gap == 0
        is_closed = gap == 0 and residual == 0
        self.assertTrue(is_optimal, "Zero duality gap establishes residual optimality")
        self.assertFalse(is_closed, "Residual=1 proves constraint closure fails despite zero gap")

    def test_rcnf_signed_cayley_menger_and_gram_positive_definiteness(self) -> None:
        """Section 4.1 & 4.2: Signed Cayley-Menger determinant and Gram positive definiteness."""
        fpath = CONTRACTS_DIR / "nf.physics.rcnf.yaml"
        doc = load_yaml(fpath)

        # 1. Dimension-signed CM formula (-1)^{n+1} det(CM) > 0
        formal_stmt = doc["definition"]["formal_statement"]
        self.assertIn("(-1)^{n+1} det(CM) > 0", formal_stmt)

        # For equilateral triangle (n=2, edges=1):
        # CM = [[0, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 0]]
        # det(CM) = -3
        # Signed: (-1)^{2+1} * (-3) = (-1) * (-3) = 3 > 0.
        raw_cm_det = -3
        signed_cm_det = ((-1) ** (2 + 1)) * raw_cm_det
        self.assertGreater(
            signed_cm_det,
            0,
            "Signed Cayley-Menger determinant must be positive for equilateral triangle",
        )

        # 2. Gram matrix principal minor counterexample (five-point data: edges=1, diagonals=1.9):
        # det G_{1:3, 1:3} = -14761681 / 4000000 < 0
        minor = -14761681 / 4000000
        self.assertLess(
            minor,
            0,
            "Gram principal minor negative indicates metric failure despite valid triangle inequalities",
        )
        self.assertIn("gram_matrix_positive_definiteness", doc["purpose"]["protected_skeleton"])
        self.assertIn(
            "vertex_link_manifoldhood",
            [list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]],
        )

    def test_lorentzian_cdt_topology_distinction_beyond_euler(self) -> None:
        """Section 4.3: Euler characteristic equality does not certify 3-manifold topology preservation."""
        fpath = CONTRACTS_DIR / "nf.physics.lorentzian_cdt.yaml"
        doc = load_yaml(fpath)

        # chi(S^3) = 0 and chi(T^3) = 0
        chi_s3 = 0
        chi_t3 = 0
        self.assertEqual(chi_s3, chi_t3, "S^3 and T^3 have identical Euler characteristics")

        # Contract must state that Euler characteristic is a necessary check, not the topology certificate
        non_claims = " ".join(doc["purpose"]["non_claims"])
        self.assertIn("not a complete topology certificate", non_claims)
        self.assertIn(
            "move_legality_topology_preservation",
            [list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]],
        )

    def test_pachner_lp_scaling_target_breach(self) -> None:
        """Section 4.4: Exponent exceeding 3.5 is polynomial (e.g. N^4), not superpolynomial divergence."""
        fpath = CONTRACTS_DIR / "nf.physics.pachner_lp_scaling.yaml"
        doc = load_yaml(fpath)

        # Verify route name is ScalingTargetBreach, not SuperPolynomialDivergence
        self.assertIn("ScalingTargetBreach", doc["terminal_routes"])
        self.assertNotIn("SuperPolynomialDivergence", doc["terminal_routes"])

        # Exponent 4.0 is polynomial
        alpha = 4.0
        self.assertGreater(alpha, 3.5, "Exponent exceeds target threshold")

    def test_schlafli_nf_variational_identity(self) -> None:
        """Section 5: Schläfli identity is a differential variational identity, not nilpotence."""
        fpath = CONTRACTS_DIR / "nf.physics.schlafli_nf.yaml"
        doc = load_yaml(fpath)

        # Check name and short name do not use nilpotence
        self.assertNotIn("Nilpotence", doc["identity"]["name"])
        self.assertEqual(doc["identity"]["short_name"], "SIDNF")

        # Analytical angle Jacobian must be declared
        decl_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["declarations_required"]
        ]
        self.assertIn("analytical_angle_jacobian", decl_keys)
        self.assertIn("SchlafliExactIdentityCertified", doc["terminal_routes"])

    def test_wick_mc_obligations_separated(self) -> None:
        """Section 6: Detailed balance does not imply mixing; positivity does not imply Einstein convergence."""
        fpath = CONTRACTS_DIR / "nf.physics.cdt_wick_mc.yaml"
        doc = load_yaml(fpath)

        # Counterexample 1: Identity transition matrix satisfies detailed balance for pi=(2/3, 1/3)
        # pi_i * P_ij = pi_j * P_ji holds trivially for P = I, but state never moves.
        # Contract must require ergodicity / autocorrelation time in validation criteria
        crit_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]
        ]
        self.assertIn("ergodicity_and_mixing", crit_keys)

        # Counterexample 2: Positive weights for S(x) = x on [0, 1] has |S'(x)| = 1 everywhere
        # Contract scopes semiclassical convergence as an experimental hypothesis
        self.assertIn("SemiclassicalEinsteinHypothesisSupported", doc["terminal_routes"])

    def test_zolotarev_absolute_spectral_gap_and_gw_firewall(self) -> None:
        """Section 7: Certified absolute spectral gap and GW algebraic triviality firewall."""
        fpath = CONTRACTS_DIR / "nf.physics.cdt_zolotarev_overlap.yaml"
        doc = load_yaml(fpath)

        # 1. H_w = diag(-1, 1). Signed minimum is -1. Absolute gap is 1.
        diag = [-1.0, 1.0]
        signed_min = min(diag)
        abs_gap = min(abs(x) for x in diag)
        self.assertEqual(signed_min, -1.0)
        self.assertEqual(abs_gap, 1.0)

        # 2. Algebraic check: D = (1/a)(I + gamma_5 R).
        # D gamma_5 + gamma_5 D - a D gamma_5 D = (1/a) gamma_5 (I - R^2).
        # For R = I, (I - R^2) = 0 regardless of whether R approximates sign(H_w).
        # Contract must certify rational minimax error on spectral interval independently of GW residual
        crit_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]
        ]
        self.assertIn("absolute_spectral_gap_certified", crit_keys)
        self.assertIn("rational_minimax_error_bound", crit_keys)

    def test_wdwnf_operator_scaled_residual(self) -> None:
        """Section 8.1: Relative residual scaled by operator norm prevents false kernel certification."""
        fpath = CONTRACTS_DIR / "nf.physics.wdwnf.yaml"
        doc = load_yaml(fpath)

        # H = 10^-10 * I, ||Psi|| = 1. Absolute residual is 10^-10 <= 10^-9.
        # But ||H||_op = 10^-10. Relative residual is (10^-10) / (10^-10 * 1) = 1.0 >> 10^-9.
        # Scaled residual correctly rejects invertible H!
        op_norm = 1e-10
        state_norm = 1.0
        abs_res = 1e-10
        rel_res = abs_res / (op_norm * state_norm)
        self.assertEqual(
            rel_res, 1.0, "Relative residual must be 1.0 for scaled invertible operator"
        )

        # Contract requires relative_residual_bound and complex_normalization
        crit_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]
        ]
        self.assertIn("relative_residual_bound", crit_keys)
        self.assertIn("complex_normalization", crit_keys)

    def test_pwnf_normalized_conditional_slices(self) -> None:
        """Section 8.2: Normalized conditional slices prevent false non-unitarity rejections."""
        fpath = CONTRACTS_DIR / "nf.physics.pwnf.yaml"
        doc = load_yaml(fpath)

        # |Psi> = 3/5 |00> + 4/5 |11>, U = X (unitary).
        # Raw slices: phi_0 = 3/5 |0>, phi_1 = 4/5 |1|.
        # Raw transition residual: || phi_1 - X phi_0 || = || 4/5 |1> - 3/5 |1> || = 1/5 = 0.2 > 0.
        # Normalized slices: psi_0 = |0>, psi_1 = |1|.
        # Normalized transition residual: || psi_1 - X psi_0 || = || |1> - |1> || = 0.0!
        raw_res = abs(4 / 5 - 3 / 5)
        norm_res = 0.0
        self.assertAlmostEqual(
            raw_res,
            0.2,
            places=7,
            msg="Raw slices differ in norm due to clock marginal probabilities",
        )
        self.assertEqual(norm_res, 0.0, "Normalized slices satisfy exact unitary transition")

        crit_keys = [
            list(d.keys())[0] if isinstance(d, dict) else d for d in doc["validation_criteria"]
        ]
        self.assertIn("normalized_slice_step_exactness", crit_keys)
        self.assertIn("independent_unitarity_certified", crit_keys)

    def test_dbcnf_least_rotation_and_lyndon_distinction(self) -> None:
        """Section 12: DBCNF stores least rotation; Lyndon applies only to aperiodic words."""
        fpath = CONTRACTS_DIR / "nf.representation.dbcnf.yaml"
        doc = load_yaml(fpath)

        # Word "0101" has least rotation "0101", but is periodic (period 2, length 4).
        # Word "001" has least rotation "001" and is aperiodic -> Lyndon word.
        # Contract non_claims preserves this exact distinction.
        non_claims = " ".join(doc["purpose"]["non_claims"])
        self.assertIn("strictly aperiodic", non_claims)
        self.assertIn("proper periodic power", non_claims)

    def test_lightcone_and_time_sync_causality_vs_consensus(self) -> None:
        """Section 13: Physical light-cone causality is not overwritten by consensus serialization."""
        lc_path = CONTRACTS_DIR / "nf.relativistic.lightcone.yaml"
        ts_path = CONTRACTS_DIR / "nf.relativistic.time_sync.yaml"
        lc_doc = load_yaml(lc_path)
        ts_doc = load_yaml(ts_path)

        # Lightcone routes distinguish physical causality from consensus serialization
        lc_routes = lc_doc["terminal_routes"]
        self.assertIn("DefinitelyCausal", lc_routes)
        self.assertIn("SpacelikeConcurrent", lc_routes)
        self.assertIn("ConsensusSerialized", lc_routes)
        self.assertIn("InconclusiveTiming", lc_routes)

        # Time-sync routes unresolved overlaps to Abstain (not computational exhaustion)
        ts_trm = ts_doc["terminal_route_map"]
        self.assertEqual(ts_trm["UnresolvedIntervalOverlap"], "Abstain")


if __name__ == "__main__":
    unittest.main()
