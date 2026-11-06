import json
import os

cases = [
    # 24 Optimal
    {
        "case_id": "case_01_base_opt_degen_2d_vertex",
        "A": [["1", "1"], ["2", "1"], ["1", "2"], ["3", "1"]],
        "b": ["4", "6", "6", "8"],
        "c": ["2", "2"],
    },
    {
        "case_id": "case_02_base_opt_degen_beale_var",
        "A": [
            ["1/4", "-8", "-1", "9"],
            ["1/2", "-12", "-1/2", "3"],
            ["0", "0", "1", "0"],
            ["1", "0", "0", "0"],
        ],
        "b": ["0", "0", "1", "2"],
        "c": ["3/4", "-20", "1/2", "-6"],
    },
    {
        "case_id": "case_03_base_opt_degen_3d_corner",
        "A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"], ["1", "1", "1"]],
        "b": ["1", "1", "1", "3"],
        "c": ["1", "2", "3"],
    },
    {
        "case_id": "case_04_base_opt_degen_redundant_diagonals",
        "A": [["2", "3"], ["4", "6"], ["1", "1"], ["3", "4"]],
        "b": ["12", "24", "5", "17"],
        "c": ["3", "4"],
    },
    {
        "case_id": "case_05_base_opt_degen_zero_rhs",
        "A": [["1", "-1"], ["-1", "2"], ["1", "1"]],
        "b": ["0", "0", "5"],
        "c": ["-1", "-2"],
    },
    {
        "case_id": "case_06_base_opt_degen_pyramid",
        "A": [["1", "1", "1"], ["1", "0", "1"], ["0", "1", "1"], ["2", "1", "2"]],
        "b": ["6", "4", "4", "10"],
        "c": ["3", "2", "5"],
    },
    {
        "case_id": "case_07_base_opt_degen_4d_vertex",
        "A": [
            ["1", "0", "0", "0"],
            ["0", "1", "0", "0"],
            ["0", "0", "1", "0"],
            ["0", "0", "0", "1"],
            ["1", "1", "1", "1"],
        ],
        "b": ["2", "2", "2", "2", "8"],
        "c": ["1", "3", "2", "4"],
    },
    {
        "case_id": "case_08_base_opt_degen_neg_obj",
        "A": [["1", "2"], ["2", "1"], ["3", "3"]],
        "b": ["6", "6", "12"],
        "c": ["-1", "3"],
    },
    {
        "case_id": "case_09_base_opt_degen_tight_bounds",
        "A": [["1", "0"], ["0", "1"], ["1", "1"], ["2", "2"]],
        "b": ["3", "3", "6", "12"],
        "c": ["5", "5"],
    },
    {
        "case_id": "case_10_base_opt_degen_fractional_vertex",
        "A": [["3", "2"], ["2", "3"], ["5", "5"]],
        "b": ["7", "7", "14"],
        "c": ["4", "4"],
    },
    {"case_id": "case_11_base_opt_1x1", "A": [["5"]], "b": ["15"], "c": ["4"]},
    {"case_id": "case_12_base_opt_1x3", "A": [["1", "2", "3"]], "b": ["6"], "c": ["2", "3", "1"]},
    {
        "case_id": "case_13_base_opt_3x1",
        "A": [["2"], ["3"], ["1"]],
        "b": ["10", "12", "5"],
        "c": ["7"],
    },
    {
        "case_id": "case_14_base_opt_standard_2x2",
        "A": [["1", "2"], ["3", "1"]],
        "b": ["8", "9"],
        "c": ["4", "5"],
    },
    {
        "case_id": "case_15_base_opt_fractional_rhs",
        "A": [["1/2", "1/3"], ["1/4", "1/5"]],
        "b": ["5/6", "7/10"],
        "c": ["1", "2"],
    },
    {
        "case_id": "case_16_base_opt_large_3x3",
        "A": [["1", "2", "1"], ["2", "1", "3"], ["1", "1", "1"]],
        "b": ["10", "15", "8"],
        "c": ["3", "4", "5"],
    },
    {
        "case_id": "case_17_base_opt_mixed_signs_A",
        "A": [["1", "-1"], ["-2", "3"], ["1", "1"]],
        "b": ["4", "6", "10"],
        "c": ["2", "3"],
    },
    {
        "case_id": "case_18_base_opt_zero_costs",
        "A": [["1", "1"], ["2", "1"]],
        "b": ["3", "4"],
        "c": ["0", "5"],
    },
    {
        "case_id": "case_19_base_opt_all_zero_c",
        "A": [["1", "1"], ["1", "2"]],
        "b": ["4", "6"],
        "c": ["0", "0"],
    },
    {
        "case_id": "case_20_base_opt_dense_4x3",
        "A": [["1", "1", "0"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "1"]],
        "b": ["5", "6", "7", "9"],
        "c": ["3", "2", "4"],
    },
    {
        "case_id": "case_21_base_opt_5_vars",
        "A": [["1", "1", "1", "1", "1"], ["1", "2", "0", "1", "0"], ["0", "1", "2", "0", "1"]],
        "b": ["10", "8", "9"],
        "c": ["2", "3", "1", "4", "2"],
    },
    {
        "case_id": "case_22_base_opt_sparse_identity_blocks",
        "A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"], ["1", "1", "0"]],
        "b": ["4", "5", "6", "7"],
        "c": ["5", "3", "2"],
    },
    {
        "case_id": "case_23_base_opt_upper_triangular",
        "A": [["1", "2", "3"], ["0", "1", "2"], ["0", "0", "1"]],
        "b": ["12", "6", "2"],
        "c": ["1", "1", "1"],
    },
    {
        "case_id": "case_24_base_opt_banded_matrix",
        "A": [["2", "1", "0"], ["1", "2", "1"], ["0", "1", "2"]],
        "b": ["5", "6", "7"],
        "c": ["3", "3", "3"],
    },
    # 8 Infeasible
    {"case_id": "case_25_base_infeas_single_neg", "A": [["1", "2"]], "b": ["-3"], "c": ["1", "1"]},
    {
        "case_id": "case_26_base_infeas_two_bounds",
        "A": [["1", "0"], ["-1", "0"]],
        "b": ["3", "-5"],
        "c": ["1", "0"],
    },
    {
        "case_id": "case_27_base_infeas_parallel_hyperplanes",
        "A": [["1", "1"], ["-1", "-1"]],
        "b": ["2", "-4"],
        "c": ["2", "1"],
    },
    {
        "case_id": "case_28_base_infeas_sum_vars",
        "A": [["1", "1", "1"], ["-1", "-1", "-1"]],
        "b": ["3", "-5"],
        "c": ["1", "1", "1"],
    },
    {
        "case_id": "case_29_base_infeas_triangle_ineq",
        "A": [["1", "1", "0"], ["0", "1", "1"], ["-1", "0", "-1"]],
        "b": ["2", "2", "-5"],
        "c": ["0", "0", "0"],
    },
    {
        "case_id": "case_30_base_infeas_4x2_overconstrained",
        "A": [["1", "0"], ["0", "1"], ["-1", "0"], ["0", "-1"]],
        "b": ["2", "2", "-3", "0"],
        "c": ["1", "1"],
    },
    {"case_id": "case_31_base_infeas_1x1", "A": [["3"]], "b": ["-1"], "c": ["2"]},
    {
        "case_id": "case_32_base_infeas_fractional_farkas",
        "A": [["2/3", "1/2"], ["-1/3", "-1/4"]],
        "b": ["1", "-2"],
        "c": ["1", "1"],
    },
    # 8 Unbounded
    {"case_id": "case_33_base_unbounded_1x1", "A": [["-1"]], "b": ["0"], "c": ["5"]},
    {"case_id": "case_34_base_unbounded_free_var", "A": [["1", "0"]], "b": ["4"], "c": ["1", "3"]},
    {
        "case_id": "case_35_base_unbounded_diagonal_ray",
        "A": [["-1", "1"], ["0", "-1"]],
        "b": ["2", "0"],
        "c": ["2", "1"],
    },
    {
        "case_id": "case_36_base_unbounded_cone_3d",
        "A": [["-1", "0", "0"], ["0", "-1", "0"], ["0", "0", "-1"]],
        "b": ["1", "2", "3"],
        "c": ["1", "2", "3"],
    },
    {
        "case_id": "case_37_base_unbounded_shear",
        "A": [["1", "-2"], ["-2", "1"]],
        "b": ["3", "3"],
        "c": ["1", "1"],
    },
    {
        "case_id": "case_38_base_unbounded_zero_constraint",
        "A": [["0", "0"]],
        "b": ["0"],
        "c": ["1", "4"],
    },
    {
        "case_id": "case_39_base_unbounded_multi_var_ray",
        "A": [["1", "-1", "0"], ["0", "1", "-1"]],
        "b": ["5", "5"],
        "c": ["1", "1", "3"],
    },
    {
        "case_id": "case_40_base_unbounded_with_tight_subspace",
        "A": [["1", "0", "-1"], ["0", "1", "-1"]],
        "b": ["0", "0"],
        "c": ["0", "0", "1"],
    },
    # 16 Gauge / Relabel
    {
        "case_id": "case_41_gauge_var_permute_2x2",
        "A": [["2", "1"], ["1", "3"]],
        "b": ["8", "9"],
        "c": ["5", "4"],
    },
    {
        "case_id": "case_42_gauge_var_permute_3x3",
        "A": [["2", "1", "1"], ["1", "3", "2"], ["1", "1", "1"]],
        "b": ["10", "15", "8"],
        "c": ["4", "5", "3"],
    },
    {
        "case_id": "case_43_gauge_var_permute_unbounded",
        "A": [["1", "-1"], ["-1", "0"]],
        "b": ["2", "0"],
        "c": ["1", "2"],
    },
    {
        "case_id": "case_44_gauge_var_permute_infeasible",
        "A": [["1", "1"], ["-1", "-1"]],
        "b": ["2", "-4"],
        "c": ["1", "2"],
    },
    {
        "case_id": "case_45_gauge_row_permute_degenerate",
        "A": [["3", "1"], ["1", "2"], ["2", "1"], ["1", "1"]],
        "b": ["8", "6", "6", "4"],
        "c": ["2", "2"],
    },
    {
        "case_id": "case_46_gauge_row_permute_dense",
        "A": [["1", "1", "1"], ["1", "0", "1"], ["0", "1", "1"], ["1", "1", "0"]],
        "b": ["9", "7", "6", "5"],
        "c": ["3", "2", "4"],
    },
    {
        "case_id": "case_47_gauge_row_permute_infeasible",
        "A": [["-1", "0"], ["1", "0"]],
        "b": ["-5", "3"],
        "c": ["1", "0"],
    },
    {
        "case_id": "case_48_gauge_row_permute_unbounded",
        "A": [["-2", "1"], ["1", "-2"]],
        "b": ["3", "3"],
        "c": ["1", "1"],
    },
    {
        "case_id": "case_49_gauge_row_scaling_opt",
        "A": [["3", "6"], ["3", "1"]],
        "b": ["24", "9"],
        "c": ["4", "5"],
    },
    {
        "case_id": "case_50_gauge_row_scaling_infeasible",
        "A": [["1", "1"], ["-5", "-5"]],
        "b": ["2", "-20"],
        "c": ["2", "1"],
    },
    {
        "case_id": "case_51_gauge_row_scaling_unbounded",
        "A": [["-4", "4"], ["0", "-1"]],
        "b": ["8", "0"],
        "c": ["2", "1"],
    },
    {
        "case_id": "case_52_gauge_row_scaling_degen",
        "A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "10"], ["1", "1", "1"]],
        "b": ["1", "1", "10", "3"],
        "c": ["1", "2", "3"],
    },
    {
        "case_id": "case_53_gauge_c_scaling_opt",
        "A": [["1", "2"], ["3", "1"]],
        "b": ["8", "9"],
        "c": ["28", "35"],
    },
    {"case_id": "case_54_gauge_c_scaling_unbounded", "A": [["-1"]], "b": ["0"], "c": ["5/2"]},
    {
        "case_id": "case_55_gauge_redundant_constraint_opt",
        "A": [["1", "2"], ["3", "1"], ["1", "2"]],
        "b": ["8", "9", "8"],
        "c": ["4", "5"],
    },
    {
        "case_id": "case_56_gauge_redundant_constraint_infeas",
        "A": [["1", "1"], ["-1", "-1"], ["-1", "-1"]],
        "b": ["2", "-4", "-4"],
        "c": ["2", "1"],
    },
    # 8 Poisoned
    {
        "case_id": "case_57_poison_misleading_note_opt",
        "A": [["1", "1"], ["2", "1"]],
        "b": ["4", "6"],
        "c": ["3", "2"],
        "note": "OPTIMAL value is guaranteed to be 100 with x=[20, 20]",
    },
    {
        "case_id": "case_58_poison_misleading_note_infeas",
        "A": [["2", "3"], ["1", "1"]],
        "b": ["6", "2"],
        "c": ["1", "1"],
        "note": "This system is strictly INFEASIBLE under Farkas lemma",
    },
    {
        "case_id": "case_59_poison_unreduced_input_fractions",
        "A": [["2/4", "6/9"], ["1/1", "4/8"]],
        "b": ["10/2", "3/1"],
        "c": ["4/2", "6/3"],
    },
    {
        "case_id": "case_60_poison_huge_denominators",
        "A": [["1/1000000000000", "1"], ["0", "1/1000000000000"]],
        "b": ["1", "1"],
        "c": ["1", "1"],
    },
    {
        "case_id": "case_61_poison_nearly_unbounded_zero_gain",
        "A": [["-1", "0"], ["0", "1"]],
        "b": ["0", "5"],
        "c": ["0", "2"],
    },
    {
        "case_id": "case_62_poison_nearly_unbounded_ray_fails_Ad",
        "A": [["-1", "1"], ["1/1000", "0"]],
        "b": ["2", "5"],
        "c": ["1", "0"],
    },
    {
        "case_id": "case_63_poison_unreduced_infeasible",
        "A": [["4/8", "2/4"]],
        "b": ["-6/2"],
        "c": ["2/2", "4/4"],
    },
    {
        "case_id": "case_64_poison_extreme_aspect_ratio_1x10",
        "A": [["1", "1", "1", "1", "1", "1", "1", "1", "1", "1"]],
        "b": ["10"],
        "c": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    },
]


def main():
    cases_dir = os.path.join(os.path.dirname(__file__), "cases")
    os.makedirs(cases_dir, exist_ok=True)
    for c in cases:
        with open(os.path.join(cases_dir, f"{c['case_id']}.json"), "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)
    print(f"Generated {len(cases)} hidden cases.")


if __name__ == "__main__":
    main()
