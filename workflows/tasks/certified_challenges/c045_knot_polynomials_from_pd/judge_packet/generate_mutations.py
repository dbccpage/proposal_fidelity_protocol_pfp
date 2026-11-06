# AuthorityEffect: None.
"""
Hostile Checker Mutation Generator for C045.
Generates 48 hostile mutated outputs designed to test whether dual checkers
kill 100% of corrupt, unnormalized, or deceptive outputs.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

_repo_root = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c045_knot_polynomials_from_pd.reference_solver.solver import (
    solve,
)


def generate_mutations() -> List[Dict[str, Any]]:
    hidden_file = Path(__file__).resolve().parent / "hidden_cases" / "c045_hidden_cases_64.json"
    with open(hidden_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    mutations: List[Dict[str, Any]] = []

    # Filter base compute, identify, compare, and refusal cases
    compute_cases = [
        c
        for c in cases
        if c.get("task") == "COMPUTE_POLYNOMIALS" and c.get("category") == "base_hidden"
    ]
    identify_cases = [
        c for c in cases if c.get("task") == "IDENTIFY" and c.get("category") == "base_hidden"
    ]
    compare_cases = [
        c for c in cases if c.get("task") == "COMPARE" and c.get("category") == "base_hidden"
    ]
    poison_cases = [c for c in cases if c.get("category") == "poisoned"]

    # 1. Perturbed case ID (4 mutations)
    for i in range(4):
        c = compute_cases[i]
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

    # 2. Perturbed writhe (4 mutations)
    for i in range(4):
        c = compute_cases[i]
        ans = solve(c)
        ans["writhe"] = ans["writhe"] + 1
        mutations.append(
            {
                "mutation_id": f"mut_perturbed_writhe_{i:02d}",
                "type": "WRITHE_PERTURBATION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 3. Unnormalized Jones polynomial (4 mutations)
    for i in range(4):
        c = compute_cases[i]
        ans = solve(c)
        jp = dict(ans["jones_polynomial"])
        first_k = next(iter(jp.keys()))
        jp[first_k] += 1
        ans["jones_polynomial"] = jp
        mutations.append(
            {
                "mutation_id": f"mut_unnormalized_jones_{i:02d}",
                "type": "JONES_NORMALIZATION_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 4. Asymmetric Alexander polynomial (4 mutations)
    for i in range(4):
        c = compute_cases[i]
        ans = solve(c)
        al = dict(ans["alexander_polynomial"])
        al["99"] = 1  # Add asymmetric term
        ans["alexander_polynomial"] = al
        mutations.append(
            {
                "mutation_id": f"mut_asymmetric_alex_{i:02d}",
                "type": "ALEXANDER_SYMMETRY_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 5. Alexander polynomial unnormalized at t=1 (4 mutations)
    for i in range(4):
        c = compute_cases[i]
        ans = solve(c)
        al = dict(ans["alexander_polynomial"])
        al["0"] = al.get("0", 0) + 2  # Breaks Delta(1) = 1
        ans["alexander_polynomial"] = al
        mutations.append(
            {
                "mutation_id": f"mut_unnormalized_alex_{i:02d}",
                "type": "ALEXANDER_EVAL1_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 6. Wrong knot identification (4 mutations)
    for i in range(4):
        c = identify_cases[i]
        ans = solve(c)
        ans["identified_knot"] = "fake_knot_99_99"
        mutations.append(
            {
                "mutation_id": f"mut_fake_knot_id_{i:02d}",
                "type": "CATALOG_MISIDENTIFICATION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 7. Inverted chirality (4 mutations)
    for i in range(4):
        c = identify_cases[i]
        ans = solve(c)
        ans["chirality"] = (
            "LEFT_HANDED" if ans.get("chirality") == "RIGHT_HANDED" else "RIGHT_HANDED"
        )
        mutations.append(
            {
                "mutation_id": f"mut_inverted_chirality_{i:02d}",
                "type": "CHIRALITY_INVERSION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 8. Swapped compare kind (4 mutations)
    for i in range(4):
        c = compare_cases[i]
        ans = solve(c)
        orig_kind = ans["kind"]
        ans["kind"] = (
            "SAME_INVARIANTS" if orig_kind == "DIFFERENT_INVARIANTS" else "DIFFERENT_INVARIANTS"
        )
        mutations.append(
            {
                "mutation_id": f"mut_swapped_cmp_kind_{i:02d}",
                "type": "COMPARE_KIND_FLIP",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 9. Identical values on separating invariant (4 mutations)
    for i in range(4):
        c = compare_cases[i]
        ans = solve(c)
        if ans["kind"] == "DIFFERENT_INVARIANTS":
            ans["val_2"] = ans["val_1"]
        else:
            ans["kind"] = "DIFFERENT_INVARIANTS"
            ans["separating_invariant"] = "jones_polynomial"
            ans["val_1"] = {"0": 1}
            ans["val_2"] = {"0": 1}
        mutations.append(
            {
                "mutation_id": f"mut_fake_separating_inv_{i:02d}",
                "type": "IDENTICAL_SEPARATING_VALUES",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 10. Refusal stripped of reason (4 mutations)
    for i in range(4):
        c = poison_cases[i]
        ans = solve(c)
        ans.pop("reason", None)
        mutations.append(
            {
                "mutation_id": f"mut_stripped_refusal_reason_{i:02d}",
                "type": "REFUSAL_WITNESS_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 11. Refusal stripped of witness (4 mutations)
    for i in range(4):
        c = poison_cases[i + 4]
        ans = solve(c)
        ans.pop("witness", None)
        mutations.append(
            {
                "mutation_id": f"mut_stripped_refusal_witness_{i:02d}",
                "type": "REFUSAL_WITNESS_CORRUPTION",
                "case": c,
                "corrupted_ans": ans,
            }
        )

    # 12. Bogus DDC operational step (4 mutations)
    for i in range(4):
        c = compute_cases[i]
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
    os.makedirs(out_dir, exist_ok=True)
    out_file = out_dir / "c045_hostile_mutations_48.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mutations, f, indent=2)
    print(f"Generated {len(mutations)} hostile mutations in {out_file}")


if __name__ == "__main__":
    main()
