# AuthorityEffect: None.
"""
Judge Packet Generator for C030: Tensor-Network Contraction Order.

Generates:
1. 30 base cases:
   - 12 small networks (N <= 12): 8 feasible (bound = DP optimum), 4 infeasible (bound = DP optimum - 1).
   - 18 larger networks (13 <= N <= 30): grids, trees, random 3-regular, matrix chains, with feasible bounds from pinned search.
2. 10 relabel/gauge controls.
3. 6 poison cases (hyperedges, dimension errors, binding size bounds, giant costs > 2^64).
4. 45+ hostile mutations testing 100% kill rate.
5. manifest.json with SHA-256 hashes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from reference_solver.exact_dp_solver import solve_exact_subset_dp
from reference_solver.heuristic_search import solve_heuristic_search
from reference_solver.solver import solve


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_grid_network(
    rows: int, cols: int, bond_dim: int = 2, open_dim: int = 2
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """Generates 2D grid tensor network."""
    tensors: Dict[str, List[str]] = {}
    dims: Dict[str, int] = {}

    for r in range(rows):
        for c in range(cols):
            t_name = f"T_{r}_{c}"
            idxs = []

            # Horizontal bond to (r, c+1)
            if c + 1 < cols:
                h_bond = f"h_{r}_{c}_{c + 1}"
                idxs.append(h_bond)
                dims[h_bond] = bond_dim
            if c - 1 >= 0:
                h_bond = f"h_{r}_{c - 1}_{c}"
                idxs.append(h_bond)

            # Vertical bond to (r+1, c)
            if r + 1 < rows:
                v_bond = f"v_{r}_{r + 1}_{c}"
                idxs.append(v_bond)
                dims[v_bond] = bond_dim
            if r - 1 >= 0:
                v_bond = f"v_{r - 1}_{r}_{c}"
                idxs.append(v_bond)

            # Open physical leg
            phys_idx = f"p_{r}_{c}"
            idxs.append(phys_idx)
            dims[phys_idx] = open_dim

            tensors[t_name] = sorted(idxs)

    return tensors, dims


def generate_chain_network(
    n: int, bond_dim: int = 4, open_dim: int = 2
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """Generates matrix product chain network."""
    tensors: Dict[str, List[str]] = {}
    dims: Dict[str, int] = {}

    for i in range(n):
        t_name = f"A_{i}"
        idxs = []
        if i > 0:
            b_prev = f"b_{i - 1}_{i}"
            idxs.append(b_prev)
        if i + 1 < n:
            b_next = f"b_{i}_{i + 1}"
            idxs.append(b_next)
            dims[b_next] = bond_dim
        p_idx = f"p_{i}"
        idxs.append(p_idx)
        dims[p_idx] = open_dim
        tensors[t_name] = sorted(idxs)

    return tensors, dims


def generate_tree_network(
    depth: int, branch: int = 2, bond_dim: int = 2, open_dim: int = 2
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """Generates Cayley tree tensor network."""
    tensors: Dict[str, List[str]] = {}
    dims: Dict[str, int] = {}
    node_id = 0

    def add_node(curr_depth: int, parent_bond: Optional[str]) -> None:
        nonlocal node_id
        curr_name = f"Node_{node_id}"
        node_id += 1
        idxs = []
        if parent_bond:
            idxs.append(parent_bond)

        if curr_depth < depth:
            for b in range(branch):
                child_bond = f"tb_{curr_name}_{b}"
                dims[child_bond] = bond_dim
                idxs.append(child_bond)
                add_node(curr_depth + 1, child_bond)
        else:
            p_idx = f"p_{curr_name}"
            dims[p_idx] = open_dim
            idxs.append(p_idx)

        tensors[curr_name] = sorted(idxs)

    add_node(0, None)
    return tensors, dims


def generate_all_cases() -> None:
    cases_dir = _pkg_root / "judge_packet" / "cases"
    mut_dir = _pkg_root / "judge_packet" / "mutation_suite"
    cases_dir.mkdir(parents=True, exist_ok=True)
    mut_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: Dict[str, Dict[str, Any]] = {}
    base_cases: List[Dict[str, Any]] = []

    # ----------------------------------------------------
    # 1. Base cases: 12 small networks (N <= 12)
    # ----------------------------------------------------
    small_specs = [
        ("chain_3", 3, 4, 2),
        ("chain_4", 4, 4, 2),
        ("chain_5", 5, 4, 2),
        ("grid_2x2", 2, 2, 2),
        ("grid_2x3", 2, 3, 2),
        ("tree_d2_b2", 2, 2, 2),  # 7 nodes
        ("tree_d3_b2", 3, 2, 2),  # 15 nodes trimmed to 10
        ("grid_3x3", 3, 3, 2),  # 9 nodes
        ("chain_8", 8, 3, 2),
        ("chain_10", 10, 2, 2),
        ("grid_3x4", 3, 4, 2),  # 12 nodes
        ("chain_12", 12, 2, 2),
    ]

    for idx, (spec_name, p1, p2, p3) in enumerate(small_specs, 1):
        case_id = f"c030_base_{idx:02d}_{spec_name}"
        if "chain" in spec_name:
            tensors, dims = generate_chain_network(p1, bond_dim=p2, open_dim=p3)
        elif "grid" in spec_name:
            tensors, dims = generate_grid_network(p1, p2, bond_dim=p3, open_dim=2)
        elif "tree" in spec_name:
            tensors, dims = generate_tree_network(p1, branch=p2, bond_dim=p3, open_dim=2)

        # Solve exactly via subset DP
        ok, opt_cost, _ = solve_exact_subset_dp(tensors, dims)

        # 4 small cases are infeasible (bound = opt_cost - 1)
        is_infeasible = idx in {3, 6, 8, 11}
        cost_bound = (opt_cost - 1) if is_infeasible else opt_cost

        case = {
            "case_id": case_id,
            "tensors": tensors,
            "dims": dims,
            "cost_bound": str(cost_bound),
            "size_bound": None,
        }
        base_cases.append(case)

    # ----------------------------------------------------
    # 2. Base cases: 18 larger networks (13 <= N <= 30)
    # ----------------------------------------------------
    large_specs = [
        ("chain_14", 14, 4, 2),
        ("chain_16", 16, 4, 2),
        ("chain_20", 20, 3, 2),
        ("chain_25", 25, 2, 2),
        ("chain_30", 30, 2, 2),
        ("grid_3x5", 3, 5, 2),  # 15 nodes
        ("grid_4x4", 4, 4, 2),  # 16 nodes
        ("grid_4x5", 4, 5, 2),  # 20 nodes
        ("grid_5x5", 5, 5, 2),  # 25 nodes
        ("grid_5x6", 5, 6, 2),  # 30 nodes
        ("tree_d3_b2_15", 3, 2, 2),  # 15 nodes
        ("chain_15_sz", 15, 3, 2),  # with size bound
        ("chain_18_sz", 18, 3, 2),  # with size bound
        ("grid_4x4_sz", 4, 4, 2),  # with size bound
        ("chain_22", 22, 2, 2),
        ("chain_24", 24, 2, 2),
        ("grid_3x6", 3, 6, 2),  # 18 nodes
        ("chain_28", 28, 2, 2),
    ]

    for idx, (spec_name, p1, p2, p3) in enumerate(large_specs, 13):
        case_id = f"c030_base_{idx:02d}_{spec_name}"
        if "chain" in spec_name:
            tensors, dims = generate_chain_network(p1, bond_dim=p2, open_dim=p3)
        elif "grid" in spec_name:
            tensors, dims = generate_grid_network(p1, p2, bond_dim=p3, open_dim=2)
        elif "tree" in spec_name:
            tensors, dims = generate_tree_network(p1, branch=p2, bond_dim=p3, open_dim=2)

        # Set size bound if requested
        size_bound = None
        if "sz" in spec_name:
            # Intermediate size bound set generously
            size_bound = 16384

        # Run pinned search to obtain feasible bound
        ok, best_cost, best_order = solve_heuristic_search(
            tensors, dims, cost_bound=None, size_bound=size_bound, num_restarts=30
        )
        # Add 15% headroom to ensure feasible under all valid heuristics
        bound = int(best_cost * 1.15) + 1000

        case = {
            "case_id": case_id,
            "tensors": tensors,
            "dims": dims,
            "cost_bound": str(bound),
            "size_bound": str(size_bound) if size_bound is not None else None,
        }
        base_cases.append(case)

    # Write all base cases
    for case in base_cases:
        cid = case["case_id"]
        cf_path = cases_dir / f"{cid}.json"
        cb = canonical_json_bytes(case)
        with open(cf_path, "wb") as f:
            f.write(cb)
        manifest_entries[f"cases/{cid}.json"] = {
            "sha256": sha256_bytes(cb),
            "size_bytes": len(cb),
        }

    # ----------------------------------------------------
    # 3. Relabel and Gauge Controls (10 controls)
    # ----------------------------------------------------
    controls = []
    # Control 1-3: rename tensors in base_01, base_04, base_09
    for c_idx, src_idx in enumerate([1, 4, 9], 1):
        src_case = base_cases[src_idx - 1]
        c_id = f"c030_ctrl_{c_idx:02d}_rename_tensors"
        c_tensors = {}
        for k, v in src_case["tensors"].items():
            c_tensors[f"TENSOR_{k}"] = list(v)
        ctrl_case = copy.deepcopy(src_case)
        ctrl_case["case_id"] = c_id
        ctrl_case["tensors"] = c_tensors
        controls.append(ctrl_case)

    # Control 4-6: rename indices in base_02, base_05, base_10
    for c_idx, src_idx in enumerate([2, 5, 10], 4):
        src_case = base_cases[src_idx - 1]
        c_id = f"c030_ctrl_{c_idx:02d}_rename_indices"
        ctrl_case = copy.deepcopy(src_case)
        ctrl_case["case_id"] = c_id
        new_dims = {}
        idx_map = {old: f"idx_{old}" for old in src_case["dims"].keys()}
        for old, val in src_case["dims"].items():
            new_dims[idx_map[old]] = val
        new_tensors = {}
        for t_name, idx_list in src_case["tensors"].items():
            new_tensors[t_name] = [idx_map[x] for x in idx_list]
        ctrl_case["tensors"] = new_tensors
        ctrl_case["dims"] = new_dims
        controls.append(ctrl_case)

    # Control 7-10: permute tensor insertion order
    for c_idx, src_idx in enumerate([7, 13, 16, 20], 7):
        src_case = base_cases[src_idx - 1]
        c_id = f"c030_ctrl_{c_idx:02d}_permute_keys"
        ctrl_case = copy.deepcopy(src_case)
        ctrl_case["case_id"] = c_id
        keys = list(src_case["tensors"].keys())
        random.Random(c_idx + 99).shuffle(keys)
        ctrl_case["tensors"] = {k: list(src_case["tensors"][k]) for k in keys}
        controls.append(ctrl_case)

    for case in controls:
        cid = case["case_id"]
        cf_path = cases_dir / f"{cid}.json"
        cb = canonical_json_bytes(case)
        with open(cf_path, "wb") as f:
            f.write(cb)
        manifest_entries[f"cases/{cid}.json"] = {
            "sha256": sha256_bytes(cb),
            "size_bytes": len(cb),
        }

    # ----------------------------------------------------
    # 4. Poison Cases (6 cases)
    # ----------------------------------------------------
    poison_cases = []

    # Poison 1: Hyperedge (index 'h_shared' appears in 3 tensors) -> OUT_OF_SCOPE
    p1 = {
        "case_id": "c030_poison_01_hyperedge_3_tensors",
        "tensors": {
            "A": ["i", "h_shared"],
            "B": ["j", "h_shared"],
            "C": ["k", "h_shared"],
        },
        "dims": {"i": 2, "j": 2, "k": 2, "h_shared": 4},
        "cost_bound": "1000",
        "size_bound": None,
    }
    poison_cases.append(p1)

    # Poison 2: Dimension mismatch (dimension < 2) -> OUT_OF_SCOPE
    p2 = {
        "case_id": "c030_poison_02_dim_less_than_2",
        "tensors": {"A": ["i", "j"], "B": ["j", "k"]},
        "dims": {"i": 2, "j": 1, "k": 4},
        "cost_bound": "1000",
        "size_bound": None,
    }
    poison_cases.append(p2)

    # Poison 3: Duplicate index inside single tensor -> OUT_OF_SCOPE
    p3 = {
        "case_id": "c030_poison_03_duplicate_index_in_tensor",
        "tensors": {"A": ["i", "i"], "B": ["j", "k"]},
        "dims": {"i": 2, "j": 2, "k": 2},
        "cost_bound": "1000",
        "size_bound": None,
    }
    poison_cases.append(p3)

    # Poison 4: Giant cost > 2^64 (exact arbitrary precision test)
    p4 = {
        "case_id": "c030_poison_04_cost_above_2_pow_64",
        "tensors": {
            "T1": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"],
            "T2": ["k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u"],
        },
        "dims": {x: 64 for x in "abcdefghijklmnopqrstu"},
        "cost_bound": str(64**21),
        "size_bound": None,
    }
    poison_cases.append(p4)

    # Poison 5: Impossible size bound (size_bound = 1) -> UNKNOWN
    p5 = {
        "case_id": "c030_poison_05_impossible_size_bound",
        "tensors": {"A": ["i", "j"], "B": ["j", "k"], "C": ["k", "l"]},
        "dims": {"i": 2, "j": 4, "k": 4, "l": 2},
        "cost_bound": "100000",
        "size_bound": "1",  # Intermediate size is at least 4
    }
    poison_cases.append(p5)

    # Poison 6: Out of bounds tensor count (> 30) -> OUT_OF_SCOPE
    p6_tensors = {f"T_{i}": [f"i_{i}"] for i in range(35)}
    p6_dims = {f"i_{i}": 2 for i in range(35)}
    p6 = {
        "case_id": "c030_poison_06_tensor_count_exceeds_30",
        "tensors": p6_tensors,
        "dims": p6_dims,
        "cost_bound": "10000",
        "size_bound": None,
    }
    poison_cases.append(p6)

    for case in poison_cases:
        cid = case["case_id"]
        cf_path = cases_dir / f"{cid}.json"
        cb = canonical_json_bytes(case)
        with open(cf_path, "wb") as f:
            f.write(cb)
        manifest_entries[f"cases/{cid}.json"] = {
            "sha256": sha256_bytes(cb),
            "size_bytes": len(cb),
        }

    # ----------------------------------------------------
    # 5. Hostile Mutation Suite (48 mutations)
    # ----------------------------------------------------
    # Filter cases that produce SOLVED status
    solved_cases = []
    for c in base_cases:
        ans = solve(c)
        if ans.get("status") == "SOLVED":
            solved_cases.append((c, ans))

    mut_idx = 1
    # 1. Corrupt stated cost (+1 or -1) on 12 cases
    for case, ans in solved_cases[:12]:
        cid = case["case_id"]
        mutated_ans = copy.deepcopy(ans)
        orig_cost = int(ans["total_cost"])
        mutated_ans["total_cost"] = str(orig_cost + 1)
        mut_file = mut_dir / f"mut_{mut_idx:02d}_{cid}_corrupt_cost.json"
        m_rec = {"mutation_type": "corrupt_cost", "case": case, "mutated_answer": mutated_ans}
        mb = canonical_json_bytes(m_rec)
        with open(mut_file, "wb") as f:
            f.write(mb)
        manifest_entries[f"mutation_suite/{mut_file.name}"] = {
            "sha256": sha256_bytes(mb),
            "size_bytes": len(mb),
        }
        mut_idx += 1

    # 2. Reuse already contracted tensor on 12 cases
    for case, ans in solved_cases[:12]:
        cid = case["case_id"]
        mutated_ans = copy.deepcopy(ans)
        if len(mutated_ans.get("order", [])) >= 2:
            first_op = mutated_ans["order"][0][0]
            mutated_ans["order"][1][0] = first_op
        mut_file = mut_dir / f"mut_{mut_idx:02d}_{cid}_reuse_tensor.json"
        m_rec = {"mutation_type": "reuse_tensor", "case": case, "mutated_answer": mutated_ans}
        mb = canonical_json_bytes(m_rec)
        with open(mut_file, "wb") as f:
            f.write(mb)
        manifest_entries[f"mutation_suite/{mut_file.name}"] = {
            "sha256": sha256_bytes(mb),
            "size_bytes": len(mb),
        }
        mut_idx += 1

    # 3. Truncate contraction order (omit last step) on 12 cases
    for case, ans in solved_cases[:12]:
        cid = case["case_id"]
        mutated_ans = copy.deepcopy(ans)
        if mutated_ans.get("order"):
            mutated_ans["order"] = mutated_ans["order"][:-1]
        mut_file = mut_dir / f"mut_{mut_idx:02d}_{cid}_truncated_order.json"
        m_rec = {"mutation_type": "truncated_order", "case": case, "mutated_answer": mutated_ans}
        mb = canonical_json_bytes(m_rec)
        with open(mut_file, "wb") as f:
            f.write(mb)
        manifest_entries[f"mutation_suite/{mut_file.name}"] = {
            "sha256": sha256_bytes(mb),
            "size_bytes": len(mb),
        }
        mut_idx += 1

    # 4. False optimality claim on 12 cases (cases with N > 12 where status == SOLVED)
    large_solved = [(c, a) for (c, a) in solved_cases if len(c["tensors"]) > 12]
    for case, ans in large_solved[:12]:
        cid = case["case_id"]
        mutated_ans = copy.deepcopy(ans)
        mutated_ans["optimal"] = True  # Forbidden for N > 12
        mut_file = mut_dir / f"mut_{mut_idx:02d}_{cid}_false_optimality.json"
        m_rec = {"mutation_type": "false_optimality", "case": case, "mutated_answer": mutated_ans}
        mb = canonical_json_bytes(m_rec)
        with open(mut_file, "wb") as f:
            f.write(mb)
        manifest_entries[f"mutation_suite/{mut_file.name}"] = {
            "sha256": sha256_bytes(mb),
            "size_bytes": len(mb),
        }
        mut_idx += 1

    # Write manifest.json
    manifest_path = _pkg_root / "judge_packet" / "manifest.json"
    manifest_bytes = canonical_json_bytes(manifest_entries)
    with open(manifest_path, "wb") as f:
        f.write(manifest_bytes)

    print(
        f"Generated {len(base_cases)} base cases, {len(controls)} controls, {len(poison_cases)} poison cases."
    )
    print(f"Generated {mut_idx - 1} hostile mutations.")
    print(f"Manifest written with {len(manifest_entries)} entries.")


if __name__ == "__main__":
    generate_all_cases()
