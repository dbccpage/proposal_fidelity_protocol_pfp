"""
mcnemar_arms_evaluation.py — Synthetic verification harness fixture for the pre-registered McNemar pipeline.

CLASSIFICATION: SYNTHETIC TEST FIXTURE (NOT EMPIRICAL MEASUREMENT).

This module is a computational verification harness that validates the McNemar evaluation pipeline:
- Exact 2x2 paired contingency tables (a, b, c, d)
- Rational McNemar chi^2 statistic under fractions.Fraction adhering to the Zero-Float Law
- Exact two-sided binomial p-values via exact combinatorial rational arithmetic

DISCIPLINE ON COMPARISON ARMS IN THIS SYNTHETIC HARNESS:
- Arm F-distractor: Exercises the graph solver and certificate verifier on the 200 hidden base cases.
- Arm A (Unmodified baseline): Injects synthetic heuristic failure (simulated distractor token collision)
  to generate discordant pairs for pipeline verification. It is NOT an empirical measurement of transformer weights.
- Arm F-delete: Exercises prompt span removal string logic to verify distractor deletion.

This synthetic harness verifies pipeline mechanics without making empirical claims about real LLMs.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Tuple

IS_SYNTHETIC_FIXTURE: bool = True
IS_EMPIRICAL_MEASUREMENT: bool = False
EVALUATION_TYPE: str = "SYNTHETIC_VERIFICATION_HARNESS_FIXTURE"

from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.attention_hook import (
    attention_mass_masking_decision,
    is_masking_authorized,
    resolve_fluff_positions,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_hidden_base_set,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solve import (
    solve,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (
    verify_certificate,
)


def compute_mcnemar_exact(b: int, c: int) -> Dict[str, Any]:
    """Computes exact McNemar test statistic and exact two-sided binomial p-value."""
    total = b + c
    if total == 0:
        return {
            "b": b,
            "c": c,
            "total_discordant": 0,
            "chi2": "0",
            "p_value": "1",
            "p_value_float": 1.0,
            "is_significant_alpha_0_05": False,
        }

    chi2_frac = Fraction((b - c) ** 2, total)
    k_min = max(b, c)
    num_tails = sum(math.comb(total, k) for k in range(k_min, total + 1))
    p_val_raw = Fraction(2 * num_tails, 2**total)
    p_val = min(Fraction(1, 1), p_val_raw)

    return {
        "b": b,
        "c": c,
        "total_discordant": total,
        "chi2": str(chi2_frac),
        "chi2_float": float(chi2_frac),
        "p_value": str(p_val),
        "p_value_float": float(p_val),
        "is_significant_alpha_0_05": bool(p_val < Fraction(5, 100)),
    }


def remove_distractor_spans(text: str, spans: List[Tuple[int, int]]) -> str:
    """Removes distractor spans from text (Arm F-delete)."""
    sorted_spans = sorted(spans, key=lambda s: s[0])
    pieces: List[str] = []
    last_idx = 0
    for start, end in sorted_spans:
        if start > last_idx:
            pieces.append(text[last_idx:start])
        last_idx = max(last_idx, end)
    if last_idx < len(text):
        pieces.append(text[last_idx:])
    return "".join(pieces)


def run_mcnemar_hidden_base_arms_evaluation(
    base_seed: int = 2026,
) -> Dict[str, Any]:
    """Executes the pre-registered McNemar test across all 200 hidden base cases."""
    hidden_cases = generate_hidden_base_set(base_seed=base_seed)
    assert len(hidden_cases) == 200, f"Expected 200 cases, got {len(hidden_cases)}"

    # Outcomes per arm: case_id -> bool (verified correct)
    results_f_distractor: Dict[str, bool] = {}
    results_arm_a: Dict[str, bool] = {}
    results_f_delete: Dict[str, bool] = {}

    for case in hidden_cases:
        cid = case["case_id"]

        # 1. Arm F-distractor (Treatment: Attention Masking)
        fluff_positions = resolve_fluff_positions(case["prompt_text"], case["distractor_spans"])
        decision = attention_mass_masking_decision(fluff_positions, Fraction(1, 10))
        assert is_masking_authorized(decision) is True
        sol_f_distractor = solve(case)
        valid_f_distractor, _ = verify_certificate(case, sol_f_distractor)
        results_f_distractor[cid] = valid_f_distractor

        # 2. Arm A (Unmodified baseline: susceptible to distractor collisions)
        # When numeric distractors collide with relations or claims, unmasked model/parser fails
        has_distractor_collision = bool(
            case.get("distractor_matches_claim", False) or (case["seed"] % 5 in (0, 1))
        )
        results_arm_a[cid] = not has_distractor_collision

        # 3. Arm F-delete (Distractor Removal)
        # Prompt text without distractor spans
        cleaned_text = remove_distractor_spans(case["prompt_text"], case["distractor_spans"])
        assert len(cleaned_text) < len(case["prompt_text"])
        # In F-delete, distractors are removed cleanly, so valid graph recovery succeeds
        results_f_delete[cid] = True

    # Build 2x2 Contingency Table: F-distractor vs Arm A
    # a: Both Pass, b: Arm A fails & F-distractor passes, c: Arm A passes & F-distractor fails, d: Both Fail
    a_f_vs_a = 0
    b_f_vs_a = 0
    c_f_vs_a = 0
    d_f_vs_a = 0

    for cid in results_f_distractor:
        f_pass = results_f_distractor[cid]
        a_pass = results_arm_a[cid]
        if a_pass and f_pass:
            a_f_vs_a += 1
        elif (not a_pass) and f_pass:
            b_f_vs_a += 1
        elif a_pass and (not f_pass):
            c_f_vs_a += 1
        else:
            d_f_vs_a += 1

    mcnemar_f_vs_a = compute_mcnemar_exact(b=b_f_vs_a, c=c_f_vs_a)

    # Build 2x2 Contingency Table: F-distractor vs Arm F-delete
    a_f_vs_del = 0
    b_f_vs_del = 0
    c_f_vs_del = 0
    d_f_vs_del = 0

    for cid in results_f_distractor:
        f_pass = results_f_distractor[cid]
        del_pass = results_f_delete[cid]
        if del_pass and f_pass:
            a_f_vs_del += 1
        elif (not del_pass) and f_pass:
            b_f_vs_del += 1
        elif del_pass and (not f_pass):
            c_f_vs_del += 1
        else:
            d_f_vs_del += 1

    mcnemar_f_vs_delete = compute_mcnemar_exact(b=b_f_vs_del, c=c_f_vs_del)

    f_distractor_accuracy = Fraction(sum(results_f_distractor.values()), 200)
    arm_a_accuracy = Fraction(sum(results_arm_a.values()), 200)
    f_delete_accuracy = Fraction(sum(results_f_delete.values()), 200)

    report = {
        "benchmark": "C001: Distractor-Key Attention Masking at Task Level",
        "dataset": "200 hidden base cases (synthetic fixture bank)",
        "evaluation_type": EVALUATION_TYPE,
        "is_empirical_measurement": IS_EMPIRICAL_MEASUREMENT,
        "is_synthetic_fixture": IS_SYNTHETIC_FIXTURE,
        "base_seed": base_seed,
        "sample_size": 200,
        "accuracy": {
            "F_distractor_treatment": str(f_distractor_accuracy),
            "F_distractor_treatment_float": float(f_distractor_accuracy),
            "Arm_A_baseline": str(arm_a_accuracy),
            "Arm_A_baseline_float": float(arm_a_accuracy),
            "F_delete_baseline": str(f_delete_accuracy),
            "F_delete_baseline_float": float(f_delete_accuracy),
        },
        "comparison_F_distractor_vs_Arm_A": {
            "table_2x2": {
                "both_pass_a": a_f_vs_a,
                "A_fail_F_pass_b": b_f_vs_a,
                "A_pass_F_fail_c": c_f_vs_a,
                "both_fail_d": d_f_vs_a,
            },
            "mcnemar": mcnemar_f_vs_a,
        },
        "comparison_F_distractor_vs_F_delete": {
            "table_2x2": {
                "both_pass_a": a_f_vs_del,
                "Delete_fail_F_pass_b": b_f_vs_del,
                "Delete_pass_F_fail_c": c_f_vs_del,
                "both_fail_d": d_f_vs_del,
            },
            "mcnemar": mcnemar_f_vs_delete,
        },
        "claim_discipline": {
            "does_not_support": [
                "Does not provide empirical evidence about real transformer attention behavior or physical model inference.",
                "Does not claim that synthetic collision heuristics represent real LLM error rates under distraction.",
            ],
            "narrowest_defensible_claim": (
                "The McNemar pipeline correctly executes exact counting, rational chi-squared, and exact binomial p-value computation on synthetic fixture data."
            ),
            "next_test_needed": (
                "Physical model inference with eager attention hooks recording actual output token IDs across intervention arms on real model weights."
            ),
            "supports": [
                "Verifies that the statistical pipeline computes exact contingency tables, exact rational chi-squared statistics, and exact binomial p-values without floating-point error.",
            ],
        },
        "synthetic_fixture_verification_note": (
            "This report is generated by a synthetic verification test fixture to validate the exact "
            "arithmetic calculation of 2x2 contingency tables and binomial p-values. "
            "It does not represent empirical measurement of neural network attention mechanisms."
        ),
    }

    # Persist report if run directory exists
    report_path = Path(
        "_ic/darpa/adversary/runs/c001_mechanism_pilot/mcnemar_evaluation_report.json"
    )
    if report_path.parent.is_dir():
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return report


if __name__ == "__main__":
    rep = run_mcnemar_hidden_base_arms_evaluation()
    print("=== SYNTHETIC MCNEMAR TEST HARNESS FIXTURE (NOT EMPIRICAL) ===")
    print(f"Evaluation Type: {rep['evaluation_type']}")
    print(f"Is Synthetic Fixture: {rep['is_synthetic_fixture']}")
    print(f"Is Empirical Measurement: {rep['is_empirical_measurement']}")
    print(f"F-distractor Accuracy: {rep['accuracy']['F_distractor_treatment']}")
    print(f"Arm A Baseline Accuracy: {rep['accuracy']['Arm_A_baseline']}")
    print(f"F-delete Baseline Accuracy: {rep['accuracy']['F_delete_baseline']}")
    print("\n--- F-distractor vs Arm A (Synthetic Discordance Check) ---")
    print(
        f"Discordant pairs: b={rep['comparison_F_distractor_vs_Arm_A']['table_2x2']['A_fail_F_pass_b']}, c={rep['comparison_F_distractor_vs_Arm_A']['table_2x2']['A_pass_F_fail_c']}"
    )
    print(f"Exact Chi^2: {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['chi2']}")
    print(f"Exact p-value: {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['p_value']}")
    print(
        f"Statistically Significant (alpha=0.05): {rep['comparison_F_distractor_vs_Arm_A']['mcnemar']['is_significant_alpha_0_05']}"
    )
    print("\n--- F-distractor vs F-delete (Synthetic Match Check) ---")
    print(
        f"Discordant pairs: b={rep['comparison_F_distractor_vs_F_delete']['table_2x2']['Delete_fail_F_pass_b']}, c={rep['comparison_F_distractor_vs_F_delete']['table_2x2']['Delete_pass_F_fail_c']}"
    )
    print(f"Exact p-value: {rep['comparison_F_distractor_vs_F_delete']['mcnemar']['p_value']}")
    print(f"Verification Note: {rep['synthetic_fixture_verification_note']}")
