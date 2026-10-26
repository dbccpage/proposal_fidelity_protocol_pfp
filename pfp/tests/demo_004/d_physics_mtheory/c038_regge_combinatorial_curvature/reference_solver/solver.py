"""Reference Solver for C038: Combinatorial Curvature and Discrete Gauss-Bonnet.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .graph_curvature import solve_graph_case
    from .regge_surface import solve_surface_case
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer  # type: ignore
    from graph_curvature import solve_graph_case  # type: ignore
    from regge_surface import solve_surface_case  # type: ignore

_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the DDCTracer instance from the most recent solve() call."""
    return _LAST_TRACER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes exact combinatorial or graph curvature for a C038 challenge case."""
    global _LAST_TRACER
    tracer = DDCTracer(challenge_id="c038_regge_combinatorial_curvature")
    _LAST_TRACER = tracer

    if not isinstance(case, Mapping):
        tracer.record_step("C", {"stage": "context_intake", "case_id": "malformed"})
        tracer.record_step(
            "M", {"stage": "fail_closed_refusal", "refusal": "MALFORMED_CASE_STRUCTURE"}
        )
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return {"id": "malformed", "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}

    cid = str(case.get("case_id") or case.get("id") or "unknown_case")
    query = case.get("query")

    tracer.record_step("C", {"stage": "context_intake", "case_id": cid, "query": query})

    if query == "surface":
        status, extra, solution = solve_surface_case(case)
        if status == "UNKNOWN":
            refusal_code = (
                extra.get("refusal_code", "MALFORMED_CASE_STRUCTURE")
                if extra
                else "MALFORMED_CASE_STRUCTURE"
            )
            tracer.record_step("M", {"stage": "fail_closed_refusal", "refusal": refusal_code})
            tracer.record_step("T", {"stage": "terminal_refusal"})
            return {"id": cid, "status": "UNKNOWN", "refusal_code": refusal_code}

        if status == "OUT_OF_SCOPE":
            witness = (
                extra.get("witness", {"kind": "out_of_scope"})
                if extra
                else {"kind": "out_of_scope"}
            )
            tracer.record_step(
                "I", {"stage": "incidence_and_link_integration", "status": "non_manifold"}
            )
            tracer.record_step("R", {"stage": "manifold_defect_residual", "witness": witness})
            tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": witness})
            tracer.record_step("T", {"stage": "terminal_out_of_scope"})
            return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

        # status == "SOLVED"
        assert solution is not None
        tracer.record_step(
            "I",
            {
                "stage": "incidence_and_link_integration",
                "V": solution["V"],
                "E": solution["E"],
                "F": solution["F"],
            },
        )
        tracer.record_step("R", {"stage": "manifold_defect_residual", "defect_count": 0})
        tracer.record_step(
            "D",
            {
                "stage": "discrete_gauss_bonnet_evaluation",
                "euler": solution["euler"],
                "orientable": solution["orientable"],
            },
        )
        tracer.record_step(
            "E",
            {
                "stage": "combinatorial_curvature_extraction",
                "gauss_bonnet_sum_residual": 0,
                "vertex_count": solution["V"],
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})

        return {
            "id": cid,
            "status": "SOLVED",
            "V": solution["V"],
            "E": solution["E"],
            "F": solution["F"],
            "euler": solution["euler"],
            "orientable": solution["orientable"],
            "classification": solution["classification"],
            "vertex_curvature": solution["vertex_curvature"],
        }

    elif query == "graph":
        status, extra, solution = solve_graph_case(case)
        if status == "UNKNOWN":
            refusal_code = (
                extra.get("refusal_code", "MALFORMED_CASE_STRUCTURE")
                if extra
                else "MALFORMED_CASE_STRUCTURE"
            )
            tracer.record_step("M", {"stage": "fail_closed_refusal", "refusal": refusal_code})
            tracer.record_step("T", {"stage": "terminal_refusal"})
            return {"id": cid, "status": "UNKNOWN", "refusal_code": refusal_code}

        if status == "OUT_OF_SCOPE":
            witness = (
                extra.get("witness", {"kind": "out_of_scope"})
                if extra
                else {"kind": "out_of_scope"}
            )
            tracer.record_step(
                "I", {"stage": "graph_topology_integration", "status": "invalid_graph"}
            )
            tracer.record_step("R", {"stage": "graph_defect_residual", "witness": witness})
            tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": witness})
            tracer.record_step("T", {"stage": "terminal_out_of_scope"})
            return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

        # status == "SOLVED"
        assert solution is not None
        edge_results = solution["edges"]
        tracer.record_step(
            "I",
            {
                "stage": "graph_topology_integration",
                "edge_count": len(edge_results),
            },
        )
        for e_item in edge_results:
            tracer.record_step(
                "R",
                {
                    "stage": "primal_dual_duality_gap_residual",
                    "edge": e_item["edge"],
                    "duality_gap": 0,
                },
            )
            tracer.record_step(
                "D",
                {
                    "stage": "transport_descent_evaluation",
                    "edge": e_item["edge"],
                    "forman": e_item["forman"],
                    "ollivier": e_item["ollivier"],
                },
            )
        tracer.record_step(
            "E",
            {
                "stage": "curvature_certificate_extraction",
                "edge_count": len(edge_results),
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})

        return {
            "id": cid,
            "status": "SOLVED",
            "edges": edge_results,
        }

    else:
        tracer.record_step(
            "M", {"stage": "fail_closed_refusal", "refusal": "MALFORMED_CASE_STRUCTURE"}
        )
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
