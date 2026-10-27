"""Unit tests for CertifiedLadderEvaluator and Domain Models (H0-H13).

AuthorityEffect: None.
Governing standards:
- RULE_VO_EXACT_TYPE_EQUALITY_001 (exact-type equality)
- HP_PY_002 (canonical immutable collections)
- RULE_CLEAN_ARCH_INWARD_001 (clean architecture inward dependencies)
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pfp.domain.pilots.certified_ladder import (
    DebtMetric,
    HypothesisVerdict,
)
from pfp.use_cases.evaluate_certified_ladder import (
    EvaluateCertifiedLadderUseCase,
)
from adversary.tests.pilots.certified_ladder.hypothesis_evaluator import (
    CertifiedLadderEvaluator,
)


class TestCertifiedLadderEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = CertifiedLadderEvaluator()
        self.use_case = EvaluateCertifiedLadderUseCase()

    def test_hypotheses_loaded_totality(self) -> None:
        self.assertEqual(len(self.evaluator.hypotheses), 14)
        for i in range(14):
            h_id = f"H{i}"
            self.assertIn(h_id, self.evaluator.hypotheses)

    def test_h0_evaluation_pass_and_refutation(self) -> None:
        pass_records = [
            {"is_cheat_or_negative": True, "verdict": "REJECTED"},
            {"is_cheat_or_negative": False, "verdict": "ACCEPTED", "pass1_verdict": "PASS", "pass2_verdict": "PASS"},
        ]
        v_pass = self.evaluator.evaluate_h0_gate_controls(pass_records)
        self.assertFalse(v_pass.refuted)
        self.assertEqual(v_pass.status, "RETAINED")

        cheat_accepted = [
            {"is_cheat_or_negative": True, "verdict": "ACCEPTED"},
        ]
        v_fail = self.evaluator.evaluate_h0_gate_controls(cheat_accepted)
        self.assertTrue(v_fail.refuted)
        self.assertEqual(v_fail.status, "REFUTED")

    def test_h1_cost_accuracy_evaluation(self) -> None:
        # Sample size guard
        v_untested = self.evaluator.evaluate_h1_cost_accuracy(0.40, 0.65, 0.04, 0.03, 20)
        self.assertEqual(v_untested.status, "UNTESTED")

        # >= 20 point accuracy gain
        v_retained = self.evaluator.evaluate_h1_cost_accuracy(0.40, 0.65, 0.04, 0.04, 35)
        self.assertEqual(v_retained.status, "RETAINED")

        # Refuted if neither accuracy gain nor cost cut holds
        v_refuted = self.evaluator.evaluate_h1_cost_accuracy(0.40, 0.45, 0.04, 0.038, 35)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h2_stage_saturation(self) -> None:
        v_retained = self.evaluator.evaluate_h2_stage_saturation({1: 0.45, 3: 0.60, 5: 0.72, 8: 0.72})
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h2_stage_saturation({1: 0.70, 3: 0.60, 5: 0.50, 8: 0.40})
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h3_minor_rewrite_invariance(self) -> None:
        v_retained = self.evaluator.evaluate_h3_minor_rewrite_invariance(0.03)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h3_minor_rewrite_invariance(0.06)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h4_antibody_transfer(self) -> None:
        v_retained = self.evaluator.evaluate_h4_antibody_transfer(False, 0.15)
        self.assertEqual(v_retained.status, "RETAINED")

        v_contam = self.evaluator.evaluate_h4_antibody_transfer(True, 0.20)
        self.assertEqual(v_contam.status, "REFUTED")

        v_low_gain = self.evaluator.evaluate_h4_antibody_transfer(False, 0.05)
        self.assertEqual(v_low_gain.status, "REFUTED")

    def test_h5_refusal_bluffing(self) -> None:
        v_retained = self.evaluator.evaluate_h5_refusal_bluffing(0.50, 0.20)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h5_refusal_bluffing(0.30, 0.40)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h6_loss_ledger_conservation(self) -> None:
        v_retained = self.evaluator.evaluate_h6_loss_ledger_conservation(0, 0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h6_loss_ledger_conservation(2, 0)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h7_licensed_context_lift(self) -> None:
        v_retained = self.evaluator.evaluate_h7_licensed_context_lift(0, 0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h7_licensed_context_lift(1, 0)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h8_curvature_refusal(self) -> None:
        v_retained = self.evaluator.evaluate_h8_curvature_refusal(0, 0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h8_curvature_refusal(1, 0)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h9_zero_float_law(self) -> None:
        v_retained = self.evaluator.evaluate_h9_zero_float_law(0, 0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h9_zero_float_law(1, 0)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h10_deductive_solver_invariance(self) -> None:
        v_retained = self.evaluator.evaluate_h10_deductive_solver_invariance(0.95, 0.95)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h10_deductive_solver_invariance(0.95, 0.90)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h11_magma_witness(self) -> None:
        v_retained = self.evaluator.evaluate_h11_magma_witness(0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h11_magma_witness(2)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h12_semantic_mutant_kill(self) -> None:
        v_retained = self.evaluator.evaluate_h12_semantic_mutant_kill({"suite_a": 4, "suite_b": 6})
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h12_semantic_mutant_kill({"suite_a": 3, "suite_b": 4})
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_h13_preflight_leak_free(self) -> None:
        v_retained = self.evaluator.evaluate_h13_preflight_leak_free(0, 0)
        self.assertEqual(v_retained.status, "RETAINED")

        v_refuted = self.evaluator.evaluate_h13_preflight_leak_free(1, 0)
        self.assertEqual(v_refuted.status, "REFUTED")

    def test_full_self_test_report(self) -> None:
        report = self.evaluator.run_self_test()
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.total_hypotheses, 14)
        self.assertEqual(report.refuted_count, 0)
        self.assertEqual(report.retained_count, 14)

    def test_debt_metric_operationalization(self) -> None:
        debt = DebtMetric(
            open_residuals=(("slot_1", 2), ("slot_2", 3)),
            boundary_residual=1,
            curvature_defect=2,
            uninverted_coordinates_count=4,
        )
        # Total debt = (2 + 3) + 1 + 2 + 4 = 12
        self.assertEqual(debt.total_debt, 12)

    def test_exact_type_equality_and_hashability(self) -> None:
        v1 = HypothesisVerdict.create("H0", "claim", False, "RETAINED", "details", {"k": "v"})
        v2 = HypothesisVerdict.create("H0", "claim", False, "RETAINED", "details", {"k": "v"})

        # Exact equality
        self.assertEqual(v1, v2)
        # Hashable
        self.assertEqual(hash(v1), hash(v2))
        s = {v1, v2}
        self.assertEqual(len(s), 1)

        # Cross-class type confusion rejected
        class FakeVerdict:
            pass

        self.assertFalse(v1 == FakeVerdict())
        self.assertFalse(v1 == "H0")

    def test_p0_gate_controls_execution_pass_to_master(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            receipt = self.evaluator.execute_p0_gate_controls(receipts_dir=Path(tmp_dir))
            self.assertEqual(receipt.status, "PASS_TO_MASTER")
            self.assertEqual(receipt.cheats_accepted, 0)
            self.assertEqual(receipt.replay_disagreements, 0)
            self.assertGreater(receipt.cheats_tested, 0)
            self.assertEqual(receipt.cheats_rejected, receipt.cheats_tested)
            self.assertGreater(receipt.controls_passed, 0)

            # Receipt written to filesystem
            receipt_file = Path(tmp_dir) / "p0_gate_controls_receipt.json"
            self.assertTrue(receipt_file.is_file())


if __name__ == "__main__":
    unittest.main()
