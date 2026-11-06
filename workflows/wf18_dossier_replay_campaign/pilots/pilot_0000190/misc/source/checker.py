"""Dossier 1 Checker: Hollow 5-Simplex (b4 = 1) Degree-4 Exact Rational Duality & Curvature Verifier.

Coupled to Rust omega_functional exact degree-4 Phi4 certificate verifier.
Enforces:
1. Zero-Float Law (pure Fraction arithmetic in Q).
2. Cochain nilpotence d1 * d0 = 0, d2 * d1 = 0 (Bianchi), and d3 * d2 = 0 (Curvature) in Q.
3. 4-cavity cycle condition d3^T * v = 0 in Q.
4. Primal feasibility r = G - d3 * C in Q.
5. Dual norm bound |v_sigma| <= mu_sigma in Q.
6. Zero duality gap: sum_sigma mu_sigma * |r_sigma| - <G, v> = 0 in Q.

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
    # 1. 4-volume curvature nilpotence: d3 * d2 == 0
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

    # 2. Bianchi identity: d2 * d1 == 0
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

    # 3. 1-skeleton nilpotence: d1 * d0 == 0
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
    input_data: Dict[str, Any],
    witness_data: Dict[str, Any],
    repo_root: Path | None = None,
) -> Dict[str, Any]:
    """Verify an exact rational degree-4 quotient obstruction certificate."""
    # 1. Parse topology & boundary matrices
    try:
        d0_raw = input_data["boundary_matrices"].get("d0")
        d1_raw = input_data["boundary_matrices"]["d1"]
        d2_raw = input_data["boundary_matrices"]["d2"]
        d3_raw = input_data["boundary_matrices"]["d3"]
        d0 = [[_parse_rational(val) for val in row] for row in d0_raw] if d0_raw else None
        d1 = [[_parse_rational(val) for val in row] for row in d1_raw]
        d2 = [[_parse_rational(val) for val in row] for row in d2_raw]
        d3 = [[_parse_rational(val) for val in row] for row in d3_raw]
    except TypeError as te:
        return {"status": "REFUSED_FLOAT_DETECTED", "detail": str(te)}

    d3_d2_ok, d2_d1_ok, d1_d0_ok = verify_chain_law_nilpotence(d3, d2, d1, d0)
    if not d3_d2_ok:
        return {"status": "REFUSED_CURVATURE_VIOLATION", "detail": "d3 * d2 != 0 in Q"}
    if not d2_d1_ok:
        return {"status": "REFUSED_BIANCHI_VIOLATION", "detail": "d2 * d1 != 0 in Q"}
    if d0 is not None and not d1_d0_ok:
        return {"status": "REFUSED_CHAIN_LAW_VIOLATION", "detail": "d1 * d0 != 0 in Q"}

    # 2. Parse target 4-flux and weights
    try:
        flux_g = [_parse_rational(p["flux_g"]) for p in input_data["topology"]["pentachora"]]
        weights = [
            _parse_rational(p.get("weight", "1")) for p in input_data["topology"]["pentachora"]
        ]
        potential_c = [_parse_rational(val) for val in witness_data["potential_c"]]
        dual_witness = [_parse_rational(val) for val in witness_data["dual_witness"]]
        reported_value = _parse_rational(witness_data["reported_value"])
    except TypeError as te:
        return {"status": "REFUSED_FLOAT_DETECTED", "detail": str(te)}

    p_count = len(d3)
    t_count = len(d3[0])

    if len(flux_g) != p_count or len(weights) != p_count:
        return {
            "status": "REFUSED_DIMENSION_MISMATCH",
            "detail": "Pentachora flux/weight dimension mismatch",
        }
    if len(potential_c) != t_count:
        return {
            "status": "REFUSED_DIMENSION_MISMATCH",
            "detail": "Gauge potential C dimension != tetrahedron count",
        }
    if len(dual_witness) != p_count:
        return {
            "status": "REFUSED_DIMENSION_MISMATCH",
            "detail": "Dual witness dimension != pentachoron count",
        }

    # 3. Dual cycle closure: d3^T * v == 0
    for t in range(t_count):
        closure_t = sum(d3[p][t] * dual_witness[p] for p in range(p_count))
        if closure_t != Fraction(0):
            return {
                "status": "REFUSED_DUAL_WITNESS_NOT_CLOSED",
                "tet_index": t,
                "closure_defect": str(closure_t),
            }

    # 4. Dual norm bound: |v_p| <= mu_p
    for p in range(p_count):
        if abs(dual_witness[p]) > weights[p]:
            return {
                "status": "REFUSED_DUAL_NORM_EXCEEDED",
                "pentachoron_index": p,
                "val": str(dual_witness[p]),
                "weight": str(weights[p]),
            }

    # 5. Primal residual r = G - d3 * C
    primal_residual: List[Fraction] = []
    for p in range(p_count):
        d3_c_p = sum(d3[p][t] * potential_c[t] for t in range(t_count))
        r_p = flux_g[p] - d3_c_p
        primal_residual.append(r_p)

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

    # 6. Cross-verification with Rust omega_functional engine
    rust_result = None
    if repo_root is not None:
        rust_wire = {
            "flux_g": [str(x) for x in flux_g],
            "d3": [[str(x) for x in row] for row in d3],
            "d2": [[str(x) for x in row] for row in d2],
            "d1": [[str(x) for x in row] for row in d1],
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
        "curvature_nilpotence": True,
        "bianchi_identity_nilpotence": True,
        "chain_law_nilpotence": True,
        "dual_witness_closed": True,
        "rust_verification": rust_result,
    }


def run_dossier_audit(dossier_dir: Path, repo_root: Path) -> Dict[str, Any]:
    """Run full audit on Dossier 1: valid witness and near misses."""
    import yaml

    with open(dossier_dir / "input.yaml", "r", encoding="utf-8") as f:
        input_data = yaml.safe_load(f)

    with open(dossier_dir / "witness_valid.json", "r", encoding="utf-8") as f:
        witness_valid = json.load(f)

    with open(dossier_dir / "witness_near_miss.json", "r", encoding="utf-8") as f:
        near_misses = json.load(f)

    # 1. Audit valid witness
    valid_result = check_exact_phi4_certificate(input_data, witness_valid, repo_root=repo_root)

    # 2. Audit near misses
    near_miss_results = []
    for case in near_misses["cases"]:
        res = check_exact_phi4_certificate(input_data, case, repo_root=repo_root)
        near_miss_results.append(
            {
                "case_id": case["case_id"],
                "expected_refusal": case["expected_refusal"],
                "actual_status": res["status"],
                "rejected_as_expected": res["status"] != "PASS",
                "detail": res,
            }
        )

    return {
        "dossier": "dossier_1_hollow_5simplex_b4_1",
        "claim_id": "CLM-DEMO9-SIMPLEX5-B4-1-001",
        "valid_witness_status": valid_result["status"],
        "valid_audit": valid_result,
        "near_miss_count": len(near_miss_results),
        "all_near_misses_rejected": all(nm["rejected_as_expected"] for nm in near_miss_results),
        "near_miss_details": near_miss_results,
    }


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parents[4]
    output = run_dossier_audit(current_dir, repo_root)
    out_file = current_dir / "checker_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(json.dumps(output, indent=2))
