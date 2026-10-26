"""Generate 12 public examples for C050 Participant Packet."""

import json
from pathlib import Path

ex_dir = Path(__file__).resolve().parent / "examples"
ex_dir.mkdir(parents=True, exist_ok=True)

examples = [
    # 1. Idempotent involution
    {
        "case_id": "eq_ex_01_involution",
        "axioms": [[["f", ["f", "x"]], "x"]],
        "goal": [["f", ["f", ["f", "a"]]], ["f", "a"]],
    },
    # 2. Idempotent commutativity countermodel
    {
        "case_id": "eq_ex_02_idempotent_comm_countermodel",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    },
    # 3. Double negation / involution identity
    {
        "case_id": "eq_ex_03_double_inv",
        "axioms": [[["i", ["i", "x"]], "x"]],
        "goal": [["i", ["i", ["i", ["i", "a"]]]], "a"],
    },
    # 4. Identity combinator
    {
        "case_id": "eq_ex_04_combinator_I",
        "axioms": [[["I", "x"], "x"]],
        "goal": [["I", ["I", "a"]], "a"],
    },
    # 5. Associative shift
    {
        "case_id": "eq_ex_05_assoc_shift",
        "axioms": [[["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    },
    # 6. Unary projection countermodel
    {
        "case_id": "eq_ex_06_unary_proj_countermodel",
        "axioms": [[["f", "x"], "x"]],
        "goal": [["f", "a"], "b"],
    },
    # 7. Commutative swap
    {
        "case_id": "eq_ex_07_comm_swap",
        "axioms": [[["m", "x", "y"], ["m", "y", "x"]]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    },
    # 8. Left identity with inverse
    {
        "case_id": "eq_ex_08_group_left_id",
        "axioms": [[["m", "e", "x"], "x"], [["m", ["i", "x"], "x"], "e"]],
        "goal": [["m", ["i", "a"], "a"], "e"],
    },
    # 9. Absorption identity in lattice
    {
        "case_id": "eq_ex_09_lattice_absorption",
        "axioms": [[["meet", "x", ["join", "x", "y"]], "x"]],
        "goal": [["meet", "a", ["join", "a", "b"]], "a"],
    },
    # 10. Non-associative magma countermodel
    {
        "case_id": "eq_ex_10_non_assoc_countermodel",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    },
    # 11. Malformed axiom (OUT_OF_SCOPE)
    {
        "case_id": "eq_ex_11_malformed_axiom",
        "axioms": "NOT_A_LIST_OF_EQUATIONS",
        "goal": ["a", "b"],
    },
    # 12. Trivial reflexivity goal
    {"case_id": "eq_ex_12_reflexivity", "axioms": [[["f", "x"], "x"]], "goal": ["a", "a"]},
]

assert len(examples) == 12, f"Expected 12 examples, got {len(examples)}"

for ex in examples:
    fpath = ex_dir / f"{ex['case_id']}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(ex, f, indent=2)

print(f"Generated {len(examples)} public examples in {ex_dir}")
