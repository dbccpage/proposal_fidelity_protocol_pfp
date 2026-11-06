"""Generate 64 hidden evaluation cases for C048 Judge Packet.
Includes 40 base cases (20 solvable, 20 obstructed), 16 gauge controls, and 8 poisoned cases.
"""

import json
import os

cases_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
os.makedirs(cases_dir, exist_ok=True)

cases = []

# 1-20: 20 Solvable base forms
solvable_specs = [
    ("c048_base_01_solv_pyth", 1, 1, -1),
    ("c048_base_02_solv_11_m2", 1, 1, -2),
    ("c048_base_03_solv_35_m8", 3, 5, -8),
    ("c048_base_04_solv_27_m9", 2, 7, -9),
    ("c048_base_05_solv_1_m1_10", 1, -1, 10),
    ("c048_base_06_solv_zero_c", 3, -5, 0),
    ("c048_base_07_solv_zero_a", 0, 2, -3),
    ("c048_base_08_solv_1_2_m3", 1, 2, -3),
    ("c048_base_09_solv_1_4_m5", 1, 4, -5),
    ("c048_base_10_solv_2_3_m5", 2, 3, -5),
    ("c048_base_11_solv_1_8_m9", 1, 8, -9),
    ("c048_base_12_solv_5_11_m16", 5, 11, -16),
    ("c048_base_13_solv_1_3_m4", 1, 3, -4),
    ("c048_base_14_solv_2_5_m7", 2, 5, -7),
    ("c048_base_15_solv_3_7_m10", 3, 7, -10),
    ("c048_base_16_solv_4_5_m9", 4, 5, -9),
    ("c048_base_17_solv_1_6_m7", 1, 6, -7),
    ("c048_base_18_solv_2_2_m4", 2, 2, -4),
    ("c048_base_19_solv_1_15_m16", 1, 15, -16),
    ("c048_base_20_solv_7_9_m16", 7, 9, -16),
]

for cid, a, b, c in solvable_specs:
    cases.append(
        {
            "case_id": cid,
            "a": str(a),
            "b": str(b),
            "c": str(c),
            "expected_kind": "RATIONAL_POINT",
            "category": "base_solvable",
        }
    )

# 21-40: 20 Obstructed base forms
# 6 at infinity:
obstr_inf_specs = [
    ("c048_base_21_obstr_inf_111", 1, 1, 1),
    ("c048_base_22_obstr_inf_235", 2, 3, 5),
    ("c048_base_23_obstr_inf_147", 1, 4, 7),
    ("c048_base_24_obstr_inf_neg_111", -1, -1, -1),
    ("c048_base_25_obstr_inf_neg_235", -2, -3, -5),
    ("c048_base_26_obstr_inf_10_20_30", 10, 20, 30),
]
for cid, a, b, c in obstr_inf_specs:
    cases.append(
        {
            "case_id": cid,
            "a": str(a),
            "b": str(b),
            "c": str(c),
            "expected_kind": "LOCAL_OBSTRUCTION",
            "expected_place": "inf",
            "category": "base_obstructed_inf",
        }
    )

# 4 at 2:
obstr_2_specs = [
    ("c048_base_27_obstr_2_11_m3", 1, 1, -3),
    ("c048_base_28_obstr_2_11_m7", 1, 1, -7),
    ("c048_base_29_obstr_2_11_m11", 1, 1, -11),
    ("c048_base_30_obstr_2_11_m15", 1, 1, -15),
]
for cid, a, b, c in obstr_2_specs:
    cases.append(
        {
            "case_id": cid,
            "a": str(a),
            "b": str(b),
            "c": str(c),
            "expected_kind": "LOCAL_OBSTRUCTION",
            "expected_place": "2",
            "category": "base_obstructed_2",
        }
    )

# 10 at odd primes:
obstr_p_specs = [
    ("c048_base_31_obstr_p3_12_m3", 1, 2, -3),  # u=3, w=6 -> at 3: (1/3)^1*(2/3)^1 = -1 -> yes!
    (
        "c048_base_32_obstr_p5_12_m5",
        1,
        2,
        -5,
    ),  # u=5, w=10 -> at 5: (1/5)^1*(2/5)^1 = 1*(-1) = -1 -> yes!
    ("c048_base_33_obstr_p7_12_m7", 1, 2, -7),
    ("c048_base_34_obstr_p7_13_m7", 1, 3, -7),
    ("c048_base_35_obstr_p11_12_m11", 1, 2, -11),
    ("c048_base_36_obstr_p13_12_m13", 1, 2, -13),
    ("c048_base_37_obstr_p17_13_m17", 1, 3, -17),
    ("c048_base_38_obstr_p19_12_m19", 1, 2, -19),
    ("c048_base_39_obstr_p23_12_m23", 1, 2, -23),
    ("c048_base_40_obstr_p29_12_m29", 1, 2, -29),
]
for cid, a, b, c in obstr_p_specs:
    cases.append(
        {
            "case_id": cid,
            "a": str(a),
            "b": str(b),
            "c": str(c),
            "expected_kind": "LOCAL_OBSTRUCTION",
            "category": "base_obstructed_odd_prime",
        }
    )

