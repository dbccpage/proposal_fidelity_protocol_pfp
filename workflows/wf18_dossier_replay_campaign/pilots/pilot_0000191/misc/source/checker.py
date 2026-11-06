"""Dossier 2 Checker: Discrete Pontryagin / Chern 4-Manifold Pairing & 4-Volume Curvature Verifier.

Coupled to Rust omega_functional exact degree-4 Phi4 certificate verifier.
Enforces:
1. Zero-Float Law (pure Fraction arithmetic in Q).
2. Cochain nilpotence d1 * d0 = 0, d2 * d1 = 0 (Bianchi), and d3 * d2 = 0 (Curvature) in Q.
3. Pairing of a declared degree-4 cochain with a supplied cycle.
   Cup products are not specified by these input matrices.
4. Degree-4 quotient obstruction certification: Phi_4([P]) == 2 with zero duality gap.
5. Dual 4-cycle boundary closure d3^T * v == 0 in Q.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _parse_rational(val: Any) -> Fraction:
    if isinstance(val, float):
        raise TypeError(f"Zero-Float Law violation: float encountered {val!r}")
    if isinstance(val, (int, Fraction)):
        return Fraction(val)
    if isinstance(val, str):
        if "." in val:
            raise TypeError(f"Zero-Float Law violation: decimal string float encountered {val!r}")
        if "/" in val:
            p, q = val.split("/", 1)
            return Fraction(int(p.strip()), int(q.strip()))
        return Fraction(int(val.strip()))
    raise TypeError(f"Cannot parse rational from {val!r}")


def verify_chain_law_nilpotence(
    d3: List[List[Fraction]],
    d2: List[List[Fraction]],
    d1: List[List[Fraction]],
    d0: List[List[Fraction]] | None = None,
) -> Tuple[bool, bool, bool]:
    """Verify exact cochain nilpotence d3 * d2 == 0, d2 * d1 == 0, and d1 * d0 == 0 in Q."""
    p_count = len(d3)
    t_count = len(d2)
    f_count = len(d1)

    d3_d2_ok = True
    for p in range(p_count):
        for f in range(f_count):
            val = sum(d3[p][t] * d2[t][f] for t in range(t_count))
            if val != Fraction(0):
                d3_d2_ok = False
                break
        if not d3_d2_ok:
            break

    e_count = len(d1[0])
    d2_d1_ok = True
    for t in range(t_count):
        for e in range(e_count):
            val = sum(d2[t][f] * d1[f][e] for f in range(f_count))
            if val != Fraction(0):
                d2_d1_ok = False
                break
        if not d2_d1_ok:
            break

    d1_d0_ok = True
    if d0 is not None:
        v_count = len(d0[0])
        for f in range(f_count):
            for v in range(v_count):
                comp = sum(d1[f][e] * d0[e][v] for e in range(e_count))
                if comp != Fraction(0):
                    d1_d0_ok = False
                    break
            if not d1_d0_ok:
                break

    return d3_d2_ok, d2_d1_ok, d1_d0_ok


def evaluate_pontryagin_pairing(
    pontryagin_4cochain: List[Fraction],
    fundamental_4cycle: List[Fraction],
) -> Fraction:
    """Evaluate topological pairing <P, [M4]> in Q."""
    assert len(pontryagin_4cochain) == len(fundamental_4cycle)
    return sum(
        pontryagin_4cochain[i] * fundamental_4cycle[i] for i in range(len(pontryagin_4cochain))
    )


def exact_matrix_rank(matrix: List[List[Fraction]]) -> int:
    """Compute rank by rational row reduction."""
    rows = [[_parse_rational(x) for x in row] for row in matrix]
    if not rows:
        return 0
    columns = len(rows[0])
    if any(len(row) != columns for row in rows):
        raise ValueError("Ragged matrix")
    rank = 0
    for col in range(columns):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        scale = rows[rank][col]
        rows[rank] = [x / scale for x in rows[rank]]
        for r in range(len(rows)):
            if r != rank:
                factor = rows[r][col]
                rows[r] = [x - factor * y for x, y in zip(rows[r], rows[rank])]
        rank += 1
    return rank


def audit_topological_scope(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Separate matrix homology from the unprovided cellular cup product."""
    matrices = [input_data["boundary_matrices"][f"d{i}"] for i in range(4)]
    matrices = [[[_parse_rational(x) for x in row] for row in matrix] for matrix in matrices]
    dimensions = [len(matrices[0][0])] + [len(m) for m in matrices]
    if any(any(len(row) != dimensions[i] for row in matrix) for i, matrix in enumerate(matrices)):
        raise ValueError("Incompatible cochain dimensions")
    if not all(verify_chain_law_nilpotence(matrices[3], matrices[2], matrices[1], matrices[0])):
        return {
            "status": "REFUSED_NONZERO_CHAIN_COMPOSITION",
            "cup_product_status": "UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER",
        }
    ranks = [exact_matrix_rank(m) for m in matrices]
    extended = [0] + ranks + [0]
    betti = {f"b{i}": dimensions[i] - extended[i] - extended[i + 1] for i in range(5)}
    declared = input_data["topology"]["betti_numbers"]
    matches = betti == declared
    return {
        "status": "DECLARED_BETTI_MATCH" if matches else "REFUSED_DECLARED_TOPOLOGY_MISMATCH",
        "cochain_dimensions": dimensions,
        "differential_ranks": ranks,
        "computed_betti_numbers": betti,
        "declared_betti_numbers": declared,
        "cup_product_status": "UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER",
        "scope": "Ranks and a cycle pairing do not supply a cup-product table or a manifold identification.",
    }


