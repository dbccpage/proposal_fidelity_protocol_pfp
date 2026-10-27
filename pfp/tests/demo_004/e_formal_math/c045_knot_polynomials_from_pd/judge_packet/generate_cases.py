# AuthorityEffect: None.
"""
Hidden Case Generator for C045.
Generates 64 evaluation cases:
- 40 base hidden cases across tasks (COMPUTE_POLYNOMIALS, IDENTIFY, COMPARE)
- 16 relabel / gauge invariance cases (crossing permutations, cyclic shifts)
- 8 poisoned schema-valid cases (non-planar, broken multiplicity, multiple components, bad orientation)
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.reference_solver.knots_catalog import (
    CANONICAL_KNOTS,
)


def shift_edges(pd: List[List[int]], shift: int) -> List[List[int]]:
    if not pd:
        return []
    n = len(pd)
    n2 = 2 * n
    return [[((e - 1 + shift) % n2) + 1 for e in c] for c in pd]


def permute_crossings(pd: List[List[int]], seed: int) -> List[List[int]]:
    if not pd:
        return []
    res = [list(c) for c in pd]
    rng = random.Random(seed)
    rng.shuffle(res)
    return res


def generate_all_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    # 1. Base hidden cases (40 cases)
    # Tasks: COMPUTE_POLYNOMIALS, IDENTIFY, COMPARE
    base_knots = list(
        CANONICAL_KNOTS.keys()
    )  # 9 knots: 0_1, 3_1, 4_1, 5_1, 5_2, 6_1, 6_2, 6_3, 7_1

    # 9 COMPUTE_POLYNOMIALS
    for idx, kid in enumerate(base_knots):
        cases.append(
            {
                "case_id": f"c045_base_compute_{idx:02d}_{kid}",
                "task": "COMPUTE_POLYNOMIALS",
                "pd": CANONICAL_KNOTS[kid]["pd"],
                "category": "base_hidden",
            }
        )

    # 9 IDENTIFY
    for idx, kid in enumerate(base_knots):
        cases.append(
            {
                "case_id": f"c045_base_identify_{idx:02d}_{kid}",
                "task": "IDENTIFY",
                "pd": CANONICAL_KNOTS[kid]["pd"],
                "category": "base_hidden",
            }
        )

    # 22 COMPARE cases
    cmp_pairs = [
        ("3_1", "4_1"),
        ("3_1", "5_1"),
        ("4_1", "5_2"),
        ("5_1", "5_2"),
        ("6_1", "6_2"),
        ("6_1", "6_3"),
        ("6_2", "6_3"),
        ("7_1", "3_1"),
        ("7_1", "5_1"),
        ("0_1", "3_1"),
        ("0_1", "4_1"),
        # Identical comparisons
        ("0_1", "0_1"),
        ("3_1", "3_1"),
        ("4_1", "4_1"),
        ("5_1", "5_1"),
        ("5_2", "5_2"),
        ("6_1", "6_1"),
        ("6_2", "6_2"),
        ("6_3", "6_3"),
        ("7_1", "7_1"),
        ("4_1", "6_3"),
        ("5_1", "7_1"),
    ]
    for idx, (k1, k2) in enumerate(cmp_pairs):
        cases.append(
            {
                "case_id": f"c045_base_compare_{idx:02d}_{k1}_vs_{k2}",
                "task": "COMPARE",
                "pd_1": CANONICAL_KNOTS[k1]["pd"],
                "pd_2": CANONICAL_KNOTS[k2]["pd"],
                "category": "base_hidden",
            }
        )

    assert len(cases) == 40, f"Expected 40 base cases, got {len(cases)}"

    # 2. Relabel / Gauge Invariance cases (16 cases)
    gauge_cases = [
        ("3_1", 2, 42),
        ("3_1", 4, 101),
        ("4_1", 1, 99),
        ("4_1", 3, 202),
        ("5_1", 2, 7),
        ("5_1", 5, 88),
        ("5_2", 3, 13),
        ("5_2", 7, 55),
        ("6_1", 2, 33),
        ("6_1", 4, 77),
        ("6_2", 1, 19),
        ("6_2", 5, 61),
        ("6_3", 3, 44),
        ("6_3", 6, 82),
        ("7_1", 2, 11),
        ("7_1", 7, 95),
    ]
    for idx, (kid, shift, seed) in enumerate(gauge_cases):
        orig_pd = CANONICAL_KNOTS[kid]["pd"]
        gauged_pd = permute_crossings(shift_edges(orig_pd, shift), seed)
        cases.append(
            {
                "case_id": f"c045_gauge_{idx:02d}_{kid}_s{shift}_p{seed}",
                "task": "COMPARE",
                "pd_1": orig_pd,
                "pd_2": gauged_pd,
                "category": "relabel_gauge",
            }
        )

    assert len(cases) == 56, f"Expected 56 cases, got {len(cases)}"

    # 3. Poisoned schema-valid cases (8 cases)
    poisoned_definitions = [
        {
            "case_id": "c045_poison_01_bad_multiplicity",
            "task": "COMPUTE_POLYNOMIALS",
            "pd": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 9]],
            "expected_reason": "EDGE_LABEL_MULTIPLICITY",
        },
        {
            "case_id": "c045_poison_02_label_out_of_range",
            "task": "COMPUTE_POLYNOMIALS",
            "pd": [[1, 7, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
            "expected_reason": "EDGE_LABEL_MULTIPLICITY",
        },
        {
            "case_id": "c045_poison_03_two_components",
            "task": "COMPUTE_POLYNOMIALS",
            # Two unlinked loops: crossings form two separate cycles
            "pd": [[1, 2, 3, 4], [3, 4, 1, 2]],
            "expected_reason": "ORIENTATION_INCONSISTENT",
        },
        {
            "case_id": "c045_poison_04_inconsistent_understrand",
            "task": "COMPUTE_POLYNOMIALS",
            # understrand incoming is 1, outgoing is 4 instead of 2
            "pd": [[1, 5, 4, 2], [3, 1, 4, 6], [5, 3, 6, 2]],
            "expected_reason": "ORIENTATION_INCONSISTENT",
        },
        {
            "case_id": "c045_poison_05_inconsistent_overstrand",
            "task": "COMPUTE_POLYNOMIALS",
            # overstrand edges 3, 5 do not connect consecutively
            "pd": [[1, 3, 2, 5], [3, 1, 4, 6], [5, 2, 6, 4]],
            "expected_reason": "ORIENTATION_INCONSISTENT",
        },
        {
            "case_id": "c045_poison_06_non_planar_twist",
            "task": "COMPUTE_POLYNOMIALS",
            # K_5 non-planar topology on 4 crossings
            "pd": [[1, 6, 2, 8], [3, 8, 4, 2], [5, 2, 6, 4], [7, 4, 8, 6]],
            "expected_reason": "ORIENTATION_INCONSISTENT",
        },
        {
            "case_id": "c045_poison_07_compare_poison_first",
            "task": "COMPARE",
            "pd_1": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 9]],
            "pd_2": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
            "expected_reason": "PD_1_EDGE_LABEL_MULTIPLICITY",
        },
        {
            "case_id": "c045_poison_08_compare_poison_second",
            "task": "COMPARE",
            "pd_1": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
            "pd_2": [[1, 7, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
            "expected_reason": "PD_2_EDGE_LABEL_MULTIPLICITY",
        },
    ]
    for p in poisoned_definitions:
        p["category"] = "poisoned"
        cases.append(p)

    assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"
    return cases


def main():
    cases = generate_all_cases()
    out_dir = os.path.join(os.path.dirname(__file__), "hidden_cases")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "c045_hidden_cases_64.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    print(f"Generated {len(cases)} hidden cases in {out_file}")


if __name__ == "__main__":
    main()
