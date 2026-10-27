"""Deterministic case generator for C020 double complex spectral sequence challenge."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from c020_spectral_sequence_double_complex.reference_solver.exact_f2 import (
    mat_mul_f2,
    rank_f2,
)


def random_invertible_f2(n: int, rng: random.Random) -> list[list[int]]:
    if n == 0:
        return []
    if n == 1:
        return [[1]]
    while True:
        mat = [[rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
        if rank_f2(mat) == n:
            return mat


def build_c020_worked_example(filtration: str = "columns") -> dict[str, Any]:
    return {
        "id": "c020_01_worked_example",
        "filtration": filtration,
        "dims": {
            "2,0": 1,
            "1,0": 1,
            "1,1": 1,
            "0,1": 1,
        },
        "d_h": {
            "2,0": [[1]],
            "1,1": [[1]],
        },
        "d_v": {
            "1,1": [[1]],
        },
    }


def build_d3_example() -> dict[str, Any]:
    # A complex with a non-zero d3 differential:
    # d3 maps (3, 0) -> (3-3, 0+3-1) = (0, 2)
    # Zig-zag across length 3:
    # a in C_{3,0}, c in C_{2,0}, e in C_{2,1}, g in C_{1,1}, h in C_{1,2}, k in C_{0,2}
    # d^h a = c
    # d^v e = c, d^h e = g
    # d^v h = g, d^h h = k
    return {
        "id": "c020_d3_zigzag",
        "filtration": "columns",
        "dims": {
            "3,0": 1,
            "2,0": 1,
            "2,1": 1,
            "1,1": 1,
            "1,2": 1,
            "0,2": 1,
        },
        "d_h": {
            "3,0": [[1]],
            "2,1": [[1]],
            "1,2": [[1]],
        },
        "d_v": {
            "2,1": [[1]],
            "1,2": [[1]],
        },
    }


def build_random_valid_double_complex(
    case_id: str,
    filtration: str,
    rng: random.Random,
    max_p: int = 3,
    max_q: int = 3,
    max_dim: int = 2,
) -> dict[str, Any]:
    # Generate independent components that automatically satisfy d^2 = 0 and d^h d^v = d^v d^h
    # By picking square cells and random commutative diagrams
    dims: dict[str, int] = {}
    for p in range(max_p + 1):
        for q in range(max_q + 1):
            if rng.random() < 0.6:
                dims[f"{p},{q}"] = rng.randint(1, max_dim)

    d_h: dict[str, list[list[int]]] = {}
    d_v: dict[str, list[list[int]]] = {}

    # To guarantee d^h d^h = 0 and d^v d^v = 0 trivially, we can populate alternating edges or ensure ranks <= 1
    # Or create direct sums of small squares and zig-zags
    # Let's create from elementary blocks:
    # Blocks:
    # 1. Trivial cells
    # 2. Horizontal edges: C_{p,q} -> C_{p-1,q}
    # 3. Vertical edges: C_{p,q} -> C_{p,q-1}
    # 4. Commuting 2x2 squares:
    #    C_{p,q} -> C_{p-1,q}
    #       |            |
    #       v            v
    #    C_{p,q-1} -> C_{p-1,q-1}
    # Both paths equal a common map M: C_{p,q} -> C_{p-1, q-1}

    # Reset clean
    dims = {}
    d_h = {}
    d_v = {}

    num_blocks = rng.randint(2, 4)
    for _ in range(num_blocks):
        btype = rng.choice(["edge_h", "edge_v", "square", "zigzag"])
        p = rng.randint(1, max_p)
        q = rng.randint(1, max_q)
        if btype == "edge_h":
            dims[f"{p},{q}"] = dims.get(f"{p},{q}", 0) + 1
            dims[f"{p - 1},{q}"] = dims.get(f"{p - 1},{q}", 0) + 1
            d_h.setdefault(f"{p},{q}", []).append((dims[f"{p - 1},{q}"] - 1, dims[f"{p},{q}"] - 1))
        elif btype == "edge_v":
            dims[f"{p},{q}"] = dims.get(f"{p},{q}", 0) + 1
            dims[f"{p},{q - 1}"] = dims.get(f"{p},{q - 1}", 0) + 1
            d_v.setdefault(f"{p},{q}", []).append((dims[f"{p},{q - 1}"] - 1, dims[f"{p},{q}"] - 1))
        elif btype == "square":
            # Commuting square: top-right to bottom-left via both paths
            c_top_r = (p, q)
            c_top_l = (p - 1, q)
            c_bot_r = (p, q - 1)
            c_bot_l = (p - 1, q - 1)
            for k in [c_top_r, c_top_l, c_bot_r, c_bot_l]:
                dims[f"{k[0]},{k[1]}"] = dims.get(f"{k[0]},{k[1]}", 0) + 1

            # dh top: top_r -> top_l
            d_h.setdefault(f"{p},{q}", []).append((dims[f"{p - 1},{q}"] - 1, dims[f"{p},{q}"] - 1))
            # dv left: top_l -> bot_l
            d_v.setdefault(f"{p - 1},{q}", []).append(
                (dims[f"{p - 1},{q - 1}"] - 1, dims[f"{p - 1},{q}"] - 1)
            )
            # dv right: top_r -> bot_r
            d_v.setdefault(f"{p},{q}", []).append((dims[f"{p},{q - 1}"] - 1, dims[f"{p},{q}"] - 1))
            # dh bot: bot_r -> bot_l
            d_h.setdefault(f"{p},{q - 1}", []).append(
                (dims[f"{p - 1},{q - 1}"] - 1, dims[f"{p},{q - 1}"] - 1)
            )
        elif btype == "zigzag":
            # (2,0) -> (1,0) <- (1,1) -> (0,1)
            if p >= 2 and q >= 1:
                for k in [(p, q - 1), (p - 1, q - 1), (p - 1, q), (p - 2, q)]:
                    dims[f"{k[0]},{k[1]}"] = dims.get(f"{k[0]},{k[1]}", 0) + 1
                d_h.setdefault(f"{p},{q - 1}", []).append(
                    (dims[f"{p - 1},{q - 1}"] - 1, dims[f"{p},{q - 1}"] - 1)
                )
                d_v.setdefault(f"{p - 1},{q}", []).append(
                    (dims[f"{p - 1},{q - 1}"] - 1, dims[f"{p - 1},{q}"] - 1)
                )
                d_h.setdefault(f"{p - 1},{q}", []).append(
                    (dims[f"{p - 2},{q}"] - 1, dims[f"{p - 1},{q}"] - 1)
                )

    # Convert sparse entries to dense matrices
    mat_dh: dict[str, list[list[int]]] = {}
    for p, q_val in [(p, q) for p in range(6) for q in range(6)]:
        dim_src = dims.get(f"{p},{q_val}", 0)
        dim_tgt = dims.get(f"{p - 1},{q_val}", 0)
        if dim_src > 0 and dim_tgt > 0 and f"{p},{q_val}" in d_h:
            mat = [[0] * dim_src for _ in range(dim_tgt)]
            for r_idx, c_idx in d_h[f"{p},{q_val}"]:
                if r_idx < dim_tgt and c_idx < dim_src:
                    mat[r_idx][c_idx] ^= 1
            mat_dh[f"{p},{q_val}"] = mat

    mat_dv: dict[str, list[list[int]]] = {}
    for p, q_val in [(p, q) for p in range(6) for q in range(6)]:
        dim_src = dims.get(f"{p},{q_val}", 0)
        dim_tgt = dims.get(f"{p},{q_val - 1}", 0)
        if dim_src > 0 and dim_tgt > 0 and f"{p},{q_val}" in d_v:
            mat = [[0] * dim_src for _ in range(dim_tgt)]
            for r_idx, c_idx in d_v[f"{p},{q_val}"]:
                if r_idx < dim_tgt and c_idx < dim_src:
                    mat[r_idx][c_idx] ^= 1
            mat_dv[f"{p},{q_val}"] = mat

    return {
        "id": case_id,
        "filtration": filtration,
        "dims": dims,
        "d_h": mat_dh,
        "d_v": mat_dv,
    }


def apply_basis_change(case: dict[str, Any], seed: int) -> dict[str, Any]:
    """Apply invertible F2 change of basis to each C_{p,q}."""
    rng = random.Random(seed)
    dims = dict(case.get("dims", {}))
    dh = dict(case.get("d_h", {}))
    dv = dict(case.get("d_v", {}))

    # Invertible matrices P_{p,q} for each (p,q)
    P_mats: dict[str, list[list[int]]] = {}
    P_inv_mats: dict[str, list[list[int]]] = {}
    for k, d in dims.items():
        if d > 0:
            p_mat = random_invertible_f2(d, rng)
            # Over F2, compute inverse
            # For d <= 4, invert via augmented RREF
            from c020_spectral_sequence_double_complex.reference_solver.exact_f2 import (
                row_reduce_f2,
            )

            aug = [p_mat[i] + [1 if i == j else 0 for j in range(d)] for i in range(d)]
            rref, _, _ = row_reduce_f2(aug)
            inv = [rref[i][d:] for i in range(d)]
            P_mats[k] = p_mat
            P_inv_mats[k] = inv

    # Transform d_h: C_{p,q} -> C_{p-1,q} : d'_h = P_{p-1,q} * d_h * P_inv_{p,q}
    new_dh: dict[str, list[list[int]]] = {}
    for k, mat in dh.items():
        p, q = map(int, k.split(","))
        tgt_k = f"{p - 1},{q}"
        p_tgt = P_mats.get(tgt_k)
        p_inv_src = P_inv_mats.get(k)
        res = mat
        if p_tgt:
            res = mat_mul_f2(p_tgt, res)
        if p_inv_src:
            res = mat_mul_f2(res, p_inv_src)
        new_dh[k] = res

    # Transform d_v: C_{p,q} -> C_{p,q-1} : d'_v = P_{p,q-1} * d_v * P_inv_{p,q}
    new_dv: dict[str, list[list[int]]] = {}
    for k, mat in dv.items():
        p, q = map(int, k.split(","))
        tgt_k = f"{p},{q - 1}"
        p_tgt = P_mats.get(tgt_k)
        p_inv_src = P_inv_mats.get(k)
        res = mat
        if p_tgt:
            res = mat_mul_f2(p_tgt, res)
        if p_inv_src:
            res = mat_mul_f2(res, p_inv_src)
        new_dv[k] = res

    return {
        "id": f"{case['id']}_relabel_s{seed}",
        "filtration": case.get("filtration", "columns"),
        "dims": dims,
        "d_h": new_dh,
        "d_v": new_dv,
    }


def transpose_complex(case: dict[str, Any]) -> dict[str, Any]:
    """Swap p <-> q, swapping roles of d_h and d_v."""
    dims = case.get("dims", {})
    dh = case.get("d_h", {})
    dv = case.get("d_v", {})

    new_dims: dict[str, int] = {}
    for k, v in dims.items():
        p, q = map(int, k.split(","))
        new_dims[f"{q},{p}"] = v

    new_dh: dict[str, list[list[int]]] = {}
    for k, mat in dv.items():
        p, q = map(int, k.split(","))
        new_dh[f"{q},{p}"] = mat

    new_dv: dict[str, list[list[int]]] = {}
    for k, mat in dh.items():
        p, q = map(int, k.split(","))
        new_dv[f"{q},{p}"] = mat

    filt = case.get("filtration", "columns")
    new_filt = "rows" if filt == "columns" else ("columns" if filt == "rows" else "both")

    return {
        "id": f"{case['id']}_transposed",
        "filtration": new_filt,
        "dims": new_dims,
        "d_h": new_dh,
        "d_v": new_dv,
    }


def main():
    root = Path(__file__).resolve().parent
    ex_dir = root / "participant_packet" / "examples"
    cases_dir = root / "judge_packet" / "cases"

    rng = random.Random(42)

    # 1. 16 Public Worked Examples
    examples: list[dict[str, Any]] = []

    # Ex 01: Worked example columns
    ex01 = build_c020_worked_example("columns")
    ex01["id"] = "c020_ex01_worked_columns"
    examples.append(ex01)

    # Ex 02: Worked example rows
    ex02 = build_c020_worked_example("rows")
    ex02["id"] = "c020_ex02_worked_rows"
    examples.append(ex02)

    # Ex 03: Worked example both
    ex03 = build_c020_worked_example("both")
    ex03["id"] = "c020_ex03_worked_both"
    examples.append(ex03)

    # Ex 04: Degenerates at E1 (d_v = 0, d_h = 0)
    ex04 = {
        "id": "c020_ex04_degen_e1",
        "filtration": "columns",
        "dims": {"1,0": 1, "0,1": 1},
        "d_h": {},
        "d_v": {},
    }
    examples.append(ex04)

    # Ex 05: Degenerates at E2 (only d_h != 0, so d_r = 0 for r >= 2)
    ex05 = {
        "id": "c020_ex05_degen_e2",
        "filtration": "columns",
        "dims": {"2,1": 1, "1,1": 1},
        "d_h": {"2,1": [[1]]},
        "d_v": {},
    }
    examples.append(ex05)

    # Ex 06: Nonzero d3 differential
    ex06 = build_d3_example()
    ex06["id"] = "c020_ex06_nonzero_d3"
    examples.append(ex06)

    # Ex 07: Nonzero total homology in three degrees
    ex07 = {
        "id": "c020_ex07_h_tot_three_degrees",
        "filtration": "columns",
        "dims": {"0,0": 1, "1,1": 1, "2,2": 1},
        "d_h": {},
        "d_v": {},
    }
    examples.append(ex07)

    # Ex 08 & Ex 09: Out of scope (noncommuting and non-chain)
    ex08 = {
        "id": "c020_ex08_out_of_scope_noncommuting",
        "filtration": "columns",
        "dims": {"1,1": 1, "1,0": 1, "0,1": 1, "0,0": 1},
        "d_h": {"1,1": [[1]], "1,0": [[1]]},
        "d_v": {"1,1": [[1]], "0,1": [[0]]},
    }
    examples.append(ex08)

    ex09 = {
        "id": "c020_ex09_out_of_scope_dh_squared",
        "filtration": "columns",
        "dims": {"2,0": 1, "1,0": 1, "0,0": 1},
        "d_h": {"2,0": [[1]], "1,0": [[1]]},
        "d_v": {},
    }
    examples.append(ex09)

    # Ex 10..16: 7 additional varied valid examples
    for i in range(10, 17):
        filt = "columns" if i % 2 == 0 else "both"
        ex = build_random_valid_double_complex(f"c020_ex{i:02d}", filt, rng, max_p=2, max_q=2)
        examples.append(ex)

    for ex in examples:
        path = ex_dir / f"{ex['id']}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(ex, f, indent=2)

    # 2. 32 Hidden Base Cases (16 per filtration, 8 asking for both)
    base_cases: list[dict[str, Any]] = []
    for i in range(1, 13):  # 12 columns
        base_cases.append(
            build_random_valid_double_complex(
                f"c020_base_{i:02d}_col", "columns", rng, max_p=3, max_q=3
            )
        )
    for i in range(13, 25):  # 12 rows
        base_cases.append(
            build_random_valid_double_complex(
                f"c020_base_{i:02d}_row", "rows", rng, max_p=3, max_q=3
            )
        )
    for i in range(25, 33):  # 8 both
        base_cases.append(
            build_random_valid_double_complex(
                f"c020_base_{i:02d}_both", "both", rng, max_p=3, max_q=3
            )
        )

    for bc in base_cases:
        with (cases_dir / f"{bc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(bc, f, indent=2)

    # 3. 12 Relabel & Transposition Controls
    ctrl_cases: list[dict[str, Any]] = []
    # 6 relabel controls
    for i in range(6):
        src = base_cases[i]
        ctrl_cases.append(apply_basis_change(src, 100 + i))
    # 6 transposition controls
    for i in range(6):
        src = base_cases[6 + i]
        ctrl_cases.append(transpose_complex(src))

    for cc in ctrl_cases:
        with (cases_dir / f"{cc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(cc, f, indent=2)

    # 4. 10 Poisoned but schema-valid cases
    poison_cases: list[dict[str, Any]] = []
    # 4 noncommuting
    for i in range(4):
        p = build_random_valid_double_complex(
            f"c020_poison_{i + 1:02d}_noncommuting", "columns", rng, max_p=2, max_q=2
        )
        # Invert one entry in dv to break commutation
        p["dims"]["1,1"] = 1
        p["dims"]["1,0"] = 1
        p["dims"]["0,1"] = 1
        p["dims"]["0,0"] = 1
        p["d_h"]["1,1"] = [[1]]
        p["d_h"]["1,0"] = [[1]]
        p["d_v"]["1,1"] = [[1]]
        p["d_v"]["0,1"] = [[0]]
        poison_cases.append(p)
    # 3 dh^2 != 0
    for i in range(3):
        p = {
            "id": f"c020_poison_{i + 5:02d}_dh_sq",
            "filtration": "columns",
            "dims": {"2,1": 1, "1,1": 1, "0,1": 1},
            "d_h": {"2,1": [[1]], "1,1": [[1]]},
            "d_v": {},
        }
        poison_cases.append(p)
    # 3 dv^2 != 0
    for i in range(3):
        p = {
            "id": f"c020_poison_{i + 8:02d}_dv_sq",
            "filtration": "rows",
            "dims": {"1,2": 1, "1,1": 1, "1,0": 1},
            "d_h": {},
            "d_v": {"1,2": [[1]], "1,1": [[1]]},
        }
        poison_cases.append(p)

    for pc in poison_cases:
        with (cases_dir / f"{pc['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(pc, f, indent=2)

    print(
        f"Generated {len(examples)} public examples, {len(base_cases)} base cases, {len(ctrl_cases)} controls, {len(poison_cases)} poisoned cases."
    )


if __name__ == "__main__":
    main()