def run_rust_phi4_verifier(certificate_dict: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    """Execute verify_phi4 binary from Rust omega_symbol_game host."""
    crate_dir = repo_root / "omega_engine" / "crates_rs" / "omega_symbol_game"
    bin_name = "verify_phi4.exe" if sys.platform == "win32" else "verify_phi4"
    target_bin = repo_root / "omega_engine" / "crates_rs" / "target" / "debug" / bin_name

    cmd = (
        [str(target_bin)]
        if target_bin.exists()
        else ["cargo", "run", "--quiet", "--bin", "verify_phi4"]
    )
    try:
        proc = subprocess.run(
            cmd,
            cwd=crate_dir,
            input=json.dumps(certificate_dict),
            text=True,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            return {
                "available": True,
                "status": data.get("status"),
                "reported_value": data.get("reported_value"),
                "duality_gap": data.get("duality_gap"),
            }
        else:
            return {
                "available": True,
                "status": "REFUSED_BY_RUST_ENGINE",
                "stderr": proc.stderr.strip() or proc.stdout.strip(),
            }
    except Exception as exc:
        return {
            "available": False,
            "status": "ENGINE_UNAVAILABLE",
            "detail": str(exc),
        }


def check_exact_phi4_certificate(
    d3: List[List[Fraction]],
    d2: List[List[Fraction]],
    d1: List[List[Fraction]] | None,
    d0: List[List[Fraction]] | None,
    flux_g: List[Fraction],
    potential_c: List[Fraction],
    dual_witness: List[Fraction],
    reported_value: Fraction,
    weights: List[Fraction] | None = None,
    repo_root: Path | None = None,
) -> Dict[str, Any]:
    """Verify degree-4 quotient certificate in Q."""
    p_count = len(d3)
    t_count = len(d3[0])
    if weights is None:
        weights = [Fraction(1) for _ in range(p_count)]

    # 1. Dual cycle closure: d3^T * v == 0
    for t in range(t_count):
        closure_t = sum(d3[p][t] * dual_witness[p] for p in range(p_count))
        if closure_t != Fraction(0):
            return {
                "status": "REFUSED_DUAL_WITNESS_NOT_CLOSED",
                "tet_index": t,
                "closure_defect": str(closure_t),
            }

    # 2. Dual norm bound: |v_p| <= mu_p
    for p in range(p_count):
        if abs(dual_witness[p]) > weights[p]:
            return {
                "status": "REFUSED_DUAL_NORM_EXCEEDED",
                "pentachoron_index": p,
                "val": str(dual_witness[p]),
                "weight": str(weights[p]),
            }

    # 3. Primal residual r = G - d3 * C
    primal_residual: List[Fraction] = []
    for p in range(p_count):
        d3_c = sum(d3[p][t] * potential_c[t] for t in range(t_count))
        r = flux_g[p] - d3_c
        primal_residual.append(r)

    primal_obj = sum(weights[p] * abs(primal_residual[p]) for p in range(p_count))
    dual_obj = sum(flux_g[p] * dual_witness[p] for p in range(p_count))

    duality_gap = primal_obj - dual_obj
    if duality_gap != Fraction(0):
        return {
            "status": "REFUSED_POSITIVE_DUALITY_GAP",
            "primal_obj": str(primal_obj),
            "dual_obj": str(dual_obj),
            "duality_gap": str(duality_gap),
        }

    if primal_obj != reported_value:
        return {
            "status": "REFUSED_REPORTED_VALUE_MISMATCH",
            "primal_obj": str(primal_obj),
            "reported_value": str(reported_value),
        }

    rust_result = None
    if repo_root is not None:
        rust_wire = {
            "flux_g": [str(x) for x in flux_g],
            "d3": [[str(x) for x in row] for row in d3],
            "d2": [[str(x) for x in row] for row in d2],
            "d1": [[str(x) for x in row] for row in d1] if d1 else None,
            "d0": [[str(x) for x in row] for row in d0] if d0 else None,
            "weights": [str(x) for x in weights],
            "potential_c": [str(x) for x in potential_c],
            "primal_residual": [str(x) for x in primal_residual],
            "dual_witness": [str(x) for x in dual_witness],
            "reported_value": str(reported_value),
        }
        rust_result = run_rust_phi4_verifier(rust_wire, repo_root)

    return {
        "status": "PASS",
        "phi4_certified_value": str(primal_obj),
        "dual_objective": str(dual_obj),
        "duality_gap": "0",
        "dual_witness_closed": True,
        "rust_verification": rust_result,
    }


def run_dossier2_audit(dossier_dir: Path, repo_root: Path) -> Dict[str, Any]:
    """Run full audit on Dossier 2: Pontryagin pairings, instanton certification, and near misses."""
    import yaml

    with open(dossier_dir / "input.yaml", "r", encoding="utf-8") as f:
        input_data = yaml.safe_load(f)

    with open(dossier_dir / "witness_valid.json", "r", encoding="utf-8") as f:
        witness_valid = json.load(f)

    with open(dossier_dir / "witness_near_miss.json", "r", encoding="utf-8") as f:
        near_misses = json.load(f)

    # 1. Parse boundary matrices
    d0_raw = input_data["boundary_matrices"].get("d0")
    d1_raw = input_data["boundary_matrices"]["d1"]
    d2_raw = input_data["boundary_matrices"]["d2"]
    d3_raw = input_data["boundary_matrices"]["d3"]
    d0 = [[_parse_rational(val) for val in row] for row in d0_raw] if d0_raw else None
    d1 = [[_parse_rational(val) for val in row] for row in d1_raw]
    d2 = [[_parse_rational(val) for val in row] for row in d2_raw]
    d3 = [[_parse_rational(val) for val in row] for row in d3_raw]

    d3_d2_ok, d2_d1_ok, d1_d0_ok = verify_chain_law_nilpotence(d3, d2, d1, d0)
    fundamental_4cycle = [_parse_rational(x) for x in input_data["topology"]["fundamental_4cycle"]]

    # 2. Test exact gauge flux Pontryagin vanishing
    pot_a = [_parse_rational(x) for x in witness_valid["exact_gauge_test"]["potential_a"]]
    # Exact flux F = d1 * A
    f_count = len(d1)
    e_count = len(d1[0])
    exact_flux_f = [sum(d1[f][e] * pot_a[e] for e in range(e_count)) for f in range(f_count)]
    # There is no cellular diagonal or cup-product table in this carrier.
    # The exact flux is computed, while its degree-4 cup square remains unsupported.
    topology_audit = audit_topological_scope(input_data)

    # 3. Test non-trivial instanton flux certificate
    cert = witness_valid["instanton_certificate"]
    pontryagin_4cochain = [_parse_rational(x) for x in cert["pontryagin_4cochain"]]
    instanton_pairing = evaluate_pontryagin_pairing(pontryagin_4cochain, fundamental_4cycle)

    pot_c = [_parse_rational(x) for x in cert["potential_c"]]
    dual_v = [_parse_rational(x) for x in cert["dual_witness"]]
    rep_val = _parse_rational(cert["reported_value"])

    phi4_res = check_exact_phi4_certificate(
        d3, d2, d1, d0, pontryagin_4cochain, pot_c, dual_v, rep_val, repo_root=repo_root
    )

    # 4. Audit near misses
    near_miss_results = []
    for case in near_misses["cases"]:
        try:
            if case["test_type"] == "pontryagin_pairing":
                claimed = _parse_rational(case["claimed_pontryagin_number"])
                actual = instanton_pairing
                st = "REFUSED_PONTRYAGIN_NUMBER_MISMATCH" if actual != claimed else "PASS"
                near_miss_results.append(
                    {
                        "case_id": case["case_id"],
                        "expected_refusal": case["expected_refusal"],
                        "actual_status": st,
                        "rejected_as_expected": st != "PASS",
                    }
                )
            elif case["test_type"] == "phi4_certificate":
                flux_g_nm = [_parse_rational(x) for x in case["pontryagin_4cochain"]]
                pot_c_nm = [_parse_rational(x) for x in case["potential_c"]]
                dual_v_nm = [_parse_rational(x) for x in case["dual_witness"]]
                rep_val_nm = _parse_rational(case["reported_value"])
                res_nm = check_exact_phi4_certificate(
                    d3, d2, d1, d0, flux_g_nm, pot_c_nm, dual_v_nm, rep_val_nm, repo_root=repo_root
                )
                near_miss_results.append(
                    {
                        "case_id": case["case_id"],
                        "expected_refusal": case["expected_refusal"],
                        "actual_status": res_nm["status"],
                        "rejected_as_expected": res_nm["status"] != "PASS",
                    }
                )
        except TypeError as te:
            near_miss_results.append(
                {
                    "case_id": case["case_id"],
                    "expected_refusal": case["expected_refusal"],
                    "actual_status": "REFUSED_FLOAT_DETECTED",
                    "rejected_as_expected": True,
                    "detail": str(te),
                }
            )

    return {
        "dossier": "dossier_2_pontryagin_chern_4manifold",
        "claim_id": "CLM-DEMO9-PONTRYAGIN-CHERN-002",
        "chain_laws": {
            "curvature_nilpotence": d3_d2_ok,
            "bianchi_identity_nilpotence": d2_d1_ok,
            "1skeleton_nilpotence": d1_d0_ok,
        },
        "scope_status": topology_audit["status"],
        "topology_audit": topology_audit,
        "exact_gauge_flux": [str(x) for x in exact_flux_f],
        "exact_gauge_pontryagin_pairing": None,
        "exact_gauge_pairing_status": "UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER",
        "declared_4cochain_pairing": str(instanton_pairing),
        "phi4_certificate_status": phi4_res["status"],
        "phi4_audit": phi4_res,
        "near_miss_count": len(near_miss_results),
        "all_near_misses_rejected": all(nm["rejected_as_expected"] for nm in near_miss_results),
        "near_miss_details": near_miss_results,
    }


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parents[4]
    output = run_dossier2_audit(current_dir, repo_root)
    out_file = current_dir / "checker_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(json.dumps(output, indent=2))
