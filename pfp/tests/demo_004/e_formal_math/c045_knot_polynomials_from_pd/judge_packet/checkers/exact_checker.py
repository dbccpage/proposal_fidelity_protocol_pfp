# AuthorityEffect: None.
"""
Exact Checker for C045 (Knot Polynomials from Planar Diagrams).
Validates solver output against algebraic specifications, catalog signatures,
and recomputable topological invariants.
"""

from typing import Any, Dict, Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.reference_solver.knots_catalog import (
    CANONICAL_KNOTS,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.reference_solver.pd_validator import (
    validate_and_parse_pd,
)


def check_exact(case: Dict[str, Any], ans: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(ans, dict):
        return False, "Answer is not a dictionary"

    if ans.get("case_id") != case.get("case_id"):
        return False, f"case_id mismatch: expected {case.get('case_id')}, got {ans.get('case_id')}"

    status = ans.get("status")
    if status not in {"SOLVED", "REFUSED"}:
        return False, f"Invalid status: {status}"

    task = case.get("task", "COMPUTE_POLYNOMIALS")

    if status == "REFUSED":
        if "reason" not in ans:
            return False, "Missing refusal reason"
        return True, f"Valid refusal with reason: {ans['reason']}"

    # Status is SOLVED
    if task == "COMPUTE_POLYNOMIALS":
        for field in [
            "writhe",
            "kauffman_bracket",
            "jones_polynomial",
            "alexander_polynomial",
            "identified_knot",
        ]:
            if field not in ans:
                return False, f"Missing field in COMPUTE_POLYNOMIALS: {field}"

        # Recompute expected writhe
        pd = case.get("pd", [])
        if len(pd) == 0:
            exp_w = 0
        else:
            ok, v_res = validate_and_parse_pd(pd)
            if not ok:
                return False, f"Input PD is invalid but solver returned SOLVED: {v_res}"
            exp_w = v_res["writhe"]

        if ans["writhe"] != exp_w:
            return False, f"Writhe mismatch: expected {exp_w}, got {ans['writhe']}"

        # Verify Laurent poly format: dict of {power_str: int}
        for p_name in ["kauffman_bracket", "jones_polynomial", "alexander_polynomial"]:
            poly = ans[p_name]
            if not isinstance(poly, dict):
                return False, f"{p_name} is not a dict"
            for k, v in poly.items():
                try:
                    int(k)
                    int(v)
                except (ValueError, TypeError):
                    return False, f"Invalid power/coeff in {p_name}: ({k}, {v})"

        # Check normalization at t=1: Jones(1) = 1 and Alexander(1) = 1
        j_1 = sum(ans["jones_polynomial"].values())
        a_1 = sum(ans["alexander_polynomial"].values())
        if j_1 != 1:
            return False, f"Jones polynomial evaluated at t=1 is {j_1}, expected 1"
        if a_1 != 1:
            return False, f"Alexander polynomial evaluated at t=1 is {a_1}, expected 1"

        kid = ans["identified_knot"]
        if kid not in CANONICAL_KNOTS:
            return False, f"Identified knot '{kid}' is not in canonical catalog"

        return True, f"Knot {kid} (writhe {ans['writhe']}) polynomials verified"

    elif task == "IDENTIFY":
        if "identified_knot" not in ans or "chirality" not in ans or "invariants" not in ans:
            return False, "Missing identification fields"

        kid = ans["identified_knot"]
        if kid not in CANONICAL_KNOTS:
            return False, f"Identified knot '{kid}' not in canonical catalog"

        cat_entry = CANONICAL_KNOTS[kid]
        chir = ans["chirality"]
        if cat_entry["chirality"] == "ACHIRAL" and chir != "ACHIRAL":
            return False, f"Knot {kid} is achiral, but answer claimed {chir}"
        elif cat_entry["chirality"] == "CHIRAL" and chir not in {"RIGHT_HANDED", "LEFT_HANDED"}:
            return False, f"Knot {kid} is chiral, but answer claimed {chir}"

        # Validate writhe against expected presentation
        invs = ans["invariants"]
        if "writhe" in invs:
            pd = case.get("pd", [])
            exp_w = 0 if len(pd) == 0 else validate_and_parse_pd(pd)[1]["writhe"]
            if invs["writhe"] != exp_w:
                return (
                    False,
                    f"Writhe mismatch in invariants: expected {exp_w}, got {invs['writhe']}",
                )

            # Check chirality matches writhe sign for chiral knots
            if cat_entry["chirality"] == "CHIRAL":
                if cat_entry["writhe"] > 0:
                    exp_chir = "RIGHT_HANDED" if exp_w > 0 else "LEFT_HANDED"
                else:
                    exp_chir = "RIGHT_HANDED" if exp_w < 0 else "LEFT_HANDED"
                if chir != exp_chir:
                    return False, f"Chirality mismatch: expected {exp_chir}, got {chir}"

        return True, f"Identified knot as {kid} ({chir})"

    elif task == "COMPARE":
        kind = ans.get("kind")
        if kind not in {"SAME_INVARIANTS", "DIFFERENT_INVARIANTS"}:
            return False, f"Invalid compare kind: {kind}"

        # Import reference solver to cross-verify truth on compare
        from omega_engine_pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.reference_solver.solver import (
            solve as ref_solve,
        )

        c1 = {"case_id": "c1", "task": "COMPUTE_POLYNOMIALS", "pd": case["pd_1"]}
        c2 = {"case_id": "c2", "task": "COMPUTE_POLYNOMIALS", "pd": case["pd_2"]}
        r1 = ref_solve(c1)
        r2 = ref_solve(c2)

        true_same = r1.get("jones_polynomial") == r2.get("jones_polynomial") and r1.get(
            "alexander_polynomial"
        ) == r2.get("alexander_polynomial")

        if true_same and kind != "SAME_INVARIANTS":
            return False, f"Knots have same invariants, but answer claimed {kind}"
        if not true_same and kind != "DIFFERENT_INVARIANTS":
            return False, f"Knots have different invariants, but answer claimed {kind}"

        if kind == "DIFFERENT_INVARIANTS":
            if "separating_invariant" not in ans or "val_1" not in ans or "val_2" not in ans:
                return False, "Missing separating invariant fields"
            if ans["val_1"] == ans["val_2"]:
                return False, "Separating invariant values are identical"
        return True, f"Compare completed with kind {kind}"

    return False, f"Unknown task: {task}"
