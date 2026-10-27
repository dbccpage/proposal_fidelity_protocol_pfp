"""Unit tests for relational, derivation, and novel CODA normal form catalog.

AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

import yaml

from pfp.infrastructure.normal_forms.evaluator import NormalFormsEvaluator


def _find_repo_root() -> Path:
    p = Path(__file__).resolve().parent
    for _ in range(8):
        if (p / "lean4").is_dir() and (
            (p / "core_research").is_dir() or (p / "research").is_dir()
        ):
            return p
        p = p.parent
    return next(
        (p for p in Path(__file__).resolve().parents if (p / ".git").exists()),
        Path(__file__).resolve().parents[4],
    )


REPO_ROOT = _find_repo_root()
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"
LEAN_DIR = REPO_ROOT / "lean4"
LEAN_FILE = LEAN_DIR / "NormalFormsCore.lean"

ALL_CONTRACTS = [
    # Classical Normal Forms
    "nf.classical.0nf.yaml",
    "nf.classical.1nf.yaml",
    "nf.classical.2nf.yaml",
    "nf.classical.3nf.yaml",
    "nf.classical.4nf.yaml",
    "nf.classical.5nf.yaml",
    "nf.classical.6nf.yaml",
    "nf.classical.bcnf.yaml",
    "nf.classical.dknf.yaml",
    "nf.classical.eknf.yaml",
    "nf.classical.etnf.yaml",
    "nf.classical.nf2.yaml",
    # Change / Maintenance Normal Form
    "nf.change.bqnf.yaml",
    # Genesis Derivation Normal Forms
    "nf.derivation.aonf.yaml",
    "nf.derivation.obnf.yaml",
    "nf.derivation.pdnf.yaml",
    "nf.derivation.rpnf.yaml",
    "nf.derivation.scnf.yaml",
    # Novel CODA Normal Forms
    "nf.coda.gbqnf.yaml",
    "nf.coda.tsnf.yaml",
    "nf.coda.eqnf.yaml",
    # Extended forms defined in normal_form_foundational_definitions.md
    "nf.representation.tbnf.yaml",
    "nf.representation.dbcnf.yaml",
    "nf.evidence.ddanf.yaml",
    "nf.logic.qanf.yaml",
    "nf.cochain.dhnf.yaml",
    "nf.runtime.zfnf.yaml",
    "nf.cohomology.acnf.yaml",
    "nf.fsp.bssnf.yaml",
    "nf.fsp.micnf.yaml",
]


class TestNfCatalog(unittest.TestCase):
    def test_lean4_normal_forms_compilation(self) -> None:
        self.assertTrue(LEAN_FILE.exists(), f"Lean file missing: {LEAN_FILE}")
        lake_path = shutil.which("lake")
        if lake_path:
            res = subprocess.run(
                [lake_path, "build", "NormalFormsCore"],
                cwd=str(LEAN_DIR),
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                res.returncode, 0, f"Lean compilation error: {res.stderr}\n{res.stdout}"
            )

    def test_all_yaml_contracts_integrity(self) -> None:
        """Validates that every registered contract parses and carries the quadrilateral."""
        self.assertEqual(len(ALL_CONTRACTS), 30)
        for c_name in ALL_CONTRACTS:
            c_path = CONTRACTS_DIR / c_name
            if not c_path.exists() and (CONTRACTS_DIR / "bqnf" / c_name).exists():
                c_path = CONTRACTS_DIR / "bqnf" / c_name
            self.assertTrue(c_path.exists(), f"Missing contract: {c_name}")
            with open(c_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.assertIn("identity", data, f"Contract {c_name} missing identity")
                self.assertIn("purpose", data, f"Contract {c_name} missing purpose")
                self.assertIn(
                    "validation_criteria",
                    data,
                    f"Contract {c_name} missing validation_criteria",
                )
                self.assertIn("terminal_routes", data, f"Contract {c_name} missing terminal_routes")
                self.assertIn(
                    "terminal_route_map",
                    data,
                    f"Contract {c_name} missing terminal_route_map",
                )
                definition = data.get("definition")
                if isinstance(definition, dict) and "quadrilateral" in definition:
                    quad = definition["quadrilateral"]
                else:
                    quad = data["quadrilateral"]
                self.assertIn("qualifies_as_true_normal_form", quad)
                self.assertIn("anomaly_exclusion", quad)
                self.assertIn("lossless_join", quad)
                self.assertIn("dependency_preservation", quad)
                self.assertIn("syntactic_decision", quad)
                self.assertFalse(data["authorization"]["certified_implies_authorized"])

    def test_published_membership_tests(self) -> None:
        """Pins the membership statements that the old contracts had collapsed."""

        def load(name: str) -> dict:
            with open(CONTRACTS_DIR / name, encoding="utf-8") as handle:
                return yaml.safe_load(handle)

        zero = load("nf.classical.0nf.yaml")
        self.assertFalse(zero["definition"]["quadrilateral"]["qualifies_as_true_normal_form"])

        third = load("nf.classical.3nf.yaml")
        self.assertEqual(
            third["definition"]["quadrilateral"]["dependency_preservation"]["status"],
            "preserved_by_synthesis",
        )

        bcnf = load("nf.classical.bcnf.yaml")
        self.assertEqual(
            bcnf["definition"]["quadrilateral"]["dependency_preservation"]["status"],
            "not_always",
        )
        self.assertEqual(
            bcnf["definition"]["preservation_counterexample"]["heading"],
            ["S", "J", "T"],
        )

        fifth = load("nf.classical.5nf.yaml")
        self.assertEqual(
            fifth["definition"]["membership_test"],
            "implied by the candidate keys",
        )
        screen = fifth["definition"]["sufficient_key_component_test"]
        self.assertEqual(screen["strength"], "sufficient")
        self.assertFalse(screen["necessary"])
        self.assertNotIn("every component", fifth["purpose"]["preserves_invariant"])

        sixth = load("nf.classical.6nf.yaml")
        self.assertFalse(sixth["definition"]["binary_fact_shape"]["defines_membership"])
        self.assertNotIn("at most one", " ".join(sixth["validation_criteria"]))

        essential = load("nf.classical.etnf.yaml")
        self.assertEqual(
            essential["definition"]["source_table_reading"]["status"],
            "not_the_membership_test",
        )
        self.assertIn("at least one", essential["definition"]["formal_statement"])

        domain_key = load("nf.classical.dknf.yaml")
        decision = domain_key["definition"]["quadrilateral"]["syntactic_decision"]["status"]
        self.assertEqual(decision, "undecidable_for_arbitrary_constraints")
        self.assertFalse(domain_key["definition"]["quadrilateral"]["qualifies_as_true_normal_form"])

        hodge = load("nf.cochain.dhnf.yaml")
        self.assertEqual(hodge["terminal_route_map"]["RecordHarmonicComponent"], "Preserve")

        meron = load("nf.fsp.micnf.yaml")
        criteria = " ".join(meron["validation_criteria"])
        self.assertIn("no fixed point", criteria)
        self.assertIn("non-empty", criteria)

        switching = load("nf.fsp.bssnf.yaml")
        self.assertIn(
            "every cycle has edge-bit sum",
            switching["definition"]["formal_statement"],
        )

        rational = load("nf.runtime.zfnf.yaml")
        self.assertEqual(rational["terminal_route_map"]["FeasiblePositiveGap"], "Escalate")
        self.assertEqual(rational["terminal_route_map"]["CertifiedOptimal"], "Preserve")

    def test_derivation_contracts_validation(self) -> None:
        """Validates specific derivation normal forms from 19L57G1 / CODA."""
        derivation_contracts = ["aonf", "obnf", "pdnf", "rpnf", "scnf"]
        for d in derivation_contracts:
            c_path = CONTRACTS_DIR / f"nf.derivation.{d}.yaml"
            with open(c_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.assertEqual(data["identity"]["family"], "derivation")
                self.assertEqual(data["identity"]["contract_status"], "draft")

    def test_coda_novel_contracts_validation(self) -> None:
        """Validates the 3 novel CODA normal forms extending BQNF."""
        novel_contracts = {
            "nf.coda.gbqnf.yaml": "GBQNF",
            "nf.coda.tsnf.yaml": "TSNF",
            "nf.coda.eqnf.yaml": "EQNF",
        }
        for c_name, short_name in novel_contracts.items():
            c_path = CONTRACTS_DIR / c_name
            with open(c_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.assertEqual(data["identity"]["short_name"], short_name)
                self.assertEqual(data["identity"]["status"], "draft")

    def test_0nf_to_1nf_normalization(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)
        raw = [
            (1, "Alice", "CS101, CS201, MATH301"),
            (2, "Bob", "PHYS101"),
            (3, "Carol", "CS101, BIO100"),
        ]
        flattened = evaluator.normalize_0nf_to_1nf(raw)
        self.assertEqual(len(flattened), 6)
        alice_courses = [t["course_code"] for t in flattened if t["student_name"] == "Alice"]
        self.assertEqual(alice_courses, ["CS101", "CS201", "MATH301"])
        evaluator.close()

    def test_5nf_compliant_project_join(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)
        tuples = [
            ("Alice", "Acme", "Widget"),
            ("Alice", "Acme", "Gadget"),
            ("Alice", "Beta", "Widget"),
            ("Alice", "Beta", "Gadget"),
        ]
        res = evaluator.evaluate_5nf_project_join_integrity(tuples)
        self.assertTrue(res["is_5nf_compliant"])
        self.assertTrue(res["instance_obeys_declared_ternary_join"])
        self.assertIsNone(res["schema_in_5nf"])
        self.assertEqual(res["spurious_tuples_count"], 0)
        self.assertEqual(res["fill2_count"], 4)
        self.assertEqual(res["shell2_count"], 4)
        evaluator.close()

    def test_5nf_violation_spurious_tuple_detection(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)
        tuples = [
            ("C1", "Co1", "P1"),
            ("C1", "Co2", "P2"),
            ("C2", "Co1", "P2"),
        ]
        res = evaluator.evaluate_5nf_project_join_integrity(tuples)
        self.assertFalse(res["is_5nf_compliant"])
        self.assertFalse(res["instance_obeys_declared_ternary_join"])
        self.assertIsNone(res["schema_in_5nf"])
        self.assertGreaterEqual(res["spurious_tuples_count"], 1)
        self.assertTrue(
            any(
                t["consultant_id"] == "C1" and t["company_id"] == "Co1" and t["product_id"] == "P2"
                for t in res["spurious_tuples"]
            )
        )
        evaluator.close()

    def test_bqnf_incremental_repair_insert_update_delete(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        # 1. Initial State: Empty
        p0 = evaluator.process_bqnf_incremental_repair()
        self.assertEqual(p0["terminal"], "Preserve")

        # 2. INSERT 3 sales across 2 regions
        evaluator.apply_sales_cdc("INSERT", 1, new_region="North", new_amount=100.0)
        evaluator.apply_sales_cdc("INSERT", 2, new_region="North", new_amount=150.0)
        evaluator.apply_sales_cdc("INSERT", 3, new_region="South", new_amount=200.0)

        p1 = evaluator.process_bqnf_incremental_repair()
        self.assertEqual(p1["terminal"], "Repair")
        self.assertTrue(p1["verified_consistent"])
        self.assertEqual(p1["cached_state"]["North"], (250.0, 2))
        self.assertEqual(p1["cached_state"]["South"], (200.0, 1))

        # 3. UPDATE: sale 1 moves from North to South and increases amount
        evaluator.apply_sales_cdc(
            "UPDATE",
            1,
            old_region="North",
            new_region="South",
            old_amount=100.0,
            new_amount=120.0,
        )

        p2 = evaluator.process_bqnf_incremental_repair()
        self.assertEqual(p2["terminal"], "Repair")
        self.assertTrue(p2["verified_consistent"])
        self.assertEqual(p2["cached_state"]["North"], (150.0, 1))
        self.assertEqual(p2["cached_state"]["South"], (320.0, 2))

        # 4. DELETE: sale 2 in North is deleted
        evaluator.apply_sales_cdc("DELETE", 2, old_region="North", old_amount=150.0)

        p3 = evaluator.process_bqnf_incremental_repair()
        self.assertEqual(p3["terminal"], "Repair")
        self.assertTrue(p3["verified_consistent"])
        self.assertNotIn("North", p3["cached_state"])
        self.assertEqual(p3["cached_state"]["South"], (320.0, 2))

        evaluator.close()

    def test_non_invertible_aggregate_cochain_repair(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        # 1. Insert 4 sales in West
        evaluator.apply_sales_cdc("INSERT", 10, new_region="West", new_amount=100.0)
        evaluator.apply_sales_cdc("INSERT", 11, new_region="West", new_amount=200.0)
        evaluator.apply_sales_cdc("INSERT", 12, new_region="West", new_amount=150.0)
        evaluator.apply_sales_cdc("INSERT", 13, new_region="West", new_amount=300.0)

        p1 = evaluator.process_bqnf_incremental_repair(use_cochain=True)
        self.assertEqual(p1["terminal"], "Repair")
        self.assertTrue(p1["verified_consistent"])
        self.assertEqual(p1["cached_state"]["West"], (750.0, 4))
        self.assertEqual(p1["cached_extrema"]["West"], (100.0, 300.0))
        self.assertEqual(p1["fallback_recomputations"], 0)

        # 2. Non-destructive deletion: delete sale 12 (150.0).
        evaluator.apply_sales_cdc("DELETE", 12, old_region="West", old_amount=150.0)
        p2 = evaluator.process_bqnf_incremental_repair(use_cochain=True)
        self.assertEqual(p2["terminal"], "Repair")
        self.assertTrue(p2["verified_consistent"])
        self.assertEqual(p2["cached_state"]["West"], (600.0, 3))
        self.assertEqual(p2["cached_extrema"]["West"], (100.0, 300.0))
        self.assertEqual(p2["fallback_recomputations"], 0)

        # 3. Destructive deletion: delete sale 10 (100.0 == min).
        evaluator.apply_sales_cdc("DELETE", 10, old_region="West", old_amount=100.0)
        p3 = evaluator.process_bqnf_incremental_repair(use_cochain=True)
        self.assertEqual(p3["terminal"], "Repair")
        self.assertTrue(p3["verified_consistent"])
        self.assertEqual(p3["cached_state"]["West"], (500.0, 2))
        self.assertEqual(p3["cached_extrema"]["West"], (200.0, 300.0))
        self.assertEqual(p3["fallback_recomputations"], 0)

        # Verify audit log in extrema_repair_log
        c = evaluator.conn.cursor()
        c.execute("""
            SELECT op_type, affected_amount, is_destructive, cochain_available, terminal_route,
                   old_min, new_min, recomputation_fallback_executed
            FROM extrema_repair_log
            WHERE region = 'West' AND op_type = 'DELETE'
            ORDER BY repair_id ASC;
        """)
        del_logs = c.fetchall()
        self.assertEqual(len(del_logs), 2)

        self.assertEqual(del_logs[0]["affected_amount"], 150.0)
        self.assertEqual(del_logs[0]["is_destructive"], 0)
        self.assertEqual(del_logs[0]["terminal_route"], "Repair")
        self.assertEqual(del_logs[0]["old_min"], 100.0)
        self.assertEqual(del_logs[0]["new_min"], 100.0)
        self.assertEqual(del_logs[0]["recomputation_fallback_executed"], 0)

        self.assertEqual(del_logs[1]["affected_amount"], 100.0)
        self.assertEqual(del_logs[1]["is_destructive"], 1)
        self.assertEqual(del_logs[1]["cochain_available"], 1)
        self.assertEqual(del_logs[1]["terminal_route"], "Repair")
        self.assertEqual(del_logs[1]["old_min"], 100.0)
        self.assertEqual(del_logs[1]["new_min"], 200.0)
        self.assertEqual(del_logs[1]["recomputation_fallback_executed"], 0)

        evaluator.close()

    def test_non_invertible_aggregate_fallback_recomputation(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        evaluator.apply_sales_cdc("INSERT", 20, new_region="East", new_amount=50.0)
        evaluator.apply_sales_cdc("INSERT", 21, new_region="East", new_amount=75.0)
        evaluator.apply_sales_cdc("INSERT", 22, new_region="East", new_amount=90.0)

        p1 = evaluator.process_bqnf_incremental_repair(use_cochain=False)
        self.assertEqual(p1["cached_extrema"]["East"], (50.0, 90.0))

        evaluator.apply_sales_cdc(
            "DELETE",
            20,
            old_region="East",
            old_amount=50.0,
            maintain_cochain=False,
        )
        p2 = evaluator.process_bqnf_incremental_repair(use_cochain=False)

        self.assertEqual(p2["terminal"], "Recompute")
        self.assertTrue(p2["verified_consistent"])
        self.assertEqual(p2["cached_state"]["East"], (165.0, 2))
        self.assertEqual(p2["cached_extrema"]["East"], (75.0, 90.0))
        self.assertEqual(p2["fallback_recomputations"], 1)

        c = evaluator.conn.cursor()
        c.execute("""
            SELECT is_destructive, cochain_available, terminal_route, old_min, new_min, recomputation_fallback_executed
            FROM extrema_repair_log
            WHERE region = 'East' AND op_type = 'DELETE';
        """)
        del_log = c.fetchone()
        self.assertEqual(del_log["is_destructive"], 1)
        self.assertEqual(del_log["cochain_available"], 0)
        self.assertEqual(del_log["terminal_route"], "Recompute")
        self.assertEqual(del_log["old_min"], 50.0)
        self.assertEqual(del_log["new_min"], 75.0)
        self.assertEqual(del_log["recomputation_fallback_executed"], 1)

        evaluator.close()

    def test_destructive_deletion_with_exhausted_cochain(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        evaluator.apply_sales_cdc("INSERT", 30, new_region="Central", new_amount=10.0)
        evaluator.apply_sales_cdc("INSERT", 31, new_region="Central", new_amount=20.0)
        evaluator.process_bqnf_incremental_repair(use_cochain=True)

        evaluator.conn.execute("DELETE FROM region_extremum_cochain WHERE region = 'Central';")
        evaluator.conn.commit()

        evaluator.apply_sales_cdc(
            "DELETE",
            30,
            old_region="Central",
            old_amount=10.0,
            maintain_cochain=False,
        )
        p = evaluator.process_bqnf_incremental_repair(use_cochain=True)

        self.assertEqual(p["terminal"], "Recompute")
        self.assertTrue(p["verified_consistent"])
        self.assertEqual(p["cached_extrema"]["Central"], (20.0, 20.0))
        self.assertEqual(p["fallback_recomputations"], 1)

        evaluator.close()

    def test_quantile_sketch_cochain_within_tolerance(self) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        for sid, val in enumerate(range(10, 110, 10), start=100):
            evaluator.apply_sales_cdc("INSERT", sid, new_region="Metro", new_amount=float(val))

        p1 = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=15.0
        )
        self.assertEqual(p1["terminal"], "Repair")
        self.assertTrue(p1["verified_consistent"])
        self.assertEqual(p1["quantile_repairs"], 1)
        self.assertEqual(p1["quantile_fallback_recomputations"], 0)
        self.assertLessEqual(abs(p1["cached_medians"]["Metro"] - 55.0), 15.0)

        evaluator.apply_sales_cdc("DELETE", 102, old_region="Metro", old_amount=30.0)
        p2 = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=15.0
        )
        self.assertEqual(p2["terminal"], "Repair")
        self.assertTrue(p2["verified_consistent"])
        self.assertEqual(p2["quantile_repairs"], 1)
        self.assertEqual(p2["quantile_fallback_recomputations"], 0)

        c = evaluator.conn.cursor()
        c.execute("""
            SELECT estimated_median, true_median, error_delta, tolerance, within_tolerance, terminal_route, recomputation_fallback_executed
            FROM quantile_repair_log
            WHERE region = 'Metro';
        """)
        logs = c.fetchall()
        self.assertEqual(len(logs), 2)
        for log_row in logs:
            self.assertEqual(log_row["within_tolerance"], 1)
            self.assertEqual(log_row["terminal_route"], "Repair")
            self.assertEqual(log_row["recomputation_fallback_executed"], 0)
            self.assertLessEqual(log_row["error_delta"], log_row["tolerance"])

        evaluator.close()

    def test_quantile_sketch_cochain_tolerance_breach_forces_recompute(
        self,
    ) -> None:
        evaluator = NormalFormsEvaluator(in_memory=True)

        evaluator.apply_sales_cdc("INSERT", 200, new_region="Rural", new_amount=10.0)
        evaluator.apply_sales_cdc("INSERT", 201, new_region="Rural", new_amount=20.0)
        evaluator.apply_sales_cdc("INSERT", 202, new_region="Rural", new_amount=500.0)

        p1 = evaluator.process_bqnf_incremental_repair(
            use_cochain=True, track_quantiles=True, quantile_tolerance=0.1
        )

        self.assertEqual(p1["terminal"], "Recompute")
        self.assertTrue(p1["verified_consistent"])
        self.assertEqual(p1["quantile_fallback_recomputations"], 1)
        self.assertEqual(p1["cached_medians"]["Rural"], 20.0)

        c = evaluator.conn.cursor()
        c.execute("""
            SELECT estimated_median, true_median, error_delta, tolerance, within_tolerance, terminal_route, recomputation_fallback_executed
            FROM quantile_repair_log
            WHERE region = 'Rural';
        """)
        log_row = c.fetchone()
        self.assertEqual(log_row["within_tolerance"], 0)
        self.assertEqual(log_row["terminal_route"], "Recompute")
        self.assertEqual(log_row["recomputation_fallback_executed"], 1)
        self.assertGreater(log_row["error_delta"], log_row["tolerance"])

        evaluator.close()


if __name__ == "__main__":
    unittest.main()