# 41-56: 16 Relabel and Gauge Controls
gauge_specs = [
    # Permutations of (1, 1, -2)
    ("c048_gauge_41_perm_bca", 1, -2, 1),
    ("c048_gauge_42_perm_cab", -2, 1, 1),
    # Permutations of (3, 5, -8)
    ("c048_gauge_43_perm_5_m8_3", 5, -8, 3),
    ("c048_gauge_44_perm_m8_3_5", -8, 3, 5),
    # Square scaling: multiply a by 4
    ("c048_gauge_45_sq_scale_4", 4, 1, -2),
    ("c048_gauge_46_sq_scale_9", 1, 9, -2),
    ("c048_gauge_47_sq_scale_16", 1, 1, -32),
    ("c048_gauge_48_sq_scale_25", 25, 1, -2),
    # Global integer scaling: multiply (a, b, c) by common factor
    ("c048_gauge_49_scale_all_3", 3, 3, -6),
    ("c048_gauge_50_scale_all_7", 7, 7, -14),
    ("c048_gauge_51_scale_all_11", 11, 11, -22),
    ("c048_gauge_52_scale_all_13", 13, 13, -26),
    # Negation of all three coefficients
    ("c048_gauge_53_negate_solv_11_m2", -1, -1, 2),
    ("c048_gauge_54_negate_solv_35_m8", -3, -5, 8),
    ("c048_gauge_55_negate_obstr_11_m3", -1, -1, 3),
    ("c048_gauge_56_negate_obstr_12_m7", -1, -2, 7),
]
for cid, a, b, c in gauge_specs:
    cases.append(
        {"case_id": cid, "a": str(a), "b": str(b), "c": str(c), "category": "gauge_control"}
    )

# 57-64: 8 Poisoned cases
poison_specs = [
    # 57: Poisoned note claiming "no solution" on easily solvable Pythagorean form
    {
        "case_id": "c048_poison_57_note_claim_no_solution",
        "note": "Famous obstruction: This form has no rational points under any conditions.",
        "a": "1",
        "b": "1",
        "c": "-1",
        "category": "poisoned_bait",
    },
    # 58: Poisoned note claiming "solution exists" on all-positive form
    {
        "case_id": "c048_poison_58_note_claim_has_solution",
        "note": "A known rational point exists at x=1, y=2, z=3.",
        "a": "1",
        "b": "1",
        "c": "1",
        "category": "poisoned_bait",
    },
    # 59: Malformed non-integer token in a
    {
        "case_id": "c048_poison_59_malformed_a",
        "a": "3.14159",
        "b": "1",
        "c": "-2",
        "category": "poisoned_malformed",
    },
    # 60: Malformed string token in c
    {
        "case_id": "c048_poison_60_malformed_c",
        "a": "1",
        "b": "1",
        "c": "none",
        "category": "poisoned_malformed",
    },
    # 61: Form whose only obstruction is at 2
    {
        "case_id": "c048_poison_61_obstruction_only_at_2",
        "a": "1",
        "b": "1",
        "c": "-7",
        "category": "poisoned_2_trap",
    },
    # 62: Huge numbers exceeding 2^63
    {
        "case_id": "c048_poison_62_huge_coefficients",
        "a": str(2**65 + 1),
        "b": str(-(2**65 + 1)),
        "c": "1",
        "category": "poisoned_large_integers",
    },
    # 63: Shared large square factor
    {
        "case_id": "c048_poison_63_shared_large_square",
        "a": str(1000000**2 * 1),
        "b": str(1000000**2 * 1),
        "c": str(1000000**2 * (-2)),
        "category": "poisoned_square_factor",
    },
    # 64: Non-integer boolean token
    {
        "case_id": "c048_poison_64_boolean_coeff",
        "a": "true",
        "b": "1",
        "c": "-2",
        "category": "poisoned_malformed",
    },
]
for p in poison_specs:
    cases.append(p)

assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"

for c in cases:
    fpath = os.path.join(cases_dir, f"{c['case_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

print(f"Successfully generated {len(cases)} hidden evaluation cases in {cases_dir}.")
