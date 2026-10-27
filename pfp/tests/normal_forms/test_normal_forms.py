"""Comprehensive test suite for Normal Form Testing Harness.

AuthorityEffect: None.

Verifies:
1. Declarative Contract Schema & Spec Verification (all YAML specs in specs/).
2. Classical Relational Normal Forms (1NF, 2NF, 3NF, BCNF, Heath's Theorem, Dependency Preservation).
3. MSS-N Tower Normal Forms (TBNF, DBCNF, ZFNF, DHNF).
4. Fermion Sign Problem Normal Forms (BSS-NF and MIC-NF).
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

from pfp.infrastructure.normal_form_loading import (
    audit_specs_directory,
    validate_contract_file,
)

repo_root = next((p for p in Path(__file__).resolve().parents if (p / '.git').exists()), Path(__file__).resolve().parents[4])
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from pfp.domain.normal_forms.contract_validation import validate_contract_dict
from pfp.domain.normal_forms.quantum_forms import verify_bssnf, verify_micnf
from pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_1nf,
    check_2nf,
    check_3nf,
    check_bcnf,
    check_dependency_preservation,
    check_lossless_decomposition,
    compute_attribute_closure,
)
from pfp.domain.normal_forms.tower_forms import (
    canonicalize_dbcnf,
    check_tbnf,
    is_dbcnf,
    verify_dhnf,
    verify_zfnf,
)

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"


class TestContractSpecsHarness(unittest.TestCase):
    """Verifies that all declarative YAML specifications conform to smplx.nf.contract.v0."""

    def test_all_active_specs_pass_structural_validation(self) -> None:
        self.assertTrue(CONTRACTS_DIR.is_dir(), f"Contracts directory not found at {CONTRACTS_DIR}")
        audit_results = audit_specs_directory(CONTRACTS_DIR)
        self.assertGreater(len(audit_results), 0, "No contract files found in contracts directory")

        expected_specs = {
            "nf.change.bqnf.yaml",
            "nf.fsp.bssnf.yaml",
            "nf.fsp.micnf.yaml",
            "nf.cochain.dhnf.yaml",
            "nf.runtime.zfnf.yaml",
        }
        self.assertTrue(expected_specs.issubset(set(audit_results.keys())))

        for filename, defects in audit_results.items():
            with self.subTest(file=filename):
                defect_msgs = [f"[{d.field}] {d.message}" for d in defects]
                self.assertEqual(defects, [], f"Defects found in {filename}: {defect_msgs}")

    def test_load_bearing_authorization_invariant(self) -> None:
        """Every contract must declare authorized_by: null and certified_implies_authorized: false."""
        for p in CONTRACTS_DIR.glob("nf.*.yaml"):
            with self.subTest(contract=p.name):
                defects = validate_contract_file(p)
                auth_defects = [d for d in defects if "authorization" in d.field]
                self.assertEqual(auth_defects, [])

    def test_defective_contracts_are_detected(self) -> None:
        valid_template = {
            "schema_version": "smplx.nf.contract.v0",
            "contract_kind": "normal_form_contract",
            "identity": {
                "id": "nf.test.dummy",
                "name": "Dummy Normal Form",
                "short_name": "DNF",
                "version": "v0",
                "status": "active",
                "family": "shape",
            },
            "classification": {
                "hierarchy_level": "certified_normal_form",
                "subject_kind": ["test_relvar"],
                "data_posture": "at_rest",
                "mathematical_posture": "operational",
            },
            "purpose": {
                "excludes_anomaly": "test anomaly",
                "preserves_invariant": "test invariant",
                "protected_skeleton": ["core"],
                "erased_structure": [],
                "non_claims": ["does not prove P != NP"],
            },
            "declarations_required": ["decl1"],
            "evidence_required": ["ev1"],
            "validation_criteria": ["crit1"],
            "terminal_routes": ["ExactRoute"],
            "terminal_route_map": {"ExactRoute": "Exact"},
            "certification": {
                "certificate_required": True,
                "verifier_required": True,
            },
            "authorization": {
                "authorized_by": None,
                "certified_implies_authorized": False,
            },
        }

        # 1. Missing non_claims in purpose
        bad_purpose = dict(valid_template)
        bad_purpose["purpose"] = dict(valid_template["purpose"])
        bad_purpose["purpose"]["non_claims"] = []
        defects = validate_contract_dict(bad_purpose)
        self.assertTrue(any("non_claims" in d.field for d in defects))

        # 2. Authorization violation: certified_implies_authorized is True
        bad_auth = dict(valid_template)
        bad_auth["authorization"] = {
            "authorized_by": None,
            "certified_implies_authorized": True,
        }
        defects = validate_contract_dict(bad_auth)
        self.assertTrue(any("certified_implies_authorized" in d.field for d in defects))

        # 3. Authorization violation: authorized_by is not None
        bad_auth2 = dict(valid_template)
        bad_auth2["authorization"] = {
            "authorized_by": "Minister of Foreign Trade",
            "certified_implies_authorized": False,
        }
        defects = validate_contract_dict(bad_auth2)
        self.assertTrue(any("authorized_by" in d.field for d in defects))

        # 4. Terminal route with missing mapping in terminal_route_map
        bad_route = dict(valid_template)
        bad_route["terminal_routes"] = ["ExactRoute", "UnmappedRoute"]
        defects = validate_contract_dict(bad_route)
        self.assertTrue(any("terminal_route_map" in d.field for d in defects))


class TestClassicalRelationalDependencyAlgebra(unittest.TestCase):
    """Verifies the 4 Pillars of True Normal Forms from Part I of foundational definitions."""

    def test_armstrong_closure_computation(self) -> None:
        # Schema: R(A, B, C, D, E)
        # FDs: A -> B, BC -> D, D -> E
        fds = {
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B, C", "D"),
            FunctionalDependency.from_str("D", "E"),
        }
        closure_a = compute_attribute_closure({"A"}, fds)
        self.assertEqual(closure_a, frozenset({"A", "B"}))

        closure_ac = compute_attribute_closure({"A", "C"}, fds)
        self.assertEqual(closure_ac, frozenset({"A", "B", "C", "D", "E"}))

    def test_canonical_student_course_instructor_bcnf_tradeoff(self) -> None:
        """Textbook schema: R(Student, Course, Instructor).

        FDs: (Student, Course) -> Instructor, Instructor -> Course.
        Candidate keys: (Student, Course) and (Student, Instructor).
        All attributes are prime.
        Satisfies 3NF but violates BCNF (Instructor is not a superkey).
        """
        attrs = frozenset({"Student", "Course", "Instructor"})
        fds = frozenset(
            {
                FunctionalDependency.from_str("Student, Course", "Instructor"),
                FunctionalDependency.from_str("Instructor", "Course"),
            }
        )
        schema = RelationalSchema(attrs, fds)

        # Candidate keys
        keys = schema.candidate_keys()
        self.assertEqual(len(keys), 2)
        self.assertIn(frozenset({"Student", "Course"}), keys)
        self.assertIn(frozenset({"Student", "Instructor"}), keys)

        # Primes
        self.assertEqual(schema.prime_attributes(), attrs)

        # Normal form evaluations
        ok_1nf, _ = check_1nf(schema)
        self.assertTrue(ok_1nf)

        ok_2nf, _ = check_2nf(schema)
        self.assertTrue(ok_2nf)

        ok_3nf, _ = check_3nf(schema)
        self.assertTrue(ok_3nf, "3NF must pass because all attributes are prime")

        ok_bcnf, err_bcnf = check_bcnf(schema)
        self.assertFalse(ok_bcnf)
        self.assertIn("Instructor", str(err_bcnf))

        # Heath's Theorem / Chase decomposition into BCNF:
        # R1 = (Instructor, Course), R2 = (Student, Instructor)
        r1 = frozenset({"Instructor", "Course"})
        r2 = frozenset({"Student", "Instructor"})

        is_lossless, _ = check_lossless_decomposition(schema, [r1, r2])
        self.assertTrue(
            is_lossless,
            "Heath's Theorem establishes lossless join under declared functional dependencies",
        )

        is_dep_pres, _ = check_dependency_preservation(schema, [r1, r2])
        self.assertFalse(
            is_dep_pres,
            "BCNF decomposition sacrifices dependency (Student, Course) -> Instructor",
        )

    def test_2nf_partial_key_violation_and_decomposition(self) -> None:
        # Schema: R(OrderID, ItemID, Quantity, ItemName)
        # (OrderID, ItemID) -> Quantity
        # ItemID -> ItemName
        # Candidate key: (OrderID, ItemID). Non-prime: Quantity, ItemName.
        # ItemID -> ItemName is a partial dependency of non-prime ItemName on candidate key.
        attrs = frozenset({"OrderID", "ItemID", "Quantity", "ItemName"})
        fds = frozenset(
            {
                FunctionalDependency.from_str("OrderID, ItemID", "Quantity"),
                FunctionalDependency.from_str("ItemID", "ItemName"),
            }
        )
        schema = RelationalSchema(attrs, fds)

        ok_2nf, err_2nf = check_2nf(schema)
        self.assertFalse(ok_2nf)
        self.assertIn("Partial Dependency", str(err_2nf))

        # Decompose into 2NF:
        # R1 = (OrderID, ItemID, Quantity)
        # R2 = (ItemID, ItemName)
        r1 = frozenset({"OrderID", "ItemID", "Quantity"})
        r2 = frozenset({"ItemID", "ItemName"})

        is_lossless, _ = check_lossless_decomposition(schema, [r1, r2])
        self.assertTrue(is_lossless)

        is_pres, _ = check_dependency_preservation(schema, [r1, r2])
        self.assertTrue(is_pres)

    def test_3nf_transitive_dependency_violation(self) -> None:
        # Schema: R(EmpID, DeptID, DeptManager)
        # EmpID -> DeptID
        # DeptID -> DeptManager
        # Candidate key: (EmpID). Non-primes: DeptID, DeptManager.
        # EmpID -> DeptManager is transitive through DeptID.
        attrs = frozenset({"EmpID", "DeptID", "DeptManager"})
        fds = frozenset(
            {
                FunctionalDependency.from_str("EmpID", "DeptID"),
                FunctionalDependency.from_str("DeptID", "DeptManager"),
            }
        )
        schema = RelationalSchema(attrs, fds)

        ok_2nf, _ = check_2nf(schema)
        self.assertTrue(ok_2nf, "No composite keys, so 2NF holds vacuously")

        ok_3nf, err_3nf = check_3nf(schema)
        self.assertFalse(ok_3nf)
        self.assertIn("Transitive Dependency", str(err_3nf))


class TestMssnTowerNormalForms(unittest.TestCase):
    """Verifies MSS-N Tower Normal Forms (TBNF, DBCNF, ZFNF, DHNF)."""

    def test_tbnf_wire_verification(self) -> None:
        # Valid wire strings pass TBNF
        self.assertTrue(check_tbnf("<>")[0])
        self.assertTrue(check_tbnf("op<<1><0>>")[0])
        self.assertTrue(check_tbnf("op<<1101>op<<11010><10><1>>op<<1110><10><1><0><1>>>")[0])

        # Strings with whitespace, uppercase, or invalid characters fail TBNF
        self.assertFalse(check_tbnf("<> ")[0])
        self.assertFalse(check_tbnf("<A>")[0])
        self.assertFalse(check_tbnf("a>b")[0])

    def test_dbcnf_lyndon_canonicalization(self) -> None:
        # Lyndon word: lexicographically least cyclic rotation
        self.assertEqual(canonicalize_dbcnf([1, 0, 1, 0]), (0, 1, 0, 1))
        self.assertEqual(canonicalize_dbcnf([1, 1, 0]), (0, 1, 1))
        self.assertEqual(canonicalize_dbcnf(["b", "a", "b"]), ("a", "b", "b"))

        self.assertTrue(is_dbcnf([0, 1, 1]))
        self.assertFalse(is_dbcnf([1, 0, 1]))

    def test_zfnf_rational_optimality_and_float_rejection(self) -> None:
        # 1. Exact zero duality gap
        res_zero = verify_zfnf(5, 5)
        self.assertEqual(res_zero.terminal, "CertifiedOptimalZeroGap")
        self.assertEqual(res_zero.duality_gap, 0)

        # 2. Suboptimal positive gap
        res_sub = verify_zfnf(Fraction(3, 2), Fraction(5, 2))
        self.assertEqual(res_sub.terminal, "SuboptimalPositiveGap")
        self.assertEqual(res_sub.duality_gap, 1)

        # 3. Infeasible dual violation
        res_viol = verify_zfnf(10, 5)
        self.assertEqual(res_viol.terminal, "InfeasibleDualViolationRefusal")
        self.assertEqual(res_viol.duality_gap, -5)

        # 4. Float contamination refusal
        with self.assertRaises(ValueError) as ctx:
            verify_zfnf(5.0, 5)
        self.assertIn("FloatContaminationRefusal", str(ctx.exception))

    def test_dhnf_discrete_hodge_decomposition(self) -> None:
        # Triangle edges: e01, e12, e20
        e01 = (0, 1)
        e12 = (1, 2)
        e20 = (2, 0)

        # 1. Exact pure gradient cochain c = d0(p) where p = {0: 0, 1: 3, 2: 7}
        # d0(p) on (0, 1) is p(1) - p(0) = 3
        # d0(p) on (1, 2) is p(2) - p(1) = 4
        # d0(p) on (2, 0) is p(0) - p(2) = -7
        d0_p = {e01: Fraction(3), e12: Fraction(4), e20: Fraction(-7)}
        h_zero = {e01: Fraction(0), e12: Fraction(0), e20: Fraction(0)}
        d1_zero = {e01: Fraction(0), e12: Fraction(0), e20: Fraction(0)}
        c_exact = dict(d0_p)

        res_exact = verify_dhnf(c_exact, d0_p, h_zero, d1_zero)
        self.assertEqual(res_exact.terminal, "HodgeDecomposedExact")
        self.assertTrue(res_exact.exact_reconstructed)
        self.assertTrue(res_exact.harmonic_zero)

        # 2. Harmonic obstruction: unit circulation h = {e01: 1, e12: 1, e20: 1}
        # <d0(p), h> = 3*1 + 4*1 + (-7)*1 = 0 (orthogonal!)
        h_unit = {e01: Fraction(1), e12: Fraction(1), e20: Fraction(1)}
        c_obstructed = {e: d0_p[e] + h_unit[e] for e in d0_p}

        res_obs = verify_dhnf(c_obstructed, d0_p, h_unit, d1_zero)
        self.assertEqual(res_obs.terminal, "HarmonicObstructionDetected")
        self.assertTrue(res_obs.exact_reconstructed)
        self.assertFalse(res_obs.harmonic_zero)

        # 3. Non-orthogonal or rounding drift failure
        h_bad = {e01: Fraction(2), e12: Fraction(1), e20: Fraction(1)}
        res_drift = verify_dhnf(c_obstructed, d0_p, h_bad, d1_zero)
        self.assertEqual(res_drift.terminal, "RoundingDriftRefusal")


class TestFspNormalForms(unittest.TestCase):
    """Verifies Fermion Sign Problem (FSP) normal forms (BSS-NF and MIC-NF)."""

    def test_bssnf_transverse_field_ising_identity_gauge(self) -> None:
        # Transverse Field Ising model (already stoquastic)
        ising_h = [
            [-1, -1, -1, 0],
            [-1, 1, 0, -1],
            [-1, 0, 1, -1],
            [0, -1, -1, -1],
        ]
        res = verify_bssnf(ising_h)
        self.assertEqual(res.terminal, "RestrictedSignGaugeRepair")
        self.assertTrue(res.gaugeable)
        self.assertEqual(res.gauge, (0, 0, 0, 0))

    def test_bssnf_non_stoquastic_gaugeable_repair(self) -> None:
        # Non-stoquastic 3x3 matrix with gauge (0, 1, 0)
        h = [
            [0, 1, -1],
            [1, 0, 1],
            [-1, 1, 0],
        ]
        res = verify_bssnf(h)
        self.assertEqual(res.terminal, "StoquasticExactRepair")
        self.assertTrue(res.gaugeable)
        self.assertEqual(res.gauge, (0, 1, 0))

        # Check all transformed off-diagonal entries are non-positive
        t = res.transformed_matrix
        self.assertIsNotNone(t)
        for i in range(len(t)):
            for j in range(i + 1, len(t)):
                self.assertLessEqual(t[i][j], 0)

    def test_bssnf_odd_cycle_frustrated_obstruction(self) -> None:
        # Triangular graph with all positive edge weights (frustrated odd cycle)
        odd_h = [
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
        ]
        res = verify_bssnf(odd_h)
        self.assertEqual(res.terminal, "OddCycleFrustratedObstruction")
        self.assertFalse(res.gaugeable)
        self.assertIsNotNone(res.odd_cycle)
        self.assertGreater(len(res.odd_cycle), 2)

    def test_bssnf_rejections(self) -> None:
        # Non-symmetric matrix rejection
        asymm_h = [
            [0, 1],
            [-1, 0],
        ]
        with self.assertRaises(ValueError) as ctx:
            verify_bssnf(asymm_h)
        self.assertIn("NonSymmetricRefusal", str(ctx.exception))

        # Float contamination rejection
        float_h = [
            [0.0, 1.0],
            [1.0, 0.0],
        ]
        with self.assertRaises(ValueError) as ctx:
            verify_bssnf(float_h)
        self.assertIn("FloatContaminationRefusal", str(ctx.exception))

    def test_micnf_valid_cancellation_identity(self) -> None:
        sectors = [
            {"path_id": "neg", "weight": "3/7", "sign": -1},
            {"path_id": "pos", "weight": "3/7", "sign": 1},
            {"path_id": "surv", "weight": "2/5", "sign": 1},
        ]
        pairing = {"neg": "pos", "pos": "neg"}
        res = verify_micnf(sectors, ["neg", "pos"], pairing)
        self.assertEqual(res.terminal, "MeronExactCancellation")
        self.assertEqual(res.pairs, (("neg", "pos"),))
        self.assertEqual(res.survivors, ("surv",))
        self.assertEqual(res.signed_sum, Fraction(2, 5))
        self.assertEqual(res.survivor_sum, Fraction(2, 5))

    def test_micnf_identity_fallacy_fixed_point_refusal(self) -> None:
        sectors = [
            {"path_id": "neg", "weight": "1/2", "sign": -1},
            {"path_id": "pos", "weight": "1/2", "sign": 1},
        ]
        pairing = {"neg": "neg", "pos": "pos"}
        res = verify_micnf(sectors, ["neg", "pos"], pairing)
        self.assertEqual(res.terminal, "FixedPointViolationRefusal")

    def test_micnf_weight_mismatch_refusal(self) -> None:
        sectors = [
            {"path_id": "neg", "weight": "1/3", "sign": -1},
            {"path_id": "pos", "weight": "1/2", "sign": 1},
        ]
        pairing = {"neg": "pos", "pos": "neg"}
        res = verify_micnf(sectors, ["neg", "pos"], pairing)
        self.assertEqual(res.terminal, "WeightMismatchRefusal")

    def test_micnf_same_sign_pairing_refusal(self) -> None:
        sectors = [
            {"path_id": "p1", "weight": "1/2", "sign": 1},
            {"path_id": "p2", "weight": "1/2", "sign": 1},
        ]
        pairing = {"p1": "p2", "p2": "p1"}
        res = verify_micnf(sectors, ["p1", "p2"], pairing)
        self.assertEqual(res.terminal, "SignPreservingPairRefusal")

    def test_micnf_negative_survivor_refusal(self) -> None:
        sectors = [
            {"path_id": "neg", "weight": "1/2", "sign": -1},
            {"path_id": "pos", "weight": "1/2", "sign": 1},
        ]
        # Omit neg from cancellation set
        res = verify_micnf(sectors, [], {})
        self.assertEqual(res.terminal, "NegativeSurvivorRefusal")


if __name__ == "__main__":
    unittest.main()
