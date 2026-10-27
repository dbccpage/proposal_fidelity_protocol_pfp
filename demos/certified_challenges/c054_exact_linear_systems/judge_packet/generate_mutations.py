"""
Generate 48 hostile mutations for Challenge C054 Judge Packet.
Verifies that all corruptions, boundary errors, float leakages, unreduced fractions,
and mathematical violations are detected and killed by both checkers.
"""

from pathlib import Path
import sys
import copy
import json
import os

for _parent in Path(__file__).resolve().parents:
    if (_parent / "sqlite_pilot_store.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from c054_exact_linear_systems.judge_packet.exact_checker import (
    check_exact,
)
from c054_exact_linear_systems.judge_packet.independent_checker import (
    independent_check,
)
from c054_exact_linear_systems.reference_solver.linear_solver import (
    solve_linear_system,
)


def main():
    mut_dir = os.path.join(os.path.dirname(__file__), "hostile_mutations")
    os.makedirs(mut_dir, exist_ok=True)

    # Base cases for mutating
    case_c2 = {"case_id": "c054_b03_2x2_full_rank", "A": [["1", "2"], ["3", "4"]], "b": ["5", "11"]}
    sol_c2 = solve_linear_system(case_c2)

    case_inc2 = {
        "case_id": "c054_b05_2x2_singular_inconsistent",
        "A": [["2", "4"], ["3", "6"]],
        "b": ["6", "10"],
    }
    sol_inc2 = solve_linear_system(case_inc2)

    case_sing_c = {
        "case_id": "c054_b04_2x2_singular_consistent",
        "A": [["2", "4"], ["3", "6"]],
        "b": ["6", "9"],
    }
    sol_sing_c = solve_linear_system(case_sing_c)

    case_wide = {
        "case_id": "c054_b11_wide_2x4_consistent",
        "A": [["1", "0", "2", "1"], ["0", "1", "-1", "3"]],
        "b": ["5", "2"],
    }
    sol_wide = solve_linear_system(case_wide)

    mutations = []

    def add_mut(mid, c, r, desc):
        mutations.append({"mutation_id": mid, "description": desc, "case": c, "mutated_result": r})

    # 1. x off by 1
    m1 = copy.deepcopy(sol_c2)
    m1["x"][0] = str(int(m1["x"][0]) + 1)
    add_mut("mut_01_x_off_by_one", case_c2, m1, "Solution x modified by +1")

    # 2. x off by 1/1000000
    m2 = copy.deepcopy(sol_c2)
    m2["x"][0] = "1000001/1000000"
    add_mut("mut_02_x_off_by_micro_fraction", case_c2, m2, "Solution x modified by tiny fraction")

    # 3. y has y^T b == 0
    m3 = copy.deepcopy(sol_inc2)
    m3["y"] = ["0", "0"]
    add_mut("mut_03_y_orthogonal_to_b", case_inc2, m3, "Inconsistency witness y has y^T b = 0")

    # 4. y has y^T A != 0
    m4 = copy.deepcopy(sol_inc2)
    m4["y"][0] = "99"
    add_mut("mut_04_y_not_in_left_kernel", case_inc2, m4, "Inconsistency witness y fails y^T A = 0")

    # 5. Claimed consistent on inconsistent system
    m5 = {
        "case_id": case_inc2["case_id"],
        "status": "SOLVED",
        "kind": "CONSISTENT",
        "x": ["1", "1"],
        "null_basis": [],
        "rank": 2,
        "rank_rows": [0, 1],
        "rank_cols": [0, 1],
        "null_rows": [],
    }
    add_mut(
        "mut_05_claimed_consistent_on_inconsistent",
        case_inc2,
        m5,
        "Inconsistent system claimed consistent",
    )

    # 6. Claimed inconsistent on consistent system
    m6 = {
        "case_id": case_c2["case_id"],
        "status": "SOLVED",
        "kind": "INCONSISTENT",
        "y": ["1", "1"],
    }
    add_mut(
        "mut_06_claimed_inconsistent_on_consistent",
        case_c2,
        m6,
        "Consistent system claimed inconsistent",
    )

    # 7. Rank overstated
    m7 = copy.deepcopy(sol_sing_c)
    m7["rank"] = 2
    m7["rank_rows"] = [0, 1]
    m7["rank_cols"] = [0, 1]
    m7["null_basis"] = []
    m7["null_rows"] = []
    add_mut("mut_07_rank_overstated", case_sing_c, m7, "Singular system rank overstated to 2")

    # 8. Rank understated
    m8 = copy.deepcopy(sol_c2)
    m8["rank"] = 1
    m8["rank_rows"] = [0]
    m8["rank_cols"] = [0]
    m8["null_basis"] = [["1", "0"]]
    m8["null_rows"] = [0]
    add_mut("mut_08_rank_understated", case_c2, m8, "Full rank system rank understated to 1")

    # 9. Rank minor singular (det = 0)
    m9 = copy.deepcopy(sol_sing_c)
    m9["rank_rows"] = [0, 1]
    m9["rank_cols"] = [0, 1]
    m9["rank"] = 2
    add_mut("mut_09_rank_minor_singular", case_sing_c, m9, "Rank minor has det = 0")

    # 10. rank_rows out of bounds
    m10 = copy.deepcopy(sol_c2)
    m10["rank_rows"] = [0, 99]
    add_mut("mut_10_rank_rows_out_of_bounds", case_c2, m10, "rank_rows index 99 out of bounds")

    # 11. rank_cols out of bounds
    m11 = copy.deepcopy(sol_c2)
    m11["rank_cols"] = [0, 99]
    add_mut("mut_11_rank_cols_out_of_bounds", case_c2, m11, "rank_cols index 99 out of bounds")

    # 12. rank_rows duplicate
    m12 = copy.deepcopy(sol_c2)
    m12["rank_rows"] = [0, 0]
    add_mut("mut_12_rank_rows_duplicate", case_c2, m12, "rank_rows contains duplicates")

    # 13. rank_cols duplicate
    m13 = copy.deepcopy(sol_c2)
    m13["rank_cols"] = [0, 0]
    add_mut("mut_13_rank_cols_duplicate", case_c2, m13, "rank_cols contains duplicates")

    # 14. Null basis vector not in kernel
    m14 = copy.deepcopy(sol_sing_c)
    m14["null_basis"][0][0] = "99"
    add_mut("mut_14_null_vector_not_in_kernel", case_sing_c, m14, "Null vector fails A v = 0")

    # 15. Null basis linearly dependent
    m15 = copy.deepcopy(sol_wide)
    # sol_wide has 2 null vectors, set second equal to first
    m15["null_basis"][1] = list(m15["null_basis"][0])
    add_mut("mut_15_null_basis_linearly_dependent", case_wide, m15, "Null basis vectors duplicated")

    # 16. Null rows singular minor
    m16 = copy.deepcopy(sol_wide)
    # Choose null_rows where null vectors both have 0
    m16["null_rows"] = [0, 1]
    # In sol_wide: pivot cols are 0, 1, so row 0, 1 might have det 0
    # Let's ensure det of minor is 0 by duplicating row
    m16["null_rows"] = [0, 0]
    add_mut("mut_16_null_rows_duplicate", case_wide, m16, "null_rows has duplicate entries")

    # 17. null_rows out of bounds
    m17 = copy.deepcopy(sol_sing_c)
    m17["null_rows"] = [99]
    add_mut("mut_17_null_rows_out_of_bounds", case_sing_c, m17, "null_rows index 99 out of bounds")

    # 18. Dimensional invariant violated: rank + len(null_basis) != n
    m18 = copy.deepcopy(sol_sing_c)
    m18["null_basis"] = []  # len 0, but rank is 1, n is 2 (1 + 0 != 2)
    m18["null_rows"] = []
    add_mut("mut_18_dim_invariant_violated", case_sing_c, m18, "rank + dim(N) != n")

    # 19. Float string in x
    m19 = copy.deepcopy(sol_c2)
    m19["x"][0] = "1.0"
    add_mut("mut_19_float_string_in_x", case_c2, m19, "Float string in x")

    # 20. Float string in y
    m20 = copy.deepcopy(sol_inc2)
    m20["y"][0] = "-1.5"
    add_mut("mut_20_float_string_in_y", case_inc2, m20, "Float string in y")

    # 21. Float string in null_basis
    m21 = copy.deepcopy(sol_sing_c)
    m21["null_basis"][0][0] = "-2.0"
    add_mut("mut_21_float_string_in_null_basis", case_sing_c, m21, "Float string in null_basis")

    # 22. Unreduced fraction in x
    m22 = copy.deepcopy(sol_c2)
    m22["x"][0] = "2/2"
    add_mut("mut_22_unreduced_fraction_in_x", case_c2, m22, "Unreduced fraction 2/2 in x")

    # 23. Unreduced fraction in y
    m23 = copy.deepcopy(sol_inc2)
    m23["y"][0] = "-6/4"
    add_mut("mut_23_unreduced_fraction_in_y", case_inc2, m23, "Unreduced fraction -6/4 in y")

    # 24. Unreduced fraction in null_basis
    m24 = copy.deepcopy(sol_sing_c)
    m24["null_basis"][0][0] = "-4/2"
    add_mut(
        "mut_24_unreduced_fraction_in_null_basis",
        case_sing_c,
        m24,
        "Unreduced fraction -4/2 in null_basis",
    )

    # 25. Boolean in x
    m25 = copy.deepcopy(sol_c2)
    m25["x"][0] = True
    add_mut("mut_25_boolean_in_x", case_c2, m25, "Boolean True in x")

    # 26. Boolean in y
    m26 = copy.deepcopy(sol_inc2)
    m26["y"][0] = False
    add_mut("mut_26_boolean_in_y", case_inc2, m26, "Boolean False in y")

    # 27. Boolean in null_basis
    m27 = copy.deepcopy(sol_sing_c)
    m27["null_basis"][0][0] = True
    add_mut("mut_27_boolean_in_null_basis", case_sing_c, m27, "Boolean True in null_basis")

    # 28. Raw integer in x
    m28 = copy.deepcopy(sol_c2)
    m28["x"][0] = 1
    add_mut("mut_28_raw_int_in_x", case_c2, m28, "Raw integer 1 in x")

    # 29. Raw integer in y
    m29 = copy.deepcopy(sol_inc2)
    m29["y"][0] = -3
    add_mut("mut_29_raw_int_in_y", case_inc2, m29, "Raw integer -3 in y")

    # 30. Raw integer in null_basis
    m30 = copy.deepcopy(sol_sing_c)
    m30["null_basis"][0][0] = -2
    add_mut("mut_30_raw_int_in_null_basis", case_sing_c, m30, "Raw integer -2 in null_basis")

    # 31. x vector too short
    m31 = copy.deepcopy(sol_c2)
    m31["x"] = m31["x"][:1]
    add_mut("mut_31_x_too_short", case_c2, m31, "x vector has length 1 instead of 2")

    # 32. x vector too long
    m32 = copy.deepcopy(sol_c2)
    m32["x"].append("0")
    add_mut("mut_32_x_too_long", case_c2, m32, "x vector has length 3 instead of 2")

    # 33. y vector too short
    m33 = copy.deepcopy(sol_inc2)
    m33["y"] = m33["y"][:1]
    add_mut("mut_33_y_too_short", case_inc2, m33, "y vector has length 1 instead of 2")

    # 34. y vector too long
    m34 = copy.deepcopy(sol_inc2)
    m34["y"].append("0")
    add_mut("mut_34_y_too_long", case_inc2, m34, "y vector has length 3 instead of 2")

    # 35. null vector too short
    m35 = copy.deepcopy(sol_sing_c)
    m35["null_basis"][0] = m35["null_basis"][0][:1]
    add_mut("mut_35_null_vector_too_short", case_sing_c, m35, "Null vector length 1 instead of 2")

    # 36. null vector too long
    m36 = copy.deepcopy(sol_sing_c)
    m36["null_basis"][0].append("0")
    add_mut("mut_36_null_vector_too_long", case_sing_c, m36, "Null vector length 3 instead of 2")

    # 37. Missing null_basis field
    m37 = copy.deepcopy(sol_sing_c)
    del m37["null_basis"]
    add_mut("mut_37_missing_null_basis_field", case_sing_c, m37, "Missing null_basis key")

    # 38. Missing rank field
    m38 = copy.deepcopy(sol_sing_c)
    del m38["rank"]
    add_mut("mut_38_missing_rank_field", case_sing_c, m38, "Missing rank key")

    # 39. Missing rank_rows field
    m39 = copy.deepcopy(sol_sing_c)
    del m39["rank_rows"]
    add_mut("mut_39_missing_rank_rows_field", case_sing_c, m39, "Missing rank_rows key")

    # 40. Missing rank_cols field
    m40 = copy.deepcopy(sol_sing_c)
    del m40["rank_cols"]
    add_mut("mut_40_missing_rank_cols_field", case_sing_c, m40, "Missing rank_cols key")

    # 41. Missing null_rows field
    m41 = copy.deepcopy(sol_sing_c)
    del m41["null_rows"]
    add_mut("mut_41_missing_null_rows_field", case_sing_c, m41, "Missing null_rows key")

    # 42. Missing x field
    m42 = copy.deepcopy(sol_c2)
    del m42["x"]
    add_mut("mut_42_missing_x_field", case_c2, m42, "Missing x key")

    # 43. Missing y field
    m43 = copy.deepcopy(sol_inc2)
    del m43["y"]
    add_mut("mut_43_missing_y_field", case_inc2, m43, "Missing y key")

    # 44. False OUT_OF_SCOPE on valid case
    m44 = {
        "case_id": case_c2["case_id"],
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "SPOOFED_OOS"},
    }
    add_mut("mut_44_false_oos_on_valid_case", case_c2, m44, "Claimed OUT_OF_SCOPE on valid case")

    # 45. Spoofed SOLVED on ragged matrix
    case_ragged = {
        "case_id": "c054_p05_ragged_row",
        "A": [["1", "2", "3"], ["4", "5"]],
        "b": ["1", "2"],
    }
    m45 = {
        "case_id": case_ragged["case_id"],
        "status": "SOLVED",
        "kind": "CONSISTENT",
        "x": ["1", "0", "0"],
        "null_basis": [],
        "rank": 2,
        "rank_rows": [0, 1],
        "rank_cols": [0, 1],
        "null_rows": [],
    }
    add_mut("mut_45_spoofed_solved_on_ragged", case_ragged, m45, "Spoofed SOLVED on ragged matrix")

    # 46. Unknown kind
    m46 = copy.deepcopy(sol_c2)
    m46["kind"] = "MAYBE_CONSISTENT"
    add_mut("mut_46_unknown_kind", case_c2, m46, "kind set to MAYBE_CONSISTENT")

    # 47. Case ID mismatch
    m47 = copy.deepcopy(sol_c2)
    m47["case_id"] = "wrong_case_id"
    add_mut("mut_47_case_id_mismatch", case_c2, m47, "case_id mismatch")

    # 48. Missing status field
    m48 = copy.deepcopy(sol_c2)
    del m48["status"]
    add_mut("mut_48_missing_status_field", case_c2, m48, "Missing status key")

    assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

    # Verify every mutation is killed by both checkers
    survived = 0
    for mut in mutations:
        mid = mut["mutation_id"]
        c = mut["case"]
        r = mut["mutated_result"]
        ok1, msg1 = check_exact(c, r)
        ok2, msg2 = independent_check(c, r)
        if ok1 or ok2:
            print(f"SURVIVED: {mid} (exact={ok1}, indep={ok2})")
            survived += 1
        path = os.path.join(mut_dir, f"{mid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mut, f, indent=2)

    if survived == 0:
        print("ALL 48 HOSTILE MUTATIONS SUCCESSFULLY KILLED BY BOTH CHECKERS!")
    else:
        raise RuntimeError(f"{survived} mutations survived!")


if __name__ == "__main__":
    main()
