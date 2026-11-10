# AuthorityEffect: None.
"""
Case and Hostile Mutation Generator for C027 (Kochen-Specker Contextuality).

Generates:
1. 24 Base Cases (Peres 33, Cabello 18, colourable subsets, supersets, single/multi-basis sets).
2. 8 Controls (ray permutations, signed coordinate flips, rational orthogonal rotations, integer scalings).
3. 6 Poisoned-but-Schema-Valid Cases (near-orthogonal trap, zero vector, dimension mismatch, oversized).
4. 40+ Hostile Mutations (testing kill rate against dual checkers).
5. manifest.json with SHA-256 digests.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# Canonical Cabello 18 vectors in dimension 4
CABELLO_18 = [
    [1, 1, 1, 1],
    [1, 1, 1, -1],
    [1, 1, 0, 0],
    [1, 1, -1, -1],
    [1, 0, 1, 0],
    [1, 0, 0, 1],
    [1, 0, 0, -1],
    [1, 0, -1, 0],
    [1, -1, 1, 1],
    [1, -1, 0, 0],
    [1, -1, -1, 1],
    [1, -1, -1, -1],
    [0, 1, 0, 1],
    [0, 1, 0, 0],
    [0, 1, -1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, -1],
    [0, 0, 0, 1],
]


def get_peres_33() -> List[List[List[int]]]:
    """Generates the 33 rays of Peres in dimension 3."""
    rays: List[List[List[int]]] = []

    # 1. 3 axes
    rays.extend(
        [
            [[1, 0], [0, 0], [0, 0]],
            [[0, 0], [1, 0], [0, 0]],
            [[0, 0], [0, 0], [1, 0]],
        ]
    )

    # 2. 6 face diagonals
    rays.extend(
        [
            [[1, 0], [1, 0], [0, 0]],
            [[1, 0], [-1, 0], [0, 0]],
            [[1, 0], [0, 0], [1, 0]],
            [[1, 0], [0, 0], [-1, 0]],
            [[0, 0], [1, 0], [1, 0]],
            [[0, 0], [1, 0], [-1, 0]],
        ]
    )

    # 3. 12 rays of type (0, 1, sqrt(2))
    for s in [1, -1]:
        rays.append([[0, 0], [1, 0], [0, s]])
        rays.append([[0, 0], [0, s], [1, 0]])
        rays.append([[1, 0], [0, 0], [0, s]])
        rays.append([[0, s], [0, 0], [1, 0]])
        rays.append([[1, 0], [0, s], [0, 0]])
        rays.append([[0, s], [1, 0], [0, 0]])

    # 4. 12 rays of type (1, 1, sqrt(2))
    for s1 in [1, -1]:
        for s2 in [1, -1]:
            rays.append([[1, 0], [s1, 0], [0, s2]])
            rays.append([[1, 0], [0, s2], [s1, 0]])
            rays.append([[0, s2], [1, 0], [s1, 0]])

    return rays


def int_vecs_to_wire(vecs: List[List[int]]) -> List[List[List[str]]]:
    return [[[str(c), "0"] for c in v] for v in vecs]


def generate_base_cases() -> List[Dict[str, Any]]:
    cabello_wire = int_vecs_to_wire(CABELLO_18)
    peres_wire = get_peres_33()

    base_cases: List[Dict[str, Any]] = [
        # Base 1: Canonical Cabello 18 (dim 4, uncolourable with parity proof)
        {
            "case_id": "base_01_cabello_18",
            "dimension": 4,
            "vectors": cabello_wire,
        },
        # Base 2: Canonical Peres 33 (dim 3, uncolourable)
        {
            "case_id": "base_02_peres_33",
            "dimension": 3,
            "vectors": peres_wire,
        },
        # Base 3: Standard basis alone in dim 4 (colourable)
        {
            "case_id": "base_03_standard_basis_dim4",
            "dimension": 4,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["0", "0"], ["1", "0"]],
            ],
        },
        # Base 4: Standard basis alone in dim 3 (colourable)
        {
            "case_id": "base_04_standard_basis_dim3",
            "dimension": 3,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"]],
            ],
        },
        # Base 5: Two bases sharing 1 ray in dim 4 (colourable)
        {
            "case_id": "base_05_two_bases_sharing_one_ray",
            "dimension": 4,
            "vectors": [
                # Shared ray: (1, 0, 0, 0)
                [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
                # Basis 1
                [["0", "0"], ["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["0", "0"], ["1", "0"]],
                # Basis 2 (orthogonal to (1, 0, 0, 0))
                [["0", "0"], ["1", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["-1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["0", "0"], ["2", "0"]],
            ],
        },
        # Base 6: Colourable 9-ray subset of Cabello 18
        {
            "case_id": "base_06_cabello_9_subset",
            "dimension": 4,
            "vectors": cabello_wire[:9],
        },
        # Base 7: Colourable 14-ray subset of Cabello 18
        {
            "case_id": "base_07_cabello_14_subset",
            "dimension": 4,
            "vectors": cabello_wire[:14],
        },
        # Base 8: Colourable 17-ray subset of Cabello 18 (one deletion)
        {
            "case_id": "base_08_cabello_17_subset",
            "dimension": 4,
            "vectors": cabello_wire[:17],
        },
        # Base 9: Colourable 10-ray subset of Peres 33
        {
            "case_id": "base_09_peres_10_subset",
            "dimension": 3,
            "vectors": peres_wire[:10],
        },
        # Base 10: Colourable 20-ray subset of Peres 33
        {
            "case_id": "base_10_peres_20_subset",
            "dimension": 3,
            "vectors": peres_wire[:20],
        },
        # Base 11: Colourable 32-ray subset of Peres 33 (one deletion)
        {
            "case_id": "base_11_peres_32_subset",
            "dimension": 3,
            "vectors": peres_wire[:32],
        },
        # Base 12: Set with no complete context (triangle in dim 4, size 3 < 4)
        {
            "case_id": "base_12_no_complete_context_dim4",
            "dimension": 4,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"], ["0", "0"]],
            ],
        },
        # Base 13: Cabello 18 padded with duplicate rays to 25
        {
            "case_id": "base_13_cabello_with_duplicates",
            "dimension": 4,
            "vectors": cabello_wire + cabello_wire[:7],
        },
        # Base 14: Cabello 18 padded with non-orthogonal dummy rays to 30
        {
            "case_id": "base_14_cabello_padded_30",
            "dimension": 4,
            "vectors": cabello_wire
            + [[["1", "0"], ["2", "0"], ["3", "0"], ["5", "0"]] for _ in range(12)],
        },
        # Base 15: Cabello 18 padded to max 60 vectors
        {
            "case_id": "base_15_cabello_max_60",
            "dimension": 4,
            "vectors": cabello_wire
            + [[["1", "0"], [str(i), "0"], ["1", "0"], ["1", "0"]] for i in range(1, 43)],
        },
        # Base 16: Peres 33 padded with duplicates to 45
        {
            "case_id": "base_16_peres_with_duplicates_45",
            "dimension": 3,
            "vectors": peres_wire + peres_wire[:12],
        },
        # Base 17: Peres 33 padded to 60 vectors
        {
            "case_id": "base_17_peres_max_60",
            "dimension": 3,
            "vectors": peres_wire + [[["1", "0"], [str(i), "0"], ["7", "0"]] for i in range(1, 28)],
        },
        # Base 18: Disjoint contexts in dim 4 (two independent bases, colourable)
        {
            "case_id": "base_18_disjoint_contexts_dim4",
            "dimension": 4,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["0", "0"], ["1", "0"]],
                [["1", "0"], ["1", "0"], ["1", "0"], ["1", "0"]],
                [["1", "0"], ["1", "0"], ["-1", "0"], ["-1", "0"]],
                [["1", "0"], ["-1", "0"], ["1", "0"], ["-1", "0"]],
                [["1", "0"], ["-1", "0"], ["-1", "0"], ["1", "0"]],
            ],
        },
        # Base 19: Disjoint contexts in dim 3 (two independent bases, colourable)
        {
            "case_id": "base_19_disjoint_contexts_dim3",
            "dimension": 3,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"]],
                [["1", "0"], ["1", "0"], ["0", "0"]],
                [["1", "0"], ["-1", "0"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["1", "0"]],
            ],
        },
        # Base 20: 3 mutually non-intersecting contexts in dim 4
        {
            "case_id": "base_20_three_contexts_dim4",
            "dimension": 4,
            "vectors": cabello_wire[0:4] + cabello_wire[4:8] + cabello_wire[8:12],
        },
        # Base 21: Q(sqrt(2)) explicit basis in dim 4
        {
            "case_id": "base_21_sqrt2_basis_dim4",
            "dimension": 4,
            "vectors": [
                [["0", "1"], ["0", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "1"], ["1", "-1"], ["0", "0"]],
                [["0", "0"], ["1", "-1"], ["-1", "-1"], ["0", "0"]],
                [["0", "0"], ["0", "0"], ["0", "0"], ["0", "2"]],
            ],
        },
        # Base 22: Q(sqrt(2)) explicit basis in dim 3
        {
            "case_id": "base_22_sqrt2_basis_dim3",
            "dimension": 3,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"]],
                [["0", "0"], ["1", "0"], ["0", "1"]],
                [["0", "0"], ["0", "-1"], ["1", "0"]],
            ],
        },
        # Base 23: Random integer rays with 1 context in dim 3
        {
            "case_id": "base_23_single_context_dim3",
            "dimension": 3,
            "vectors": [
                [["1", "0"], ["2", "0"], ["2", "0"]],
                [["2", "0"], ["1", "0"], ["-2", "0"]],
                [["-2", "0"], ["2", "0"], ["-1", "0"]],
            ],
        },
        # Base 24: Single context in dim 4 with integer entries
        {
            "case_id": "base_24_single_context_dim4",
            "dimension": 4,
            "vectors": [
                [["1", "0"], ["1", "0"], ["1", "0"], ["1", "0"]],
                [["1", "0"], ["1", "0"], ["-1", "0"], ["-1", "0"]],
                [["1", "0"], ["-1", "0"], ["1", "0"], ["-1", "0"]],
                [["1", "0"], ["-1", "0"], ["-1", "0"], ["1", "0"]],
            ],
        },
    ]
    return base_cases


def generate_control_cases() -> List[Dict[str, Any]]:
    cabello_wire = int_vecs_to_wire(CABELLO_18)
    peres_wire = get_peres_33()

    controls: List[Dict[str, Any]] = [
        # Ctrl 1: Permutation of Cabello 18 rays
        {
            "case_id": "ctrl_01_permuted_cabello",
            "dimension": 4,
            "vectors": cabello_wire[::-1],
        },
        # Ctrl 2: Permutation of Peres 33 rays
        {
            "case_id": "ctrl_02_permuted_peres",
            "dimension": 3,
            "vectors": peres_wire[10:] + peres_wire[:10],
        },
        # Ctrl 3: Signed coordinate permutation on Cabello 18: (x, y, z, w) -> (-y, x, -w, z)
        {
            "case_id": "ctrl_03_coord_perm_cabello",
            "dimension": 4,
            "vectors": [
                [
                    [str(-int(v[1][0])), "0"],
                    [v[0][0], "0"],
                    [str(-int(v[3][0])), "0"],
                    [v[2][0], "0"],
                ]
                for v in cabello_wire
            ],
        },
        # Ctrl 4: Coordinate sign flip on Peres 33: (x, y, z) -> (-x, y, -z)
        {
            "case_id": "ctrl_04_coord_flip_peres",
            "dimension": 3,
            "vectors": [
                [
                    [str(-int(v[0][0])), str(-int(v[0][1]))],
                    [v[1][0], v[1][1]],
                    [str(-int(v[2][0])), str(-int(v[2][1]))],
                ]
                for v in peres_wire
            ],
        },
        # Ctrl 5: Rescale vectors by distinct non-zero integers: v_i -> (i + 1) * v_i
        {
            "case_id": "ctrl_05_scaled_cabello",
            "dimension": 4,
            "vectors": [
                [[str(int(c[0]) * (idx + 1)), "0"] for c in v] for idx, v in enumerate(cabello_wire)
            ],
        },
        # Ctrl 6: Rescale vectors by sqrt(2) on Peres 33
        {
            "case_id": "ctrl_06_sqrt2_scaled_peres",
            "dimension": 3,
            "vectors": [
                # (a + b*sqrt(2))*sqrt(2) = 2b + a*sqrt(2)
                [[str(2 * int(c[1])), str(int(c[0]))] for c in v]
                for v in peres_wire
            ],
        },
        # Ctrl 7: Rotation on coordinates 0, 1 by [[3/5, -4/5], [4/5, 3/5]], cleared by 5
        {
            "case_id": "ctrl_07_rotated_cabello",
            "dimension": 4,
            "vectors": [
                [
                    [str(3 * int(v[0][0]) - 4 * int(v[1][0])), "0"],
                    [str(4 * int(v[0][0]) + 3 * int(v[1][0])), "0"],
                    [str(5 * int(v[2][0])), "0"],
                    [str(5 * int(v[3][0])), "0"],
                ]
                for v in cabello_wire
            ],
        },
        # Ctrl 8: Permuted and scaled colourable subset
        {
            "case_id": "ctrl_08_perm_scaled_subset",
            "dimension": 4,
            "vectors": [[[str(int(c[0]) * 3), "0"] for c in v] for v in cabello_wire[4:14]],
        },
    ]
    return controls


def generate_poisoned_cases() -> List[Dict[str, Any]]:
    cabello_wire = int_vecs_to_wire(CABELLO_18)

    # Near-orthogonal trap: perturb one coordinate of cabello vector 0 so u . v != 0
    # (sqrt(2) - 1)^4 = 17 - 12*sqrt(2)
    near_cabello = copy.deepcopy(cabello_wire)
    # add [17, -12] to last coordinate of vector 0
    c3 = near_cabello[0][3]
    near_cabello[0][3] = [str(int(c3[0]) + 17), "-12"]

    return [
        # Poison 1: Near-orthogonal perturbation breaks context
        {
            "case_id": "poison_01_near_orthogonal_trap",
            "dimension": 4,
            "vectors": near_cabello,
            "_trap": "near_orthogonal_not_exact",
        },
        # Poison 2: Zero vector in list
        {
            "case_id": "poison_02_zero_vector_trap",
            "dimension": 4,
            "vectors": cabello_wire[:5]
            + [[["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"]]]
            + cabello_wire[5:10],
            "_trap": "zero_vector",
        },
        # Poison 3: Dimension mismatch (vector has length 3 instead of 4)
        {
            "case_id": "poison_03_dimension_mismatch",
            "dimension": 4,
            "vectors": cabello_wire[:4] + [[["1", "0"], ["0", "0"], ["0", "0"]]],
            "_trap": "vector_dimension_mismatch",
        },
        # Poison 4: Invalid dimension (dimension 5 out of bounds)
        {
            "case_id": "poison_04_invalid_dimension_5",
            "dimension": 5,
            "vectors": [[["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"], ["0", "0"]]],
            "_trap": "dimension_not_3_or_4",
        },
        # Poison 5: Duplicate ray scaled as -v
        {
            "case_id": "poison_05_negated_duplicate_ray",
            "dimension": 4,
            "vectors": [
                [["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
                [["-1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]],
            ],
            "_trap": "parallel_opposite_sign",
        },
        # Poison 6: Too many vectors (65 > 60)
        {
            "case_id": "poison_06_too_many_vectors",
            "dimension": 4,
            "vectors": [[["1", "0"], ["0", "0"], ["0", "0"], ["0", "0"]] for _ in range(65)],
            "_trap": "vector_count_gt_60",
        },
    ]


def generate_mutations(
    base_cases: List[Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    mutations: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    mut_idx = 1

    # 1. Uncolourable case falsely claimed colourable
    case_cabello = base_cases[0]  # Cabello 18
    ans_false_colourable = {
        "id": case_cabello["case_id"],
        "status": "SOLVED",
        "colourable": True,
        "colouring": [1] + [0] * 17,
    }
    mutations.append(
        (f"mut_{mut_idx:02d}_false_colourable_claim", case_cabello, ans_false_colourable)
    )
    mut_idx += 1

    # 2. Colourable case falsely claimed uncolourable
    case_basis = base_cases[2]  # Standard basis dim 4
    ans_false_uncolourable = {
        "id": case_basis["case_id"],
        "status": "SOLVED",
        "colourable": False,
        "subset": [0, 1, 2, 3],
        "certificate": {"kind": "parity", "contexts": [[0, 1, 2, 3]]},
    }
    mutations.append(
        (f"mut_{mut_idx:02d}_false_uncolourable_claim", case_basis, ans_false_uncolourable)
    )
    mut_idx += 1

    # 3. Two orthogonal rays both coloured 1
    ans_ortho_violation = {
        "id": case_basis["case_id"],
        "status": "SOLVED",
        "colourable": True,
        "colouring": [1, 1, 0, 0],  # 0 and 1 are orthogonal!
    }
    mutations.append((f"mut_{mut_idx:02d}_orthogonal_both_one", case_basis, ans_ortho_violation))
    mut_idx += 1

    # 4. Context sum is 0 (all zeros in context)
    ans_zero_sum = {
        "id": case_basis["case_id"],
        "status": "SOLVED",
        "colourable": True,
        "colouring": [0, 0, 0, 0],
    }
    mutations.append((f"mut_{mut_idx:02d}_context_sum_zero", case_basis, ans_zero_sum))
    mut_idx += 1

    # 5. Parity certificate with even number of contexts
    sol_cabello = solve(case_cabello)
    ans_even_contexts = copy.deepcopy(sol_cabello)
    if "certificate" in ans_even_contexts and "contexts" in ans_even_contexts["certificate"]:
        ans_even_contexts["certificate"]["contexts"] = ans_even_contexts["certificate"]["contexts"][
            :-1
        ]  # 9 -> 8
        mutations.append(
            (f"mut_{mut_idx:02d}_parity_even_contexts", case_cabello, ans_even_contexts)
        )
        mut_idx += 1

    # 6. Parity certificate naming an invalid context
    ans_fake_ctx = copy.deepcopy(sol_cabello)
    if "certificate" in ans_fake_ctx and "contexts" in ans_fake_ctx["certificate"]:
        ans_fake_ctx["certificate"]["contexts"][0] = [0, 1, 2, 3]  # Not an orthogonal context!
        mutations.append((f"mut_{mut_idx:02d}_parity_invalid_context", case_cabello, ans_fake_ctx))
        mut_idx += 1

    # 7. Parity certificate with an odd ray frequency
    ans_odd_degree = copy.deepcopy(sol_cabello)
    if "certificate" in ans_odd_degree and "contexts" in ans_odd_degree["certificate"]:
        ctx0 = list(ans_odd_degree["certificate"]["contexts"][0])
        ctx0[0] = (ctx0[0] + 1) % 18
        ans_odd_degree["certificate"]["contexts"][0] = ctx0
        mutations.append((f"mut_{mut_idx:02d}_parity_odd_degree", case_cabello, ans_odd_degree))
        mut_idx += 1

    # 8. Colouring with invalid value (e.g. 2 instead of 0 or 1)
    ans_bad_val = {
        "id": case_basis["case_id"],
        "status": "SOLVED",
        "colourable": True,
        "colouring": [2, 0, 0, 0],
    }
    mutations.append((f"mut_{mut_idx:02d}_colouring_invalid_value", case_basis, ans_bad_val))
    mut_idx += 1

    # 9. Colouring with truncated length
    ans_trunc = {
        "id": case_basis["case_id"],
        "status": "SOLVED",
        "colourable": True,
        "colouring": [1, 0],
    }
    mutations.append((f"mut_{mut_idx:02d}_colouring_truncated", case_basis, ans_trunc))
    mut_idx += 1

    # 10. Systematic mutations across base cases
    for case in base_cases[:12]:
        sol = solve(case)
        cid = case["case_id"]

        if sol.get("colourable"):
            # Mut A: Corrupted value
            ans_a = copy.deepcopy(sol)
            ans_a["colouring"][0] = 5
            mutations.append((f"mut_{mut_idx:02d}_{cid}_corrupted_colour_val", case, ans_a))
            mut_idx += 1

            # Mut B: Set all rays to 1 to guarantee orthogonality and context violations
            ans_b = copy.deepcopy(sol)
            ans_b["colouring"] = [1] * len(ans_b["colouring"])
            mutations.append((f"mut_{mut_idx:02d}_{cid}_all_ones_violation", case, ans_b))
            mut_idx += 1

            # Mut C: False uncolourable
            ans_c = {
                "id": cid,
                "status": "SOLVED",
                "colourable": False,
                "certificate": {"kind": "parity", "contexts": []},
            }
            mutations.append((f"mut_{mut_idx:02d}_{cid}_false_uncolourable", case, ans_c))
            mut_idx += 1
        else:
            # Mut D: Corrupt certificate
            ans_d = copy.deepcopy(sol)
            if (
                "certificate" in ans_d
                and "contexts" in ans_d["certificate"]
                and len(ans_d["certificate"]["contexts"]) > 0
            ):
                ans_d["certificate"]["contexts"] = ans_d["certificate"]["contexts"][:1]
                mutations.append((f"mut_{mut_idx:02d}_{cid}_single_context_parity", case, ans_d))
                mut_idx += 1
            else:
                ans_d["certificate"]["kind"] = "invalid_proof_kind"
                mutations.append(
                    (f"mut_{mut_idx:02d}_{cid}_corrupted_refutation_kind", case, ans_d)
                )
                mut_idx += 1

            # Mut E: False colourable
            ans_e = {"id": cid, "status": "SOLVED", "colourable": True, "colouring": [1] * 18}
            mutations.append((f"mut_{mut_idx:02d}_{cid}_all_ones_colouring", case, ans_e))
            mut_idx += 1

    # Malformed refusal mutations
    case_oob = {"case_id": "mut_oob", "dimension": 4, "vectors": [[["1", "0"] * 4]] * 65}
    ans_bad_refusal = {"id": "mut_oob", "status": "UNKNOWN", "refusal_code": "WRONG_REFUSAL"}
    mutations.append((f"mut_{mut_idx:02d}_bad_refusal_code", case_oob, ans_bad_refusal))
    mut_idx += 1

    ans_oob_solved = {
        "id": "mut_oob",
        "status": "SOLVED",
        "colourable": True,
        "colouring": [1] * 65,
    }
    mutations.append((f"mut_{mut_idx:02d}_oob_falsely_solved", case_oob, ans_oob_solved))
    mut_idx += 1

    return mutations


def main() -> None:
    pkg_dir = Path(__file__).resolve().parent
    cases_dir = pkg_dir / "cases"
    mut_dir = pkg_dir / "mutation_suite"

    cases_dir.mkdir(parents=True, exist_ok=True)
    mut_dir.mkdir(parents=True, exist_ok=True)

    base_cases = generate_base_cases()
    ctrl_cases = generate_control_cases()
    poison_cases = generate_poisoned_cases()

    all_cases = base_cases + ctrl_cases + poison_cases

    for case in all_cases:
        cid = case["case_id"]
        out_path = cases_dir / f"{cid}.json"
        with open(out_path, "wb") as f:
            f.write(canonical_json_bytes(case))

    mutations = generate_mutations(base_cases)
    for m_id, m_case, m_ans in mutations:
        m_file = mut_dir / f"{m_id}.json"
        payload = {"case": m_case, "answer": m_ans}
        with open(m_file, "wb") as f:
            f.write(canonical_json_bytes(payload))

    print(
        f"Generated {len(all_cases)} judge cases ({len(base_cases)} base, {len(ctrl_cases)} controls, {len(poison_cases)} poison) and {len(mutations)} hostile mutations."
    )

    # Generate manifest.json
    manifest: Dict[str, Any] = {
        "challenge_id": "C027",
        "domain": "c_quantum",
        "tier": "T3",
        "cases_count": len(all_cases),
        "mutations_count": len(mutations),
        "files": {},
    }

    for root, _, files in os.walk(pkg_dir):
        for fname in sorted(files):
            if fname == "manifest.json":
                continue
            fpath = Path(root) / fname
            rel_path = fpath.relative_to(pkg_dir).as_posix()
            manifest["files"][rel_path] = sha256_file(fpath)

    manifest_path = pkg_dir / "manifest.json"
    with open(manifest_path, "wb") as f:
        f.write(canonical_json_bytes(manifest))

    print(f"Manifest written with {len(manifest['files'])} hashed entries.")


if __name__ == "__main__":
    main()
