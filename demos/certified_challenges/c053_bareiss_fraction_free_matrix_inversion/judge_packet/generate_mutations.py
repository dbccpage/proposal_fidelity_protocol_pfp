"""Generate 48 hostile mutations for C053: Bareiss Fraction-Free Matrix Inversion."""

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "sqlite_pilot_store.py").is_file()
)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from c053_bareiss_fraction_free_matrix_inversion.reference_solver import (
    solve,
)


def generate():
    mut_dir = Path(__file__).resolve().parent / "hostile_mutations"
    mut_dir.mkdir(parents=True, exist_ok=True)

    # Base 2x2 invertible
    inv_2x2 = {"case_id": "bf_mut_inv_2x2", "matrix": [["1", "2"], ["3", "4"]]}
    sol_inv_2x2 = solve(inv_2x2)
    # sol_inv_2x2: det="-2", adj=[["4", "-2"], ["-3", "1"]], inv=[["-2", "1"], ["3/2", "-1/2"]]

    # Base 2x2 singular
    sing_2x2 = {"case_id": "bf_mut_sing_2x2", "matrix": [["1", "2"], ["2", "4"]]}
    sol_sing_2x2 = solve(sing_2x2)
    # sol_sing_2x2: det="0", null_vector=["-2", "1"]

    # Base 3x3 invertible
    inv_3x3 = {
        "case_id": "bf_mut_inv_3x3",
        "matrix": [["1", "0", "2"], ["2", "-1", "3"], ["4", "1", "8"]],
    }
    sol_inv_3x3 = solve(inv_3x3)

    mutations = []

    # 01-04: Determinant corruptions
    m1 = copy.deepcopy(sol_inv_2x2)
    m1["det"] = "-1"  # off by 1
    mutations.append(("mut_01_det_off_by_one", inv_2x2, m1))

    m2 = copy.deepcopy(sol_inv_2x2)
    m2["det"] = "-3"
    mutations.append(("mut_02_det_off_by_neg_one", inv_2x2, m2))

    m3 = copy.deepcopy(sol_inv_2x2)
    m3["det"] = "2"  # sign flipped
    mutations.append(("mut_03_det_sign_flipped", inv_2x2, m3))

    m4 = copy.deepcopy(sol_inv_2x2)
    m4["det"] = "0"  # zero det on invertible
    mutations.append(("mut_04_det_zero_on_invertible", inv_2x2, m4))

    # 05-08: Adjugate matrix corruptions
    m5 = copy.deepcopy(sol_inv_2x2)
    m5["adjugate"][0][0] = "5"
    mutations.append(("mut_05_adj_entry_corrupted", inv_2x2, m5))

    m6 = copy.deepcopy(sol_inv_2x2)
    m6["adjugate"][0][1] = "2"  # sign flipped
    mutations.append(("mut_06_adj_off_diag_sign_flipped", inv_2x2, m6))

    m7 = copy.deepcopy(sol_inv_2x2)
    # Transposed adjugate (i.e. cofactor matrix instead of its transpose)
    m7["adjugate"] = [["4", "-3"], ["-2", "1"]]
    mutations.append(("mut_07_adj_untransposed_cofactor", inv_2x2, m7))

    m8 = copy.deepcopy(sol_inv_2x2)
    m8["adjugate"] = [["-4", "2"], ["3", "-1"]]  # all signs flipped
    mutations.append(("mut_08_adj_all_signs_flipped", inv_2x2, m8))

    # 09-12: Inverse matrix corruptions
    m9 = copy.deepcopy(sol_inv_2x2)
    m9["inverse"][0][0] = "-1"
    mutations.append(("mut_09_inv_entry_corrupted", inv_2x2, m9))

    m10 = copy.deepcopy(sol_inv_2x2)
    m10["inverse"][1][0] = "1"
    mutations.append(("mut_10_inv_off_diag_corrupted", inv_2x2, m10))

    m11 = copy.deepcopy(sol_inv_2x2)
    m11["inverse"] = m11["adjugate"]  # forgot to divide by det
    mutations.append(("mut_11_inv_equals_adjugate_undivided", inv_2x2, m11))

    m12 = copy.deepcopy(sol_inv_2x2)
    m12["inverse"] = [["2", "-1"], ["-3/2", "1/2"]]  # signs inverted
    mutations.append(("mut_12_inv_signs_inverted", inv_2x2, m12))

    # 13-16: Float string formatting
    m13 = copy.deepcopy(sol_inv_2x2)
    m13["det"] = "-2.0"
    mutations.append(("mut_13_float_string_det", inv_2x2, m13))

    m14 = copy.deepcopy(sol_inv_2x2)
    m14["adjugate"][0][0] = "4.0"
    mutations.append(("mut_14_float_string_adj", inv_2x2, m14))

    m15 = copy.deepcopy(sol_inv_2x2)
    m15["inverse"][0][1] = "1.0"
    mutations.append(("mut_15_float_string_inv", inv_2x2, m15))

    m16 = copy.deepcopy(sol_inv_2x2)
    m16["det"] = True
    mutations.append(("mut_16_bool_det", inv_2x2, m16))

    # 17-20: Bool and raw ints
    m17 = copy.deepcopy(sol_inv_2x2)
    m17["adjugate"][0][0] = True
    mutations.append(("mut_17_bool_adj_entry", inv_2x2, m17))

    m18 = copy.deepcopy(sol_inv_2x2)
    m18["inverse"][0][0] = False
    mutations.append(("mut_18_bool_inv_entry", inv_2x2, m18))

    m19 = copy.deepcopy(sol_inv_2x2)
    m19["det"] = -2  # raw int
    mutations.append(("mut_19_raw_int_det", inv_2x2, m19))

    m20 = copy.deepcopy(sol_inv_2x2)
    m20["adjugate"][0][0] = 4  # raw int
    mutations.append(("mut_20_raw_int_adj", inv_2x2, m20))

    # 21-24: Dimension mismatches on invertible
    m21 = copy.deepcopy(sol_inv_2x2)
    m21["inverse"][0] = ["-2"]  # row too short
    mutations.append(("mut_21_inv_row_too_short", inv_2x2, m21))

    m22 = copy.deepcopy(sol_inv_2x2)
    m22["adjugate"].append(["0", "0"])  # too many rows
    mutations.append(("mut_22_adj_too_many_rows", inv_2x2, m22))

    m23 = copy.deepcopy(sol_inv_2x2)
    m23["inverse"] = "invalid_string"
    mutations.append(("mut_23_inv_not_a_list", inv_2x2, m23))

    m24 = copy.deepcopy(sol_inv_2x2)
    m24["adjugate"] = None
    mutations.append(("mut_24_adj_is_null", inv_2x2, m24))

    # 25-28: Singular claimed as invertible or bad det
    m25 = copy.deepcopy(sol_inv_2x2)
    m25["case_id"] = "bf_mut_sing_2x2"
    mutations.append(("mut_25_singular_claimed_invertible", sing_2x2, m25))

    m26 = copy.deepcopy(sol_sing_2x2)
    m26["det"] = "1"  # non-zero det on singular
    mutations.append(("mut_26_singular_nonzero_det", sing_2x2, m26))

    m27 = copy.deepcopy(sol_sing_2x2)
    m27["null_vector"] = ["0", "0"]  # all zero vector
    mutations.append(("mut_27_all_zero_null_vector", sing_2x2, m27))

    m28 = copy.deepcopy(sol_sing_2x2)
    m28["null_vector"] = ["1", "1"]  # not in nullspace: A * [1, 1]^T = [3, 6]^T != 0
    mutations.append(("mut_28_invalid_null_vector", sing_2x2, m28))

    # 29-32: Null vector dimensions and formatting
    m29 = copy.deepcopy(sol_sing_2x2)
    m29["null_vector"] = ["-2", "1", "0"]  # length 3 instead of 2
    mutations.append(("mut_29_null_vector_too_long", sing_2x2, m29))

    m30 = copy.deepcopy(sol_sing_2x2)
    m30["null_vector"] = ["-2"]  # length 1 instead of 2
    mutations.append(("mut_30_null_vector_too_short", sing_2x2, m30))

    m31 = copy.deepcopy(sol_sing_2x2)
    m31["null_vector"] = ["-2.0", "1"]  # float string
    mutations.append(("mut_31_float_string_null_vector", sing_2x2, m31))

    m32 = copy.deepcopy(sol_sing_2x2)
    m32["null_vector"] = [True, False]  # bools
    mutations.append(("mut_32_bool_null_vector", sing_2x2, m32))

    # 33-36: Null vector types and missing fields
    m33 = copy.deepcopy(sol_sing_2x2)
    m33["null_vector"] = [-2, 1]  # raw ints
    mutations.append(("mut_33_raw_int_null_vector", sing_2x2, m33))

    m34 = copy.deepcopy(sol_sing_2x2)
    del m34["null_vector"]
    mutations.append(("mut_34_missing_null_vector_field", sing_2x2, m34))

    m35 = copy.deepcopy(sol_sing_2x2)
    m35["null_vector"] = None
    mutations.append(("mut_35_null_vector_is_none", sing_2x2, m35))

    m36 = copy.deepcopy(sol_sing_2x2)
    m36["kind"] = "UNKNOWN_KIND"
    mutations.append(("mut_36_unknown_kind", sing_2x2, m36))

    # 37-40: 3x3 matrix corruptions
    m37 = copy.deepcopy(sol_inv_3x3)
    m37["det"] = "2"  # true det is 1
    mutations.append(("mut_37_3x3_det_corrupted", inv_3x3, m37))

    m38 = copy.deepcopy(sol_inv_3x3)
    m38["adjugate"][1][2] = "99"
    mutations.append(("mut_38_3x3_adj_entry_corrupted", inv_3x3, m38))

    m39 = copy.deepcopy(sol_inv_3x3)
    m39["inverse"][0][0] = "5"
    mutations.append(("mut_39_3x3_inv_entry_corrupted", inv_3x3, m39))

    m40 = copy.deepcopy(sol_inv_3x3)
    m40["inverse"][2][2] = "99"
    mutations.append(("mut_40_3x3_inv_diag_corrupted", inv_3x3, m40))

    # 41-44: Invertible claimed as singular & spoofed cases
    m41 = copy.deepcopy(sol_sing_2x2)
    m41["case_id"] = "bf_mut_inv_2x2"
    mutations.append(("mut_41_invertible_claimed_singular", inv_2x2, m41))

    rect_case = {"case_id": "bf_mut_rect_2x3", "matrix": [["1", "2", "3"], ["4", "5", "6"]]}
    m42 = {
        "case_id": "bf_mut_rect_2x3",
        "status": "SOLVED",
        "kind": "INVERTIBLE",
        "det": "1",
        "adjugate": [["1"]],
        "inverse": [["1"]],
    }
    mutations.append(("mut_42_spoofed_solved_on_rect_matrix", rect_case, m42))

    ragged_case = {"case_id": "bf_mut_ragged", "matrix": [["1", "2"], ["3"]]}
    m43 = {
        "case_id": "bf_mut_ragged",
        "status": "SOLVED",
        "kind": "SINGULAR",
        "det": "0",
        "null_vector": ["1", "0"],
    }
    mutations.append(("mut_43_spoofed_solved_on_ragged_matrix", ragged_case, m43))

    empty_case = {"case_id": "bf_mut_empty", "matrix": []}
    m44 = {
        "case_id": "bf_mut_empty",
        "status": "SOLVED",
        "kind": "INVERTIBLE",
        "det": "1",
        "adjugate": [],
        "inverse": [],
    }
    mutations.append(("mut_44_spoofed_solved_on_empty_matrix", empty_case, m44))

    # 45-48: Status violations & case ID mismatches
    m45 = copy.deepcopy(sol_inv_2x2)
    m45["status"] = "OUT_OF_SCOPE"  # false OOS on valid case
    mutations.append(("mut_45_false_oos_on_valid_case", inv_2x2, m45))

    m46 = copy.deepcopy(sol_inv_2x2)
    m46["status"] = "UNKNOWN"
    mutations.append(("mut_46_spoofed_unknown", inv_2x2, m46))

    m47 = copy.deepcopy(sol_inv_2x2)
    m47["case_id"] = "wrong_case_id"
    mutations.append(("mut_47_case_id_mismatch", inv_2x2, m47))

    m48 = copy.deepcopy(sol_inv_2x2)
    del m48["status"]
    mutations.append(("mut_48_missing_status_field", inv_2x2, m48))

    for name, c, corrupted in mutations:
        payload = {"mutation_id": name, "case": c, "corrupted_result": corrupted}
        with open(mut_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    print(f"Generated {len(mutations)} hostile mutations in {mut_dir}")


if __name__ == "__main__":
    generate()
