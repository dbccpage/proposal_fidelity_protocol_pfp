"""Generate 48 hostile mutations for C052: Max-Flow with Min-Cut Certificates."""

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

from c052_maxflow_mincut_certificates.reference_solver import (
    solve,
)


def generate():
    mut_dir = Path(__file__).resolve().parent / "hostile_mutations"
    mut_dir.mkdir(parents=True, exist_ok=True)

    # Base reference case
    base_case = {
        "case_id": "mf_base_mut_ref",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "3"], [0, 2, "2"], [1, 2, "1"], [1, 3, "2"], [2, 3, "3"]],
    }
    base_sol = solve(base_case)
    # base_sol: value='5', flow=['3','2','1','2','3'], cut_S=[0]

    mutations = []

    # 01-04: Arc over capacity
    m1 = copy.deepcopy(base_sol)
    m1["flow"][0] = str(int(m1["flow"][0]) + 1)
    mutations.append(("mut_01_arc_over_cap_by_1", base_case, m1))

    m2 = copy.deepcopy(base_sol)
    m2["flow"][1] = str(int(m2["flow"][1]) + 10)
    mutations.append(("mut_02_arc_over_cap_by_10", base_case, m2))

    # 03-04: Flow conservation break
    m3 = copy.deepcopy(base_sol)
    m3["flow"][2] = str(int(m3["flow"][2]) + 1)  # arc 1->2 flow increased without updating out of 2
    mutations.append(("mut_03_flow_conservation_break_internal_1", base_case, m3))

    m4 = copy.deepcopy(base_sol)
    m4["flow"][3] = str(int(m4["flow"][3]) - 1)  # arc 1->3 flow decreased
    mutations.append(("mut_04_flow_conservation_break_internal_2", base_case, m4))

    # 05-08: Source / Sink balance mismatch
    m5 = copy.deepcopy(base_sol)
    m5["value"] = str(int(m5["value"]) + 1)
    mutations.append(("mut_05_source_balance_mismatch_plus_1", base_case, m5))

    m6 = copy.deepcopy(base_sol)
    m6["value"] = str(int(m6["value"]) - 1)
    mutations.append(("mut_06_source_balance_mismatch_minus_1", base_case, m6))

    m7 = copy.deepcopy(base_sol)
    m7["value"] = "999"
    mutations.append(("mut_07_source_balance_mismatch_large", base_case, m7))

    m8 = copy.deepcopy(base_sol)
    m8["value"] = "0"
    mutations.append(("mut_08_source_balance_mismatch_zero", base_case, m8))

    # 09-12: Cut boundary errors
    m9 = copy.deepcopy(base_sol)
    m9["cut_S"] = [0, 3]  # includes sink
    mutations.append(("mut_09_cut_contains_sink_t", base_case, m9))

    m10 = copy.deepcopy(base_sol)
    m10["cut_S"] = [1, 2]  # missing source
    mutations.append(("mut_10_cut_missing_source_s", base_case, m10))

    m11 = copy.deepcopy(base_sol)
    m11["cut_S"] = [0, 99]  # node out of bounds
    mutations.append(("mut_11_cut_node_out_of_bounds", base_case, m11))

    m12 = copy.deepcopy(base_sol)
    m12["cut_S"] = [0, -1]  # negative node
    mutations.append(("mut_12_cut_negative_node", base_case, m12))

    # 13-16: Cut duplicate node and sub-optimal cut
    m13 = copy.deepcopy(base_sol)
    m13["cut_S"] = [0, 0]  # duplicate node
    mutations.append(("mut_13_cut_duplicate_node", base_case, m13))

    m14 = copy.deepcopy(base_sol)
    m14["cut_S"] = [
        0,
        1,
    ]  # cut capacity: (0->2: 2) + (1->2: 1) + (1->3: 2) = 5, but wait: arc 1->2 cap=1, 1->3 cap=2, 0->2 cap=2.
    # What if cut_S is [0, 1, 2]? Arcs leaving {0,1,2} to {3}: (1->3: 2) + (2->3: 3) = 5. That's also min cut!
    # To make sub-optimal cut, consider a case with strictly larger cut:
    diamond_case_2 = {
        "case_id": "mf_mut_diamond_2",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "10"], [0, 2, "10"], [1, 2, "1"], [1, 3, "2"], [2, 3, "2"]],
    }
    diamond_sol_2 = solve(diamond_case_2)  # max flow is 4, min cut is {0, 1, 2} capacity 4.
    m14 = copy.deepcopy(diamond_sol_2)
    m14["cut_S"] = [0]  # cut capacity is 20 > 4!
    mutations.append(("mut_14_cut_capacity_exceeds_min_cut", diamond_case_2, m14))

    m15 = copy.deepcopy(base_sol)
    m15["value"] = "-5"  # negative value
    mutations.append(("mut_15_value_negative", base_case, m15))

    m16 = copy.deepcopy(base_sol)
    m16["value"] = "05"  # non-canonical leading zero
    mutations.append(("mut_16_value_non_canonical_leading_zero", base_case, m16))

    # 17-20: Float string and invalid flow formatting
    m17 = copy.deepcopy(base_sol)
    m17["flow"][0] = "3.0"
    mutations.append(("mut_17_float_string_flow", base_case, m17))

    m18 = copy.deepcopy(base_sol)
    m18["flow"][1] = "2e0"
    mutations.append(("mut_18_scientific_notation_flow", base_case, m18))

    m19 = copy.deepcopy(base_sol)
    m19["flow"][0] = "-1"
    mutations.append(("mut_19_negative_flow", base_case, m19))

    m20 = copy.deepcopy(base_sol)
    m20["flow"][0] = "03"
    mutations.append(("mut_20_non_canonical_flow_leading_zero", base_case, m20))

    # 21-24: Type errors in cut_S
    m21 = copy.deepcopy(base_sol)
    m21["cut_S"] = [True]  # bool instead of int
    mutations.append(("mut_21_bool_node_in_cut_S", base_case, m21))

    m22 = copy.deepcopy(base_sol)
    m22["cut_S"] = [False]
    mutations.append(("mut_22_bool_false_in_cut_S", base_case, m22))

    m23 = copy.deepcopy(base_sol)
    m23["cut_S"] = ["0"]  # string instead of int
    mutations.append(("mut_23_string_node_in_cut_S", base_case, m23))

    m24 = copy.deepcopy(base_sol)
    m24["cut_S"] = [0.0]  # float instead of int
    mutations.append(("mut_24_float_node_in_cut_S", base_case, m24))

    # 25-28: Complementary slackness violations
    # In base_sol: arcs = [[0,1,"3"],[0,2,"2"],[1,2,"1"],[1,3,"2"],[2,3,"3"]], cut_S = [0]
    # Forward cut edges: (0,1, cap=3) and (0,2, cap=2). Both have flow=3,2 (saturated).
    m25 = copy.deepcopy(base_sol)
    # Unsaturate forward cut edge (0,1) to 2, and reduce value and out balance
    m25["flow"] = ["2", "2", "0", "2", "2"]
    m25["value"] = "4"
    mutations.append(("mut_25_forward_cut_edge_not_saturated", base_case, m25))

    # Backward cut edge non-zero flow
    antiparallel_case = {
        "case_id": "mf_mut_antiparallel",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "5"], [1, 0, "5"], [1, 3, "5"]],
    }
    antiparallel_sol = solve(antiparallel_case)  # cut_S = [0, 1] cap=5, value=5, arc 1->0 flow=0
    m26 = copy.deepcopy(antiparallel_sol)
    # Set backward cut edge flow (1->0) to 1
    m26["flow"][1] = "1"
    mutations.append(("mut_26_backward_cut_edge_has_flow", antiparallel_case, m26))

    m27 = copy.deepcopy(base_sol)
    m27["flow"] = m27["flow"][:-1]  # flow vector truncated
    mutations.append(("mut_27_flow_vector_truncated", base_case, m27))

    m28 = copy.deepcopy(base_sol)
    m28["flow"].append("0")  # flow vector too long
    mutations.append(("mut_28_flow_vector_too_long", base_case, m28))

    # 29-32: Spoofed status on malformed cases
    malformed_s_eq_t = {
        "case_id": "mf_malformed_s_eq_t",
        "n": 3,
        "s": 1,
        "t": 1,
        "arcs": [[0, 1, "5"], [1, 2, "5"]],
    }
    m29 = {
        "case_id": "mf_malformed_s_eq_t",
        "status": "SOLVED",
        "value": "0",
        "flow": ["0", "0"],
        "cut_S": [1],
    }
    mutations.append(("mut_29_spoofed_solved_on_s_equals_t", malformed_s_eq_t, m29))

    malformed_neg_cap = {
        "case_id": "mf_malformed_neg_cap",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "5"], [1, 2, "-3"]],
    }
    m30 = {
        "case_id": "mf_malformed_neg_cap",
        "status": "SOLVED",
        "value": "5",
        "flow": ["5", "0"],
        "cut_S": [0],
    }
    mutations.append(("mut_30_spoofed_solved_on_neg_cap", malformed_neg_cap, m30))

    malformed_node_oob = {
        "case_id": "mf_malformed_node_oob",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "5"], [1, 99, "5"]],
    }
    m31 = {
        "case_id": "mf_malformed_node_oob",
        "status": "SOLVED",
        "value": "5",
        "flow": ["5", "0"],
        "cut_S": [0],
    }
    mutations.append(("mut_31_spoofed_solved_on_node_oob", malformed_node_oob, m31))

    m32 = {
        "case_id": "mf_base_mut_ref",
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "FAKE_REASON"},
    }
    mutations.append(("mut_32_spoofed_oos_on_valid_case", base_case, m32))

    # 33-36: Spoofed UNKNOWN and missing fields
    m33 = {"case_id": "mf_base_mut_ref", "status": "UNKNOWN", "code": "GAVE_UP"}
    mutations.append(("mut_33_spoofed_unknown", base_case, m33))

    m34 = copy.deepcopy(base_sol)
    del m34["value"]
    mutations.append(("mut_34_missing_value_field", base_case, m34))

    m35 = copy.deepcopy(base_sol)
    del m35["flow"]
    mutations.append(("mut_35_missing_flow_field", base_case, m35))

    m36 = copy.deepcopy(base_sol)
    del m36["cut_S"]
    mutations.append(("mut_36_missing_cut_S_field", base_case, m36))

    # 37-40: Null values and wrong top-level types
    m37 = copy.deepcopy(base_sol)
    m37["value"] = None
    mutations.append(("mut_37_null_value", base_case, m37))

    m38 = copy.deepcopy(base_sol)
    m38["flow"] = None
    mutations.append(("mut_38_null_flow", base_case, m38))

    m39 = copy.deepcopy(base_sol)
    m39["cut_S"] = None
    mutations.append(("mut_39_null_cut_S", base_case, m39))

    m40 = copy.deepcopy(base_sol)
    m40["cut_S"] = {"0": True}
    mutations.append(("mut_40_dict_cut_S", base_case, m40))

    # 41-44: Raw integers instead of strings in flow/value
    m41 = copy.deepcopy(base_sol)
    m41["value"] = 5  # raw int instead of str
    mutations.append(("mut_41_raw_int_in_value", base_case, m41))

    m42 = copy.deepcopy(base_sol)
    m42["flow"] = [3, 2, 1, 2, 3]  # raw ints instead of strs
    mutations.append(("mut_42_raw_int_in_flow", base_case, m42))

    m43 = copy.deepcopy(base_sol)
    m43["flow"] = "3,2,1,2,3"  # string instead of list
    mutations.append(("mut_43_string_flow_vector", base_case, m43))

    m44 = copy.deepcopy(base_sol)
    m44["case_id"] = "wrong_case_id"
    mutations.append(("mut_44_wrong_case_id", base_case, m44))

    # 45-48: Inverted cut partition and edge corruptions
    m45 = copy.deepcopy(base_sol)
    m45["cut_S"] = [1, 2, 3]  # completely inverted cut S = V \ S (contains t, lacks s)
    mutations.append(("mut_45_inverted_cut_S", base_case, m45))

    m46 = copy.deepcopy(base_sol)
    m46["cut_S"] = []  # empty cut
    mutations.append(("mut_46_empty_cut_S", base_case, m46))

    m47 = copy.deepcopy(base_sol)
    m47["flow"][0] = None
    mutations.append(("mut_47_null_flow_element", base_case, m47))

    m48 = copy.deepcopy(base_sol)
    m48["status"] = "INVALID_STATUS"
    mutations.append(("mut_48_invalid_status_enum", base_case, m48))

    for name, c, corrupted in mutations:
        payload = {"mutation_id": name, "case": c, "corrupted_result": corrupted}
        with open(mut_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    print(f"Generated {len(mutations)} hostile mutations in {mut_dir}")


if __name__ == "__main__":
    generate()
