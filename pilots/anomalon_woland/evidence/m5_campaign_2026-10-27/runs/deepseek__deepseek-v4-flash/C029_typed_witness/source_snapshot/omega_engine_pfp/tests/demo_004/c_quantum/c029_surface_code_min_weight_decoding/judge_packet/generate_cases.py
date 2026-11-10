# AuthorityEffect: None.
"""
Case and Hostile Mutation Generator for C029 (Minimum-Weight Surface-Code Decoding).

Generates:
1. 36 Base Cases (Rotated d in {3, 5, 7}, Toric L in {3, 4, 5}; uniform and random weights).
2. 10 Controls (lattice reflections, translations, check/qubit relabellings).
3. 6 Poisoned Cases (odd parity torus, distance out of bounds, greedy traps).
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

from judge_packet.checkers.dual_evaluator import evaluate_dual
from reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def make_toric_hz(L: int) -> List[List[int]]:
    """Builds H_Z for L x L toric code."""
    m = L * L
    n = 2 * L * L
    hz = [[0] * n for _ in range(m)]
    for x in range(L):
        for y in range(L):
            p = x * L + y
            e_h_bot = x * L + y
            e_h_top = ((x + 1) % L) * L + y
            e_v_left = L * L + (x * L + y)
            e_v_right = L * L + (x * L + ((y + 1) % L))
            for e in [e_h_bot, e_h_top, e_v_left, e_v_right]:
                hz[p][e] ^= 1
    return hz


def make_rotated_hz(d: int) -> List[List[int]]:
    """Builds H_Z for d x d rotated surface code."""
    n = d * d
    z_checks = []
    for r in range(-1, d):
        for c in range(-1, d):
            if (r + c) % 2 != 0:
                continue
            qubits = []
            for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                qr, qc = r + dr, c + dc
                if 0 <= qr < d and 0 <= qc < d:
                    qubits.append(qr * d + qc)
            if (c == -1 or c == d - 1) and (r != -1 and r != d - 1):
                continue
            if len(qubits) in (2, 4):
                z_checks.append(qubits)

    m = (d * d - 1) // 2
    hz = [[0] * n for _ in range(m)]
    for idx, q_list in enumerate(z_checks[:m]):
        for q in q_list:
            hz[idx][q] = 1
    return hz


def generate_error_syndrome(hz: List[List[int]], error_qubits: List[int]) -> List[int]:
    """Generates syndrome s = H_Z * e mod 2."""
    m = len(hz)
    n = len(hz[0]) if m > 0 else 0
    s = [0] * m
    for r in range(m):
        row_sum = sum(hz[r][q] for q in error_qubits if 0 <= q < n) % 2
        s[r] = row_sum
    return s


def build_base_cases() -> List[Dict[str, Any]]:
    cases = []
    case_idx = 1

    # Rotated surface codes: d in {3, 5, 7}, 8 cases each (24 cases total)
    for d in [3, 5, 7]:
        hz = make_rotated_hz(d)
        len(hz)
        n = len(hz[0])

        for sub_i in range(8):
            rng = random.Random(1000 * d + sub_i)
            # Uniform weights in half, random in 1..5 in half
            if sub_i % 2 == 0:
                weights = [1] * n
            else:
                weights = [rng.randint(1, 5) for _ in range(n)]

            # Generate error pattern
            if sub_i == 0:
                # s = 0 case
                error_qubits = []
            elif sub_i == 1:
                # single error near boundary
                error_qubits = [0]
            elif sub_i == 2:
                # single error in interior
                error_qubits = [n // 2]
            else:
                # random small error chain
                num_err = rng.randint(2, min(d + 1, n // 2))
                error_qubits = rng.sample(range(n), num_err)

            syndrome = generate_error_syndrome(hz, error_qubits)
            cases.append(
                {
                    "case_id": f"c029_base_{case_idx:02d}_rot_d{d}_sub{sub_i}",
                    "code": "rotated",
                    "distance": d,
                    "hz": hz,
                    "weights": weights,
                    "syndrome": syndrome,
                }
            )
            case_idx += 1

    # Toric codes: L in {3, 4, 5}, 4 cases each (12 cases total)
    for L in [3, 4, 5]:
        hz = make_toric_hz(L)
        len(hz)
        n = len(hz[0])

        for sub_i in range(4):
            rng = random.Random(2000 * L + sub_i)
            if sub_i % 2 == 0:
                weights = [1] * n
            else:
                weights = [rng.randint(1, 5) for _ in range(n)]

            if sub_i == 0:
                error_qubits = []
            elif sub_i == 1:
                error_qubits = [0]
            else:
                num_err = rng.randint(2, min(L + 1, n // 2))
                error_qubits = rng.sample(range(n), num_err)

            syndrome = generate_error_syndrome(hz, error_qubits)
            cases.append(
                {
                    "case_id": f"c029_base_{case_idx:02d}_toric_L{L}_sub{sub_i}",
                    "code": "toric",
                    "distance": L,
                    "hz": hz,
                    "weights": weights,
                    "syndrome": syndrome,
                }
            )
            case_idx += 1

    return cases


def build_control_cases() -> List[Dict[str, Any]]:
    controls = []
    ctrl_idx = 1

    # 1. Toric translation symmetry control (shift all qubits and checks by 1 on torus)
    hz_toric_3 = make_toric_hz(3)
    # Permute columns and rows cyclically
    hz_t_shift = [hz_toric_3[(r + 1) % 9] for r in range(9)]
    weights_shift = [1] * 18
    s_shift = generate_error_syndrome(hz_t_shift, [2, 5])
    controls.append(
        {
            "case_id": f"c029_control_{ctrl_idx:02d}_toric_translation_symmetry",
            "code": "toric",
            "distance": 3,
            "hz": hz_t_shift,
            "weights": weights_shift,
            "syndrome": s_shift,
        }
    )
    ctrl_idx += 1

    # 2. Rotated reflection symmetry control (reverse check rows and columns)
    hz_rot_3 = make_rotated_hz(3)
    hz_rot_rev = [list(reversed(row)) for row in reversed(hz_rot_3)]
    controls.append(
        {
            "case_id": f"c029_control_{ctrl_idx:02d}_rotated_reflection_symmetry",
            "code": "rotated",
            "distance": 3,
            "hz": hz_rot_rev,
            "weights": [1] * 9,
            "syndrome": [1, 0, 0, 1],
        }
    )
    ctrl_idx += 1

    # 3-10: Check and qubit permutations preserving decoding invariants
    for i in range(3, 11):
        d_val = 3 if i <= 6 else 5
        hz_orig = make_rotated_hz(d_val)
        m = len(hz_orig)
        n = len(hz_orig[0])

        rng = random.Random(3000 + i)
        q_perm = list(range(n))
        rng.shuffle(q_perm)

        hz_perm = [[hz_orig[r][q_perm[c]] for c in range(n)] for r in range(m)]
        weights_perm = [1] * n
        err = [q_perm[0], q_perm[1]]
        s_perm = generate_error_syndrome(hz_perm, err)

        controls.append(
            {
                "case_id": f"c029_control_{ctrl_idx:02d}_relabeled_d{d_val}_seed{i}",
                "code": "rotated",
                "distance": d_val,
                "hz": hz_perm,
                "weights": weights_perm,
                "syndrome": s_perm,
            }
        )
        ctrl_idx += 1

    return controls


def build_poison_cases() -> List[Dict[str, Any]]:
    poisons = []

    # poison_01: Toric code with odd parity syndrome (impossible image)
    hz_t3 = make_toric_hz(3)
    poisons.append(
        {
            "case_id": "c029_poison_01_toric_odd_parity",
            "code": "toric",
            "distance": 3,
            "hz": hz_t3,
            "weights": [1] * 18,
            "syndrome": [1, 0, 0, 0, 0, 0, 0, 0, 0],  # sum is 1 (odd)
        }
    )

    # poison_02: Toric code with odd parity on L=4
    hz_t4 = make_toric_hz(4)
    s_odd_16 = [0] * 16
    s_odd_16[0] = 1
    s_odd_16[1] = 1
    s_odd_16[2] = 1  # sum is 3 (odd)
    poisons.append(
        {
            "case_id": "c029_poison_02_toric_odd_parity_L4",
            "code": "toric",
            "distance": 4,
            "hz": hz_t4,
            "weights": [1] * 32,
            "syndrome": s_odd_16,
        }
    )

    # poison_03: Rotated code with distance out of bounds (d=9)
    poisons.append(
        {
            "case_id": "c029_poison_03_distance_out_of_bounds_rot9",
            "code": "rotated",
            "distance": 9,
            "hz": [[0] * 81],
            "weights": [1] * 81,
            "syndrome": [0],
        }
    )

    # poison_04: Toric code with distance out of bounds (L=6)
    poisons.append(
        {
            "case_id": "c029_poison_04_distance_out_of_bounds_toric6",
            "code": "toric",
            "distance": 6,
            "hz": [[0] * 72],
            "weights": [1] * 72,
            "syndrome": [0],
        }
    )

    # poison_05: Greedy trap: pair of defects closer in hop count, but cheaper detour in weighted metric
    hz_r3 = make_rotated_hz(3)
    # Give heavy weight to direct edge 1, make detour edges light
    weights_trap = [1, 5, 1, 1, 1, 1, 1, 1, 1]
    s_trap = generate_error_syndrome(hz_r3, [1])
    poisons.append(
        {
            "case_id": "c029_poison_05_greedy_weight_trap",
            "code": "rotated",
            "distance": 3,
            "hz": hz_r3,
            "weights": weights_trap,
            "syndrome": s_trap,
        }
    )

    # poison_06: Chain of weight ceil(d/2) crossing logical class
    hz_r5 = make_rotated_hz(5)
    s_chain = generate_error_syndrome(hz_r5, [0, 1, 2])
    poisons.append(
        {
            "case_id": "c029_poison_06_logical_boundary_chain",
            "code": "rotated",
            "distance": 5,
            "hz": hz_r5,
            "weights": [1] * 25,
            "syndrome": s_chain,
        }
    )

    return poisons


def build_mutations(
    base_cases: List[Dict[str, Any]], poison_cases: List[Dict[str, Any]]
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    mutations: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    mut_idx = 1

    case_02 = base_cases[1]  # non-empty correction
    sol_02 = solve(case_02)

    # 1. Right syndrome, but one extra spurious qubit (suboptimal)
    ans_extra_q = copy.deepcopy(sol_02)
    # Find a qubit not in correction
    corr_set = set(ans_extra_q["correction"])
    n_qubits = len(case_02["weights"])
    for q in range(n_qubits):
        if q not in corr_set:
            ans_extra_q["correction"].append(q)
            ans_extra_q["weight"] += case_02["weights"][q]
            break
    mutations.append((f"mut_{mut_idx:02d}_extra_spurious_qubit", case_02, ans_extra_q))
    mut_idx += 1

    # 2. Correction with wrong syndrome (drop one qubit from correction)
    ans_wrong_s = copy.deepcopy(sol_02)
    if ans_wrong_s["correction"]:
        ans_wrong_s["correction"] = ans_wrong_s["correction"][1:]
        ans_wrong_s["weight"] = sum(case_02["weights"][q] for q in ans_wrong_s["correction"])
    mutations.append((f"mut_{mut_idx:02d}_dropped_qubit_wrong_syndrome", case_02, ans_wrong_s))
    mut_idx += 1

    # 3. Dual certificate with smaller objective than actual weight (fake certificate)
    ans_small_dual = copy.deepcopy(sol_02)
    if ans_small_dual["certificate"]["vertex_duals"]:
        ans_small_dual["certificate"]["vertex_duals"][0] = "0"
    mutations.append((f"mut_{mut_idx:02d}_smaller_dual_objective", case_02, ans_small_dual))
    mut_idx += 1

    # 4. Dual violating edge feasibility constraint on unmatched edge
    ans_violated_edge = copy.deepcopy(sol_02)
    if ans_small_dual["certificate"]["vertex_duals"]:
        ans_violated_edge["certificate"]["vertex_duals"][0] = "999"
    mutations.append(
        (f"mut_{mut_idx:02d}_dual_violating_edge_constraint", case_02, ans_violated_edge)
    )
    mut_idx += 1

    # 5. Stated weight mismatch
    ans_weight_mismatch = copy.deepcopy(sol_02)
    ans_weight_mismatch["weight"] = ans_weight_mismatch["weight"] + 1
    mutations.append((f"mut_{mut_idx:02d}_stated_weight_mismatch", case_02, ans_weight_mismatch))
    mut_idx += 1

    # 6. Claimed SOLVED on odd parity toric poison case
    p1 = poison_cases[0]
    ans_p1_solved = copy.deepcopy(sol_02)
    ans_p1_solved["id"] = p1["case_id"]
    ans_p1_solved["status"] = "SOLVED"
    mutations.append((f"mut_{mut_idx:02d}_claimed_solved_on_odd_torus", p1, ans_p1_solved))
    mut_idx += 1

    # 7. False refusal code on oversized distance
    p3 = poison_cases[2]
    sol_p3 = solve(p3)
    ans_p3_bad_ref = copy.deepcopy(sol_p3)
    ans_p3_bad_ref["refusal_code"] = "WRONG_REFUSAL_CODE"
    mutations.append((f"mut_{mut_idx:02d}_wrong_refusal_code", p3, ans_p3_bad_ref))
    mut_idx += 1

    # 8. Negative blossom dual
    ans_neg_blossom = copy.deepcopy(sol_02)
    ans_neg_blossom["certificate"]["odd_set_duals"] = [[[0, 1, 2], "-1"]]
    mutations.append((f"mut_{mut_idx:02d}_negative_blossom_dual", case_02, ans_neg_blossom))
    mut_idx += 1

    # 9. Even size blossom
    ans_even_blossom = copy.deepcopy(sol_02)
    ans_even_blossom["certificate"]["odd_set_duals"] = [[[0, 1], "1"]]
    mutations.append((f"mut_{mut_idx:02d}_even_blossom_size", case_02, ans_even_blossom))
    mut_idx += 1

    # 10. False OUT_OF_SCOPE status on valid case
    ans_false_oos = copy.deepcopy(sol_02)
    ans_false_oos["status"] = "OUT_OF_SCOPE"
    mutations.append((f"mut_{mut_idx:02d}_false_out_of_scope", case_02, ans_false_oos))
    mut_idx += 1

    # Systematic mutations 11..48 across base cases
    for case in base_cases[:20]:
        sol = solve(case)
        cid = case["case_id"]

        # Mut A: Corrupt stated weight
        ans_a = copy.deepcopy(sol)
        ans_a["weight"] = ans_a["weight"] + 10
        mutations.append((f"mut_{mut_idx:02d}_{cid}_corrupt_weight", case, ans_a))
        mut_idx += 1

        # Mut B: Perturb duals
        if ans_a.get("certificate", {}).get("vertex_duals"):
            ans_b = copy.deepcopy(sol)
            ans_b["certificate"]["vertex_duals"][0] = "99"
            mutations.append((f"mut_{mut_idx:02d}_{cid}_perturbed_dual", case, ans_b))
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

    for idx, case in enumerate(base_cases, 1):
        p = cases_dir / f"base_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

    for idx, case in enumerate(control_cases, 1):
        p = cases_dir / f"control_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

    for idx, case in enumerate(poison_cases, 1):
        p = cases_dir / f"poison_{idx:02d}.json"
        p.write_bytes(canonical_json_bytes(case))

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

    manifest: Dict[str, Any] = {
        "challenge_id": "c029_surface_code_min_weight_decoding",
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
