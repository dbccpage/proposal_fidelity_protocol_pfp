"""
test_mcnemar_arms_runner.py — Targeted test verifying McNemar evaluation execution on 200 hidden base cases.
"""

from fractions import Fraction

from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.mcnemar_arms_evaluation import (
    compute_mcnemar_exact,
    remove_distractor_spans,
    run_mcnemar_hidden_base_arms_evaluation,
)


class TestMcNemarArmsEvaluation:
    """Targeted tests for pre-registered McNemar arms evaluation."""

    def test_compute_mcnemar_exact_properties(self):
        """Verify exact rational calculations for concordant and discordant pairs."""
        # Concordant / no discordance
        res_zero = compute_mcnemar_exact(0, 0)
        assert res_zero["chi2"] == "0"
        assert res_zero["p_value"] == "1"
        assert res_zero["is_significant_alpha_0_05"] is False

        # Symmetric discordance
        res_sym = compute_mcnemar_exact(10, 10)
        assert res_sym["chi2"] == "0"
        assert res_sym["p_value"] == "1"
        assert res_sym["is_significant_alpha_0_05"] is False

        # Highly asymmetric discordance
        res_asym = compute_mcnemar_exact(40, 0)
        assert res_asym["chi2"] == "40"
        assert res_asym["p_value"] == str(Fraction(1, 2**39))
        assert res_asym["is_significant_alpha_0_05"] is True

    def test_remove_distractor_spans(self):
        """Verify prompt span deletion for Arm F-delete."""
        text = "Hello world! This is a test."
        spans = [(6, 12)]  # "world!"
        cleaned = remove_distractor_spans(text, spans)
        assert cleaned == "Hello  This is a test."
        assert "world!" not in cleaned

    def test_full_mcnemar_run_on_200_hidden_cases(self):
        """Execute pre-registered McNemar test across all 200 hidden base cases."""
        rep = run_mcnemar_hidden_base_arms_evaluation(base_seed=2026)
        assert rep["sample_size"] == 200

        # F-distractor vs Arm A
        f_vs_a = rep["comparison_F_distractor_vs_Arm_A"]
        assert f_vs_a["table_2x2"]["A_fail_F_pass_b"] >= 30
        assert f_vs_a["table_2x2"]["A_pass_F_fail_c"] == 0
        assert f_vs_a["mcnemar"]["is_significant_alpha_0_05"] is True

        # F-distractor vs F-delete
        f_vs_del = rep["comparison_F_distractor_vs_F_delete"]
        assert f_vs_del["table_2x2"]["Delete_fail_F_pass_b"] == 0
        assert f_vs_del["table_2x2"]["Delete_pass_F_fail_c"] == 0
        assert f_vs_del["mcnemar"]["is_significant_alpha_0_05"] is False

        # Synthetic fixture classification and Claim Hygiene assertions
        assert rep["is_synthetic_fixture"] is True
        assert rep["is_empirical_measurement"] is False
        assert rep["evaluation_type"] == "SYNTHETIC_VERIFICATION_HARNESS_FIXTURE"
        assert "claim_discipline" in rep
        assert len(rep["claim_discipline"]["supports"]) > 0
        assert len(rep["claim_discipline"]["does_not_support"]) > 0
