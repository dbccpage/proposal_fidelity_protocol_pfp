# AuthorityEffect: None.
"""
Case and Mutation Generator for C025.

Generates:
1. 15 Base Cases (prime powers, partial sets, composites, open requests).
2. 8 Gauge / Relabel Controls (fixed first basis B_0).
3. 5 Poisoned Schema-Valid Cases (modular arithmetic traps, open problem traps).
4. 40 Hostile Mutations (testing kill rate against dual checkers).
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

from reference_solver.mub_construction import get_standard_mubs
from reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_base_cases() -> List[Dict[str, Any]]:
    """15 base cases: prime powers, partial sets, composites, open requests."""
    return [
        # Complete sets in prime powers
        {"case_id": "base_01_d2_k3", "dimension": 2, "num_bases": 3, "fixed_first_basis": None},
        {"case_id": "base_02_d3_k4", "dimension": 3, "num_bases": 4, "fixed_first_basis": None},
        {"case_id": "base_03_d4_k5", "dimension": 4, "num_bases": 5, "fixed_first_basis": None},
        {"case_id": "base_04_d5_k6", "dimension": 5, "num_bases": 6, "fixed_first_basis": None},
        {"case_id": "base_05_d7_k8", "dimension": 7, "num_bases": 8, "fixed_first_basis": None},
        {"case_id": "base_06_d8_k9", "dimension": 8, "num_bases": 9, "fixed_first_basis": None},
        {"case_id": "base_07_d9_k10", "dimension": 9, "num_bases": 10, "fixed_first_basis": None},
        # Partial sets
        {"case_id": "base_08_d3_k2", "dimension": 3, "num_bases": 2, "fixed_first_basis": None},
        {"case_id": "base_09_d4_k3", "dimension": 4, "num_bases": 3, "fixed_first_basis": None},
        {"case_id": "base_10_d5_k3", "dimension": 5, "num_bases": 3, "fixed_first_basis": None},
        # Composites (tensor bound k=3)
        {"case_id": "base_11_d6_k3", "dimension": 6, "num_bases": 3, "fixed_first_basis": None},
        {"case_id": "base_12_d10_k3", "dimension": 10, "num_bases": 3, "fixed_first_basis": None},
        # Open requests in d=6
        {
            "case_id": "base_13_d6_k4_open",
            "dimension": 6,
            "num_bases": 4,
            "fixed_first_basis": None,
        },
        {
            "case_id": "base_14_d6_k5_open",
            "dimension": 6,
            "num_bases": 5,
            "fixed_first_basis": None,
        },
        {
            "case_id": "base_15_d6_k7_open",
            "dimension": 6,
            "num_bases": 7,
            "fixed_first_basis": None,
        },
    ]


def make_hadamard_2() -> List[Dict[str, Any]]:
    # |+>, |-> in Q(zeta_4)
    # entry coords length 4
    # |0> + |1>: coord0 = 1, coord1 = 1
    # |0> - |1>: coord0 = 1, coord1 = -1
    v0 = {"norm2": "2", "entries": [["1", "0", "0", "0"], ["1", "0", "0", "0"]]}
    v1 = {"norm2": "2", "entries": [["1", "0", "0", "0"], ["-1", "0", "0", "0"]]}
    return [v0, v1]


def make_pauli_y_2() -> List[Dict[str, Any]]:
    # |+i>, |-i> in Q(zeta_4)
    # |0> + i|1>, |0> - i|1>
    v0 = {"norm2": "2", "entries": [["1", "0", "0", "0"], ["0", "1", "0", "0"]]}
    v1 = {"norm2": "2", "entries": [["1", "0", "0", "0"], ["0", "-1", "0", "0"]]}
    return [v0, v1]


def make_cyclic_perm(d: int, m: int, shift: int = 1) -> List[Dict[str, Any]]:
    # e_{(k + shift) % d}
    basis = []
    for k in range(d):
        target = (k + shift) % d
        entries = []
        for coord in range(d):
            coeffs = ["0"] * m
            if coord == target:
                coeffs[0] = "1"
            entries.append(coeffs)
        basis.append({"norm2": "1", "entries": entries})
    return basis


def make_fourier_3() -> List[Dict[str, Any]]:
    # Fourier basis in d=3, m=3: v_k = sum_j zeta_3^{k*j} |j>, norm2 = 3
    basis = []
    for k in range(3):
        entries = []
        for j in range(3):
            pow_val = (k * j) % 3
            coeffs = ["0", "0", "0"]
            coeffs[pow_val] = "1"
            entries.append(coeffs)
        basis.append({"norm2": "3", "entries": entries})
    return basis


def make_hadamard_tensor_4() -> List[Dict[str, Any]]:
    # H (x) H in d=4, m=4
    # |s0, s1> = (|0> + s0 |1>) (x) (|0> + s1 |1>)
    basis = []
    for s0 in (1, -1):
        for s1 in (1, -1):
            # entries in |00>, |01>, |10>, |11|
            # (1, s1, s0, s0*s1)
            entries = [
                ["1", "0", "0", "0"],
                [str(s1), "0", "0", "0"],
                [str(s0), "0", "0", "0"],
                [str(s0 * s1), "0", "0", "0"],
            ]
            basis.append({"norm2": "4", "entries": entries})
    return basis


def make_reversal_perm(d: int, m: int) -> List[Dict[str, Any]]:
    basis = []
    for k in range(d):
        target = d - 1 - k
        entries = []
        for coord in range(d):
            coeffs = ["0"] * m
            if coord == target:
                coeffs[0] = "1"
            entries.append(coeffs)
        basis.append({"norm2": "1", "entries": entries})
    return basis


def generate_control_cases() -> List[Dict[str, Any]]:
    """8 controls with fixed first basis B_0."""
    return [
        {
            "case_id": "ctrl_01_d2_hadamard",
            "dimension": 2,
            "num_bases": 3,
            "fixed_first_basis": make_hadamard_2(),
        },
        {
            "case_id": "ctrl_02_d2_pauli_y",
            "dimension": 2,
            "num_bases": 3,
            "fixed_first_basis": make_pauli_y_2(),
        },
        {
            "case_id": "ctrl_03_d3_perm",
            "dimension": 3,
            "num_bases": 4,
            "fixed_first_basis": make_cyclic_perm(3, 3, 1),
        },
        {
            "case_id": "ctrl_04_d3_fourier",
            "dimension": 3,
            "num_bases": 4,
            "fixed_first_basis": make_fourier_3(),
        },
        {
            "case_id": "ctrl_05_d4_perm",
            "dimension": 4,
            "num_bases": 5,
            "fixed_first_basis": make_cyclic_perm(4, 4, 2),
        },
        {
            "case_id": "ctrl_06_d4_h_kron_h",
            "dimension": 4,
            "num_bases": 5,
            "fixed_first_basis": make_hadamard_tensor_4(),
        },
        {
            "case_id": "ctrl_07_d5_perm",
            "dimension": 5,
            "num_bases": 3,
            "fixed_first_basis": make_cyclic_perm(5, 5, 2),
        },
        {
            "case_id": "ctrl_08_d7_reversal",
            "dimension": 7,
            "num_bases": 3,
            "fixed_first_basis": make_reversal_perm(7, 7),
        },
    ]


def generate_poisoned_cases() -> List[Dict[str, Any]]:
    """5 poisoned schema-valid cases."""
    # Fixed B0 for d=6 from tensor product
    m6, b6 = get_standard_mubs(6)
    tensor_b0 = b6[0]
    return [
        {
            "case_id": "poison_01_d4_z4_trap",
            "dimension": 4,
            "num_bases": 5,
            "fixed_first_basis": None,
            "_trap": "modular_z4_arithmetic",
        },
        {
            "case_id": "poison_02_d8_z8_trap",
            "dimension": 8,
            "num_bases": 9,
            "fixed_first_basis": None,
            "_trap": "modular_z8_arithmetic",
        },
        {
            "case_id": "poison_03_d9_z9_trap",
            "dimension": 9,
            "num_bases": 10,
            "fixed_first_basis": None,
            "_trap": "modular_z9_arithmetic",
        },
        {
            "case_id": "poison_04_d6_k4_fixed_b0",
            "dimension": 6,
            "num_bases": 4,
            "fixed_first_basis": tensor_b0,
            "_trap": "claim_tensor_completion",
        },
        {
            "case_id": "poison_05_d10_k3_tensor_trap",
            "dimension": 10,
            "num_bases": 3,
            "fixed_first_basis": None,
            "_trap": "claim_d5_bound_in_d10",
        },
    ]


def generate_mutations(
    base_cases: List[Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """
    Generates 40 hostile mutations targeting:
    - float corruption
    - norm corruption
    - non-orthogonality
    - non-unbiasedness
    - false completion on d=6
    - missing fixed B0
    - schema corruptions
    """
    mutations: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []

    # 1. d=6 false completion: 7 bases claimed
    case_d6 = {"case_id": "mut_d6_open_claimed", "dimension": 6, "num_bases": 4}
    # fake answer claiming SOLVED with 4 bases
    m6, b6 = get_standard_mubs(6)
    fake_b4 = b6 + [b6[0]]  # duplicate
    ans_fake_d6 = {
        "id": "mut_d6_open_claimed",
        "status": "SOLVED",
        "cyclotomic_order": 12,
        "bases": fake_b4,
    }
    mutations.append(("mut_01_d6_open_falsely_solved", case_d6, ans_fake_d6))

    # 2. d=6 claimed with wrong refusal code
    ans_wrong_code = {
        "id": "mut_d6_wrong_code",
        "status": "UNKNOWN",
        "refusal_code": "NOT_AN_OPEN_PROBLEM",
    }
    mutations.append(("mut_02_d6_wrong_refusal_code", case_d6, ans_wrong_code))

    # 3. out of scope claimed as SOLVED
    case_oos = {"case_id": "mut_oos", "dimension": 3, "num_bases": 5}
    sol_d3 = solve({"case_id": "d3", "dimension": 3, "num_bases": 4})
    ans_oos_solved = copy.deepcopy(sol_d3)
    ans_oos_solved["id"] = "mut_oos"
    ans_oos_solved["bases"].append(ans_oos_solved["bases"][0])
    mutations.append(("mut_03_oos_falsely_solved", case_oos, ans_oos_solved))

    # 4. out of scope with missing witness
    ans_oos_no_witness = {"id": "mut_oos_bad_wit", "status": "OUT_OF_SCOPE", "witness": {}}
    mutations.append(("mut_04_oos_bad_witness", case_oos, ans_oos_no_witness))

    # 5. Z4 arithmetic in d=4 (Z4 chirps: core_4^{s*x^2 + k*x})
    case_d4 = {"case_id": "mut_d4_z4", "dimension": 4, "num_bases": 5}
    z4_bases = []
    # comp basis
    b0_z4 = []
    for k in range(4):
        ent = [["1", "0", "0", "0"] if c == k else ["0", "0", "0", "0"] for c in range(4)]
        b0_z4.append({"norm2": "1", "entries": ent})
    z4_bases.append(b0_z4)
    # Z4 chirps: (s*j^2 + k*j) mod 4
    for s in range(4):
        bs = []
        for k in range(4):
            ent = []
            for j in range(4):
                pow_val = (s * j * j + k * j) % 4
                coeffs = ["0", "0", "0", "0"]
                coeffs[pow_val] = "1"
                ent.append(coeffs)
            bs.append({"norm2": "4", "entries": ent})
        z4_bases.append(bs)
    ans_z4 = {"id": "mut_d4_z4", "status": "SOLVED", "cyclotomic_order": 4, "bases": z4_bases}
    mutations.append(("mut_05_d4_z4_modular_trap", case_d4, ans_z4))

    # Generate more mutations by perturbing valid solutions
    test_dims = [(2, 3), (3, 4), (4, 5), (5, 6), (7, 8), (8, 9), (9, 10)]
    mut_idx = 6

    for d, k in test_dims:
        case = {"case_id": f"mut_case_d{d}", "dimension": d, "num_bases": k}
        sol = solve(case)

        # Mut A: Bad norm2
        ans_bad_norm = copy.deepcopy(sol)
        ans_bad_norm["bases"][0][0]["norm2"] = "2"  # declared 2 but computed 1
        mutations.append((f"mut_{mut_idx:02d}_d{d}_bad_norm2", case, ans_bad_norm))
        mut_idx += 1

        # Mut B: Negative norm2
        ans_neg_norm = copy.deepcopy(sol)
        ans_neg_norm["bases"][0][0]["norm2"] = "-1"
        mutations.append((f"mut_{mut_idx:02d}_d{d}_neg_norm2", case, ans_neg_norm))
        mut_idx += 1

        # Mut C: Perturb one entry by root of unity
        ans_root_pert = copy.deepcopy(sol)
        ans_root_pert["cyclotomic_order"]
        # In basis 1, vector 0, coordinate 0: shift coefficient
        c0 = ans_root_pert["bases"][1][0]["entries"][0]
        # rotate coefficients
        ans_root_pert["bases"][1][0]["entries"][0] = c0[1:] + c0[:1]
        mutations.append((f"mut_{mut_idx:02d}_d{d}_phase_perturbation", case, ans_root_pert))
        mut_idx += 1

        # Mut D: Duplicate basis (loses mutual unbiasedness)
        if k >= 3:
            ans_dup_basis = copy.deepcopy(sol)
            ans_dup_basis["bases"][1] = copy.deepcopy(ans_dup_basis["bases"][0])
            mutations.append((f"mut_{mut_idx:02d}_d{d}_duplicate_basis", case, ans_dup_basis))
            mut_idx += 1

        # Mut E: Non-orthogonal vectors (replace vector with copy of another vector)
        ans_dup_vec = copy.deepcopy(sol)
        ans_dup_vec["bases"][1][1] = copy.deepcopy(ans_dup_vec["bases"][1][0])
        mutations.append((f"mut_{mut_idx:02d}_d{d}_duplicate_vector", case, ans_dup_vec))
        mut_idx += 1

    # Missing fixed B0 mutation
    case_ctrl = {
        "case_id": "mut_ctrl_missing_b0",
        "dimension": 3,
        "num_bases": 4,
        "fixed_first_basis": make_fourier_3(),
    }
    sol_with_b0 = solve(case_ctrl)
    ans_no_b0 = copy.deepcopy(sol_with_b0)
    # Mutate first vector of B0 so it does not match fixed B0
    ans_no_b0["bases"][0][0]["entries"] = [["1", "0", "0"], ["0", "0", "0"], ["0", "0", "0"]]
    mutations.append((f"mut_{mut_idx:02d}_missing_fixed_b0", case_ctrl, ans_no_b0))
    mut_idx += 1

    # Truncated bases list
    case_trunc = {"case_id": "mut_trunc", "dimension": 3, "num_bases": 4}
    ans_trunc = solve(case_trunc)
    ans_trunc["bases"] = ans_trunc["bases"][:3]  # only 3 bases instead of 4
    mutations.append((f"mut_{mut_idx:02d}_truncated_bases", case_trunc, ans_trunc))
    mut_idx += 1

    # Truncated vector entries
    case_vec_trunc = {"case_id": "mut_vec_trunc", "dimension": 3, "num_bases": 4}
    ans_vec_trunc = solve(case_vec_trunc)
    ans_vec_trunc["bases"][0][0]["entries"] = ans_vec_trunc["bases"][0][0]["entries"][
        :2
    ]  # 2 coords instead of 3
    mutations.append((f"mut_{mut_idx:02d}_truncated_coordinates", case_vec_trunc, ans_vec_trunc))
    mut_idx += 1

    # Invalid fraction string
    case_frac = {"case_id": "mut_frac", "dimension": 2, "num_bases": 3}
    ans_frac = solve(case_frac)
    ans_frac["bases"][0][0]["norm2"] = "not_a_fraction"
    mutations.append((f"mut_{mut_idx:02d}_invalid_fraction", case_frac, ans_frac))
    mut_idx += 1

    # Non-integer cyclotomic order
    case_m = {"case_id": "mut_m", "dimension": 2, "num_bases": 3}
    ans_m = solve(case_m)
    ans_m["cyclotomic_order"] = 0
    mutations.append((f"mut_{mut_idx:02d}_invalid_order", case_m, ans_m))
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

    print(f"Generated {len(all_cases)} judge cases and {len(mutations)} hostile mutations.")

    # Generate manifest.json
    manifest: Dict[str, Any] = {
        "challenge_id": "C025",
        "domain": "c_quantum",
        "tier": "T2",
        "cases_count": len(all_cases),
        "mutations_count": len(mutations),
        "files": {},
    }

    # Hash all files in judge_packet
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
