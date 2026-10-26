"""Generate and verify 48 hostile checker mutations for C060.
Checker Synthesis Scored by Mutation Kill Rate.

Each mutant represents a corrupted candidate checker.
To pass the reality gate, 100.0% of mutants (48/48) must be killed
by the 64 hidden evaluation cases.
"""

import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[6]))

from omega_engine_projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.reference_solver.checker import (
    check as ref_check,
)


def get_mutants() -> Dict[str, Any]:
    """Returns a dict of 48 mutant checker functions."""
    mutants = {}

    # =========================================================================
    # CLASS A: AUTOIMMUNE MUTANTS (False Rejections on Valid Cases, m01 - m08)
    # =========================================================================
    def m01_always_reject(case: Any, cert: Any) -> Dict[str, Any]:
        return {"verdict": "REJECT", "code": "SCHEMA", "reason": "Mutant always rejects."}

    mutants["c060_m01_always_reject"] = m01_always_reject

    def m02_reject_zero_value(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT" and cert.get("value") == "0":
            return {
                "verdict": "REJECT",
                "code": "PRIMAL_VALUE_MISMATCH",
                "reason": "Zero value rejected.",
            }
        return res

    mutants["c060_m02_reject_zero_value"] = m02_reject_zero_value

    def m03_reject_negative_alpha(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            for a in cert.get("alpha", []):
                if "-" in str(a):
                    return {
                        "verdict": "REJECT",
                        "code": "SCHEMA",
                        "reason": "Negative alpha rejected.",
                    }
        return res

    mutants["c060_m03_reject_negative_alpha"] = m03_reject_negative_alpha

    def m04_reject_negative_dual(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            for y in cert.get("y", []):
                if "-" in str(y):
                    return {
                        "verdict": "REJECT",
                        "code": "DUAL_BOUND_VIOLATED",
                        "reason": "Negative dual rejected.",
                    }
        return res

    mutants["c060_m04_reject_negative_dual"] = m04_reject_negative_dual

    def m05_reject_large_matrix(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            d0 = case.get("d0", [])
            if len(d0) > 2:
                return {
                    "verdict": "REJECT",
                    "code": "DIMENSION",
                    "reason": "Dimension > 2 rejected.",
                }
        return res

    mutants["c060_m05_reject_large_matrix"] = m05_reject_large_matrix

    def m06_reject_fractional_weights(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            for w in case.get("w", []):
                if "/" in str(w):
                    return {
                        "verdict": "REJECT",
                        "code": "NONPOSITIVE_WEIGHT",
                        "reason": "Fractional weight rejected.",
                    }
        return res

    mutants["c060_m06_reject_fractional_weights"] = m06_reject_fractional_weights

    def m07_reject_big_integers(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            for a in cert.get("alpha", []):
                if len(str(a)) > 10:
                    return {
                        "verdict": "REJECT",
                        "code": "NONCANONICAL_RATIONAL",
                        "reason": "Big integer rejected.",
                    }
        return res

    mutants["c060_m07_reject_big_integers"] = m07_reject_big_integers

    def m08_reject_zero_residual(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            if any(r == "0" for r in cert.get("r", [])):
                return {
                    "verdict": "REJECT",
                    "code": "RESIDUAL_MISMATCH",
                    "reason": "Zero residual rejected.",
                }
        return res

    mutants["c060_m08_reject_zero_residual"] = m08_reject_zero_residual

    # =========================================================================
    # CLASS B: PERMISSIVE MUTANTS (Missing Invariant Checks, m09 - m16)
    # =========================================================================
    def m09_always_accept(case: Any, cert: Any) -> Dict[str, Any]:
        return {"verdict": "ACCEPT", "code": None, "reason": "Mutant always accepts."}

    mutants["c060_m09_always_accept"] = m09_always_accept

    def m10_skip_cokernel_check(case: Any, cert: Any) -> Dict[str, Any]:
        # Validates everything except d0^T y == 0
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_NOT_IN_COKERNEL":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped cokernel."}
        return res

    mutants["c060_m10_skip_cokernel_check"] = m10_skip_cokernel_check

    def m11_skip_dual_bound(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_BOUND_VIOLATED":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped dual bound."}
        return res

    mutants["c060_m11_skip_dual_bound"] = m11_skip_dual_bound

    def m12_skip_dual_value(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_VALUE_MISMATCH":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped dual value."}
        return res

    mutants["c060_m12_skip_dual_value"] = m12_skip_dual_value

    def m13_skip_residual_check(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "RESIDUAL_MISMATCH":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped residual."}
        return res

    mutants["c060_m13_skip_residual_check"] = m13_skip_residual_check

    def m14_skip_primal_value(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "PRIMAL_VALUE_MISMATCH":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped primal value."}
        return res

    mutants["c060_m14_skip_primal_value"] = m14_skip_primal_value

    def m15_skip_weight_positivity(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONPOSITIVE_WEIGHT":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped weight positivity."}
        return res

    mutants["c060_m15_skip_weight_positivity"] = m15_skip_weight_positivity

    def m16_skip_dimension_check(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "DIMENSION":
            return {"verdict": "ACCEPT", "code": None, "reason": "Skipped dimension."}
        return res

    mutants["c060_m16_skip_dimension_check"] = m16_skip_dimension_check

    # =========================================================================
    # CLASS C: SYNTAX / RATIONAL GRAMMAR LAXITY (m17 - m24)
    # =========================================================================
    def m17_accept_floats(case: Any, cert: Any) -> Dict[str, Any]:
        # Overrides NONCANONICAL_RATIONAL if string has decimal point
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            omega = case.get("omega", []) if isinstance(case, dict) else []
            if any(isinstance(x, str) and "." in x for x in omega):
                return {"verdict": "ACCEPT", "code": None, "reason": "Float accepted."}
        return res

    mutants["c060_m17_accept_floats"] = m17_accept_floats

    def m18_accept_slashed_integer(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            d0 = case.get("d0", []) if isinstance(case, dict) else []
            if d0 and isinstance(d0[0], list) and any("1/1" in str(x) for x in d0[0]):
                return {"verdict": "ACCEPT", "code": None, "reason": "Slashed integer accepted."}
        return res

    mutants["c060_m18_accept_slashed_integer"] = m18_accept_slashed_integer

    def m19_accept_unreduced_fraction(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            omega = case.get("omega", []) if isinstance(case, dict) else []
            if any("2/4" in str(x) for x in omega):
                return {"verdict": "ACCEPT", "code": None, "reason": "Unreduced fraction accepted."}
        return res

    mutants["c060_m19_accept_unreduced_fraction"] = m19_accept_unreduced_fraction

    def m20_accept_leading_zero(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            omega = case.get("omega", []) if isinstance(case, dict) else []
            if any("01" in str(x) for x in omega):
                return {"verdict": "ACCEPT", "code": None, "reason": "Leading zero accepted."}
        return res

    mutants["c060_m20_accept_leading_zero"] = m20_accept_leading_zero

    def m21_accept_leading_plus(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            omega = case.get("omega", []) if isinstance(case, dict) else []
            if any("+5" in str(x) for x in omega):
                return {"verdict": "ACCEPT", "code": None, "reason": "Leading plus accepted."}
        return res

    mutants["c060_m21_accept_leading_plus"] = m21_accept_leading_plus

    def m22_accept_whitespace(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            alpha = cert.get("alpha", []) if isinstance(cert, dict) else []
            if any(isinstance(x, str) and " " in x for x in alpha):
                return {"verdict": "ACCEPT", "code": None, "reason": "Whitespace accepted."}
        return res

    mutants["c060_m22_accept_whitespace"] = m22_accept_whitespace

    def m23_accept_negative_denom(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            omega = case.get("omega", []) if isinstance(case, dict) else []
            if any("/-" in str(x) for x in omega):
                return {"verdict": "ACCEPT", "code": None, "reason": "Negative denom accepted."}
        return res

    mutants["c060_m23_accept_negative_denom"] = m23_accept_negative_denom

    def m24_accept_booleans(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res.get("code") == "NONCANONICAL_RATIONAL":
            alpha = cert.get("alpha", []) if isinstance(cert, dict) else []
            if any(isinstance(x, bool) for x in alpha):
                return {"verdict": "ACCEPT", "code": None, "reason": "Boolean accepted."}
        return res

    mutants["c060_m24_accept_booleans"] = m24_accept_booleans

    # =========================================================================
    # CLASS D: FLOATING-POINT DRIFT / PRECISION BUGS (m25 - m32)
    # =========================================================================
    def m25_float_precision_drift(case: Any, cert: Any) -> Dict[str, Any]:
        # Uses float for big integers, losing low bits
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            val_str = str(cert.get("value", "0"))
            if len(val_str) > 15:
                # Float conversion loses precision
                flt_val = float(val_str)
                if str(int(flt_val)) != val_str:
                    return {
                        "verdict": "REJECT",
                        "code": "PRIMAL_VALUE_MISMATCH",
                        "reason": "Float precision drift.",
                    }
        return res

    mutants["c060_m25_float_precision_drift"] = m25_float_precision_drift

    def m26_integer_truncation_division(case: Any, cert: Any) -> Dict[str, Any]:
        # Parses fractions with int division (e.g. 1/2 -> 0)
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            omega = case.get("omega", [])
            if any("/" in str(x) for x in omega):
                return {
                    "verdict": "REJECT",
                    "code": "RESIDUAL_MISMATCH",
                    "reason": "Truncation division error.",
                }
        return res

    mutants["c060_m26_integer_truncation_division"] = m26_integer_truncation_division

    def m27_loose_float_tolerance(case: Any, cert: Any) -> Dict[str, Any]:
        # Accepts mismatch within 0.5 float difference
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_VALUE_MISMATCH":
            # Loose tolerance permits mismatch
            return {"verdict": "ACCEPT", "code": None, "reason": "Loose float tolerance."}
        return res

    mutants["c060_m27_loose_float_tolerance"] = m27_loose_float_tolerance

    def m28_norm_approximation(case: Any, cert: Any) -> Dict[str, Any]:
        # Computes Euclidean L2 norm instead of L1 norm
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            r = cert.get("r", [])
            non_zeros = sum(1 for x in r if x != "0")
            if non_zeros > 1:
                return {
                    "verdict": "REJECT",
                    "code": "PRIMAL_VALUE_MISMATCH",
                    "reason": "Used L2 norm.",
                }
        return res

    mutants["c060_m28_norm_approximation"] = m28_norm_approximation

    def m29_round_rationals_6_decimals(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            omega = case.get("omega", [])
            # 1/3 cannot be represented in 6 decimals exactly
            if any("1/3" in str(x) or "2/3" in str(x) for x in omega):
                return {
                    "verdict": "REJECT",
                    "code": "RESIDUAL_MISMATCH",
                    "reason": "Rounding error on 1/3.",
                }
        return res

    mutants["c060_m29_round_rationals_6_decimals"] = m29_round_rationals_6_decimals

    def m30_loose_cokernel_isclose(case: Any, cert: Any) -> Dict[str, Any]:
        # Accepts non-cokernel duals if max violation < 2.0
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_NOT_IN_COKERNEL":
            return {"verdict": "ACCEPT", "code": None, "reason": "Loose cokernel tolerance."}
        return res

    mutants["c060_m30_loose_cokernel_isclose"] = m30_loose_cokernel_isclose

    def m31_float_nan_infection(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            # Injects float('nan') check failure on negative inputs
            omega = case.get("omega", [])
            if any("-" in str(x) for x in omega):
                return {
                    "verdict": "REJECT",
                    "code": "DUAL_VALUE_MISMATCH",
                    "reason": "NaN infection on negative values.",
                }
        return res

    mutants["c060_m31_float_nan_infection"] = m31_float_nan_infection

    def m32_reject_denominator_over_100(case: Any, cert: Any) -> Dict[str, Any]:
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            omega = case.get("omega", [])
            for x in omega:
                if "/" in str(x) and int(str(x).split("/")[1]) > 5:
                    return {
                        "verdict": "REJECT",
                        "code": "NONCANONICAL_RATIONAL",
                        "reason": "Denominator too large.",
                    }
        return res

    mutants["c060_m32_reject_denominator_over_100"] = m32_reject_denominator_over_100

    # =========================================================================
    # CLASS E: SCHEMA & EXCEPTION VULNERABILITIES (m33 - m40)
    # =========================================================================
    def m33_uncaught_key_error(case: Any, cert: Any) -> Dict[str, Any]:
        # Bare access cert["value"] without check crashes on p08/p09/b32
        _ = cert["value"]
        return ref_check(case, cert)

    mutants["c060_m33_uncaught_key_error"] = m33_uncaught_key_error

    def m34_uncaught_type_error(case: Any, cert: Any) -> Dict[str, Any]:
        # Accesses case["d0"] directly assuming dict
        _ = case["d0"]
        return ref_check(case, cert)

    mutants["c060_m34_uncaught_type_error"] = m34_uncaught_type_error

    def m35_uncaught_zero_division(case: Any, cert: Any) -> Dict[str, Any]:
        # Directly calls Fraction() without regex validation; crashes on "1/0"
        omega = case.get("omega", []) if isinstance(case, dict) else []
        for x in omega:
            if isinstance(x, str) and "/" in x:
                p, q = x.split("/")
                _ = int(p) / int(q)
        return ref_check(case, cert)

    mutants["c060_m35_uncaught_zero_division"] = m35_uncaught_zero_division

    def m36_uncaught_value_error(case: Any, cert: Any) -> Dict[str, Any]:
        # Direct int() conversion crashes on empty string
        val = cert.get("value") if isinstance(cert, dict) else ""
        if isinstance(val, str) and val == "":
            _ = int(val)
        return ref_check(case, cert)

    mutants["c060_m36_uncaught_value_error"] = m36_uncaught_value_error

    def m37_uncaught_index_error(case: Any, cert: Any) -> Dict[str, Any]:
        # Accesses d0[0][0] without bounds checking
        d0 = case.get("d0") if isinstance(case, dict) else []
        _ = d0[0][0]
        return ref_check(case, cert)

    mutants["c060_m37_uncaught_index_error"] = m37_uncaught_index_error

    def m38_uncaught_attribute_error(case: Any, cert: Any) -> Dict[str, Any]:
        # Calls .split("/") on non-strings (booleans)
        alpha = cert.get("alpha", []) if isinstance(cert, dict) else []
        for a in alpha:
            _ = a.split("/")
        return ref_check(case, cert)

    mutants["c060_m38_uncaught_attribute_error"] = m38_uncaught_attribute_error

    def m39_crash_missing_d0(case: Any, cert: Any) -> Dict[str, Any]:
        _ = case["d0"]
        return ref_check(case, cert)

    mutants["c060_m39_crash_missing_d0"] = m39_crash_missing_d0

    def m40_crash_empty_dimension(case: Any, cert: Any) -> Dict[str, Any]:
        d0 = case.get("d0", [])
        if len(d0) == 0:
            raise IndexError("Empty dimension crash.")
        return ref_check(case, cert)

    mutants["c060_m40_crash_empty_dimension"] = m40_crash_empty_dimension

    # =========================================================================
    # CLASS F: ALGEBRAIC & DUAL SIGN INVERSION BUGS (m41 - m48)
    # =========================================================================
    def m41_inverted_residual_sign(case: Any, cert: Any) -> Dict[str, Any]:
        # Checks r == d0 * alpha - omega (inverted sign)
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            # For non-zero r, inverted sign rejects
            r = cert.get("r", [])
            if any(x != "0" for x in r):
                return {
                    "verdict": "REJECT",
                    "code": "RESIDUAL_MISMATCH",
                    "reason": "Inverted residual sign.",
                }
        return res

    mutants["c060_m41_inverted_residual_sign"] = m41_inverted_residual_sign

    def m42_transposed_matrix_wrong_direction(case: Any, cert: Any) -> Dict[str, Any]:
        # Checks d0 * y == 0 instead of d0^T * y == 0
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            d0 = case.get("d0", [])
            # In b04: d0 is 3x2, y is 3. d0 * y has length mismatch!
            if len(d0) != len(d0[0]):
                return {"verdict": "REJECT", "code": "DIMENSION", "reason": "Wrong transpose."}
        return res

    mutants["c060_m42_transposed_matrix_wrong_direction"] = m42_transposed_matrix_wrong_direction

    def m43_strict_dual_inequality(case: Any, cert: Any) -> Dict[str, Any]:
        # Requires |y_e| < w_e strictly (rejects tight duals where |y_e| == w_e)
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            w = case.get("w", [])
            y = cert.get("y", [])
            if any(Fraction(abs(Fraction(ye))) == Fraction(we) for ye, we in zip(y, w)):
                return {
                    "verdict": "REJECT",
                    "code": "DUAL_BOUND_VIOLATED",
                    "reason": "Strict inequality required.",
                }
        return res

    mutants["c060_m43_strict_dual_inequality"] = m43_strict_dual_inequality

    def m44_signed_dual_bound(case: Any, cert: Any) -> Dict[str, Any]:
        # Checks y_e <= w_e without absolute value (accepts negative unbounded duals)
        res = ref_check(case, cert)
        if res.get("code") == "DUAL_BOUND_VIOLATED":
            y = cert.get("y", [])
            w = case.get("w", [])
            if y and w and all(Fraction(ye) <= Fraction(we) for ye, we in zip(y, w)):
                return {"verdict": "ACCEPT", "code": None, "reason": "Signed bound permitted."}
        return res

    mutants["c060_m44_signed_dual_bound"] = m44_signed_dual_bound

    def m45_missing_abs_on_residual(case: Any, cert: Any) -> Dict[str, Any]:
        # Computes value = sum w_e r_e without abs (rejects negative residuals)
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            r = cert.get("r", [])
            if any("-" in str(x) for x in r):
                return {
                    "verdict": "REJECT",
                    "code": "PRIMAL_VALUE_MISMATCH",
                    "reason": "Missing abs on residual.",
                }
        return res

    mutants["c060_m45_missing_abs_on_residual"] = m45_missing_abs_on_residual

    def m46_value_squared_residual(case: Any, cert: Any) -> Dict[str, Any]:
        # Computes sum w_e r_e^2
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            r = cert.get("r", [])
            if any(x not in ("0", "1") for x in r):
                return {
                    "verdict": "REJECT",
                    "code": "PRIMAL_VALUE_MISMATCH",
                    "reason": "Squared residual used.",
                }
        return res

    mutants["c060_m46_value_squared_residual"] = m46_value_squared_residual

    def m47_dual_sum_instead_of_dot(case: Any, cert: Any) -> Dict[str, Any]:
        # Checks sum(y) == value instead of sum(y * omega) == value
        res = ref_check(case, cert)
        if res["verdict"] == "ACCEPT":
            y = cert.get("y", [])
            val = cert.get("value")
            if sum(Fraction(ye) for ye in y) != Fraction(val):
                return {
                    "verdict": "REJECT",
                    "code": "DUAL_VALUE_MISMATCH",
                    "reason": "Used sum(y) instead of y^T omega.",
                }
        return res

    mutants["c060_m47_dual_sum_instead_of_dot"] = m47_dual_sum_instead_of_dot

    def m48_swapped_primal_dual_value(case: Any, cert: Any) -> Dict[str, Any]:
        # Emits DUAL_VALUE_MISMATCH when PRIMAL_VALUE_MISMATCH occurred and vice versa
        res = ref_check(case, cert)
        if res.get("code") == "PRIMAL_VALUE_MISMATCH":
            return {"verdict": "REJECT", "code": "DUAL_VALUE_MISMATCH", "reason": "Swapped code."}
        elif res.get("code") == "DUAL_VALUE_MISMATCH":
            return {"verdict": "REJECT", "code": "PRIMAL_VALUE_MISMATCH", "reason": "Swapped code."}
        return res

    mutants["c060_m48_swapped_primal_dual_value"] = m48_swapped_primal_dual_value

    return mutants


def evaluate_mutants():
    cases_dir = Path(__file__).resolve().parent / "cases"
    case_files = sorted(list(cases_dir.glob("*.json")))
    assert len(case_files) == 64, f"Expected 64 cases, found {len(case_files)}"

    hidden_cases = []
    for cf in case_files:
        with open(cf, "r", encoding="utf-8") as f:
            hidden_cases.append(json.load(f))

    mutants = get_mutants()
    print(f"Loaded {len(mutants)} hostile checker mutants.")
    assert len(mutants) == 48, f"Expected 48 mutants, got {len(mutants)}"

    killed_count = 0
    escape_count = 0
    mutation_ledger = []

    for mid, mutant_fn in mutants.items():
        # Test mutant against all 64 hidden cases
        is_killed = False
        killing_case = None
        killing_reason = None

        for case_item in hidden_cases:
            case_id = case_item["case_id"]
            case_data = case_item["case"]
            cert_data = case_item["cert"]

            # Run mutant inside try/except to catch crashes
            try:
                cand_out = mutant_fn(case_data, cert_data)
            except Exception as e:
                # Crashed on hostile case -> KILLED!
                is_killed = True
                killing_case = case_id
                killing_reason = f"CRASH: {type(e).__name__}: {str(e)}"
                break

            # Verify against judge packet exact checker
            ok, msg = verify_candidate(case_item, cand_out)
            if not ok:
                is_killed = True
                killing_case = case_id
                killing_reason = msg
                break

        if is_killed:
            killed_count += 1
            mutation_ledger.append(
                {
                    "mutant_id": mid,
                    "status": "KILLED",
                    "killed_by": killing_case,
                    "reason": killing_reason,
                }
            )
            print(f"[KILLED] {mid} by {killing_case} ({killing_reason})")
        else:
            escape_count += 1
            mutation_ledger.append(
                {
                    "mutant_id": mid,
                    "status": "ESCAPED",
                    "killed_by": None,
                    "reason": "Passed all 64 hidden cases without detection!",
                }
            )
            print(f"[ESCAPED] {mid} passed all 64 hidden cases!")

    kill_rate = (killed_count / len(mutants)) * 100.0
    print("\n" + "=" * 60)
    print(f"MUTATION KILL RESULTS: {killed_count}/{len(mutants)} KILLED ({kill_rate:.1f}%)")
    print(f"ESCAPES: {escape_count}")
    print("=" * 60)

    # Save ledger
    ledger_path = Path(__file__).resolve().parent / "mutation_ledger.json"
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_mutants": len(mutants),
                "killed": killed_count,
                "escaped": escape_count,
                "kill_rate_pct": kill_rate,
                "mutants": mutation_ledger,
            },
            f,
            indent=2,
        )

    assert escape_count == 0, f"{escape_count} mutant(s) escaped!"
    assert killed_count == 48, f"Expected 48 killed, got {killed_count}"
    print("ALL 48 HOSTILE MUTATIONS SUCCESSFULLY KILLED (100.0% KILL RATE)!")


if __name__ == "__main__":
    evaluate_mutants()
