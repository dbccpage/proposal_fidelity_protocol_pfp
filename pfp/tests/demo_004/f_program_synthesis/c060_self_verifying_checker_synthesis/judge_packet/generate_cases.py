"""Generate and dual-verify 64 hidden evaluation cases for C060.
Checker Synthesis Scored by Mutation Kill Rate.
"""

import json
import sys
from fractions import Fraction
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[6]))

from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.reference_solver.checker import (
    check as ref_check,
)

cases_dir = Path(__file__).resolve().parent / "cases"
cases_dir.mkdir(parents=True, exist_ok=True)


def build_cases():
    cases = []

    # =========================================================================
    # PART 1: 32 BASE CASES (b01 - b32)
    # =========================================================================
    # 16 Valid Self-Certificates (ACCEPT)
    # b01: Single-edge tree exact repair
    cases.append(
        {
            "case_id": "c060_b01_valid_single_edge_tree",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b02: Two-edge path exact repair
    cases.append(
        {
            "case_id": "c060_b02_valid_two_edge_path",
            "case": {"d0": [["1", "-1"], ["0", "1"]], "omega": ["3", "-2"], "w": ["1", "1"]},
            "cert": {"alpha": ["1", "-2"], "r": ["0", "0"], "y": ["0", "0"], "value": "0"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b03: Triangle cycle with frustrated obstruction
    # d0: 3 edges, 3 vertices (v0-v1, v1-v2, v2-v0)
    # cycle chord forces residual
    cases.append(
        {
            "case_id": "c060_b03_valid_triangle_frustrated",
            "case": {
                "d0": [["1", "-1", "0"], ["0", "1", "-1"], ["-1", "0", "1"]],
                "omega": ["1", "0", "0"],
                "w": ["1", "1", "1"],
            },
            "cert": {
                "alpha": ["0", "0", "0"],
                "r": ["1", "0", "0"],
                "y": ["1", "1", "1"],
                "value": "1",
            },
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b04: Triangle with fractional weights
    cases.append(
        {
            "case_id": "c060_b04_valid_triangle_fractional_weights",
            "case": {
                "d0": [["1", "-1"], ["0", "1"], ["-1", "0"]],
                "omega": ["1", "0", "0"],
                "w": ["1/2", "1/2", "1/2"],
            },
            "cert": {
                "alpha": ["0", "0"],
                "r": ["1", "0", "0"],
                "y": ["1/2", "1/2", "1/2"],
                "value": "1/2",
            },
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b05: 4-cycle with obstruction
    cases.append(
        {
            "case_id": "c060_b05_valid_4cycle",
            "case": {
                "d0": [
                    ["1", "-1", "0", "0"],
                    ["0", "1", "-1", "0"],
                    ["0", "0", "1", "-1"],
                    ["-1", "0", "0", "1"],
                ],
                "omega": ["1", "1", "0", "0"],
                "w": ["1", "1", "1", "1"],
            },
            "cert": {
                "alpha": ["0", "0", "0", "0"],
                "r": ["1", "1", "0", "0"],
                "y": ["1", "1", "1", "1"],
                "value": "2",
            },
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b06: Two-component graph with zero cochain
    cases.append(
        {
            "case_id": "c060_b06_valid_zero_cochain",
            "case": {"d0": [["1"], ["-1"]], "omega": ["0", "0"], "w": ["2", "3"]},
            "cert": {"alpha": ["0"], "r": ["0", "0"], "y": ["0", "0"], "value": "0"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b07: Single edge, non-zero residual
    cases.append(
        {
            "case_id": "c060_b07_valid_single_edge_survivor",
            "case": {"d0": [["0"]], "omega": ["5"], "w": ["2"]},
            "cert": {"alpha": ["0"], "r": ["5"], "y": ["2"], "value": "10"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b08: Negative cochain with signed dual
    cases.append(
        {
            "case_id": "c060_b08_valid_negative_cochain",
            "case": {"d0": [["0"]], "omega": ["-7"], "w": ["3"]},
            "cert": {"alpha": ["0"], "r": ["-7"], "y": ["-3"], "value": "21"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b09: Large numbers (10^6)
    cases.append(
        {
            "case_id": "c060_b09_valid_large_numbers",
            "case": {
                "d0": [["1", "0"], ["0", "1"]],
                "omega": ["1000000", "2000000"],
                "w": ["5", "10"],
            },
            "cert": {
                "alpha": ["1000000", "2000000"],
                "r": ["0", "0"],
                "y": ["0", "0"],
                "value": "0",
            },
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b10: Big integers beyond 2^64
    big_val = "18446744073709551617"  # 2^64 + 1
    cases.append(
        {
            "case_id": "c060_b10_valid_big_integers",
            "case": {"d0": [["0"]], "omega": [big_val], "w": ["1"]},
            "cert": {"alpha": [big_val], "r": [big_val], "y": ["1"], "value": big_val},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b11: Non-trivial dual witness with tight bounds
    cases.append(
        {
            "case_id": "c060_b11_valid_tight_dual_bound",
            "case": {"d0": [["1", "-1"], ["-1", "1"]], "omega": ["4", "0"], "w": ["2", "2"]},
            "cert": {"alpha": ["2", "0"], "r": ["2", "2"], "y": ["2", "2"], "value": "8"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b12: Multiple columns in d0
    cases.append(
        {
            "case_id": "c060_b12_valid_three_variables",
            "case": {
                "d0": [["1", "2", "3"], ["-1", "0", "1"]],
                "omega": ["6", "0"],
                "w": ["1", "1"],
            },
            "cert": {"alpha": ["1", "1", "1"], "r": ["0", "0"], "y": ["0", "0"], "value": "0"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b13: Rational weights with non-trivial denominator
    cases.append(
        {
            "case_id": "c060_b13_valid_rational_weights",
            "case": {"d0": [["1"], ["-1"]], "omega": ["1/3", "2/3"], "w": ["3/4", "3/4"]},
            "cert": {"alpha": ["0"], "r": ["1/3", "2/3"], "y": ["3/4", "3/4"], "value": "3/4"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b14: Diamond graph
    cases.append(
        {
            "case_id": "c060_b14_valid_diamond",
            "case": {
                "d0": [["1", "-1", "0"], ["0", "1", "-1"], ["1", "0", "-1"]],
                "omega": ["1", "1", "0"],
                "w": ["1", "1", "1"],
            },
            "cert": {
                "alpha": ["0", "0", "0"],
                "r": ["1", "1", "0"],
                "y": ["1", "1", "-1"],
                "value": "2",
            },
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b15: 3-edge cycle with zero residual on edges 1 and 2
    cases.append(
        {
            "case_id": "c060_b15_valid_partial_zero_residual",
            "case": {"d0": [["1"], ["-1"]], "omega": ["1", "-1"], "w": ["2", "5"]},
            "cert": {"alpha": ["1"], "r": ["0", "0"], "y": ["0", "0"], "value": "0"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # b16: Fractional dual values with denominator 7
    cases.append(
        {
            "case_id": "c060_b16_valid_denom_seven",
            "case": {"d0": [["0"]], "omega": ["2/7"], "w": ["1"]},
            "cert": {"alpha": ["0"], "r": ["2/7"], "y": ["1"], "value": "2/7"},
            "expected_verdict": "ACCEPT",
            "expected_code": None,
        }
    )

    # 16 Corrupted / Invalid Certificates (REJECT)
    # b17: RESIDUAL_MISMATCH (r corrupted)
    cases.append(
        {
            "case_id": "c060_b17_residual_mismatch",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["1"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "RESIDUAL_MISMATCH",
        }
    )

    # b18: PRIMAL_VALUE_MISMATCH (value doesn't match sum w_e |r_e|)
    cases.append(
        {
            "case_id": "c060_b18_primal_value_mismatch",
            "case": {"d0": [["0"]], "omega": ["5"], "w": ["2"]},
            "cert": {"alpha": ["0"], "r": ["5"], "y": ["2"], "value": "9"},
            "expected_verdict": "REJECT",
            "expected_code": "PRIMAL_VALUE_MISMATCH",
        }
    )

    # b19: DUAL_NOT_IN_COKERNEL (d0^T * y != 0)
    cases.append(
        {
            "case_id": "c060_b19_dual_not_in_cokernel",
            "case": {"d0": [["1"], ["-1"]], "omega": ["1", "0"], "w": ["1", "1"]},
            "cert": {"alpha": ["1/2"], "r": ["1/2", "1/2"], "y": ["1", "-1"], "value": "1"},
            "expected_verdict": "REJECT",
            "expected_code": "DUAL_NOT_IN_COKERNEL",
        }
    )

    # b20: DUAL_BOUND_VIOLATED (|y_e| > w_e, but y_e <= w_e for signed test)
    cases.append(
        {
            "case_id": "c060_b20_dual_bound_violated",
            "case": {"d0": [["0"]], "omega": ["0"], "w": ["1"]},
            "cert": {"alpha": ["0"], "r": ["0"], "y": ["-2"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DUAL_BOUND_VIOLATED",
        }
    )

    # b21: DUAL_VALUE_MISMATCH (y^T * omega != value)
    cases.append(
        {
            "case_id": "c060_b21_dual_value_mismatch",
            "case": {"d0": [["0"]], "omega": ["5"], "w": ["2"]},
            "cert": {"alpha": ["0"], "r": ["5"], "y": ["1"], "value": "10"},
            "expected_verdict": "REJECT",
            "expected_code": "DUAL_VALUE_MISMATCH",
        }
    )

    # b22: NONPOSITIVE_WEIGHT (w_e == 0)
    cases.append(
        {
            "case_id": "c060_b22_zero_weight",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["0"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONPOSITIVE_WEIGHT",
        }
    )

    # b23: NONPOSITIVE_WEIGHT (w_e < 0)
    cases.append(
        {
            "case_id": "c060_b23_negative_weight",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["-1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONPOSITIVE_WEIGHT",
        }
    )

    # b24: DIMENSION (d0 row count mismatch)
    cases.append(
        {
            "case_id": "c060_b24_d0_row_mismatch",
            "case": {"d0": [["1"], ["-1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )

    # b25: DIMENSION (d0 column count mismatch)
    cases.append(
        {
            "case_id": "c060_b25_d0_col_mismatch",
            "case": {"d0": [["1", "2"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )

    # b26: DIMENSION (r length mismatch)
    cases.append(
        {
            "case_id": "c060_b26_r_length_mismatch",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0", "0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )

    # b27: DIMENSION (y length mismatch)
    cases.append(
        {
            "case_id": "c060_b27_y_length_mismatch",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": [], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )

    # b28: NONCANONICAL_RATIONAL (slashed integer "1/1")
    cases.append(
        {
            "case_id": "c060_b28_slashed_integer",
            "case": {"d0": [["1/1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )

    # b29: NONCANONICAL_RATIONAL (unreduced fraction "2/4")
    cases.append(
        {
            "case_id": "c060_b29_unreduced_fraction",
            "case": {"d0": [["1"]], "omega": ["2/4"], "w": ["1"]},
            "cert": {"alpha": ["1/2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )

    # b30: NONCANONICAL_RATIONAL (float string "1.5")
    cases.append(
        {
            "case_id": "c060_b30_float_string",
            "case": {"d0": [["1"]], "omega": ["1.5"], "w": ["1"]},
            "cert": {"alpha": ["3/2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )

    # b31: NONCANONICAL_RATIONAL (leading zeroes "01")
    cases.append(
        {
            "case_id": "c060_b31_leading_zero",
            "case": {"d0": [["1"]], "omega": ["01"], "w": ["1"]},
            "cert": {"alpha": ["1"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )

    # b32: SCHEMA (missing required field 'value')
    cases.append(
        {
            "case_id": "c060_b32_missing_value_field",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"]},
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )

    # =========================================================================
    # PART 2: 16 RELABEL / GAUGE CONTROLS (g01 - g16)
    # =========================================================================
    for idx in range(1, 17):
        base_c = cases[idx - 1]
        gid = f"c060_g{idx:02d}_relabel_control"

        # Clone base case
        g_case = json.loads(json.dumps(base_c))
        g_case["case_id"] = gid

        # Apply scaling to omega, alpha, r, value by 2
        # (Preserves validity and all primal-dual relations exactly)
        if base_c["expected_verdict"] == "ACCEPT":
            d_case = g_case["case"]
            d_cert = g_case["cert"]

            # Multiply omega, alpha, r, value by 2
            d_case["omega"] = [str(Fraction(x) * 2) for x in d_case["omega"]]
            d_cert["alpha"] = [str(Fraction(x) * 2) for x in d_cert["alpha"]]
            d_cert["r"] = [str(Fraction(x) * 2) for x in d_cert["r"]]
            d_cert["value"] = str(Fraction(d_cert["value"]) * 2)
            # y unchanged, w unchanged -> valid scale invariant!

        cases.append(g_case)

    # =========================================================================
    # PART 3: 16 POISONED / BOUNDARY TRAP CASES (p01 - p16)
    # =========================================================================
    # p01: Boolean True as element
    cases.append(
        {
            "case_id": "c060_p01_boolean_in_alpha",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": [True], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p02: Boolean False in w
    cases.append(
        {
            "case_id": "c060_p02_boolean_in_w",
            "case": {"d0": [["1"]], "omega": ["2"], "w": [False]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p03: None / null in omega
    cases.append(
        {
            "case_id": "c060_p03_null_in_omega",
            "case": {"d0": [["1"]], "omega": [None], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p04: Empty string in value
    cases.append(
        {
            "case_id": "c060_p04_empty_string_value",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": ""},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p05: Whitespace in fraction " 1/2 "
    cases.append(
        {
            "case_id": "c060_p05_whitespace_in_fraction",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": [" 1/2 "], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p06: Negative denominator "-1/-2"
    cases.append(
        {
            "case_id": "c060_p06_negative_denominator",
            "case": {"d0": [["1"]], "omega": ["-1/-2"], "w": ["1"]},
            "cert": {"alpha": ["1/2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p07: Leading plus "+5"
    cases.append(
        {
            "case_id": "c060_p07_leading_plus",
            "case": {"d0": [["1"]], "omega": ["+5"], "w": ["1"]},
            "cert": {"alpha": ["5"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p08: cert is a string, not dict
    cases.append(
        {
            "case_id": "c060_p08_cert_not_dict",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": '{"alpha": ["2"]}',
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )
    # p09: cert is a list, not dict
    cases.append(
        {
            "case_id": "c060_p09_cert_is_list",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": ["alpha", "2"],
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )
    # p10: case is a list, not dict
    cases.append(
        {
            "case_id": "c060_p10_case_is_list",
            "case": [["1"]],
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )
    # p11: Negative value with zero residual
    cases.append(
        {
            "case_id": "c060_p11_negative_value",
            "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "-1"},
            "expected_verdict": "REJECT",
            "expected_code": "PRIMAL_VALUE_MISMATCH",
        }
    )
    # p12: Zero denominator "1/0"
    cases.append(
        {
            "case_id": "c060_p12_zero_denominator",
            "case": {"d0": [["1"]], "omega": ["1/0"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "NONCANONICAL_RATIONAL",
        }
    )
    # p13: Empty omega dimension
    cases.append(
        {
            "case_id": "c060_p13_empty_dimension",
            "case": {"d0": [], "omega": [], "w": []},
            "cert": {"alpha": [], "r": [], "y": [], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )
    # p14: d0 row has wrong type (integer instead of list)
    cases.append(
        {
            "case_id": "c060_p14_d0_row_not_list",
            "case": {"d0": [1], "omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )
    # p15: d0 row column count uneven
    cases.append(
        {
            "case_id": "c060_p15_d0_uneven_rows",
            "case": {"d0": [["1", "0"], ["0"]], "omega": ["2", "3"], "w": ["1", "1"]},
            "cert": {"alpha": ["2", "3"], "r": ["0", "0"], "y": ["0", "0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "DIMENSION",
        }
    )
    # p16: Missing d0 in case
    cases.append(
        {
            "case_id": "c060_p16_missing_d0",
            "case": {"omega": ["2"], "w": ["1"]},
            "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
            "expected_verdict": "REJECT",
            "expected_code": "SCHEMA",
        }
    )

    return cases


def main():
    cases = build_cases()
    print(f"Total cases generated: {len(cases)}")
    assert len(cases) == 64, f"Expected exactly 64 cases, got {len(cases)}"

    for c in cases:
        cid = c["case_id"]
        # Save case JSON
        with open(cases_dir / f"{cid}.json", "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)

        # Verify with reference checker and dual checkers
        cand_out = ref_check(c["case"], c["cert"])
        ok1, msg1 = verify_candidate(c, cand_out)
        assert ok1, f"Exact checker failed on {cid}: {msg1}"

        ok2, msg2 = independent_check(c, cand_out)
        assert ok2, f"Independent checker failed on {cid}: {msg2}"

    print("Generated 64/64 hidden cases dual-verified successfully!")


if __name__ == "__main__":
    main()
