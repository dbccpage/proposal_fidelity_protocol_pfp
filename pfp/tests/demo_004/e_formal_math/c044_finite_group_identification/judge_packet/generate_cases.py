# AuthorityEffect: None.
"""
Judge Packet Case and Mutation Suite Generator for C044.
Generates 64 hidden cases (40 base, 16 relabel/gauge, 8 poisoned) and 48 hostile mutations.
"""

import json
import random
from pathlib import Path

from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.catalog.build_catalog import (
    build_catalog_database,
)


def generate():
    catalog = build_catalog_database()
    base_dir = Path(__file__).resolve().parent
    cases_dir = base_dir / "hidden_cases"
    mut_dir = base_dir / "mutation_suite"
    cases_dir.mkdir(parents=True, exist_ok=True)
    mut_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(4444)
    hidden_cases = []

    # 1. 40 Base cases (24 IDENTIFY, 16 COMPARE)
    # Order 32 & 64 groups included (at least 12)
    # Identify cases:
    # Small orders: C1, C2, C3, C4, V4, S3, C6, C8, D8, Q8, C9, D10, A4, D12, C16, D16, QD16, Q16, F20, S4, Heis3
    # Order 32: C32, C16xC2, D32, C8xC4, C4xC4xC2, C2^5
    # Order 60: A5
    # Order 64: C64, D64, C4^3, C2^6

    identify_targets = [
        # Small / intermediate orders (12 cases)
        [1, 1],
        [3, 1],
        [4, 1],
        [4, 2],
        [6, 1],
        [8, 3],
        [8, 4],
        [9, 2],
        [10, 1],
        [12, 3],
        [16, 7],
        [27, 3],
        # Order 32 and 64 orders (12 cases)
        [32, 1],
        [32, 16],
        [32, 18],
        [32, 21],
        [32, 45],
        [32, 51],
        [60, 5],
        [64, 1],
        [64, 52],
        [64, 182],
        [64, 267],
        [24, 12],
    ]

    for idx, rep_id in enumerate(identify_targets):
        cid = f"c044_hid_base_{idx + 1:02d}"
        rep = next(r for r in catalog if r["id"] == rep_id)
        # Presentation: use table for some, perm generators for others
        n = rep["order"]
        case = {
            "case_id": cid,
            "task": "IDENTIFY",
            "presentation": "table",
            "order": n,
            "table": rep["table"],
            "rep_id_expected": rep_id,
            "note": f"Base IDENTIFY case for {rep['name']}",
        }
        hidden_cases.append(case)

    # 16 COMPARE cases
    compare_pairs = [
        # (rep1, rep2, isomorphic)
        ([4, 1], [4, 2], False),
        ([8, 3], [8, 4], False),
        ([8, 1], [8, 2], False),
        ([12, 3], [12, 4], False),
        ([16, 1], [16, 2], False),
        ([16, 7], [16, 9], False),
        ([16, 7], [16, 8], False),
        ([27, 1], [27, 3], False),
        ([32, 1], [32, 18], False),
        ([32, 16], [32, 21], False),
        ([64, 1], [64, 52], False),
        ([64, 182], [64, 267], False),
        # Isomorphic pairs (using different table orderings)
        ([6, 1], [6, 1], True),
        ([8, 4], [8, 4], True),
        ([12, 3], [12, 3], True),
        ([32, 51], [32, 51], True),
    ]

    for c_idx, (r1_id, r2_id, is_iso) in enumerate(compare_pairs):
        cid = f"c044_hid_base_{len(hidden_cases) + 1:02d}"
        r1 = next(r for r in catalog if r["id"] == r1_id)
        r2 = next(r for r in catalog if r["id"] == r2_id)
        case = {
            "case_id": cid,
            "task": "COMPARE",
            "G": {"presentation": "table", "order": r1["order"], "table": r1["table"]},
            "H": {"presentation": "table", "order": r2["order"], "table": r2["table"]},
            "is_isomorphic_expected": is_iso,
            "note": f"Base COMPARE case {r1['name']} vs {r2['name']}",
        }
        hidden_cases.append(case)

    assert len(hidden_cases) == 40, f"Expected 40 base cases, got {len(hidden_cases)}"

    # 2. 16 Relabel / Gauge Controls
    # Conjugate elements, permute table labels (fixing 0)
    for g_idx in range(16):
        cid = f"c044_hid_gauge_{g_idx + 1:02d}"
        # Pick a base case from identify targets
        rep_id = identify_targets[g_idx % len(identify_targets)]
        rep = next(r for r in catalog if r["id"] == rep_id)
        n = rep["order"]

        # Random permutation fixing 0
        perm = [0] + rng.sample(range(1, n), n - 1)
        inv_p = [0] * n
        for i, x in enumerate(perm):
            inv_p[x] = i

        # Conjugate table: T'[perm[i]][perm[j]] = perm[T[i][j]]
        relabel_table = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                relabel_table[perm[i]][perm[j]] = perm[rep["table"][i][j]]

        case = {
            "case_id": cid,
            "task": "IDENTIFY",
            "presentation": "table",
            "order": n,
            "table": relabel_table,
            "rep_id_expected": rep_id,
            "gauge_perm": perm,
            "note": f"Relabelled gauge control for {rep['name']}",
        }
        hidden_cases.append(case)

    assert len(hidden_cases) == 56

    # 3. 8 Poisoned Cases
    # Non-associative quasigroup
    p1 = {
        "case_id": "c044_hid_poison_01",
        "task": "IDENTIFY",
        "presentation": "table",
        "order": 5,
        "table": [
            [0, 1, 2, 3, 4],
            [1, 2, 0, 4, 3],
            [2, 0, 1, 3, 4],
            [3, 4, 3, 1, 2],
            [4, 3, 4, 2, 1],
        ],
        "poison_type": "NON_ASSOCIATIVE",
    }

    p2 = {
        "case_id": "c044_hid_poison_02",
        "task": "IDENTIFY",
        "presentation": "table",
        "order": 4,
        "table": [
            [0, 1, 2, 3],
            [1, 0, 3, 2],
            [2, 3, 0, 1],
            [3, 1, 2, 0],  # Non-associative: (1*2)*1 = 3*1 = 1 != 1*(2*1) = 1*3 = 2
        ],
        "poison_type": "NOT_ASSOCIATIVE",
    }

    p3 = {
        "case_id": "c044_hid_poison_03",
        "task": "IDENTIFY",
        "presentation": "perm",
        "degree": 6,
        "gens": [[1, 2, 3, 4, 5, 0], [1, 0, 2, 3, 4, 5]],  # S6: 720 > 64 elements
        "poison_type": "EXCEEDS_MAX_ORDER",
    }

    p4 = {
        "case_id": "c044_hid_poison_04",
        "task": "COMPARE",
        "G": {"presentation": "table", "order": 8, "table": catalog[8]["table"]},  # D8
        "H": {"presentation": "table", "order": 8, "table": catalog[9]["table"]},  # Q8
        "note": "Claimed isomorphic in user note but actually not isomorphic",
        "poison_type": "DANGER_NOTE_FALSE_ISOMORPHISM",
    }

    p5 = {
        "case_id": "c044_hid_poison_05",
        "task": "IDENTIFY",
        "presentation": "table",
        "order": 3,
        "table": [[0, 1, 2], [1, 2, 0], [2, 2, 1]],
        "poison_type": "MISSING_INVERSE",
    }

    p6 = {
        "case_id": "c044_hid_poison_06",
        "task": "IDENTIFY",
        "presentation": "perm",
        "degree": 4,
        "gens": [[0, 1, 2, 3], [1, 2, 3, 0]],  # includes identity generator
        "poison_type": "IDENTITY_IN_GENS",
    }

    p7 = {
        "case_id": "c044_hid_poison_07",
        "task": "COMPARE",
        "G": {
            "presentation": "table",
            "order": 16,
            "table": next(r["table"] for r in catalog if r["id"] == [16, 7]),
        },  # D16
        "H": {
            "presentation": "table",
            "order": 16,
            "table": next(r["table"] for r in catalog if r["id"] == [16, 8]),
        },  # QD16
        "note": "Agree on center order 2 and derived order 4, but non-isomorphic",
        "poison_type": "PARTIAL_INVARIANT_MATCH",
    }

    p8 = {
        "case_id": "c044_hid_poison_08",
        "task": "IDENTIFY",
        "presentation": "perm",
        "degree": 7,
        "gens": [[1, 2, 3, 4, 5, 6, 0], [1, 0, 2, 3, 4, 5, 6]],  # S7: 5040 elements
        "poison_type": "EXCEEDS_MAX_ORDER",
    }

    hidden_cases.extend([p1, p2, p3, p4, p5, p6, p7, p8])
    assert len(hidden_cases) == 64, f"Expected 64 hidden cases, got {len(hidden_cases)}"

    # Save hidden cases
    for c in hidden_cases:
        with open(cases_dir / f"{c['case_id']}.json", "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)

    # 4. 48 Hostile Mutations
    for m_idx in range(48):
        mut_id = f"c044_mut_{m_idx + 1:02d}"
        target_case = hidden_cases[m_idx % len(hidden_cases)]

        if m_idx < 10:
            # Mutation 1: Images given as Booleans
            ans = {
                "case_id": target_case["case_id"],
                "status": "SOLVED",
                "kind": "IDENTIFIED",
                "rep_id": [4, 1],
                "images": [True, False],
            }
            exp_rej = "Booleans in images"

        elif m_idx < 20:
            # Mutation 2: Wrong representative ID
            ans = {
                "case_id": target_case["case_id"],
                "status": "SOLVED",
                "kind": "IDENTIFIED",
                "rep_id": [99, 99],
                "images": [0],
            }
            exp_rej = "Representative ID missing from catalog"

        elif m_idx < 30:
            # Mutation 3: Non-homomorphic generator images
            ans = {
                "case_id": target_case["case_id"],
                "status": "SOLVED",
                "kind": "IDENTIFIED",
                "rep_id": [4, 1],
                "images": [0],  # identity does not generate C4
            }
            exp_rej = "Generator images do not extend to isomorphism"

        elif m_idx < 40:
            # Mutation 4: Unknown / illicit invariant name
            ans = {
                "case_id": target_case["case_id"],
                "status": "SOLVED",
                "kind": "NOT_ISOMORPHIC",
                "invariant": "non_existent_fake_invariant",
                "G_value": 999,
                "H_value": 888,
            }
            exp_rej = "Unknown invariant name"

        else:
            # Mutation 5: Images containing strings
            ans = {
                "case_id": target_case["case_id"],
                "status": "SOLVED",
                "kind": "ISOMORPHIC",
                "images": ["not_an_int", "invalid_element"],
            }
            exp_rej = "Invalid image element types"

        payload = {
            "mut_id": mut_id,
            "case": target_case,
            "answer": ans,
            "expected_rejection": exp_rej,
        }
        with open(mut_dir / f"{mut_id}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    print(f"Generated {len(hidden_cases)} hidden cases and {48} hostile mutations.")


if __name__ == "__main__":
    generate()
