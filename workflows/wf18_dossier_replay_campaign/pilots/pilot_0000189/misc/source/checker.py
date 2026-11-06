"""Exact Rational Linear Programming Duality & Certificate Checker.

Verifies:
1. Exact rational parsing (enforcing the Zero-Float Law).
2. Primal feasibility: u_e >= |c_e - (d0*alpha)_e| and u_e >= 0.
3. Dual feasibility: -omega_e <= w_e <= omega_e and d0^T * w == 0.
4. Exact duality gap: sum(omega_e * u_e) - w^T * c == 0 in Q.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LpCheckReceipt:
    claim_id: str
    case_name: str
    status: str
    admitted: bool
    detail: str
    primal_feasible: bool
    dual_feasible: bool
    primal_objective: str | None
    dual_objective: str | None
    duality_gap: str | None
    is_exact_zero_gap: bool


def parse_rational(val: Any, location: str) -> Fraction:
    if isinstance(val, bool) or not isinstance(val, (int, str, Fraction)):
        raise ValueError(
            f"{location}: value {val!r} must be an integer, exact fraction string, or Fraction"
        )
    if isinstance(val, str) and not val.strip():
        raise ValueError(f"{location}: empty string is not a valid rational")
    try:
        return Fraction(val)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{location}: {val!r} is not a valid rational number") from exc


def parse_vector(data: list[Any], location: str) -> list[Fraction]:
    return [parse_rational(x, f"{location}[{i}]") for i, x in enumerate(data)]


def parse_matrix(data: list[list[Any]], location: str) -> list[list[Fraction]]:
    return [
        [parse_rational(x, f"{location}[{i}][{j}]") for j, x in enumerate(row)]
        for i, row in enumerate(data)
    ]


def matvec_mul_rational(m: list[list[Fraction]], v: list[Fraction]) -> list[Fraction]:
    rows = len(m)
    cols = len(m[0])
    res: list[Fraction] = []
    for i in range(rows):
        s = Fraction(0)
        for j in range(cols):
            s += m[i][j] * v[j]
        res.append(s)
    return res


def transpose_matvec_mul_rational(m: list[list[Fraction]], v: list[Fraction]) -> list[Fraction]:
    rows = len(m)
    cols = len(m[0])
    res: list[Fraction] = []
    for j in range(cols):
        s = Fraction(0)
        for i in range(rows):
            s += m[i][j] * v[i]
        res.append(s)
    return res


def verify_lp_certificate(
    input_spec: dict[str, Any],
    candidate_spec: dict[str, Any],
    case_name: str = "default",
) -> LpCheckReceipt:
    claim_id = candidate_spec.get("claim_id", "CLM-DEMO4-EXACT-LP-001")
    d0 = parse_matrix(input_spec["matrices"]["d0"], "d0")
    c = parse_vector(input_spec["target_cochain"]["values"], "target_cochain")
    weights = [
        parse_rational(e.get("weight", "1"), f"edge_weights[{i}]")
        for i, e in enumerate(input_spec["carrier"]["edges"])
    ]

    primal = candidate_spec.get("primal_candidate")
    dual = candidate_spec.get("dual_witness")

    if not primal or not dual:
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_INCOMPLETE_CERTIFICATE",
            admitted=False,
            detail="Certificate must supply both primal_candidate and dual_witness",
            primal_feasible=False,
            dual_feasible=False,
            primal_objective=None,
            dual_objective=None,
            duality_gap=None,
            is_exact_zero_gap=False,
        )

    # 1. Parse and verify primal candidate
    try:
        alpha = parse_vector(primal["alpha"], "alpha")
        u = parse_vector(primal["primal_upper_bound_u"], "u")
    except ValueError as exc:
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_RATIONAL_PARSE_ERROR",
            admitted=False,
            detail=str(exc),
            primal_feasible=False,
            dual_feasible=False,
            primal_objective=None,
            dual_objective=None,
            duality_gap=None,
            is_exact_zero_gap=False,
        )

    # d0 * alpha
    d0_alpha = matvec_mul_rational(d0, alpha)
    residuals = [c[i] - d0_alpha[i] for i in range(len(c))]

    # Check primal feasibility: u[i] >= |residuals[i]| and u[i] >= 0
    primal_feasible = True
    for i in range(len(residuals)):
        if u[i] < abs(residuals[i]) or u[i] < 0:
            primal_feasible = False
            break

    primal_obj = sum(weights[i] * u[i] for i in range(len(u)))

    if not primal_feasible:
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_PRIMAL_INFEASIBLE",
            admitted=False,
            detail="Primal bounding vector u violates u_e >= |c_e - (d0*alpha)_e|",
            primal_feasible=False,
            dual_feasible=False,
            primal_objective=str(primal_obj),
            dual_objective=None,
            duality_gap=None,
            is_exact_zero_gap=False,
        )

    # 2. Parse and verify dual witness
    try:
        w = parse_vector(dual["w"], "w")
    except ValueError as exc:
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_RATIONAL_PARSE_ERROR",
            admitted=False,
            detail=str(exc),
            primal_feasible=True,
            dual_feasible=False,
            primal_objective=str(primal_obj),
            dual_objective=None,
            duality_gap=None,
            is_exact_zero_gap=False,
        )

    # Check dual feasibility: |w_e| <= omega_e and d0^T * w == 0
    dual_bounds_feasible = all(abs(w[i]) <= weights[i] for i in range(len(w)))
    d0_t_w = transpose_matvec_mul_rational(d0, w)
    divergence_zero = all(val == 0 for val in d0_t_w)
    dual_feasible = dual_bounds_feasible and divergence_zero

    dual_obj = sum(w[i] * c[i] for i in range(len(w)))
    gap = primal_obj - dual_obj

    if not dual_feasible:
        detail_msg = []
        if not dual_bounds_feasible:
            detail_msg.append(
                f"Dual multiplier bounds violated: max|w_e| = {max(abs(x) for x in w)} > 1"
            )
        if not divergence_zero:
            detail_msg.append(
                f"Dual divergence non-zero: d0^T * w = {[str(x) for x in d0_t_w]} != 0"
            )
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_DUAL_INFEASIBLE",
            admitted=False,
            detail="; ".join(detail_msg),
            primal_feasible=True,
            dual_feasible=False,
            primal_objective=str(primal_obj),
            dual_objective=str(dual_obj),
            duality_gap=str(gap),
            is_exact_zero_gap=(gap == 0),
        )

    # 3. Check exact duality gap
    if gap != 0:
        return LpCheckReceipt(
            claim_id=claim_id,
            case_name=case_name,
            status="REFUSED_NONZERO_DUALITY_GAP",
            admitted=False,
            detail=f"Duality gap is non-zero in Q: gap = {gap} != 0",
            primal_feasible=True,
            dual_feasible=True,
            primal_objective=str(primal_obj),
            dual_objective=str(dual_obj),
            duality_gap=str(gap),
            is_exact_zero_gap=False,
        )

    return LpCheckReceipt(
        claim_id=claim_id,
        case_name=case_name,
        status="CERTIFIED_OPTIMAL_LP_GAP_ZERO",
        admitted=True,
        detail=(
            f"Exact optimality certified in Q: primal_obj = {primal_obj}, dual_obj = {dual_obj}, "
            f"duality_gap = 0. Both primal and dual feasibility conditions independently checked."
        ),
        primal_feasible=True,
        dual_feasible=True,
        primal_objective=str(primal_obj),
        dual_objective=str(dual_obj),
        duality_gap="0",
        is_exact_zero_gap=True,
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

    res_valid = verify_lp_certificate(inp, w_valid, case_name="valid_rational_certificate")

    near_results: list[dict[str, Any]] = []
    for case in w_near.get("test_cases", []):
        res_case = verify_lp_certificate(inp, case, case_name=case.get("name", "unknown"))
        near_results.append(asdict(res_case))

    output = {
        "dossier": "dossier_2_exact_lp_certificate",
        "valid_witness_result": asdict(res_valid),
        "near_miss_results": near_results,
    }

    out_file = base_dir / "checker_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output


if __name__ == "__main__":
    out = run_standalone()
    print("Dossier 2 Checker Execution Completed.")
    print("Valid witness status:", out["valid_witness_result"]["status"])
    for nr in out["near_miss_results"]:
        print(f"Near miss [{nr['case_name']}] status: {nr['status']}")
