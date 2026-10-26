"""Independent certificate verification for supported cohomology operations.

C011 checks exact primal/dual feasibility and zero duality gap. C011/C012
scope refusals require a matching defect in the input. C012-C020 mathematical
certificates remain unverified until an independent checker is available.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from .models import CertificateCheckResult
from .solver import detect_challenge
from .validation import exact_fraction, exact_values, parse_c011_case, scope_violations


def check_certificate(case_dict: Mapping[str, Any], res_dict: Mapping[str, Any]) -> CertificateCheckResult:
    """Verify evidence without treating a refusal or an unavailable check as success."""
    cid = "unknown"
    case_id = "unnamed"
    status = "INVALID"
    try:
        if not isinstance(case_dict, Mapping) or not isinstance(res_dict, Mapping):
            raise ValueError("Case and result must be objects")
        cid = detect_challenge(case_dict)
        case_id = str(case_dict.get("case_id") or case_dict.get("id") or "unnamed")
        status = res_dict.get("status")
        if type(status) is not str:
            raise ValueError("Status must be a string")
        if cid not in {f"c{n:03d}" for n in range(11, 21)}:
            raise ValueError(f"Unsupported challenge: {cid}")
        if status == "UNKNOWN":
            passed, error = False, "UNKNOWN is a refusal, not a verified certificate"
        elif status == "OUT_OF_SCOPE":
            passed, error = _check_out_of_scope(case_dict, res_dict)
        elif status != "SOLVED":
            passed, error = False, f"Unexpected status: {status}"
        elif cid == "c011":
            passed, error = _check_c011(case_dict, res_dict)
        else:
            passed, error = False, f"Independent certificate verification unavailable for {cid}"
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError) as exc:
        passed, error = False, f"Invalid certificate input: {exc}"
    return CertificateCheckResult(
        case_id=case_id, challenge_id=cid, passed=passed, status=str(status), error=error
    )


def _check_out_of_scope(case: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[bool, str | None]:
    witness = result.get("witness")
    if not isinstance(witness, Mapping):
        return False, "OUT_OF_SCOPE requires an object witness"
    reason, edge = witness.get("reason"), witness.get("edge")
    if type(reason) is not str or type(edge) is not str:
        return False, "OUT_OF_SCOPE witness needs a reason and edge"
    defects = scope_violations(case)
    if any(defect["reason"] == reason and defect["edge"] == edge for defect in defects):
        return True, None
    return False, "OUT_OF_SCOPE witness does not match a defect in the input"


def _check_c011(case: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[bool, str | None]:
    """Check an exact L1 optimum using its supplied primal and dual witnesses."""
    if scope_violations(case):
        return False, "C011 input is out of scope and cannot be certified SOLVED"
    nodes, edges, claims, weights = parse_c011_case(case)
    node_set = set(nodes)
    edge_set = {f"{u}->{v}" for u, v in edges}
    phi1 = exact_fraction(result["phi1"])
    potential = exact_values(result.get("potential"), node_set, "potential")
    if set(potential) != node_set:
        return False, "Potential must give an exact value for every node"
    repair = exact_values(result.get("repair", {}), edge_set, "repair")
    dual = exact_values(result.get("dual", {}), edge_set, "dual")

    primal_l1 = Fraction(0)
    dual_val = Fraction(0)
    divergence = {node: Fraction(0) for node in nodes}
    for u, v in edges:
        key = f"{u}->{v}"
        c_e = claims.get(key, Fraction(0))
        w_e = weights.get(key, Fraction(1))
        r_e = repair.get(key, Fraction(0))
        y_e = dual.get(key, Fraction(0))
        if c_e - r_e != potential[v] - potential[u]:
            return False, f"Primal feasibility violated on {key}"
        if abs(y_e) > w_e:
            return False, f"Dual bound violated on {key}"
        primal_l1 += w_e * abs(r_e)
        dual_val += c_e * y_e
        divergence[u] -= y_e
        divergence[v] += y_e

    for node, value in divergence.items():
        if value:
            return False, f"Dual circulation condition violated at {node}"
    if primal_l1 != dual_val:
        return False, f"Duality gap non-zero: primal {primal_l1} != dual {dual_val}"
    if primal_l1 != phi1:
        return False, f"Phi1 mismatch: reported {phi1} != calculated {primal_l1}"
    return True, None
