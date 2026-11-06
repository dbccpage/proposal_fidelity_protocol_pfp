# AuthorityEffect: None.
"""
Case and Hostile Mutation Generator for C028 (Jordan-Wigner & Majorana Mapping).

Generates:
1. 24 Base Cases (N from 2 to 12: JW, Parity, BK, Random invertible encodings; hopping, ring, Hubbard, quartic).
2. 8 Controls (same H under different encodings, term anticommutation rewrites, term reordering, cancelling terms).
3. 6 Poisoned Cases (singular M, non-Hermitian H, out-of-bound N=13).
4. 45+ Hostile Mutations (testing kill rate against dual checkers).
5. manifest.json with SHA-256 digests.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from c028_jordan_wigner_majorana_mapping.judge_packet.checkers.dual_evaluator import evaluate_dual
from c028_jordan_wigner_majorana_mapping.reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def identity_encoding(N: int) -> List[List[int]]:
    return [[1 if i == j else 0 for j in range(N)] for i in range(N)]


def parity_encoding(N: int) -> List[List[int]]:
    return [[1 if i >= j else 0 for j in range(N)] for i in range(N)]


def bravyi_kitaev_encoding(N: int) -> List[List[int]]:
    M = [[0] * N for _ in range(N)]
    for i in range(N):
        k = i + 1
        p2 = k & (-k)
        for j in range(i - p2 + 1, i + 1):
            M[i][j] = 1
    return M


def random_invertible_encoding(N: int, seed: int) -> List[List[int]]:
    rng = random.Random(seed)
    M = identity_encoding(N)
    for _ in range(N * 3):
        i = rng.randint(0, N - 1)
        j = rng.randint(0, N - 1)
        if i != j:
            for col in range(N):
                M[i][col] ^= M[j][col]
    return M


def make_hopping_chain(N: int, t_re: str = "1", t_im: str = "0") -> List[dict]:
    terms = []
    # c_t * a_j^dag a_{j+1} + c_t^* * a_{j+1}^dag a_j
    # if t = t_re + i t_im, t^* = t_re - i t_im
    t_im_neg = (
        str(-int(t_im))
        if "/" not in t_im and t_im != "0"
        else ("-1" if t_im == "1" else ("1" if t_im == "-1" else "0"))
    )
    for j in range(N - 1):
        terms.append(
            {
                "coeff": [t_re, t_im],
                "ops": [["dag", j], ["ann", j + 1]],
            }
        )
        terms.append(
            {
                "coeff": [t_re, t_im_neg],
                "ops": [["dag", j + 1], ["ann", j]],
            }
        )
    return terms


def make_hopping_ring(N: int, t_re: str = "1") -> List[dict]:
    terms = make_hopping_chain(N, t_re)
    terms.append(
        {
            "coeff": [t_re, "0"],
            "ops": [["dag", N - 1], ["ann", 0]],
        }
    )
    terms.append(
        {
            "coeff": [t_re, "0"],
            "ops": [["dag", 0], ["ann", N - 1]],
        }
    )
    return terms


def make_number_terms(N: int, u_re: str = "1/2") -> List[dict]:
    terms = []
    for j in range(N):
        terms.append(
            {
                "coeff": [u_re, "0"],
                "ops": [["dag", j], ["ann", j]],
            }
        )
    return terms


def make_quartic_pair(i: int, j: int, k: int, l: int, v_re: str = "1/4") -> List[dict]:
    # v * a_i^dag a_j^dag a_k a_l + v * a_l^dag a_k^dag a_j a_i
    return [
        {"coeff": [v_re, "0"], "ops": [["dag", i], ["dag", j], ["ann", k], ["ann", l]]},
        {"coeff": [v_re, "0"], "ops": [["dag", l], ["dag", k], ["ann", j], ["ann", i]]},
    ]


def build_base_cases() -> List[Dict[str, Any]]:
    cases = []

    # base_01: N=2, JW, 2-mode hopping (fq_06)
    cases.append(
        {
            "case_id": "c028_base_01_jw_2mode_hopping",
            "num_modes": 2,
            "encoding": identity_encoding(2),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # base_02: N=2, Parity, 2-mode hopping
    cases.append(
        {
            "case_id": "c028_base_02_parity_2mode_hopping",
            "num_modes": 2,
            "encoding": parity_encoding(2),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # base_03: N=2, BK, 2-mode hopping
    cases.append(
        {
            "case_id": "c028_base_03_bk_2mode_hopping",
            "num_modes": 2,
            "encoding": bravyi_kitaev_encoding(2),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # base_04: N=3, JW, tight-binding chain + chemical potential
    cases.append(
        {
            "case_id": "c028_base_04_jw_3mode_chain",
            "num_modes": 3,
            "encoding": identity_encoding(3),
            "terms": make_hopping_chain(3, "1") + make_number_terms(3, "1/3"),
        }
    )

    # base_05: N=3, Parity, hopping ring
    cases.append(
        {
            "case_id": "c028_base_05_parity_3mode_ring",
            "num_modes": 3,
            "encoding": parity_encoding(3),
            "terms": make_hopping_ring(3, "1/2"),
        }
    )

    # base_06: N=4, JW, number operators
    cases.append(
        {
            "case_id": "c028_base_06_jw_4mode_number",
            "num_modes": 4,
            "encoding": identity_encoding(4),
            "terms": make_number_terms(4, "1"),
        }
    )

    # base_07: N=4, BK, Hubbard-type chain with quartic interaction
    cases.append(
        {
            "case_id": "c028_base_07_bk_4mode_hubbard",
            "num_modes": 4,
            "encoding": bravyi_kitaev_encoding(4),
            "terms": make_hopping_chain(4, "1") + make_quartic_pair(0, 1, 2, 3, "1/2"),
        }
    )

    # base_08: N=4, Random invertible, 4-mode quartic interaction
    cases.append(
        {
            "case_id": "c028_base_08_rnd_4mode_quartic",
            "num_modes": 4,
            "encoding": random_invertible_encoding(4, seed=101),
            "terms": make_quartic_pair(0, 2, 1, 3, "3/4") + make_hopping_chain(4, "1/4"),
        }
    )

    # base_09: N=5, JW, 5-mode ring
    cases.append(
        {
            "case_id": "c028_base_09_jw_5mode_ring",
            "num_modes": 5,
            "encoding": identity_encoding(5),
            "terms": make_hopping_ring(5, "1"),
        }
    )

    # base_10: N=5, Parity, alternating complex hopping chain: i a_j^dag a_{j+1} - i a_{j+1}^dag a_j
    cases.append(
        {
            "case_id": "c028_base_10_parity_5mode_complex_hopping",
            "num_modes": 5,
            "encoding": parity_encoding(5),
            "terms": make_hopping_chain(5, t_re="0", t_im="1") + make_number_terms(5, "1/4"),
        }
    )

    # base_11: N=6, BK, long-range hopping between distant modes 0 and 5
    cases.append(
        {
            "case_id": "c028_base_11_bk_6mode_long_range",
            "num_modes": 6,
            "encoding": bravyi_kitaev_encoding(6),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 5]]},
                {"coeff": ["1", "0"], "ops": [["dag", 5], ["ann", 0]]},
                {"coeff": ["1/2", "0"], "ops": [["dag", 2], ["ann", 3]]},
                {"coeff": ["1/2", "0"], "ops": [["dag", 3], ["ann", 2]]},
            ],
        }
    )

    # base_12: N=6, Random invertible, random quadratic Hamiltonian
    cases.append(
        {
            "case_id": "c028_base_12_rnd_6mode_quadratic",
            "num_modes": 6,
            "encoding": random_invertible_encoding(6, seed=202),
            "terms": make_hopping_chain(6, "1/3") + make_number_terms(6, "2/5"),
        }
    )

    # base_13: N=7, JW, 7-mode chain with local potentials
    cases.append(
        {
            "case_id": "c028_base_13_jw_7mode_chain",
            "num_modes": 7,
            "encoding": identity_encoding(7),
            "terms": make_hopping_chain(7, "1/2") + make_number_terms(7, "1/7"),
        }
    )

    # base_14: N=7, Parity, 7-mode ring
    cases.append(
        {
            "case_id": "c028_base_14_parity_7mode_ring",
            "num_modes": 7,
            "encoding": parity_encoding(7),
            "terms": make_hopping_ring(7, "3/5"),
        }
    )

    # base_15: N=8, BK, 8-mode Hubbard model
    cases.append(
        {
            "case_id": "c028_base_15_bk_8mode_hubbard",
            "num_modes": 8,
            "encoding": bravyi_kitaev_encoding(8),
            "terms": make_hopping_chain(8, "1")
            + make_quartic_pair(0, 1, 2, 3, "1/8")
            + make_quartic_pair(4, 5, 6, 7, "1/8"),
        }
    )

    # base_16: N=8, Random invertible, random quadratic + quartic
    cases.append(
        {
            "case_id": "c028_base_16_rnd_8mode_mixed",
            "num_modes": 8,
            "encoding": random_invertible_encoding(8, seed=303),
            "terms": make_hopping_chain(8, "1/4") + make_number_terms(8, "1/2"),
        }
    )

    # base_17: N=9, JW, 9-mode chain
    cases.append(
        {
            "case_id": "c028_base_17_jw_9mode_chain",
            "num_modes": 9,
            "encoding": identity_encoding(9),
            "terms": make_hopping_chain(9, "1") + make_number_terms(9, "1/9"),
        }
    )

    # base_18: N=9, Parity, 9-mode ring
    cases.append(
        {
            "case_id": "c028_base_18_parity_9mode_ring",
            "num_modes": 9,
            "encoding": parity_encoding(9),
            "terms": make_hopping_ring(9, "1/3"),
        }
    )

    # base_19: N=10, BK, 10-mode long range hopping
    cases.append(
        {
            "case_id": "c028_base_19_bk_10mode_long_range",
            "num_modes": 10,
            "encoding": bravyi_kitaev_encoding(10),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 9]]},
                {"coeff": ["1", "0"], "ops": [["dag", 9], ["ann", 0]]},
                {"coeff": ["1/2", "0"], "ops": [["dag", 3], ["ann", 7]]},
                {"coeff": ["1/2", "0"], "ops": [["dag", 7], ["ann", 3]]},
            ],
        }
    )

    # base_20: N=10, Random invertible, 10-mode quadratic
    cases.append(
        {
            "case_id": "c028_base_20_rnd_10mode_quadratic",
            "num_modes": 10,
            "encoding": random_invertible_encoding(10, seed=404),
            "terms": make_hopping_chain(10, "1/5") + make_number_terms(10, "1/10"),
        }
    )

    # base_21: N=11, JW, 11-mode chain
    cases.append(
        {
            "case_id": "c028_base_21_jw_11mode_chain",
            "num_modes": 11,
            "encoding": identity_encoding(11),
            "terms": make_hopping_chain(11, "1") + make_number_terms(11, "1/11"),
        }
    )

    # base_22: N=11, Parity, 11-mode ring
    cases.append(
        {
            "case_id": "c028_base_22_parity_11mode_ring",
            "num_modes": 11,
            "encoding": parity_encoding(11),
            "terms": make_hopping_ring(11, "1/2"),
        }
    )

    # base_23: N=12, BK, 12-mode chain at bound
    cases.append(
        {
            "case_id": "c028_base_23_bk_12mode_bound",
            "num_modes": 12,
            "encoding": bravyi_kitaev_encoding(12),
            "terms": make_hopping_chain(12, "1") + make_number_terms(12, "1/12"),
        }
    )

    # base_24: N=12, Random invertible, 12-mode Hamiltonian at bound
    cases.append(
        {
            "case_id": "c028_base_24_rnd_12mode_bound",
            "num_modes": 12,
            "encoding": random_invertible_encoding(12, seed=505),
            "terms": make_hopping_chain(12, "1/6") + make_quartic_pair(0, 1, 2, 3, "1/12"),
        }
    )

    return cases


def build_control_cases() -> List[Dict[str, Any]]:
    controls = []

    # control_01: N=3, Same H under Jordan-Wigner vs Parity encoding
    controls.append(
        {
            "case_id": "c028_control_01_jw_vs_parity_n3",
            "num_modes": 3,
            "encoding": parity_encoding(3),
            "terms": make_hopping_chain(3, "1"),
        }
    )

    # control_02: N=4, Same H under Jordan-Wigner vs Bravyi-Kitaev
    controls.append(
        {
            "case_id": "c028_control_02_jw_vs_bk_n4",
            "num_modes": 4,
            "encoding": bravyi_kitaev_encoding(4),
            "terms": make_hopping_ring(4, "1/2"),
        }
    )

    # control_03: N=4, Out-of-normal-order term: a_2 a_1^dag entered as -a_1^dag a_2
    controls.append(
        {
            "case_id": "c028_control_03_out_of_order_anticommutation",
            "num_modes": 4,
            "encoding": identity_encoding(4),
            "terms": [
                # Instead of a_1^dag a_2, write - a_2 a_1^dag
                {"coeff": ["-1", "0"], "ops": [["ann", 2], ["dag", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 2], ["ann", 1]]},
            ],
        }
    )

    # control_04: N=3, Number operator written as 1 - a_j a_j^dag vs a_j^dag a_j
    controls.append(
        {
            "case_id": "c028_control_04_number_anti_normal_order",
            "num_modes": 3,
            "encoding": identity_encoding(3),
            "terms": [
                # 1 - a_0 a_0^dag = 1 * I - a_0 a_0^dag
                {"coeff": ["1", "0"], "ops": []},
                {"coeff": ["-1", "0"], "ops": [["ann", 0], ["dag", 0]]},
            ],
        }
    )

    # control_05: N=4, Nilpotent term a_1 a_1 (evaluates to zero)
    controls.append(
        {
            "case_id": "c028_control_05_nilpotent_zero_term",
            "num_modes": 4,
            "encoding": bravyi_kitaev_encoding(4),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["ann", 1], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # control_06: N=4, Cancelling pair: +T and -T
    controls.append(
        {
            "case_id": "c028_control_06_cancelling_pair",
            "num_modes": 4,
            "encoding": parity_encoding(4),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 2]]},
                {"coeff": ["1", "0"], "ops": [["dag", 2], ["ann", 0]]},
                {"coeff": ["1/2", "0"], "ops": [["dag", 1], ["ann", 3]]},
                {"coeff": ["-1/2", "0"], "ops": [["dag", 1], ["ann", 3]]},
            ],
        }
    )

    # control_07: N=5, Permuted term ordering in input list
    base_9_terms = list(make_hopping_ring(5, "1"))
    random.Random(777).shuffle(base_9_terms)
    controls.append(
        {
            "case_id": "c028_control_07_permuted_terms",
            "num_modes": 5,
            "encoding": identity_encoding(5),
            "terms": base_9_terms,
        }
    )

    # control_08: N=6, Quartic terms rewritten with anticommutation: a_0^dag a_1^dag = -a_1^dag a_0^dag
    controls.append(
        {
            "case_id": "c028_control_08_quartic_anticommuted",
            "num_modes": 6,
            "encoding": bravyi_kitaev_encoding(6),
            "terms": [
                # -v * a_1^dag a_0^dag a_2 a_3 + h.c.
                {"coeff": ["-1/4", "0"], "ops": [["dag", 1], ["dag", 0], ["ann", 2], ["ann", 3]]},
                {"coeff": ["-1/4", "0"], "ops": [["dag", 3], ["dag", 2], ["ann", 0], ["ann", 1]]},
            ],
        }
    )

    return controls


def build_poison_cases() -> List[Dict[str, Any]]:
    poisons = []

    # poison_01: N=3, Singular encoding matrix (row 0 = row 1)
    poisons.append(
        {
            "case_id": "c028_poison_01_singular_duplicate_rows",
            "num_modes": 3,
            "encoding": [
                [1, 0, 1],
                [1, 0, 1],
                [0, 1, 0],
            ],
            "terms": make_hopping_chain(3, "1"),
        }
    )

    # poison_02: N=4, Singular encoding matrix (all 1s)
    poisons.append(
        {
            "case_id": "c028_poison_02_singular_all_ones",
            "num_modes": 4,
            "encoding": [
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1],
            ],
            "terms": make_hopping_chain(4, "1"),
        }
    )

    # poison_03: N=3, Non-Hermitian: single hopping a_0^dag a_1 without adjoint
    poisons.append(
        {
            "case_id": "c028_poison_03_non_hermitian_missing_adjoint",
            "num_modes": 3,
            "encoding": identity_encoding(3),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
            ],
        }
    )

    # poison_04: N=3, Non-Hermitian: a_0^dag a_1 + 2 a_1^dag a_0 (coefficients 1 and 2 don't match)
    poisons.append(
        {
            "case_id": "c028_poison_04_non_hermitian_mismatched_coeffs",
            "num_modes": 3,
            "encoding": parity_encoding(3),
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["2", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # poison_05: N=4, Non-Hermitian: i a_0^dag a_1 + i a_1^dag a_0 (wrong sign on imaginary coupling)
    poisons.append(
        {
            "case_id": "c028_poison_05_non_hermitian_wrong_imaginary_sign",
            "num_modes": 4,
            "encoding": bravyi_kitaev_encoding(4),
            "terms": [
                {"coeff": ["0", "1"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["0", "1"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
    )

    # poison_06: N=13, Too many modes (N=13 > 12 bound)
    poisons.append(
        {
            "case_id": "c028_poison_06_too_many_modes",
            "num_modes": 13,
            "encoding": identity_encoding(13),
            "terms": make_hopping_chain(13, "1"),
        }
    )

    return poisons


def build_mutations(
    base_cases: List[Dict[str, Any]], poison_cases: List[Dict[str, Any]]
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    mutations: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    mut_idx = 1

    # 1. Flip sign on first Majorana (+ -> -)
    case_01 = base_cases[0]
    sol_01 = solve(case_01)
    ans_mut_01 = copy.deepcopy(sol_01)
    maj0 = ans_mut_01["majoranas"][0]
    flipped_maj0 = ("-" if maj0[0] == "+" else "+") + maj0[1:]
    ans_mut_01["majoranas"][0] = flipped_maj0
    mutations.append((f"mut_{mut_idx:02d}_flip_sign_first_majorana", case_01, ans_mut_01))
    mut_idx += 1

    # 2. Flip sign on last Majorana
    ans_mut_02 = copy.deepcopy(sol_01)
    majl = ans_mut_02["majoranas"][-1]
    flipped_majl = ("-" if majl[0] == "+" else "+") + majl[1:]
    ans_mut_02["majoranas"][-1] = flipped_majl
    mutations.append((f"mut_{mut_idx:02d}_flip_sign_last_majorana", case_01, ans_mut_02))
    mut_idx += 1

    # 3. Z string one qubit short in Majorana (dropped Z -> replaced with I)
    case_04 = base_cases[3]  # N=3
    sol_04 = solve(case_04)
    ans_mut_03 = copy.deepcopy(sol_04)
    for i, m_str in enumerate(ans_mut_03["majoranas"]):
        if "Z" in m_str:
            ans_mut_03["majoranas"][i] = m_str.replace("Z", "I", 1)
            break
    mutations.append((f"mut_{mut_idx:02d}_z_string_truncated", case_04, ans_mut_03))
    mut_idx += 1

    # 4. Y written as X in odd Majorana
    ans_mut_04 = copy.deepcopy(sol_04)
    for i, m_str in enumerate(ans_mut_04["majoranas"]):
        if "Y" in m_str:
            ans_mut_04["majoranas"][i] = m_str.replace("Y", "X", 1)
            break
    mutations.append((f"mut_{mut_idx:02d}_y_written_as_x", case_04, ans_mut_04))
    mut_idx += 1

    # 5. X written as Z in even Majorana
    ans_mut_05 = copy.deepcopy(sol_04)
    for i, m_str in enumerate(ans_mut_05["majoranas"]):
        if "X" in m_str:
            ans_mut_05["majoranas"][i] = m_str.replace("X", "Z", 1)
            break
    mutations.append((f"mut_{mut_idx:02d}_x_written_as_z", case_04, ans_mut_05))
    mut_idx += 1

    # 6. Non-anticommuting Majorana pair: copy maj[0] into maj[1]
    ans_mut_06 = copy.deepcopy(sol_01)
    ans_mut_06["majoranas"][1] = ans_mut_06["majoranas"][0]
    mutations.append((f"mut_{mut_idx:02d}_non_anticommuting_pair", case_01, ans_mut_06))
    mut_idx += 1

    # 7. Stray imaginary coefficient in Hamiltonian
    ans_mut_07 = copy.deepcopy(sol_01)
    ans_mut_07["hamiltonian"][0][1] = "1/2+i"
    mutations.append((f"mut_{mut_idx:02d}_stray_imaginary_pauli_coeff", case_01, ans_mut_07))
    mut_idx += 1

    # 8. Altered real coefficient: "1/2" -> "-1/2"
    ans_mut_08 = copy.deepcopy(sol_01)
    ans_mut_08["hamiltonian"][0][1] = "-1/2"
    mutations.append((f"mut_{mut_idx:02d}_altered_coefficient_sign", case_01, ans_mut_08))
    mut_idx += 1

    # 9. Merged pair with wrong sum: "1/2" -> "1"
    ans_mut_09 = copy.deepcopy(sol_01)
    ans_mut_09["hamiltonian"][0][1] = "1"
    mutations.append((f"mut_{mut_idx:02d}_merged_pair_wrong_sum", case_01, ans_mut_09))
    mut_idx += 1

    # 10. Identity / leading term dropped from Hamiltonian
    ans_mut_10 = copy.deepcopy(sol_01)
    ans_mut_10["hamiltonian"] = ans_mut_10["hamiltonian"][1:]
    mutations.append((f"mut_{mut_idx:02d}_dropped_pauli_term", case_01, ans_mut_10))
    mut_idx += 1

    # 11. Extra spurious Pauli term added
    ans_mut_11 = copy.deepcopy(sol_01)
    ans_mut_11["hamiltonian"].append(["ZZ", "1/4"])
    mutations.append((f"mut_{mut_idx:02d}_extra_spurious_pauli", case_01, ans_mut_11))
    mut_idx += 1

    # 12. Changed status from SOLVED to OUT_OF_SCOPE
    ans_mut_12 = copy.deepcopy(sol_01)
    ans_mut_12["status"] = "OUT_OF_SCOPE"
    mutations.append((f"mut_{mut_idx:02d}_false_out_of_scope", case_01, ans_mut_12))
    mut_idx += 1

    # 13. Altered kernel vector in singular witness to non-kernel vector
    case_p1 = poison_cases[0]
    sol_p1 = solve(case_p1)
    ans_mut_13 = copy.deepcopy(sol_p1)
    ans_mut_13["witness"]["kernel_vector"] = [1, 0, 0]  # Not in kernel!
    mutations.append((f"mut_{mut_idx:02d}_fake_kernel_vector", case_p1, ans_mut_13))
    mut_idx += 1

    # 14. Claimed SOLVED on singular encoding poison case
    ans_mut_14 = copy.deepcopy(sol_01)
    ans_mut_14["id"] = case_p1["case_id"]
    ans_mut_14["status"] = "SOLVED"
    mutations.append((f"mut_{mut_idx:02d}_claimed_solved_on_singular", case_p1, ans_mut_14))
    mut_idx += 1

    # 15. Claimed SOLVED on non-Hermitian poison case
    case_p3 = poison_cases[2]
    ans_mut_15 = copy.deepcopy(sol_04)
    ans_mut_15["id"] = case_p3["case_id"]
    ans_mut_15["status"] = "SOLVED"
    mutations.append((f"mut_{mut_idx:02d}_claimed_solved_on_non_hermitian", case_p3, ans_mut_15))
    mut_idx += 1

    # 16. Changed refusal code on N=13 poison case
    case_p6 = poison_cases[5]
    sol_p6 = solve(case_p6)
    ans_mut_16 = copy.deepcopy(sol_p6)
    ans_mut_16["refusal_code"] = "WRONG_REFUSAL"
    mutations.append((f"mut_{mut_idx:02d}_wrong_refusal_code_oversized", case_p6, ans_mut_16))
    mut_idx += 1

    # Systematic mutations 17..48 across base cases
    for case in base_cases[:16]:
        sol = solve(case)
        cid = case["case_id"]

        # Mut A: Sign flip on a random Majorana
        ans_a = copy.deepcopy(sol)
        idx_flip = len(ans_a["majoranas"]) // 2
        m_str = ans_a["majoranas"][idx_flip]
        ans_a["majoranas"][idx_flip] = ("-" if m_str[0] == "+" else "+") + m_str[1:]
        mutations.append((f"mut_{mut_idx:02d}_{cid}_majorana_sign_flip", case, ans_a))
        mut_idx += 1

        # Mut B: Coefficient perturbation in Hamiltonian
        if ans_a.get("hamiltonian"):
            ans_b = copy.deepcopy(sol)
            c_val = ans_b["hamiltonian"][0][1]
            ans_b["hamiltonian"][0][1] = "999" if c_val != "999" else "1"
            mutations.append((f"mut_{mut_idx:02d}_{cid}_coeff_perturbation", case, ans_b))
            mut_idx += 1

    return mutations


def main() -> None:
    judge_dir = _pkg_root / "judge_packet"
    cases_dir = judge_dir / "cases"
    mut_dir = judge_dir / "mutation_suite"

    cases_dir.mkdir(parents=True, exist_ok=True)
    mut_dir.mkdir(parents=True, exist_ok=True)

    base_cases = build_base_cases()
    control_cases = build_control_cases()
    poison_cases = build_poison_cases()

    print(
        f"Generated {len(base_cases)} base cases, {len(control_cases)} control cases, {len(poison_cases)} poison cases."
    )

    # Write cases
    for idx, case in enumerate(base_cases, 1):
        p = cases_dir / f"base_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

    for idx, case in enumerate(control_cases, 1):
        p = cases_dir / f"control_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

    for idx, case in enumerate(poison_cases, 1):
        p = cases_dir / f"poison_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

    # Generate and write mutations
    mutations = build_mutations(base_cases, poison_cases)
    print(f"Generated {len(mutations)} hostile mutations.")

    mut_kill_count = 0
    for idx, (m_id, case, mut_ans) in enumerate(mutations, 1):
        passed, msg, _ = evaluate_dual(case, mut_ans)
        if not passed:
            mut_kill_count += 1
        else:
            print(f"WARNING: Mutation {m_id} was NOT killed: {msg}")

        mut_record = {
            "id": m_id,
            "case": case,
            "mutated_answer": mut_ans,
            "expected_rejection": True,
            "kill_verified": not passed,
            "rejection_message": msg,
        }
        p = mut_dir / f"{m_id}.json"
        p.write_bytes(canonical_json_bytes(mut_record))

    print(
        f"Mutation kill rate: {mut_kill_count}/{len(mutations)} ({mut_kill_count / len(mutations) * 100:.1f}%)"
    )

    # Generate manifest.json
    manifest: Dict[str, Any] = {
        "challenge_id": "c028_jordan_wigner_majorana_mapping",
        "authority_effect": "None",
        "counts": {
            "base_cases": len(base_cases),
            "control_cases": len(control_cases),
            "poison_cases": len(poison_cases),
            "mutations": len(mutations),
            "mutations_killed": mut_kill_count,
        },
        "files": {},
    }

    all_files = sorted(list(cases_dir.glob("*.json")) + list(mut_dir.glob("*.json")))
    for f in all_files:
        rel_path = f.relative_to(judge_dir).as_posix()
        manifest["files"][rel_path] = {
            "sha256": sha256_file(f),
            "size": f.stat().st_size,
        }

    manifest_path = judge_dir / "manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    print(f"Wrote manifest.json with {len(manifest['files'])} hashed entries.")


if __name__ == "__main__":
    main()
