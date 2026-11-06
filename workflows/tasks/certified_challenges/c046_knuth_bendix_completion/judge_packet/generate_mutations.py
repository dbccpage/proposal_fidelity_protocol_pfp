# AuthorityEffect: None.
"""
Hostile Checker Mutation Generator for C046 (Knuth-Bendix Completion).
Generates 48 hostile mutated outputs designed to test whether dual checkers
kill 100% of corrupt, non-confluent, ordering-violating, or deceptive outputs.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_repo_root = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c046_knuth_bendix_completion.reference_solver.solver import (
    solve,
)


def generate_mutations() -> List[Dict[str, Any]]:
    hidden_file = Path(__file__).resolve().parent / "hidden_cases" / "c046_hidden_cases_64.json"
    with open(hidden_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    mutations: List[Dict[str, Any]] = []

    complete_cases = [
        c for c in cases if c.get("task") == "COMPLETE" and c.get("category") == "base_hidden"
    ]
    confluence_cases = [
        c
        for c in cases
        if c.get("task") == "CHECK_CONFLUENCE" and c.get("category") == "base_hidden"
    ]
    reduce_cases = [
        c for c in cases if c.get("task") == "REDUCE" and c.get("category") == "base_hidden"
    ]
    poison_cases = [c for c in cases if c.get("category") == "poisoned"]

    # 1. Perturbed case ID (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        ans["case_id"] = "corrupted_id"
        mutations.append(
            {
                "mutation_id": f"mut_bad_case_id_{i:02d}",
                "type": "METADATA_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 2. Rule violating term order (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        rules = list(ans["rules"])
        # Add non-terminating rule: x -> f(x)
        rules.append({"lhs": "x", "rhs": "mul(e, x)"})
        ans["rules"] = rules
        ans["rules_count"] = len(rules)
        mutations.append(
            {
                "mutation_id": f"mut_order_violation_{i:02d}",
                "type": "ORDER_VIOLATION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 3. Unbound variable on RHS (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        rules = list(ans["rules"])
        rules.append({"lhs": "f(x)", "rhs": "g(x, y)"})
        ans["rules"] = rules
        ans["rules_count"] = len(rules)
        mutations.append(
            {
                "mutation_id": f"mut_unbound_rhs_var_{i:02d}",
                "type": "UNBOUND_RHS_VARIABLE",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 4. Rules count mismatch (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        ans["rules_count"] = ans["rules_count"] + 5
        mutations.append(
            {
                "mutation_id": f"mut_rules_count_mismatch_{i:02d}",
                "type": "COUNT_MISMATCH",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 5. Non-confluent rule omission (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        # Drop half the rules, making it non-confluent
        ans["rules"] = ans["rules"][:2]
        ans["rules_count"] = len(ans["rules"])
        mutations.append(
            {
                "mutation_id": f"mut_non_confluent_omission_{i:02d}",
                "type": "NON_CONFLUENT_TRUNCATION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 6. Swapped confluence verdict (4 mutations)
    for i in range(4):
        c = confluence_cases[i]
        ans = solve(c)
        ans["is_confluent"] = not ans["is_confluent"]
        mutations.append(
            {
                "mutation_id": f"mut_swapped_confluence_{i:02d}",
                "type": "CONFLUENCE_VERDICT_FLIP",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 7. Wrong normal form in REDUCE (4 mutations)
    for i in range(4):
        c = reduce_cases[i]
        ans = solve(c)
        ans["normal_form"] = "wrong_bogus_normal_form"
        mutations.append(
            {
                "mutation_id": f"mut_wrong_normal_form_{i:02d}",
                "type": "REDUCTION_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 8. Unreduced normal form in REDUCE (4 mutations)
    for i in range(4):
        c = reduce_cases[i + 4]
        ans = solve(c)
        ans["normal_form"] = c["term"]  # Unreduced original term
        mutations.append(
            {
                "mutation_id": f"mut_unreduced_term_{i:02d}",
                "type": "UNREDUCED_TERM_AS_NORMAL_FORM",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 9. Refusal stripped of reason (4 mutations)
    for i in range(4):
        c = poison_cases[i]
        ans = solve(c)
        ans.pop("reason", None)
        mutations.append(
            {
                "mutation_id": f"mut_stripped_reason_{i:02d}",
                "type": "REFUSAL_WITNESS_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 10. Refusal stripped of witness (4 mutations)
    for i in range(4):
        c = poison_cases[i + 4]
        ans = solve(c)
        ans.pop("witness", None)
        mutations.append(
            {
                "mutation_id": f"mut_stripped_witness_{i:02d}",
                "type": "REFUSAL_WITNESS_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 11. Malformed rule dictionary (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        rules = list(ans["rules"])
        rules[0] = {"bogus_key": "val"}
        ans["rules"] = rules
        mutations.append(
            {
                "mutation_id": f"mut_malformed_rule_dict_{i:02d}",
                "type": "SCHEMA_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 12. Bogus DDC operation (4 mutations)
    for i in range(4):
        c = complete_cases[i]
        ans = solve(c)
        trace = ans.get("ddc_trace", {})
        steps = list(trace.get("steps", []))
        steps.append({"op": "ILLEGAL_OP", "detail": "corrupted step"})
        trace["steps"] = steps
        ans["ddc_trace"] = trace
        mutations.append(
            {
                "mutation_id": f"mut_bogus_ddc_op_{i:02d}",
                "type": "DDC_ALPHABET_VIOLATION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"
    return mutations


def main():
    mutations = generate_mutations()
    out_dir = Path(__file__).resolve().parent / "mutation_suite"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "c046_hostile_mutations_48.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mutations, f, indent=2)
    print(f"Generated {len(mutations)} hostile mutations in {out_file}")


if __name__ == "__main__":
    main()
