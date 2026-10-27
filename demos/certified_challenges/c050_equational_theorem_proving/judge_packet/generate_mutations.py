"""Generate 48 hostile mutations for C050: Equational Theorem Proving.
Stress-tests exact_checker and independent_checker against invalid rewrite steps and fake countermodels.
"""

import json
from pathlib import Path

cases_dir = Path(__file__).resolve().parent / "cases"
muts_dir = Path(__file__).resolve().parent / "hostile_mutations"
muts_dir.mkdir(parents=True, exist_ok=True)

# Load base cases
base_cases = {}
for p in cases_dir.glob("*.json"):
    with open(p, "r", encoding="utf-8") as f:
        c = json.load(f)
        base_cases[c["case_id"]] = c

mutations = []

# 1-6: Step at invalid position
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_02_involution_4",
        "c050_base_03_negation_double",
        "c050_base_04_combinator_identity_nested",
        "c050_base_05_idempotent_unary",
        "c050_base_07_assoc_reassoc_left",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 1:02d}_invalid_position",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "steps": [
                    {
                        "axiom": 0,
                        "dir": "lr",
                        "pos": [99, 99],  # Out of bounds position
                        "subst": {"x": "a"},
                        "result": "a",
                    }
                ],
            },
            "expected_rejection": "invalid position",
        }
    )

# 7-12: Non-matching substitution
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_02_involution_4",
        "c050_base_03_negation_double",
        "c050_base_04_combinator_identity_nested",
        "c050_base_05_idempotent_unary",
        "c050_base_07_assoc_reassoc_left",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 7:02d}_bad_substitution",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "steps": [
                    {
                        "axiom": 0,
                        "dir": "lr",
                        "pos": [],
                        "subst": {"x": "WRONG_TERM_VARIABLE"},  # Subterm does not match
                        "result": "WRONG_RESULT",
                    }
                ],
            },
            "expected_rejection": "pattern mismatch",
        }
    )

# 13-18: Claimed step result does not match computed replacement
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_03_negation_double",
        "c050_base_04_combinator_identity_nested",
        "c050_base_05_idempotent_unary",
        "c050_base_09_monoid_left_unit",
        "c050_base_10_monoid_right_unit",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 13:02d}_forged_step_result",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "steps": [
                    {
                        "axiom": 0,
                        "dir": "lr",
                        "pos": [0],
                        "subst": {"x": "a"},
                        "result": "TAMPERED_RESULT_NOT_MATCHING",  # Tampered result
                    }
                ],
            },
            "expected_rejection": "result mismatch",
        }
    )

# 19-24: Skipped step (unjustified jump in rewrite chain)
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_02_involution_4",
        "c050_base_03_negation_double",
        "c050_base_04_combinator_identity_nested",
        "c050_base_05_idempotent_unary",
        "c050_base_07_assoc_reassoc_left",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 19:02d}_skipped_step_jump",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "steps": [],  # Empty steps claiming immediate goal
            },
            "expected_rejection": "proof incomplete",
        }
    )

# 25-30: Proof ends at wrong term
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_02_involution_4",
        "c050_base_03_negation_double",
        "c050_base_04_combinator_identity_nested",
        "c050_base_05_idempotent_unary",
        "c050_base_07_assoc_reassoc_left",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 25:02d}_wrong_goal_rhs",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "steps": [
                    {
                        "axiom": 0,
                        "dir": "lr",
                        "pos": [],
                        "subst": {"x": "a"},
                        "result": "SOME_DIFFERENT_TERM",
                    }
                ],
            },
            "expected_rejection": "chain ended at wrong term",
        }
    )

# 31-36: Fake countermodel where goal actually holds
for i, cid in enumerate(
    [
        "c050_base_27_cm_idempotent_comm",
        "c050_base_28_cm_unary_proj",
        "c050_base_29_cm_idempotent_assoc",
        "c050_base_30_cm_left_unit_implies_right",
        "c050_base_31_cm_left_inv_implies_comm",
        "c050_base_32_cm_semigroup_not_comm",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 31:02d}_countermodel_goal_holds",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "COUNTERMODEL",
                "size": 1,  # Trivial 1-element model where every equation holds
                "tables": {"m": [[0]], "f": [0], "i": [0]},
                "assignment": {"a": 0, "b": 0, "c": 0},
            },
            "expected_rejection": "goal holds in countermodel",
        }
    )

# 37-42: Countermodel violating size bounds
for i, cid in enumerate(
    [
        "c050_base_27_cm_idempotent_comm",
        "c050_base_28_cm_unary_proj",
        "c050_base_29_cm_idempotent_assoc",
        "c050_base_30_cm_left_unit_implies_right",
        "c050_base_31_cm_left_inv_implies_comm",
        "c050_base_32_cm_semigroup_not_comm",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 37:02d}_countermodel_size_out_of_bounds",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "COUNTERMODEL",
                "size": 99,  # Domain size out of bounds (max 8)
                "tables": {"m": []},
                "assignment": {},
            },
            "expected_rejection": "size out of bounds",
        }
    )

# 43-48: False OUT_OF_SCOPE on valid problem
for i, cid in enumerate(
    [
        "c050_base_01_involution_3",
        "c050_base_02_involution_4",
        "c050_base_07_assoc_reassoc_left",
        "c050_base_11_comm_assoc_swap",
        "c050_base_27_cm_idempotent_comm",
        "c050_base_28_cm_unary_proj",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 43:02d}_false_out_of_scope",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "OUT_OF_SCOPE",
                "witness": "FALSE_OUT_OF_SCOPE_ON_VALID_CASE",
            },
            "expected_rejection": "false OUT_OF_SCOPE",
        }
    )

assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

for m in mutations:
    fpath = muts_dir / f"{m['mutation_id']}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

print(f"Generated {len(mutations)} hostile mutations in {muts_dir}")
