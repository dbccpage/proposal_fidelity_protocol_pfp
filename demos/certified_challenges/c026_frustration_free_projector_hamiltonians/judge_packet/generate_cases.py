# AuthorityEffect: None.
"""
Case and Mutation Generator for C026 (Frustration-Free Projector Hamiltonians).

Generates:
1. 24 Base Cases (hard-core graphs, singlets, triplets, entangled kernels, D=64).
2. 8 Controls (site permutations, rational rotations [[3/5, -4/5], [4/5, 3/5]], weight rescalings).
3. 6 Poisoned-but-Schema-Valid Cases (entangled-only, pairwise-satisfiable frustrated,
   P^2 != P perturbation, P != P^dag, invalid site, D > 64).
4. 40+ Hostile Mutations (testing kill rate against dual checkers).
5. manifest.json with SHA-256 digests.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Tuple

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from c026_frustration_free_projector_hamiltonians.reference_solver.gaussian_rational import GaussianRat
from c026_frustration_free_projector_hamiltonians.reference_solver.kronecker import extend_local_matrix
from c026_frustration_free_projector_hamiltonians.reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# Standard local 2-qubit projectors
def proj_11() -> List[List[List[str]]]:
    """|11><11| projector on 2 qubits (4x4)."""
    return [[["1", "0"] if r == 3 and c == 3 else ["0", "0"] for c in range(4)] for r in range(4)]


def proj_00() -> List[List[List[str]]]:
    """|00><00| projector on 2 qubits (4x4)."""
    return [[["1", "0"] if r == 0 and c == 0 else ["0", "0"] for c in range(4)] for r in range(4)]


def proj_singlet() -> List[List[List[str]]]:
    """Singlet projector |psi-><psi-| on 2 qubits (4x4)."""
    # |psi-> = (|01> - |10>)/sqrt(2) => 1/2 [[0,0,0,0],[0,1,-1,0],[0,-1,1,0],[0,0,0,0]]
    mat = [[["0", "0"] for _ in range(4)] for _ in range(4)]
    mat[1][1] = ["1/2", "0"]
    mat[1][2] = ["-1/2", "0"]
    mat[2][1] = ["-1/2", "0"]
    mat[2][2] = ["1/2", "0"]
    return mat


def proj_triplet() -> List[List[List[str]]]:
    """Triplet symmetric subspace projector I - |psi-><psi-| on 2 qubits (4x4)."""
    mat = [[["1", "0"] if r == c else ["0", "0"] for c in range(4)] for r in range(4)]
    mat[1][1] = ["1/2", "0"]
    mat[1][2] = ["1/2", "0"]
    mat[2][1] = ["1/2", "0"]
    mat[2][2] = ["1/2", "0"]
    return mat


def proj_plus() -> List[List[List[str]]]:
    """|+><+| projector on 1 qubit (2x2)."""
    return [[["1/2", "0"], ["1/2", "0"]], [["1/2", "0"], ["1/2", "0"]]]


def proj_minus() -> List[List[List[str]]]:
    """|-><-| projector on 1 qubit (2x2)."""
    return [[["1/2", "0"], ["-1/2", "0"]], [["-1/2", "0"], ["1/2", "0"]]]


def rotate_2x2(proj_2x2: List[List[List[str]]]) -> List[List[List[str]]]:
    """Apply rational orthogonal rotation R = [[3/5, -4/5], [4/5, 3/5]] to 2x2 projector: R * P * R^T."""
    R = [
        [GaussianRat(Fraction(3, 5)), GaussianRat(Fraction(-4, 5))],
        [GaussianRat(Fraction(4, 5)), GaussianRat(Fraction(3, 5))],
    ]
    RT = [
        [GaussianRat(Fraction(3, 5)), GaussianRat(Fraction(4, 5))],
        [GaussianRat(Fraction(-4, 5)), GaussianRat(Fraction(3, 5))],
    ]
    P = [[GaussianRat.from_wire(elem) for elem in row] for row in proj_2x2]

    # RP = R * P
    RP = [[GaussianRat.zero() for _ in range(2)] for _ in range(2)]
    for i in range(2):
        for j in range(2):
            for k in range(2):
                RP[i][j] = RP[i][j] + (R[i][k] * P[k][j])

    # RPRT = RP * RT
    RPRT = [[GaussianRat.zero() for _ in range(2)] for _ in range(2)]
    for i in range(2):
        for j in range(2):
            for k in range(2):
                RPRT[i][j] = RPRT[i][j] + (RP[i][k] * RT[k][j])

    return [[elem.to_wire() for elem in row] for row in RPRT]


def generate_base_cases() -> List[Dict[str, Any]]:
    """24 base cases."""
    p11 = proj_11()
    p00 = proj_00()
    sing = proj_singlet()
    trip = proj_triplet()
    pp = proj_plus()
    pm = proj_minus()

    cases = []

    # 1-4: Hard-core graphs on 3-5 qubits
    # Triangle (dim K = 4)
    cases.append(
        {
            "case_id": "base_01_hardcore_triangle",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [1, 2], "weight": "1", "matrix": p11},
                {"support": [0, 2], "weight": "1", "matrix": p11},
            ],
        }
    )
    # 4-cycle C4 (dim K = 7)
    cases.append(
        {
            "case_id": "base_02_hardcore_c4",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [1, 2], "weight": "1", "matrix": p11},
                {"support": [2, 3], "weight": "1", "matrix": p11},
                {"support": [3, 0], "weight": "1", "matrix": p11},
            ],
        }
    )
    # 5-path P5 (dim K = 13: Fibonacci independent sets)
    cases.append(
        {
            "case_id": "base_03_hardcore_p5",
            "local_dims": [2, 2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [1, 2], "weight": "1", "matrix": p11},
                {"support": [2, 3], "weight": "1", "matrix": p11},
                {"support": [3, 4], "weight": "1", "matrix": p11},
            ],
        }
    )
    # Star graph K_{1, 3} (dim K = 9)
    cases.append(
        {
            "case_id": "base_04_hardcore_star4",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [0, 2], "weight": "1", "matrix": p11},
                {"support": [0, 3], "weight": "1", "matrix": p11},
            ],
        }
    )

    # 5-8: Singlet & Triplet mixtures on 3-4 qubits
    # Singlet triangle (dim K = 4)
    cases.append(
        {
            "case_id": "base_05_singlet_triangle",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": sing},
                {"support": [1, 2], "weight": "1", "matrix": sing},
                {"support": [0, 2], "weight": "1", "matrix": sing},
            ],
        }
    )
    # Triplet triangle (dim K = 0, frustrated)
    cases.append(
        {
            "case_id": "base_06_triplet_triangle_frustrated",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": trip},
                {"support": [1, 2], "weight": "1", "matrix": trip},
                {"support": [0, 2], "weight": "1", "matrix": trip},
            ],
        }
    )
    # Singlet chain of 4 qubits
    cases.append(
        {
            "case_id": "base_07_singlet_chain4",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": sing},
                {"support": [1, 2], "weight": "1", "matrix": sing},
                {"support": [2, 3], "weight": "1", "matrix": sing},
            ],
        }
    )
    # Mixed singlet and hardcore
    cases.append(
        {
            "case_id": "base_08_mixed_singlet_hardcore",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": sing},
                {"support": [1, 2], "weight": "2", "matrix": p11},
            ],
        }
    )

    # 9-12: Single rank-1 terms and 1-local terms
    cases.append(
        {
            "case_id": "base_09_single_term_rank1",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_10_single_qubit_projectors",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0], "weight": "1", "matrix": pp},
                {"support": [1], "weight": "1", "matrix": pm},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_11_contradictory_1local_frustrated",
            "local_dims": [2, 2],
            "terms": [
                {"support": [0], "weight": "1", "matrix": pp},
                {"support": [0], "weight": "1", "matrix": pm},  # P_+ and P_- sum to I_2
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_12_disjoint_support_terms",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [2, 3], "weight": "1", "matrix": p00},
            ],
        }
    )

    # 13-16: 6-qubit cases (D = 64)
    cases.append(
        {
            "case_id": "base_13_d64_hardcore_path6",
            "local_dims": [2, 2, 2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [1, 2], "weight": "1", "matrix": p11},
                {"support": [2, 3], "weight": "1", "matrix": p11},
                {"support": [3, 4], "weight": "1", "matrix": p11},
                {"support": [4, 5], "weight": "1", "matrix": p11},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_14_d64_star6",
            "local_dims": [2, 2, 2, 2, 2, 2],
            "terms": [{"support": [0, i], "weight": "1", "matrix": p11} for i in range(1, 6)],
        }
    )
    cases.append(
        {
            "case_id": "base_15_d64_ladder_singlet",
            "local_dims": [2, 2, 2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": sing},
                {"support": [2, 3], "weight": "1", "matrix": sing},
                {"support": [4, 5], "weight": "1", "matrix": sing},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_16_d64_frustrated_overcomplete",
            "local_dims": [2, 2, 2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": trip},
                {"support": [1, 2], "weight": "1", "matrix": trip},
                {"support": [0, 2], "weight": "1", "matrix": trip},
            ],
        }
    )

    # 17-20: Qutrit cases (local_dim 3, D up to 27)
    # 3x3 projector on qutrit: |2><2|
    p22_qutrit = [
        [["1", "0"] if r == 2 and c == 2 else ["0", "0"] for c in range(3)] for r in range(3)
    ]
    cases.append(
        {
            "case_id": "base_17_qutrit_pair",
            "local_dims": [3, 3],
            "terms": [
                {"support": [0], "weight": "1", "matrix": p22_qutrit},
                {"support": [1], "weight": "1", "matrix": p22_qutrit},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_18_qutrit_triangle",
            "local_dims": [3, 3, 3],
            "terms": [
                {"support": [0], "weight": "1", "matrix": p22_qutrit},
                {"support": [1], "weight": "1", "matrix": p22_qutrit},
                {"support": [2], "weight": "1", "matrix": p22_qutrit},
            ],
        }
    )
    # Mixed qubit-qutrit
    cases.append(
        {
            "case_id": "base_19_mixed_qubit_qutrit",
            "local_dims": [2, 3, 2],
            "terms": [
                {"support": [0], "weight": "1", "matrix": pp},
                {"support": [1], "weight": "1", "matrix": p22_qutrit},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_20_mixed_qubit_qutrit_chain",
            "local_dims": [2, 3, 3],
            "terms": [
                {"support": [0], "weight": "1", "matrix": pp},
                {"support": [2], "weight": "1", "matrix": p22_qutrit},
            ],
        }
    )

    # 21-24: Overlapping supports & entangled kernels
    cases.append(
        {
            "case_id": "base_21_overlapping_singlet_hardcore",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": sing},
                {"support": [1, 2], "weight": "1", "matrix": sing},
                {"support": [2, 3], "weight": "1", "matrix": p11},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_22_frustrated_quad",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": trip},
                {"support": [1, 2], "weight": "1", "matrix": trip},
                {"support": [2, 0], "weight": "1", "matrix": trip},
                {"support": [3], "weight": "1", "matrix": pp},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_23_cluster_state_stabilizer_projectors",
            "local_dims": [2, 2, 2],
            # Projectors onto -1 eigenspaces of stabilizers
            "terms": [
                {"support": [0], "weight": "1", "matrix": pm},
                {"support": [1], "weight": "1", "matrix": pm},
            ],
        }
    )
    cases.append(
        {
            "case_id": "base_24_toric_plaquette_projectors",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p00},
                {"support": [2, 3], "weight": "1", "matrix": p11},
            ],
        }
    )

    return cases


def generate_control_cases() -> List[Dict[str, Any]]:
    """8 relabel and gauge controls."""
    p11 = proj_11()
    sing = proj_singlet()
    trip = proj_triplet()
    pp = proj_plus()
    pp_rot = rotate_2x2(pp)

    controls = [
        # Ctrl 1: Site permutation on triangle (0, 1, 2) -> (2, 0, 1)
        {
            "case_id": "ctrl_01_site_perm_triangle",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [2, 0], "weight": "1", "matrix": p11},
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [2, 1], "weight": "1", "matrix": p11},
            ],
        },
        # Ctrl 2: Site permutation on C4
        {
            "case_id": "ctrl_02_site_perm_c4",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [3, 2], "weight": "1", "matrix": p11},
                {"support": [2, 1], "weight": "1", "matrix": p11},
                {"support": [1, 0], "weight": "1", "matrix": p11},
                {"support": [0, 3], "weight": "1", "matrix": p11},
            ],
        },
        # Ctrl 3: Weight rescaling (w = 3/2, 5/4, 2) on singlet triangle
        {
            "case_id": "ctrl_03_weight_rescaling_singlet",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "3/2", "matrix": sing},
                {"support": [1, 2], "weight": "5/4", "matrix": sing},
                {"support": [0, 2], "weight": "2", "matrix": sing},
            ],
        },
        # Ctrl 4: Weight rescaling on triplet triangle
        {
            "case_id": "ctrl_04_weight_rescaling_triplet",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "7/3", "matrix": trip},
                {"support": [1, 2], "weight": "1/2", "matrix": trip},
                {"support": [0, 2], "weight": "5", "matrix": trip},
            ],
        },
        # Ctrl 5: Local rational rotation [[3/5, -4/5], [4/5, 3/5]] on site 0
        {
            "case_id": "ctrl_05_local_rotation_site0",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0], "weight": "1", "matrix": pp_rot},
                {"support": [1], "weight": "1", "matrix": pp},
            ],
        },
        # Ctrl 6: Local rotation on site 1
        {
            "case_id": "ctrl_06_local_rotation_site1",
            "local_dims": [2, 2],
            "terms": [
                {"support": [1], "weight": "1", "matrix": pp_rot},
            ],
        },
        # Ctrl 7: Permutation + weights on star graph
        {
            "case_id": "ctrl_07_perm_and_weights_star",
            "local_dims": [2, 2, 2, 2],
            "terms": [
                {"support": [3, 0], "weight": "2", "matrix": p11},
                {"support": [3, 1], "weight": "3", "matrix": p11},
                {"support": [3, 2], "weight": "4", "matrix": p11},
            ],
        },
        # Ctrl 8: Qutrit site permutation
        {
            "case_id": "ctrl_08_qutrit_perm",
            "local_dims": [3, 3, 3],
            "terms": [
                {
                    "support": [2],
                    "weight": "2",
                    "matrix": [
                        [["1", "0"] if r == 2 and c == 2 else ["0", "0"] for c in range(3)]
                        for r in range(3)
                    ],
                },
                {
                    "support": [0],
                    "weight": "3",
                    "matrix": [
                        [["1", "0"] if r == 2 and c == 2 else ["0", "0"] for c in range(3)]
                        for r in range(3)
                    ],
                },
            ],
        },
    ]
    return controls


def generate_poisoned_cases() -> List[Dict[str, Any]]:
    """6 poisoned-but-schema-valid cases."""
    proj_singlet()
    trip = proj_triplet()
    p11 = proj_11()

    # Off-diagonal perturbed matrix that fails P^2 = P
    perturbed_p11 = copy.deepcopy(p11)
    perturbed_p11[0][1] = ["1/10", "0"]
    perturbed_p11[1][0] = ["1/10", "0"]  # Hermitian but not idempotent!

    # Non-Hermitian matrix
    non_herm = copy.deepcopy(p11)
    non_herm[0][1] = ["1/2", "0"]
    non_herm[1][0] = ["0", "0"]

    return [
        # Poison 1: Entangled-only kernel (no product state)
        {
            "case_id": "poison_01_entangled_only_kernel",
            "local_dims": [2, 2, 2],
            "terms": [
                # Hardcore on (0,1), (1,2), (0,2) plus projection eliminating |000>
                {"support": [0, 1], "weight": "1", "matrix": p11},
                {"support": [1, 2], "weight": "1", "matrix": p11},
                {"support": [0, 2], "weight": "1", "matrix": p11},
                {"support": [0, 1], "weight": "1", "matrix": proj_00()},
            ],
            "_trap": "no_product_state_in_kernel",
        },
        # Poison 2: Pairwise satisfiable but globally frustrated (triplet triangle)
        {
            "case_id": "poison_02_pairwise_satisfiable_frustrated",
            "local_dims": [2, 2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": trip},
                {"support": [1, 2], "weight": "1", "matrix": trip},
                {"support": [0, 2], "weight": "1", "matrix": trip},
            ],
            "_trap": "pairwise_satisfiable_global_frustration",
        },
        # Poison 3: Hermitian but P^2 != P (malformed projector)
        {
            "case_id": "poison_03_not_idempotent_trap",
            "local_dims": [2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": perturbed_p11},
            ],
            "_trap": "hermitian_not_idempotent",
        },
        # Poison 4: Non-Hermitian matrix (malformed projector)
        {
            "case_id": "poison_04_not_hermitian_trap",
            "local_dims": [2, 2],
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": non_herm},
            ],
            "_trap": "non_hermitian",
        },
        # Poison 5: Support naming out-of-bounds site index
        {
            "case_id": "poison_05_invalid_site_index",
            "local_dims": [2, 2],
            "terms": [
                {"support": [0, 2], "weight": "1", "matrix": p11},  # site 2 does not exist
            ],
            "_trap": "site_index_out_of_bounds",
        },
        # Poison 6: Total dimension D = 128 > 64 (7 qubits)
        {
            "case_id": "poison_06_dimension_out_of_bounds",
            "local_dims": [2, 2, 2, 2, 2, 2, 2],  # D = 128
            "terms": [
                {"support": [0, 1], "weight": "1", "matrix": p11},
            ],
            "_trap": "dimension_gt_64",
        },
    ]


def generate_mutations(
    base_cases: List[Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """
    Generates 40+ hostile mutations targeting:
    - Basis vector violating annihilation (P_i v != 0)
    - Dependent basis vectors
    - kernel_dim declared one too small (product-state-only answer)
    - Left inverse off in one entry (L * M != I)
    - Frustrated claim for frustration-free case
    - Frustration-free claim for frustrated case
    - Wrong witness for OUT_OF_SCOPE
    - Truncated vectors
    """
    mutations: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    mut_idx = 1

    # 1. Frustrated claim on frustration-free case
    case_ff = base_cases[0]  # hardcore triangle
    ans_ff_falsely_frustrated = {
        "id": case_ff["case_id"],
        "status": "SOLVED",
        "frustration_free": False,
        "certificate": {"kind": "left_inverse", "matrix": [[["1", "0"]] * 24] * 8},
    }
    mutations.append(
        (f"mut_{mut_idx:02d}_false_frustrated_claim", case_ff, ans_ff_falsely_frustrated)
    )
    mut_idx += 1

    # 2. Frustration-free claim on frustrated case
    case_frust = base_cases[5]  # triplet triangle
    ans_frust_falsely_ff = {
        "id": case_frust["case_id"],
        "status": "SOLVED",
        "frustration_free": True,
        "kernel_dim": 1,
        "kernel_basis": [[["1", "0"]] + [["0", "0"]] * 7],
    }
    mutations.append((f"mut_{mut_idx:02d}_false_ff_claim", case_frust, ans_frust_falsely_ff))
    mut_idx += 1

    # 3. Product-state-only answer (kernel_dim one too small)
    sol_ff = solve(case_ff)
    ans_subspace = copy.deepcopy(sol_ff)
    ans_subspace["kernel_dim"] = len(ans_subspace["kernel_basis"]) - 1
    ans_subspace["kernel_basis"] = ans_subspace["kernel_basis"][:-1]
    mutations.append((f"mut_{mut_idx:02d}_product_state_only_subspace", case_ff, ans_subspace))
    mut_idx += 1

    # 4. Basis vector violates annihilation by P_i
    ans_non_annihilated = copy.deepcopy(sol_ff)
    # Add |111> which is not in the kernel of hardcore terms
    ans_non_annihilated["kernel_basis"][0][7] = ["1", "0"]
    mutations.append((f"mut_{mut_idx:02d}_vector_not_annihilated", case_ff, ans_non_annihilated))
    mut_idx += 1

    # 5. Linearly dependent basis vectors
    ans_dep = copy.deepcopy(sol_ff)
    if len(ans_dep["kernel_basis"]) >= 2:
        ans_dep["kernel_basis"][1] = copy.deepcopy(ans_dep["kernel_basis"][0])
        mutations.append((f"mut_{mut_idx:02d}_dependent_basis", case_ff, ans_dep))
        mut_idx += 1

    # 6. Left inverse off in one entry
    sol_frust = solve(case_frust)
    ans_bad_left_inv = copy.deepcopy(sol_frust)
    # Perturb first entry of L
    ans_bad_left_inv["certificate"]["matrix"][0][0] = ["99", "0"]
    mutations.append((f"mut_{mut_idx:02d}_corrupted_left_inverse", case_frust, ans_bad_left_inv))
    mut_idx += 1

    # 7. Left inverse missing kind
    ans_bad_cert_kind = copy.deepcopy(sol_frust)
    ans_bad_cert_kind["certificate"]["kind"] = "not_a_left_inverse"
    mutations.append((f"mut_{mut_idx:02d}_bad_certificate_kind", case_frust, ans_bad_cert_kind))
    mut_idx += 1

    # 8. Truncated left inverse rows
    ans_trunc_left_inv = copy.deepcopy(sol_frust)
    ans_trunc_left_inv["certificate"]["matrix"] = ans_trunc_left_inv["certificate"]["matrix"][:-1]
    mutations.append((f"mut_{mut_idx:02d}_truncated_left_inverse", case_frust, ans_trunc_left_inv))
    mut_idx += 1

    # Generate systematic mutations across base cases
    for case in base_cases[:13]:
        sol = solve(case)
        cid = case["case_id"]

        if sol.get("frustration_free"):
            # Mut A: Corrupted coordinate length
            ans_bad_coord = copy.deepcopy(sol)
            ans_bad_coord["kernel_basis"][0] = ans_bad_coord["kernel_basis"][0][:-1]
            mutations.append((f"mut_{mut_idx:02d}_{cid}_truncated_coord", case, ans_bad_coord))
            mut_idx += 1

            # Mut B: Unparseable fraction string
            ans_bad_frac = copy.deepcopy(sol)
            ans_bad_frac["kernel_basis"][0][0] = ["invalid", "0"]
            mutations.append((f"mut_{mut_idx:02d}_{cid}_invalid_fraction", case, ans_bad_frac))
            mut_idx += 1

            # Mut C: Add non-kernel state (an eigenvector of term 0 with eigenvalue 1)
            ans_bad_state = copy.deepcopy(sol)
            t0 = case["terms"][0]
            mat_raw = [[GaussianRat.from_wire(elem) for elem in row] for row in t0["matrix"]]
            ext_p0 = extend_local_matrix(case["local_dims"], t0["support"], mat_raw)
            bad_vec = None
            for col_idx in range(len(ext_p0)):
                if any(not ext_p0[r][col_idx].is_zero() for r in range(len(ext_p0))):
                    bad_vec = [ext_p0[r][col_idx].to_wire() for r in range(len(ext_p0))]
                    break
            if bad_vec:
                ans_bad_state["kernel_basis"][0] = bad_vec
            else:
                ans_bad_state["kernel_basis"][0][-1] = ["99", "0"]
            mutations.append((f"mut_{mut_idx:02d}_{cid}_perturbed_state", case, ans_bad_state))
            mut_idx += 1
        else:
            # Mut D: Corrupted left inverse
            ans_corrupt_l = copy.deepcopy(sol)
            if "certificate" in ans_corrupt_l and "matrix" in ans_corrupt_l["certificate"]:
                ans_corrupt_l["certificate"]["matrix"][0][0] = ["5", "0"]
                mutations.append((f"mut_{mut_idx:02d}_{cid}_bad_left_inv", case, ans_corrupt_l))
                mut_idx += 1

    # Malformed refusal mutations
    case_oob = {"case_id": "mut_oob", "local_dims": [2] * 7, "terms": []}
    ans_bad_refusal = {"id": "mut_oob", "status": "UNKNOWN", "refusal_code": "WRONG_CODE"}
    mutations.append((f"mut_{mut_idx:02d}_bad_refusal_code", case_oob, ans_bad_refusal))
    mut_idx += 1

    ans_oob_solved = {
        "id": "mut_oob",
        "status": "SOLVED",
        "frustration_free": True,
        "kernel_dim": 1,
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
        "challenge_id": "C026",
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
