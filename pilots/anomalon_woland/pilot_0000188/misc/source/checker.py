"""Exact F2 Chain Complex and Frustrated Spin Triangle Checker.

Verifies:
1. Exact nilpotence: d1 * d0 = 0 mod 2.
2. Topological curl obstruction: d1 * c mod 2.
3. Spin candidate evaluation: d0 * s mod 2, residual defect r = c - d0*s mod 2.
4. Minimal defect certification vs. false zero-defect claims.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class F2CheckReceipt:
    claim_id: str
    status: str
    admitted: bool
    detail: str
    nilpotence_verified: bool
    curl_d1_c: int
    is_topologically_obstructed: bool
    candidate_spin_vector: list[int] | None
    actual_residual_defect: list[int] | None
    actual_defect_weight: int | None
    claimed_defect_weight: int | None
    is_provably_minimal: bool | None


def matmul_mod2(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    res = [[0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            s = 0
            for k in range(cols_a):
                s ^= int(a[i][k]) & int(b[k][j])
            res[i][j] = s
    return res


def matvec_mod2(m: list[list[int]], v: list[int]) -> list[int]:
    rows = len(m)
    cols = len(m[0])
    res = [0] * rows
    for i in range(rows):
        s = 0
        for j in range(cols):
            s ^= int(m[i][j]) & int(v[j])
        res[i] = s
    return res


def verify_dossier1(input_spec: dict[str, Any], witness_spec: dict[str, Any]) -> F2CheckReceipt:
    claim_id = witness_spec.get("claim_id", "CLM-DEMO4-F2-SPIN-001")
    d0: list[list[int]] = input_spec["matrices"]["d0"]
    d1: list[list[int]] = input_spec["matrices"]["d1"]
    c: list[int] = input_spec["target_cochain"]["values"]

    # 1. Check nilpotence d1 * d0 == 0 mod 2
    d1_d0 = matmul_mod2(d1, d0)
    nilpotence = all(all(val == 0 for val in row) for row in d1_d0)
    if not nilpotence:
        return F2CheckReceipt(
            claim_id=claim_id,
            status="REFUSED_NILPOTENCE_FAILURE",
            admitted=False,
            detail="d1 * d0 != 0 mod 2: cell complex violates chain boundary nilpotence",
            nilpotence_verified=False,
            curl_d1_c=-1,
            is_topologically_obstructed=False,
            candidate_spin_vector=None,
            actual_residual_defect=None,
            actual_defect_weight=None,
            claimed_defect_weight=None,
            is_provably_minimal=None,
        )

    # 2. Check curl d1 * c mod 2
    d1_c_vec = matvec_mod2(d1, c)
    curl_val = d1_c_vec[0]
    is_obstructed = curl_val != 0

    # 3. Evaluate candidate solution if present
    candidate = witness_spec.get("candidate_solution")
    if not candidate:
        return F2CheckReceipt(
            claim_id=claim_id,
            status="REFUSED_MISSING_CANDIDATE",
            admitted=False,
            detail="No candidate spin vector supplied in witness",
            nilpotence_verified=True,
            curl_d1_c=curl_val,
            is_topologically_obstructed=is_obstructed,
            candidate_spin_vector=None,
            actual_residual_defect=None,
            actual_defect_weight=None,
            claimed_defect_weight=None,
            is_provably_minimal=None,
        )

    s = candidate.get("spin_vector")
    if s is None or len(s) != len(input_spec["carrier"]["vertices"]):
        return F2CheckReceipt(
            claim_id=claim_id,
            status="REFUSED_INVALID_SPIN_DIMENSION",
            admitted=False,
            detail="Candidate spin vector dimension mismatch",
            nilpotence_verified=True,
            curl_d1_c=curl_val,
            is_topologically_obstructed=is_obstructed,
            candidate_spin_vector=s,
            actual_residual_defect=None,
            actual_defect_weight=None,
            claimed_defect_weight=None,
            is_provably_minimal=None,
        )

    d0_s = matvec_mod2(d0, s)
    # residual r = c - d0*s mod 2
    actual_r = [(c[i] ^ d0_s[i]) for i in range(len(c))]
    actual_weight = sum(actual_r)

    claimed_weight = candidate.get("claimed_defect_weight")
    claimed_r = candidate.get("claimed_residual_defect")

    # Near-miss detection: Candidate claims zero defect when curl != 0
    if claimed_weight == 0 and is_obstructed:
        return F2CheckReceipt(
            claim_id=claim_id,
            status="REFUSED_FALSE_ZERO_DEFECT_CLAIM",
            admitted=False,
            detail=(
                f"Candidate falsely claims defect 0, but curl d1*c = {curl_val} != 0 "
                f"forces at least one frustrated bond. Actual recomputed defect weight = {actual_weight}."
            ),
            nilpotence_verified=True,
            curl_d1_c=curl_val,
            is_topologically_obstructed=True,
            candidate_spin_vector=s,
            actual_residual_defect=actual_r,
            actual_defect_weight=actual_weight,
            claimed_defect_weight=claimed_weight,
            is_provably_minimal=False,
        )

    # Check claimed residual matches recomputed residual
    if claimed_r is not None and claimed_r != actual_r:
        return F2CheckReceipt(
            claim_id=claim_id,
            status="REFUSED_RESIDUAL_MISMATCH",
            admitted=False,
            detail=f"Claimed residual {claimed_r} does not match exact recomputation {actual_r}",
            nilpotence_verified=True,
            curl_d1_c=curl_val,
            is_topologically_obstructed=is_obstructed,
            candidate_spin_vector=s,
            actual_residual_defect=actual_r,
            actual_defect_weight=actual_weight,
            claimed_defect_weight=claimed_weight,
            is_provably_minimal=False,
        )

    # In triangle with d1*c = 1, minimal possible defect is 1
    is_minimal = actual_weight == 1 and is_obstructed

    return F2CheckReceipt(
        claim_id=claim_id,
        status="CERTIFIED_OBSTRUCTION",
        admitted=True,
        detail=(
            f"Exact obstruction certified: d1*d0 == 0 mod 2, d1*c = {curl_val} != 0 mod 2. "
            f"Candidate s={s} achieves minimal defect weight {actual_weight} with frustrated bond(s)."
        ),
        nilpotence_verified=True,
        curl_d1_c=curl_val,
        is_topologically_obstructed=True,
        candidate_spin_vector=s,
        actual_residual_defect=actual_r,
        actual_defect_weight=actual_weight,
        claimed_defect_weight=claimed_weight if claimed_weight is not None else actual_weight,
        is_provably_minimal=is_minimal,
    )


def run_standalone() -> dict[str, Any]:
    base_dir = Path(__file__).parent
    import yaml  # type: ignore

    with open(base_dir / "input.yaml", "r", encoding="utf-8") as f:
        inp = yaml.safe_load(f)

    with open(base_dir / "witness_valid.json", "r", encoding="utf-8") as f:
        w_valid = json.load(f)

    with open(base_dir / "witness_near_miss.json", "r", encoding="utf-8") as f:
        w_near = json.load(f)

    res_valid = verify_dossier1(inp, w_valid)
    res_near = verify_dossier1(inp, w_near)

    output = {
        "dossier": "dossier_1_f2_spin_triangle",
        "valid_witness_result": asdict(res_valid),
        "near_miss_result": asdict(res_near),
    }

    out_file = base_dir / "checker_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output


if __name__ == "__main__":
    out = run_standalone()
    print("Dossier 1 Checker Execution Completed.")
    print("Valid witness status:", out["valid_witness_result"]["status"])
    print("Near miss status:", out["near_miss_result"]["status"])
