"""Reference Solver for C039: Lattice Z2 Gauge Theory and Gauss Law.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace over {E, R, C, I, Lambda, D, M, T}.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .cell_complex import solve_degeneracy_query
    from .ddc_tracer import DDCTracer
    from .gauss_sector import solve_gauss_law_sector
except (ImportError, ValueError):
    from cell_complex import solve_degeneracy_query  # type: ignore
    from ddc_tracer import DDCTracer  # type: ignore
    from gauss_sector import solve_gauss_law_sector  # type: ignore

_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the DDCTracer instance from the most recent solve() call."""
    return _LAST_TRACER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes exact toric code degeneracy or Gauss-law sector dimension."""
    global _LAST_TRACER
    tracer = DDCTracer(challenge_id="c039_lattice_z2_gauge_theory_gauss_law")
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

    # If query not explicitly provided, infer from keys
    if query is None:
        if "charges" in case:
            query = "gauss_law_sector"
        elif "faces" in case:
            query = "degeneracy"

    tracer.record_step("C", {"stage": "context_intake", "case_id": cid, "query": query})

    if query == "degeneracy":
        status, extra, solution = solve_degeneracy_query(case)
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
            tracer.record_step("I", {"stage": "cell_complex_integration", "status": "non_manifold"})
            tracer.record_step("R", {"stage": "manifold_defect_residual", "witness": witness})
            tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": witness})
            tracer.record_step("T", {"stage": "terminal_out_of_scope"})
            return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

        # status == "SOLVED"
        assert solution is not None
        tracer.record_step(
            "I",
            {
                "stage": "incidence_integration_mod2",
                "V": solution["V"],
                "E": solution["E"],
                "F": solution["F"],
                "rank_star": solution["rank_star"],
                "rank_plaquette": solution["rank_plaquette"],
                "euler": solution["euler"],
            },
        )
        tracer.record_step(
            "Lambda",
            {
                "stage": "lift_cycles_and_cocycles",
                "k": solution["k"],
            },
        )
        tracer.record_step(
            "R",
            {
                "stage": "commutation_residual",
                "qubit_count": solution["k"],
            },
        )
        tracer.record_step(
            "D",
            {
                "stage": "symplectic_basis_repair",
                "k": solution["k"],
            },
        )
        tracer.record_step(
            "E",
            {
                "stage": "symplectic_basis_extraction",
                "gsd": solution["gsd"],
                "k": solution["k"],
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
            "rank_star": solution["rank_star"],
            "rank_plaquette": solution["rank_plaquette"],
            "k": solution["k"],
            "gsd": solution["gsd"],
            "logicals": solution["logicals"],
        }

    elif query == "gauss_law_sector":
        status, extra, solution = solve_gauss_law_sector(case)
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
        dim = solution["sector_dimension"]
        if dim == 0:
            witness = solution.get("witness", {"charge_product": -1})
            tracer.record_step("I", {"stage": "sector_charges_integration", "charge_product": -1})
            tracer.record_step("R", {"stage": "empty_sector_residual", "witness": witness})
            tracer.record_step("E", {"stage": "exact_dimension_extraction", "sector_dimension": 0})
            tracer.record_step("T", {"stage": "terminal_complete"})
            return {
                "id": cid,
                "status": "SOLVED",
                "sector_dimension": 0,
                "witness": witness,
            }
        else:
            tracer.record_step("I", {"stage": "sector_charges_integration", "charge_product": 1})
            tracer.record_step("D", {"stage": "cycle_rank_evaluation"})
            tracer.record_step(
                "E", {"stage": "exact_dimension_extraction", "sector_dimension": dim}
            )
            tracer.record_step("T", {"stage": "terminal_complete"})
            return {
                "id": cid,
                "status": "SOLVED",
                "sector_dimension": dim,
            }

    else:
        tracer.record_step(
            "M", {"stage": "fail_closed_refusal", "refusal": "MALFORMED_CASE_STRUCTURE"}
        )
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
