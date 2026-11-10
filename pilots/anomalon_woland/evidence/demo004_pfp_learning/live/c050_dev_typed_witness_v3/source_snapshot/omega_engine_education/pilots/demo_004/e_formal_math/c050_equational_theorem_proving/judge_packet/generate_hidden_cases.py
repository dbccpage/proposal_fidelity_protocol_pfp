"""Generate 64 hidden evaluation cases for C050: Equational Theorem Proving.
Comprises:
- 26 base theorems (provable by term rewriting)
- 10 base non-theorems (falsifiable by finite countermodels)
- 16 relabel / gauge / symmetry invariance controls
- 12 poisoned cases (malformed syntax or false proof bait)
"""

import json
from pathlib import Path

cases_dir = Path(__file__).resolve().parent / "cases"
cases_dir.mkdir(parents=True, exist_ok=True)

cases = []

# --- 26 Base Theorems ---
# 1-6: Involution and unary operations
cases.append(
    {
        "case_id": "c050_base_01_involution_3",
        "axioms": [[["f", ["f", "x"]], "x"]],
        "goal": [["f", ["f", ["f", "a"]]], ["f", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_02_involution_4",
        "axioms": [[["f", ["f", "x"]], "x"]],
        "goal": [["f", ["f", ["f", ["f", "a"]]]], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_03_negation_double",
        "axioms": [[["neg", ["neg", "x"]], "x"]],
        "goal": [["neg", ["neg", "b"]], "b"],
    }
)
cases.append(
    {
        "case_id": "c050_base_04_combinator_identity_nested",
        "axioms": [[["I", "x"], "x"]],
        "goal": [["I", ["I", ["I", "c"]]], "c"],
    }
)
cases.append(
    {
        "case_id": "c050_base_05_idempotent_unary",
        "axioms": [[["h", ["h", "x"]], ["h", "x"]]],
        "goal": [["h", ["h", ["h", "a"]]], ["h", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_06_two_involutions_commute",
        "axioms": [
            [["f", ["f", "x"]], "x"],
            [["g", ["g", "x"]], "x"],
            [["f", ["g", "x"]], ["g", ["f", "x"]]],
        ],
        "goal": [["f", ["g", ["f", "a"]]], ["g", "a"]],
    }
)

# 7-14: Semigroups and monoids
cases.append(
    {
        "case_id": "c050_base_07_assoc_reassoc_left",
        "axioms": [[["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    }
)
cases.append(
    {
        "case_id": "c050_base_08_assoc_reassoc_right",
        "axioms": [[["m", "x", ["m", "y", "z"]], ["m", ["m", "x", "y"], "z"]]],
        "goal": [["m", "a", ["m", "b", "c"]], ["m", ["m", "a", "b"], "c"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_09_monoid_left_unit",
        "axioms": [[["m", "e", "x"], "x"]],
        "goal": [["m", "e", ["m", "e", "a"]], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_10_monoid_right_unit",
        "axioms": [[["m", "x", "e"], "x"]],
        "goal": [["m", ["m", "a", "e"], "e"], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_11_comm_assoc_swap",
        "axioms": [
            [["m", "x", "y"], ["m", "y", "x"]],
            [["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]],
        ],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_12_idempotent_semigroup_collapse",
        "axioms": [
            [["m", "x", "x"], "x"],
            [["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]],
        ],
        "goal": [["m", "a", "a"], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_13_left_zero",
        "axioms": [[["m", "z", "x"], "z"]],
        "goal": [["m", "z", ["m", "a", "b"]], "z"],
    }
)
cases.append(
    {
        "case_id": "c050_base_14_right_zero",
        "axioms": [[["m", "x", "z"], "z"]],
        "goal": [["m", ["m", "a", "b"], "z"], "z"],
    }
)

# 15-20: Group theory fragments
cases.append(
    {
        "case_id": "c050_base_15_group_left_inv",
        "axioms": [[["m", "e", "x"], "x"], [["m", ["i", "x"], "x"], "e"]],
        "goal": [["m", ["i", "a"], "a"], "e"],
    }
)
cases.append(
    {
        "case_id": "c050_base_16_group_involution_square",
        "axioms": [[["m", "x", "x"], "e"], [["m", "e", "x"], "x"]],
        "goal": [["m", "a", "a"], "e"],
    }
)
cases.append(
    {
        "case_id": "c050_base_17_group_left_cancel_step",
        "axioms": [
            [["m", "e", "x"], "x"],
            [["m", ["i", "x"], "x"], "e"],
            [["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]],
        ],
        "goal": [["m", ["i", "a"], ["m", "a", "b"]], ["m", ["m", ["i", "a"], "a"], "b"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_18_group_triple_product",
        "axioms": [[["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]]],
        "goal": [["m", ["m", ["m", "a", "b"], "c"], "d"], ["m", ["m", "a", "b"], ["m", "c", "d"]]],
    }
)
cases.append(
    {
        "case_id": "c050_base_19_abelian_group_comm_square",
        "axioms": [[["m", "x", "y"], ["m", "y", "x"]]],
        "goal": [["m", ["m", "a", "b"], ["m", "c", "d"]], ["m", ["m", "c", "d"], ["m", "a", "b"]]],
    }
)
cases.append(
    {
        "case_id": "c050_base_20_central_element",
        "axioms": [[["m", "c0", "x"], ["m", "x", "c0"]]],
        "goal": [["m", "c0", ["m", "a", "b"]], ["m", ["m", "a", "b"], "c0"]],
    }
)

# 21-26: Lattices, Boolean fragments & Combinators
cases.append(
    {
        "case_id": "c050_base_21_lattice_meet_absorb",
        "axioms": [[["meet", "x", ["join", "x", "y"]], "x"]],
        "goal": [["meet", "a", ["join", "a", "b"]], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_22_lattice_join_absorb",
        "axioms": [[["join", "x", ["meet", "x", "y"]], "x"]],
        "goal": [["join", "a", ["meet", "a", "b"]], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_23_distributive_left",
        "axioms": [
            [["mul", "x", ["add", "y", "z"]], ["add", ["mul", "x", "y"], ["mul", "x", "z"]]]
        ],
        "goal": [["mul", "a", ["add", "b", "c"]], ["add", ["mul", "a", "b"], ["mul", "a", "c"]]],
    }
)
cases.append(
    {
        "case_id": "c050_base_24_boolean_not_and",
        "axioms": [[["not", ["not", "x"]], "x"], [["and", "x", "x"], "x"]],
        "goal": [["not", ["not", ["and", "a", "a"]]], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_25_combinator_K",
        "axioms": [[["K", "x", "y"], "x"]],
        "goal": [["K", "a", "b"], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_26_combinator_K_nested",
        "axioms": [[["K", "x", "y"], "x"]],
        "goal": [["K", ["K", "a", "b"], "c"], "a"],
    }
)

# --- 10 Base Non-Theorems (Finite Countermodels) ---
cases.append(
    {
        "case_id": "c050_base_27_cm_idempotent_comm",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_28_cm_unary_proj",
        "axioms": [[["f", "x"], "x"]],
        "goal": [["f", "a"], "b"],
    }
)
cases.append(
    {
        "case_id": "c050_base_29_cm_idempotent_assoc",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    }
)
cases.append(
    {
        "case_id": "c050_base_30_cm_left_unit_implies_right",
        "axioms": [[["m", "e", "x"], "x"]],
        "goal": [["m", "a", "e"], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_base_31_cm_left_inv_implies_comm",
        "axioms": [[["m", ["i", "x"], "x"], "e"], [["m", "e", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_32_cm_semigroup_not_comm",
        "axioms": [[["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_33_cm_distributive_not_comm",
        "axioms": [[["m", "x", ["m", "y", "z"]], ["m", ["m", "x", "y"], ["m", "x", "z"]]]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_base_34_cm_constant_swap",
        "axioms": [[["f", "x"], "c0"]],
        "goal": [["f", "a"], "b"],
    }
)
cases.append(
    {
        "case_id": "c050_base_35_cm_left_zero_not_right_zero",
        "axioms": [[["m", "z", "x"], "z"]],
        "goal": [["m", "a", "z"], "z"],
    }
)
cases.append(
    {
        "case_id": "c050_base_36_cm_projection_not_equal",
        "axioms": [[["pi1", "x", "y"], "x"]],
        "goal": [["pi1", "a", "b"], "b"],
    }
)

# --- 16 Relabel / Gauge / Symmetry Invariance Controls ---
for i in range(1, 9):
    # Relabel symbol names in base theorems 1..8
    b_case = cases[i - 1]
    cases.append(
        {
            "case_id": f"c050_gauge_{36 + i:02d}_relabel_sym_{i}",
            "axioms": b_case["axioms"],
            "goal": [b_case["goal"][1], b_case["goal"][0]],  # Reoriented symmetry goal
        }
    )

for i in range(1, 9):
    # Reoriented axioms in base theorems 9..16
    b_case = cases[8 + i - 1]
    reoriented_axioms = [[ax[1], ax[0]] for ax in b_case["axioms"]]
    cases.append(
        {
            "case_id": f"c050_gauge_{44 + i:02d}_reorient_ax_{i}",
            "axioms": reoriented_axioms,
            "goal": b_case["goal"],
        }
    )

# --- 12 Poisoned Cases ---
# 53-56: Non-theorems with misleading proof notes
cases.append(
    {
        "case_id": "c050_poison_53_fake_note_comm",
        "note": "Proven in Robbins algebra: idempotency universally implies commutativity.",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)
cases.append(
    {
        "case_id": "c050_poison_54_fake_note_assoc",
        "note": "Known theorem: left unit guarantees associativity in all finite magmas.",
        "axioms": [[["m", "e", "x"], "x"]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    }
)
cases.append(
    {
        "case_id": "c050_poison_55_fake_note_unit",
        "note": "Trivial deduction: left unit is universally equal to right unit.",
        "axioms": [[["m", "e", "x"], "x"]],
        "goal": [["m", "a", "e"], "a"],
    }
)
cases.append(
    {
        "case_id": "c050_poison_56_fake_note_inv",
        "note": "Standard textbook lemma: left inverse commutes with all elements.",
        "axioms": [[["m", ["i", "x"], "x"], "e"], [["m", "e", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    }
)

# 57-60: Malformed inputs -> OUT_OF_SCOPE
cases.append(
    {"case_id": "c050_poison_57_malformed_axiom_type", "axioms": "NOT_A_LIST", "goal": ["a", "b"]}
)
cases.append(
    {
        "case_id": "c050_poison_58_malformed_equation_length",
        "axioms": [[["f", "x"]]],  # Missing right-hand side
        "goal": ["a", "b"],
    }
)
cases.append(
    {
        "case_id": "c050_poison_59_malformed_goal_type",
        "axioms": [[["f", "x"], "x"]],
        "goal": "NOT_A_PAIR",
    }
)
cases.append(
    {
        "case_id": "c050_poison_60_malformed_goal_triple",
        "axioms": [[["f", "x"], "x"]],
        "goal": ["a", "b", "c"],
    }
)

# 61-64: More non-theorems with deceptive structure
cases.append(
    {
        "case_id": "c050_poison_61_fake_comm_three_vars",
        "axioms": [[["m", "x", "y"], ["m", "x", "z"]]],  # degenerate axiom
        "goal": [["m", "a", "b"], "c"],
    }
)
cases.append(
    {
        "case_id": "c050_poison_62_fake_distributive",
        "axioms": [[["f", "x"], "x"]],
        "goal": [["f", ["m", "a", "b"]], ["m", ["f", "b"], ["f", "a"]]],
    }
)
cases.append(
    {"case_id": "c050_poison_63_malformed_nested_int", "axioms": 12345, "goal": ["a", "b"]}
)
cases.append(
    {"case_id": "c050_poison_64_malformed_axiom_entry_none", "axioms": [None], "goal": ["a", "b"]}
)

assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"

for c in cases:
    fpath = cases_dir / f"{c['case_id']}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

print(f"Generated {len(cases)} hidden evaluation cases in {cases_dir}")
