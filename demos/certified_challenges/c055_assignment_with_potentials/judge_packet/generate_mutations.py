"""
Generate 48 hostile mutations for Challenge C055 Judge Packet.
Verifies that all corruptions, dual inequality violations, fake Hall sets,
float leakages, and contract breaches are rejected by both checkers.
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

from c055_assignment_with_potentials.judge_packet.exact_checker import (
    check_exact,
)
from c055_assignment_with_potentials.judge_packet.independent_checker import (
    independent_check,
)
from c055_assignment_with_potentials.reference_solver.hungarian import (
    solve_assignment,
)


def main():
    mut_dir = os.path.join(os.path.dirname(__file__), "hostile_mutations")
    os.makedirs(mut_dir, exist_ok=True)

    # Base cases for mutating
    case_3x3 = {
        "case_id": "c055_b03_3x3_textbook",
        "sense": "min",
        "cost": [["4", "1", "3"], ["2", "0", "5"], ["3", "2", "2"]],
    }
    sol_3x3 = solve_assignment(case_3x3)

    case_hall = {
        "case_id": "c055_b04_hall_violator_2_share_1",
        "sense": "min",
        "cost": [["1", None, None], ["2", None, None], ["1", "3", "5"]],
    }
    sol_hall = solve_assignment(case_hall)

    case_max = {
        "case_id": "c055_b11_maximization_3x3",
        "sense": "max",
        "cost": [["4", "1", "3"], ["2", "0", "5"], ["3", "2", "2"]],
    }
    sol_max = solve_assignment(case_max)

    case_sparse = {
        "case_id": "c055_b13_sparse_allowed_feasible",
        "sense": "min",
        "cost": [
            ["1", None, "4", None],
            [None, "2", None, "5"],
            [None, "3", "2", None],
            ["6", None, None, "1"],
        ],
    }
    sol_sparse = solve_assignment(case_sparse)

    mutations = []

    def add_mut(mid, c, r, desc):
        mutations.append({"mutation_id": mid, "description": desc, "case": c, "mutated_result": r})

    # 1. u[0] increased by 1 (violates u_i + v_j <= c_ij)
    m1 = copy.deepcopy(sol_3x3)
    m1["u"][0] = str(int(m1["u"][0]) + 1)
    add_mut("mut_01_potential_u_increased", case_3x3, m1, "u[0] increased breaking dual inequality")

    # 2. v[0] increased by 1
    m2 = copy.deepcopy(sol_3x3)
    m2["v"][0] = str(int(m2["v"][0]) + 1)
    add_mut("mut_02_potential_v_increased", case_3x3, m2, "v[0] increased breaking dual inequality")

    # 3. Sum mismatch: sum(u) + sum(v) != value
    m3 = copy.deepcopy(sol_3x3)
    m3["u"][0] = str(
        int(m3["u"][0]) - 1
    )  # sum decreased by 1, but inequalities still hold, sum != value
    add_mut("mut_03_sum_mismatch", case_3x3, m3, "sum(u) + sum(v) != value")

    # 4. sigma uses forbidden entry
    m4 = copy.deepcopy(sol_sparse)
    m4["sigma"] = [1, 1, 2, 3]  # (0, 1) is None
    add_mut("mut_04_sigma_uses_forbidden_entry", case_sparse, m4, "sigma uses forbidden null entry")

    # 5. sigma duplicate column (not permutation)
    m5 = copy.deepcopy(sol_3x3)
    m5["sigma"] = [1, 1, 2]
    add_mut("mut_05_sigma_duplicate_col", case_3x3, m5, "sigma has duplicate column")

    # 6. sigma out of bounds
    m6 = copy.deepcopy(sol_3x3)
    m6["sigma"] = [0, 1, 99]
    add_mut("mut_06_sigma_out_of_bounds", case_3x3, m6, "sigma entry 99 out of bounds")

    # 7. sigma too short
    m7 = copy.deepcopy(sol_3x3)
    m7["sigma"] = [0, 1]
    add_mut("mut_07_sigma_too_short", case_3x3, m7, "sigma length 2 instead of 3")

    # 8. sigma too long
    m8 = copy.deepcopy(sol_3x3)
    m8["sigma"] = [1, 0, 2, 3]
    add_mut("mut_08_sigma_too_long", case_3x3, m8, "sigma length 4 instead of 3")

    # 9. value off by 1
    m9 = copy.deepcopy(sol_3x3)
    m9["value"] = str(int(m9["value"]) + 1)
    add_mut("mut_09_value_off_by_one", case_3x3, m9, "value modified by +1")

    # 10. value sign inverted
    m10 = copy.deepcopy(sol_3x3)
    m10["value"] = str(-int(m10["value"]))
    add_mut("mut_10_value_sign_inverted", case_3x3, m10, "value sign flipped")

    # 11. Optimal claimed on Hall case
    m11 = {
        "case_id": case_hall["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [0, 0, 1],
        "u": ["0", "0", "0"],
        "v": ["0", "0", "0"],
        "value": "0",
    }
    add_mut(
        "mut_11_optimal_claimed_on_hall", case_hall, m11, "Claimed OPTIMAL on infeasible Hall case"
    )

    # 12. Hall claimed on optimal case
    m12 = {
        "case_id": case_3x3["case_id"],
        "status": "SOLVED",
        "kind": "NO_PERFECT_ASSIGNMENT",
        "hall_rows": [0],
    }
    add_mut("mut_12_hall_claimed_on_optimal", case_3x3, m12, "Claimed Hall on optimal case")

    # 13. Fake Hall set condition not violated: |N(S)| >= |S|
    m13 = copy.deepcopy(sol_hall)
    m13["hall_rows"] = [2]  # row 2 has allowed cols [0, 1, 2], |N(S)| = 3 >= 1
    add_mut(
        "mut_13_fake_hall_set_condition_holds",
        case_hall,
        m13,
        "hall_rows does not violate Hall's condition",
    )

    # 14. Hall set empty
    m14 = copy.deepcopy(sol_hall)
    m14["hall_rows"] = []
    add_mut("mut_14_hall_set_empty", case_hall, m14, "hall_rows is empty")

    # 15. Hall set out of bounds
    m15 = copy.deepcopy(sol_hall)
    m15["hall_rows"] = [0, 99]
    add_mut("mut_15_hall_set_out_of_bounds", case_hall, m15, "hall_rows index 99 out of bounds")

    # 16. Hall set duplicate
    m16 = copy.deepcopy(sol_hall)
    m16["hall_rows"] = [0, 0]
    add_mut("mut_16_hall_set_duplicate", case_hall, m16, "hall_rows contains duplicate")

    # 17. Max sense dual violated
    m17 = copy.deepcopy(sol_max)
    m17["u"][0] = str(int(m17["u"][0]) + 10)
    add_mut(
        "mut_17_max_sense_dual_violated",
        case_max,
        m17,
        "u[0] modified breaking max dual inequality",
    )

    # 18. Max sense sum mismatch
    m18 = copy.deepcopy(sol_max)
    m18["value"] = str(int(m18["value"]) + 5)
    add_mut(
        "mut_18_max_sense_sum_mismatch",
        case_max,
        m18,
        "value does not match permutation cost in max",
    )

    # 19. Float string in u
    m19 = copy.deepcopy(sol_3x3)
    m19["u"][0] = "3.0"
    add_mut("mut_19_float_string_in_u", case_3x3, m19, "Float string '3.0' in u")

    # 20. Float string in v
    m20 = copy.deepcopy(sol_3x3)
    m20["v"][0] = "0.0"
    add_mut("mut_20_float_string_in_v", case_3x3, m20, "Float string '0.0' in v")

    # 21. Float string in value
    m21 = copy.deepcopy(sol_3x3)
    m21["value"] = "5.0"
    add_mut("mut_21_float_string_in_value", case_3x3, m21, "Float string '5.0' in value")

    # 22. Boolean in u
    m22 = copy.deepcopy(sol_3x3)
    m22["u"][0] = True
    add_mut("mut_22_boolean_in_u", case_3x3, m22, "Boolean True in u")

    # 23. Boolean in v
    m23 = copy.deepcopy(sol_3x3)
    m23["v"][0] = False
    add_mut("mut_23_boolean_in_v", case_3x3, m23, "Boolean False in v")

    # 24. Boolean in value
    m24 = copy.deepcopy(sol_3x3)
    m24["value"] = True
    add_mut("mut_24_boolean_in_value", case_3x3, m24, "Boolean True in value")

    # 25. Raw int in u
    m25 = copy.deepcopy(sol_3x3)
    m25["u"][0] = 3
    add_mut("mut_25_raw_int_in_u", case_3x3, m25, "Raw integer 3 in u")

    # 26. Raw int in v
    m26 = copy.deepcopy(sol_3x3)
    m26["v"][0] = 0
    add_mut("mut_26_raw_int_in_v", case_3x3, m26, "Raw integer 0 in v")

    # 27. Raw int in value
    m27 = copy.deepcopy(sol_3x3)
    m27["value"] = 5
    add_mut("mut_27_raw_int_in_value", case_3x3, m27, "Raw integer 5 in value")

    # 28. u vector too short
    m28 = copy.deepcopy(sol_3x3)
    m28["u"] = m28["u"][:2]
    add_mut("mut_28_u_too_short", case_3x3, m28, "u vector length 2 instead of 3")

    # 29. u vector too long
    m29 = copy.deepcopy(sol_3x3)
    m29["u"].append("0")
    add_mut("mut_29_u_too_long", case_3x3, m29, "u vector length 4 instead of 3")

    # 30. v vector too short
    m30 = copy.deepcopy(sol_3x3)
    m30["v"] = m30["v"][:2]
    add_mut("mut_30_v_too_short", case_3x3, m30, "v vector length 2 instead of 3")

    # 31. v vector too long
    m31 = copy.deepcopy(sol_3x3)
    m31["v"].append("0")
    add_mut("mut_31_v_too_long", case_3x3, m31, "v vector length 4 instead of 3")

    # 32. Missing sigma
    m32 = copy.deepcopy(sol_3x3)
    del m32["sigma"]
    add_mut("mut_32_missing_sigma", case_3x3, m32, "Missing sigma key")

    # 33. Missing u
    m33 = copy.deepcopy(sol_3x3)
    del m33["u"]
    add_mut("mut_33_missing_u", case_3x3, m33, "Missing u key")

    # 34. Missing v
    m34 = copy.deepcopy(sol_3x3)
    del m34["v"]
    add_mut("mut_34_missing_v", case_3x3, m34, "Missing v key")

    # 35. Missing value
    m35 = copy.deepcopy(sol_3x3)
    del m35["value"]
    add_mut("mut_35_missing_value", case_3x3, m35, "Missing value key")

    # 36. Missing hall_rows
    m36 = copy.deepcopy(sol_hall)
    del m36["hall_rows"]
    add_mut("mut_36_missing_hall_rows", case_hall, m36, "Missing hall_rows key")

    # 37. Unknown kind
    m37 = copy.deepcopy(sol_3x3)
    m37["kind"] = "APPROXIMATE"
    add_mut("mut_37_unknown_kind", case_3x3, m37, "kind set to APPROXIMATE")

    # 38. Case ID mismatch
    m38 = copy.deepcopy(sol_3x3)
    m38["case_id"] = "fake_case_id"
    add_mut("mut_38_case_id_mismatch", case_3x3, m38, "case_id mismatch")

    # 39. Missing status
    m39 = copy.deepcopy(sol_3x3)
    del m39["status"]
    add_mut("mut_39_missing_status", case_3x3, m39, "Missing status key")

    # 40. False OUT_OF_SCOPE on valid case
    m40 = {
        "case_id": case_3x3["case_id"],
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "SPOOFED_REASON"},
    }
    add_mut("mut_40_false_oos_on_valid_case", case_3x3, m40, "False OUT_OF_SCOPE on valid case")

    # 41. Spoofed SOLVED on non-square matrix
    case_rect = {"case_id": "c055_p03_non_square_2x3", "cost": [["1", "2", "3"], ["4", "5", "6"]]}
    m41 = {
        "case_id": case_rect["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [0, 1],
        "u": ["0", "0"],
        "v": ["0", "0"],
        "value": "5",
    }
    add_mut(
        "mut_41_spoofed_solved_on_non_square", case_rect, m41, "Spoofed SOLVED on non-square matrix"
    )

    # 42. Spoofed SOLVED on ragged matrix
    case_ragged = {"case_id": "c055_p05_ragged_row", "cost": [["1", "2", "3"], ["4", "5"]]}
    m42 = {
        "case_id": case_ragged["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [0, 1],
        "u": ["0", "0"],
        "v": ["0", "0"],
        "value": "5",
    }
    add_mut("mut_42_spoofed_solved_on_ragged", case_ragged, m42, "Spoofed SOLVED on ragged matrix")

    # 43. Spoofed SOLVED on non-numeric
    case_non_num = {"case_id": "c055_p06_non_numeric", "cost": [["1", "abc"], ["3", "4"]]}
    m43 = {
        "case_id": case_non_num["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [0, 1],
        "u": ["0", "0"],
        "v": ["0", "0"],
        "value": "5",
    }
    add_mut(
        "mut_43_spoofed_solved_on_non_numeric", case_non_num, m43, "Spoofed SOLVED on non-numeric"
    )

    # 44. Spoofed SOLVED on empty cost list
    case_empty = {"case_id": "c055_p08_empty_cost_list", "cost": []}
    m44 = {
        "case_id": case_empty["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": [],
        "u": [],
        "v": [],
        "value": "0",
    }
    add_mut("mut_44_spoofed_solved_on_empty", case_empty, m44, "Spoofed SOLVED on empty matrix")

    # 45. Suboptimal permutation with mismatched value
    m45 = copy.deepcopy(sol_3x3)
    m45["sigma"] = [0, 1, 2]  # cost = 4 + 0 + 2 = 6, value says 5
    m45["value"] = "5"
    add_mut("mut_45_suboptimal_permutation", case_3x3, m45, "Suboptimal sigma with value mismatch")

    # 46. Unreduced fraction string in u
    m46 = copy.deepcopy(sol_3x3)
    m46["u"][0] = "6/2"
    add_mut("mut_46_unreduced_fraction", case_3x3, m46, "Unreduced fraction string in u")

    # 47. Non-numeric string in potential
    m47 = copy.deepcopy(sol_3x3)
    m47["u"][0] = "xyz"
    add_mut("mut_47_non_numeric_potential", case_3x3, m47, "Non-numeric string in u")

    # 48. hall_rows is string not list
    m48 = copy.deepcopy(sol_hall)
    m48["hall_rows"] = "0 1"
    add_mut("mut_48_hall_rows_not_list", case_hall, m48, "hall_rows is string not list")

    assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

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
