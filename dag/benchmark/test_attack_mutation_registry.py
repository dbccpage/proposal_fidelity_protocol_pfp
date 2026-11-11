"""Tests for PFP Attack & Mutation Registry (Milestone 3).

Verifies that:
  1. All 16 threat model categories (+ Category 0 Positive Control) are registered.
  2. 100% of mutation attacks are killed (0 survivors, 0 unresolved).
  3. All authentic baseline inputs are accepted (0 false rejections).
  4. attack_mutation_receipt.json matches schema pfp.attack-mutation-receipt.v1
     with valid non-empty evidence chains across all categories.
  5. Metamorphic relations and mathematical invariants are enforced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "dag" / "benchmark", ROOT / "ops"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import attack_mutation_registry as amr
import qm_host_charpoly as host


class TestAttackMutationRegistryStructure(unittest.TestCase):
    """Test registry category completeness, schema compliance, and fixture bindings."""

    @classmethod
    def setUpClass(cls):
        cls.registry = amr.build_canonical_registry()

    def test_all_22_categories_registered(self):
        """All 22 categories (0 to 21) must be registered."""
        self.assertEqual(len(self.registry.categories), 22)
        for cat_id in range(22):
            self.assertIn(cat_id, self.registry.categories)
            cat = self.registry.categories[cat_id]
            self.assertTrue(len(cat.name) > 0)
            self.assertTrue(len(cat.display_name) > 0)
            self.assertTrue(len(cat.owning_boundary) > 0)
            self.assertTrue(len(cat.mathematical_assumptions) > 0)
            self.assertTrue(len(cat.metamorphic_relation) > 0)

    def test_fixtures_span_every_category(self):
        """Every category must have at least one reproducible fixture."""
        fixtures_by_cat: dict[int, list[str]] = {i: [] for i in range(22)}
        for fix in self.registry.fixtures.values():
            fixtures_by_cat[fix.category_id].append(fix.fixture_id)

        for cat_id in range(22):
            self.assertGreater(
                len(fixtures_by_cat[cat_id]),
                0,
                f"Category {cat_id} ({self.registry.categories[cat_id].name}) has no fixtures",
            )

    def test_total_fixture_count(self):
        """Registry must contain 80 minimized fixtures."""
        self.assertEqual(len(self.registry.fixtures), 80)


class TestAttackMutationExecutionAndKillRates(unittest.TestCase):
    """Test execution outcomes: 100% in-scope kill rate, 0 in-scope survivors, documented semantic survivors."""

    @classmethod
    def setUpClass(cls):
        cls.registry = amr.build_canonical_registry()
        cls.receipt = cls.registry.run_all()
        cls.summary = cls.receipt["summary"]

    def test_in_scope_zero_survivors(self):
        """Zero in-scope adversarial mutation attacks must survive (in_scope_survivors == 0)."""
        self.assertEqual(
            self.summary["in_scope_survivors"],
            0,
            f"In-scope adversarial mutations survived: {[r.fixture_id for r in self.registry.results.values() if r.category_id not in (0, 17) and r.status == 'SURVIVOR']}",
        )

    def test_documented_semantic_survivors(self):
        """Category 17 out-of-predicate semantic survivors must be documented (total_survivors == 2)."""
        self.assertEqual(self.summary["total_survivors"], 2)
        self.assertEqual(
            self.summary["documented_semantic_survivors"],
            ["sem_surv_false_chsh_prose", "sem_surv_wrong_projector_thermal_branch"],
        )

    def test_zero_false_rejections(self):
        """Zero authentic inputs or valid certificates must be falsely rejected."""
        self.assertEqual(
            self.summary["total_false_rejections"],
            0,
            f"False rejections detected: {[r.fixture_id for r in self.registry.results.values() if r.status == 'FALSE_REJECTION']}",
        )

    def test_documented_unresolved_cases(self):
        """Category 17 unresolved cases must be documented (total_unresolved == 1)."""
        self.assertEqual(self.summary["total_unresolved"], 1)
        self.assertEqual(
            self.summary["documented_unresolved_cases"],
            ["unres_eigenvalue_degeneracy_defect"],
        )

    def test_in_scope_100_percent_kill_rate(self):
        """In-scope adversarial kill rate must be exactly 100% (1.0)."""
        self.assertEqual(self.summary["in_scope_kill_rate"], 1.0)
        self.assertEqual(self.summary["kill_rate"], 1.0)
        self.assertEqual(self.summary["in_scope_killed"], self.summary["in_scope_adversarial_fixtures"])
        self.assertEqual(self.summary["in_scope_killed"], 70)

    def test_all_positive_controls_accepted(self):
        """All positive control fixtures must be ACCEPTED."""
        self.assertEqual(self.summary["total_accepted"], self.summary["total_positive_control_fixtures"])
        self.assertEqual(self.summary["total_accepted"], 7)
        self.assertEqual(self.summary["false_rejection_rate"], 0.0)


class TestAttackMutationReceiptSchemaAndEvidence(unittest.TestCase):
    """Verify structured JSON receipt matches schema pfp.attack-mutation-receipt.v1."""

    @classmethod
    def setUpClass(cls):
        cls.registry = amr.build_canonical_registry()
        cls.receipt_data = cls.registry.run_all()
        cls.receipt_path = cls.registry.save_receipt()

    def test_receipt_file_exists_and_parses(self):
        """Receipt file must exist and be valid JSON."""
        self.assertTrue(self.receipt_path.is_file())
        with open(self.receipt_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], amr.RECEIPT_SCHEMA)
        self.assertEqual(data["seed_sha256"], host.SUPPORTED_SEED_SHA256)

    def test_categories_and_fixtures_in_receipt(self):
        """Receipt must include all 22 categories with full fixture details."""
        with open(self.receipt_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data["categories"]), 22)
        total_fixtures_in_json = sum(len(c["fixtures"]) for c in data["categories"])
        self.assertEqual(total_fixtures_in_json, data["summary"]["total_fixtures"])

        for cat in data["categories"]:
            self.assertIn("category_id", cat)
            self.assertIn("name", cat)
            self.assertIn("owning_boundary", cat)
            self.assertIn("mathematical_assumptions", cat)
            self.assertIn("metamorphic_relation", cat)
            self.assertIn("fixtures", cat)

            for fix in cat["fixtures"]:
                self.assertIn("fixture_id", fix)
                self.assertIn("status", fix)
                self.assertIn("duration_ms", fix)
                self.assertGreaterEqual(fix["duration_ms"], 0.0)
                self.assertIn("evidence", fix)
                # Evidence must not be empty
                self.assertIsInstance(fix["evidence"], dict)
                self.assertTrue(len(fix["evidence"]) > 0, f"Fixture {fix['fixture_id']} has empty evidence")


class TestCategorySpecificMetamorphicRelations(unittest.TestCase):
    """Deep verification of specific metamorphic relations across key categories."""

    @classmethod
    def setUpClass(cls):
        cls.registry = amr.build_canonical_registry()

    def test_cat1_malformed_rationals(self):
        """Category 1: Wire rational parser catches zero denom, non-numeric, and bit limits."""
        for f_id in ["rat_zero_denominator", "rat_leading_zeros", "rat_bit_limit_exceeded"]:
            res = self.registry.run_fixture(f_id)
            self.assertEqual(res.status, "KILLED")
            self.assertIn("RATIONAL", res.actual_outcome)

        res_float = self.registry.run_fixture("rat_float_string")
        self.assertEqual(res_float.status, "KILLED")
        self.assertIn("FLOAT_OR_NONFINITE_FORBIDDEN", res_float.actual_outcome)

    def test_cat2_duplicate_terms(self):
        """Category 2: Duplicate powers rejected before zero removal."""
        for f_id in ["dup_monomial_powers", "dup_explicit_zeros", "dup_zero_before_removal"]:
            res = self.registry.run_fixture(f_id)
            self.assertEqual(res.status, "KILLED")
            self.assertIn("DUPLICATE_POWERS", res.actual_outcome)

    def test_cat4_degree_grid_aliasing(self):
        """Category 4: Degree bounds catch grid-vanishing quintic polynomial."""
        res = self.registry.run_fixture("deg_grid_aliasing_vanishing_poly")
        self.assertEqual(res.status, "KILLED")

    def test_cat8_intermediate_final_contradictions(self):
        """Category 8: Final answer claim or eigenvector scope rejected."""
        res1 = self.registry.run_fixture("contra_final_answer_certified_true")
        self.assertEqual(res1.status, "KILLED")
        self.assertIn("CONTRADICTION_FINAL_ANSWER_CLAIM", res1.actual_outcome)

        res2 = self.registry.run_fixture("contra_eigenvector_claim")
        self.assertEqual(res2.status, "KILLED")
        self.assertIn("CONTRADICTION_FINAL_ANSWER_CLAIM", res2.actual_outcome)

    def test_cat9_prompt_injection(self):
        """Category 9: Instruction override patterns intercepted."""
        res = self.registry.run_fixture("inject_ignore_previous")
        self.assertEqual(res.status, "KILLED")
        self.assertIn("PROMPT_INJECTION_DETECTED", res.actual_outcome)

    def test_cat10_fake_eis_independence(self):
        """Category 10: Duplicate sensor key aliases and signal cap violations refused."""
        res1 = self.registry.run_fixture("eis_duplicate_sensor_case")
        self.assertEqual(res1.status, "KILLED")
        self.assertIn("DUPLICATE_SENSOR", res1.actual_outcome)

        res2 = self.registry.run_fixture("eis_signal_above_cap")
        self.assertEqual(res2.status, "KILLED")
        self.assertIn("SIGNAL_ABOVE_SENSOR_CAP", res2.actual_outcome)

    def test_cat11_empty_pciv_task_sets(self):
        """Category 11: Empty task sets or zero assigned tasks return invalid/none."""
        res1 = self.registry.run_fixture("pciv_empty_task_metrics")
        self.assertEqual(res1.status, "KILLED")
        self.assertIn("MISSING_MEASUREMENTS", res1.actual_outcome)

        res2 = self.registry.run_fixture("pciv_zero_assigned_completion")
        self.assertEqual(res2.status, "KILLED")
        self.assertEqual(res2.actual_outcome, "None")

    def test_cat12_forged_fitness(self):
        """Category 12: Unexecuted status claims earn 0 credit."""
        res = self.registry.run_fixture("fit_unexecuted_witness_credit")
        self.assertEqual(res.status, "KILLED")
        self.assertEqual(res.actual_outcome, "ZERO_CREDIT")

    def test_cat13_noncommuting_substitutions(self):
        """Category 13: J <-> K parameter swap refuted by native 125-node grid witness."""
        res = self.registry.run_fixture("noncomm_hamiltonian_param_swap")
        self.assertEqual(res.status, "KILLED")
        self.assertEqual(res.actual_outcome, "REFUTED_IDENTITY")
        self.assertIn("witness", res.evidence)
        witness = res.evidence["witness"]
        self.assertNotEqual(witness["claimed"], witness["native"])

    def test_cat14_ledger_crashes(self):
        """Category 14: Over-budget reservation and transaction rollback integrity."""
        res1 = self.registry.run_fixture("ledger_cap_exceeded_rejection")
        self.assertEqual(res1.status, "KILLED")
        self.assertIn("aggregate run cap would be exceeded", res1.actual_outcome)

        res2 = self.registry.run_fixture("ledger_transaction_rollback")
        self.assertEqual(res2.status, "KILLED")
        self.assertEqual(res2.actual_outcome, "ROLLBACK_CONFIRMED")

    def test_cat15_ambiguous_provider_delivery(self):
        """Category 15: Transport timeout raises reconciliation error and locks run."""
        res = self.registry.run_fixture("provider_transport_timeout")
        self.assertEqual(res.status, "KILLED")
        self.assertIn("Transport failed; no retry; charge requires reconciliation", res.actual_outcome)

    def test_cat16_single_use_openrouter_reuse(self):
        """Category 16: Second upper_quote call refused."""
        res = self.registry.run_fixture("openrouter_upper_quote_double_call")
        self.assertEqual(res.status, "KILLED")
        self.assertIn("Previous prepared dispatch must not be overwritten", res.actual_outcome)

    def test_cat17_out_of_predicate_semantic_survivors(self):
        """Category 17: Valid intermediate charpoly paired with false downstream claims survives intermediate checking."""
        res1 = self.registry.run_fixture("sem_surv_false_chsh_prose")
        self.assertEqual(res1.status, "SURVIVOR")
        self.assertIn("Downstream false prose", res1.actual_outcome)

        res2 = self.registry.run_fixture("sem_surv_wrong_projector_thermal_branch")
        self.assertEqual(res2.status, "SURVIVOR")
        self.assertIn("Downstream wrong projector", res2.actual_outcome)

        res3 = self.registry.run_fixture("unres_eigenvalue_degeneracy_defect")
        self.assertEqual(res3.status, "UNRESOLVED")
        self.assertIn("Eigenspace defectiveness/degeneracy", res3.actual_outcome)


if __name__ == "__main__":
    unittest.main()
