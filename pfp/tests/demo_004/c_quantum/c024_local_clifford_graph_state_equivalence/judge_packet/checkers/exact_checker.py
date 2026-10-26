"""Exact Checker for C024 (Local Clifford Graph State Equivalence).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from ...reference_solver.cut_rank import cut_rank
from ...reference_solver.graph import SimpleGraph, validate_simple_graph
from ...reference_solver.solver import solve as ref_solve
from .schema_guard import validate_certificate


def check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Verifies candidate solution against case specification."""
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return {"verdict": "FAIL", "reason": schema_error}
    status = cert.get("status")
    expected = ref_solve(case)
    expected_status = expected.get("status")

    if status != expected_status:
        return {
            "verdict": "FAIL",
            "reason": f"Status mismatch: expected {expected_status}, got {status}",
        }

    # Handle UNKNOWN
    if status == "UNKNOWN":
        refusal_code = cert.get("refusal_code")
        exp_code = expected.get("refusal_code")
        if refusal_code != exp_code:
            return {
                "verdict": "FAIL",
                "reason": f"Refusal code mismatch: expected {exp_code}, got {refusal_code}",
            }
        if "equivalent" in cert:
            return {
                "verdict": "FAIL",
                "reason": "UNKNOWN must not assert an equivalence decision",
            }
        if refusal_code == "ORBIT_SEARCH_BUDGET_EXHAUSTED":
            witness = cert.get("witness")
            expected_witness = expected.get("witness")
            if witness != expected_witness:
                return {
                    "verdict": "FAIL",
                    "reason": "Orbit budget witness does not match the bounded reference replay",
                }
        return {"verdict": "PASS", "details": f"Refusal verified: {refusal_code}"}

    # Handle OUT_OF_SCOPE
    if status == "OUT_OF_SCOPE":
        act_w = cert.get("witness", {})
        kind = act_w.get("kind")
        if not kind:
            return {"verdict": "FAIL", "reason": "Malformed OUT_OF_SCOPE witness: missing kind"}

        # Validate that G or G' actually violates simple graph specification
        num_v = case.get("num_vertices", 0)
        edges_g = case.get("g")
        edges_gp = case.get("g_prime")
        vg, _ = validate_simple_graph(num_v, edges_g)
        vgp, _ = validate_simple_graph(num_v, edges_gp)
        if vg and vgp:
            return {
                "verdict": "FAIL",
                "reason": "Claimed OUT_OF_SCOPE but both graphs are valid simple graphs",
            }

        return {"verdict": "PASS", "details": f"Out of scope defect verified: {kind}"}

    # Handle SOLVED
    equiv = cert.get("equivalent")
    exp_equiv = expected.get("equivalent")
    if equiv != exp_equiv:
        return {
            "verdict": "FAIL",
            "reason": f"Equivalence decision mismatch: expected {exp_equiv}, got {equiv}",
        }

    num_v = case.get("num_vertices", 0)
    edges_g = case.get("g", [])
    edges_gp = case.get("g_prime", [])

    g = SimpleGraph(num_v, edges_g)
    gp = SimpleGraph(num_v, edges_gp)

    if equiv is True:
        # Verify sequence of local complementations
        seq = cert.get("sequence")
        if not isinstance(seq, list):
            return {"verdict": "FAIL", "reason": "Missing or non-list sequence for equivalent=True"}

        curr = g.copy()
        for idx, v in enumerate(seq):
            if not isinstance(v, int) or v < 0 or v >= num_v:
                return {
                    "verdict": "FAIL",
                    "reason": f"Invalid vertex in sequence at index {idx}: {v}",
                }
            curr = curr.local_complementation(v)

        if curr != gp:
            return {
                "verdict": "FAIL",
                "reason": "Replaying local complementation sequence did not produce target graph G'",
            }

        return {"verdict": "PASS", "details": f"Equivalent sequence verified (length {len(seq)})"}
    else:
        # Verify separating witness
        witness = cert.get("witness")
        if not isinstance(witness, dict):
            return {"verdict": "FAIL", "reason": "Missing witness dictionary for equivalent=False"}

        kind = witness.get("kind")
        if kind == "cut_rank":
            subset = witness.get("subset")
            if not isinstance(subset, list) or not subset:
                return {
                    "verdict": "FAIL",
                    "reason": "Malformed cut_rank witness: subset must be a non-empty list",
                }

            for u in subset:
                if not isinstance(u, int) or u < 0 or u >= num_v:
                    return {"verdict": "FAIL", "reason": f"Invalid vertex in cut_rank subset: {u}"}

            r_g = cut_rank(g, subset)
            r_gp = cut_rank(gp, subset)

            if r_g == r_gp:
                return {
                    "verdict": "FAIL",
                    "reason": f"Reported cut_rank subset does not separate graphs: rank_g == rank_g_prime == {r_g}",
                }

            rep_rg = witness.get("rank_g")
            rep_rgp = witness.get("rank_g_prime")
            if rep_rg != r_g or rep_rgp != r_gp:
                return {
                    "verdict": "FAIL",
                    "reason": f"Cut-rank values mismatch: computed ({r_g}, {r_gp}) != reported ({rep_rg}, {rep_rgp})",
                }

            return {
                "verdict": "PASS",
                "details": f"Cut-rank separation verified on subset of size {len(subset)}",
            }
        elif kind == "orbit_exhaustion":
            expected_witness = expected.get("witness")
            if (
                not isinstance(expected_witness, dict)
                or expected_witness.get("kind") != "orbit_exhaustion"
            ):
                return {
                    "verdict": "FAIL",
                    "reason": "Reference replay did not exhaust an orbit",
                }
            if witness != expected_witness:
                return {
                    "verdict": "FAIL",
                    "reason": "Orbit exhaustion witness does not match the complete reference replay",
                }
            return {"verdict": "PASS", "details": "Orbit exhaustion witness verified"}
        else:
            return {"verdict": "FAIL", "reason": f"Unknown separating witness kind: {kind}"}


__all__ = [
    "check_certificate",
]
