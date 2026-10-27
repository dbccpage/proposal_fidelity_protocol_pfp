"""Generate 48 hostile mutations for C049 Judge Packet.
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

# 1-8: False DOES_NOT_EXIST for cases where limit/colimit DOES exist
exists_cids = [
    "c049_base_01_product_poset_3",
    "c049_base_02_product_poset_4",
    "c049_base_03_equalizer_same",
    "c049_base_04_equalizer_parallel",
    "c049_base_05_pullback_cospan",
    "c049_base_06_terminal_linear",
    "c049_base_07_coproduct_poset",
    "c049_base_08_coequalizer_same",
]
for i, cid in enumerate(exists_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 1:02d}_false_does_not_exist",
            "case": base_cases[cid],
            "candidate": {"case_id": cid, "status": "SOLVED", "kind": "DOES_NOT_EXIST"},
            "expected_rejection": "false DOES_NOT_EXIST",
        }
    )

# 9-16: False EXISTS with invalid / fake apex
for i, cid in enumerate(exists_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 9:02d}_fake_apex",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "EXISTS",
                "apex": "fake_apex_999",
                "legs": {},
            },
            "expected_rejection": "non-existent apex",
        }
    )

# 17-24: False EXISTS for cases where limit/colimit DOES NOT exist
no_exists_cids = [
    "c049_base_13_no_product_disc2",
    "c049_base_14_no_terminal_disc3",
    "c049_base_15_no_initial_disc3",
    "c049_base_16_no_coproduct_disc2",
    "c049_base_17_no_product_monoid_z2",
    "c049_base_18_no_coproduct_monoid_z3",
    "c049_base_19_no_equalizer",
    "c049_base_20_no_coequalizer",
]
for i, cid in enumerate(no_exists_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 17:02d}_false_exists",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "EXISTS",
                "apex": "0",
                "legs": {},
            },
            "expected_rejection": "false EXISTS",
        }
    )

# 25-32: Corrupt legs (non-existent morphisms)
for i, cid in enumerate(exists_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 25:02d}_corrupt_legs",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "EXISTS",
                "apex": "0",
                "legs": {"0": "non_existent_mor_XYZ"},
            },
            "expected_rejection": "corrupt legs",
        }
    )

# 33-40: False NOT_ADJOINT on valid adjoint functors
adj_cids = [
    "c049_base_25_adj_id_poset2",
    "c049_base_26_adj_id_poset3",
    "c049_base_27_adj_id_disc2",
    "c049_base_28_adj_galois_2_3",
    "c049_base_29_adj_trivial_1",
    "c049_base_30_adj_id_disc3",
    "c049_base_31_adj_id_poset4",
    "c049_base_32_adj_to_terminal",
]
for i, cid in enumerate(adj_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 33:02d}_false_not_adjoint",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "NOT_ADJOINT",
                "witness": {"type": "HOM_CARDINALITY", "c": "0", "d": "0", "lhs": 9, "rhs": 1},
            },
            "expected_rejection": "false NOT_ADJOINT",
        }
    )

# 41-44: False ADJOINT on non-adjoint functors
no_adj_cids = [
    "c049_base_33_not_adj_card_1_2",
    "c049_base_34_not_adj_card_parallel",
    "c049_base_35_not_adj_reversed_poset",
    "c049_base_36_not_adj_disc_to_linear",
]
for i, cid in enumerate(no_adj_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 41:02d}_false_adjoint",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "ADJOINT",
                "unit": {"0": "id0"},
                "counit": {"0": "id0"},
            },
            "expected_rejection": "false ADJOINT",
        }
    )

# 45-48: Claiming SOLVED on poisoned/invalid categories
poison_cids = [
    "c049_poison_57_non_associative",
    "c049_poison_58_missing_identity",
    "c049_poison_59_unclosed_composition",
    "c049_poison_61_adj_non_assoc_C",
]
for i, cid in enumerate(poison_cids):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 45:02d}_solved_on_poison",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "EXISTS",
                "apex": "0",
                "legs": {},
            },
            "expected_rejection": "claiming SOLVED on invalid category",
        }
    )

assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

for m in mutations:
    fpath = os.path.join(muts_dir, f"{m['mutation_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

print(f"Successfully generated {len(mutations)} hostile mutations in {muts_dir}.")
