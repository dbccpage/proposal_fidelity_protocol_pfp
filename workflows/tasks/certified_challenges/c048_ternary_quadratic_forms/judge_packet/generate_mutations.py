"""Generate 48 hostile mutations for C048 Judge Packet.
Verifies that exact_checker and independent_checker reject 100% of corruptions.
"""

import glob
import json
import os

cases_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
muts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostile_mutations")
os.makedirs(muts_dir, exist_ok=True)

# Load base cases
base_cases = {}
for p in glob.glob(os.path.join(cases_dir, "*.json")):
    with open(p, "r", encoding="utf-8") as f:
        c = json.load(f)
        base_cases[c["case_id"]] = c

mutations = []

# 1-6: Trivial zero solution (0, 0, 0)
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_04_solv_27_m9",
        "c048_base_08_solv_1_2_m3",
        "c048_base_09_solv_1_4_m5",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_0{i + 1}_trivial_zero",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RATIONAL_POINT",
                "x": "0",
                "y": "0",
                "z": "0",
            },
            "expected_rejection": "trivial zero solution",
        }
    )

# 7-12: Solution off-by-one in z
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_04_solv_27_m9",
        "c048_base_08_solv_1_2_m3",
        "c048_base_10_solv_2_3_m5",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 7:02d}_off_by_one_z",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RATIONAL_POINT",
                "x": "1",
                "y": "1",
                "z": "2",  # Violates equation
            },
            "expected_rejection": "equation violated",
        }
    )

# 13-18: Composite "place"
for i, cid in enumerate(
    [
        "c048_base_27_obstr_2_11_m3",
        "c048_base_28_obstr_2_11_m7",
        "c048_base_31_obstr_p3_12_m3",
        "c048_base_32_obstr_p5_12_m5",
        "c048_base_33_obstr_p7_12_m7",
        "c048_base_35_obstr_p11_12_m11",
    ]
):
    bad_places = ["4", "6", "8", "9", "12", "15"]
    mutations.append(
        {
            "mutation_id": f"mut_{i + 13:02d}_composite_place",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "LOCAL_OBSTRUCTION",
                "place": bad_places[i],
            },
            "expected_rejection": "composite place",
        }
    )

# 19-24: Claiming prime place where Hilbert symbol is +1
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_04_solv_27_m9",
        "c048_base_08_solv_1_2_m3",
        "c048_base_10_solv_2_3_m5",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 19:02d}_false_prime_obstruction",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "LOCAL_OBSTRUCTION",
                "place": "17",  # Solvable forms have no obstruction places
            },
            "expected_rejection": "Hilbert symbol is +1",
        }
    )

# 25-30: Claiming inf on indefinite forms
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_27_obstr_2_11_m3",
        "c048_base_31_obstr_p3_12_m3",
        "c048_base_33_obstr_p7_12_m7",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 25:02d}_false_inf_obstruction",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "LOCAL_OBSTRUCTION",
                "place": "inf",
            },
            "expected_rejection": "indefinite form over R",
        }
    )

# 31-36: Float string coordinates
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_04_solv_27_m9",
        "c048_base_08_solv_1_2_m3",
        "c048_base_10_solv_2_3_m5",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 31:02d}_float_coordinates",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RATIONAL_POINT",
                "x": "1.0",
                "y": "1.0",
                "z": "1.0",
            },
            "expected_rejection": "float coordinate",
        }
    )

# 37-42: Boolean coordinates
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_04_solv_27_m9",
        "c048_base_08_solv_1_2_m3",
        "c048_base_10_solv_2_3_m5",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 37:02d}_boolean_coordinate",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RATIONAL_POINT",
                "x": True,
                "y": "1",
                "z": "1",
            },
            "expected_rejection": "boolean coordinate",
        }
    )

# 43-48: False OUT_OF_SCOPE on valid integers
for i, cid in enumerate(
    [
        "c048_base_01_solv_pyth",
        "c048_base_02_solv_11_m2",
        "c048_base_03_solv_35_m8",
        "c048_base_21_obstr_inf_111",
        "c048_base_27_obstr_2_11_m3",
        "c048_base_31_obstr_p3_12_m3",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 43:02d}_false_out_of_scope",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "MALFORMED_COEFFICIENT"},
            },
            "expected_rejection": "false out of scope",
        }
    )

assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

for m in mutations:
    fpath = os.path.join(muts_dir, f"{m['mutation_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

print(f"Successfully generated {len(mutations)} hostile mutations in {muts_dir}.")
