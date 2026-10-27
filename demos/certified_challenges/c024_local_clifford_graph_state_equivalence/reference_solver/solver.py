"""Reference Solver Entry Point for C024 (Local Clifford Graph State Equivalence).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

try:
    from .ddc_tracer import DDCTracer
    from .graph import SimpleGraph, validate_simple_graph
    from .orbit_search import decide_local_equivalence
except (ImportError, ValueError):
    try:
        from c024_local_clifford_graph_state_equivalence.reference_solver.ddc_tracer import DDCTracer
        from c024_local_clifford_graph_state_equivalence.reference_solver.graph import SimpleGraph, validate_simple_graph
        from c024_local_clifford_graph_state_equivalence.reference_solver.orbit_search import decide_local_equivalence
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from graph import SimpleGraph, validate_simple_graph
        from orbit_search import decide_local_equivalence


def solve(case: dict[str, Any]) -> dict[str, Any]:
    """Solves a C024 local Clifford graph state equivalence problem instance."""
    case_id = case.get("id") or case.get("case_id", "c024_unnamed")
    tracer = DDCTracer(run_id=f"c024_{case_id}")

    tracer.record_step("C", "intake_case", {"case_id": case_id})

    num_vertices = case.get("num_vertices")
    edges_g = case.get("g")
    edges_g_prime = case.get("g_prime")

    # Validate num_vertices
    if not isinstance(num_vertices, int) or num_vertices < 2 or num_vertices > 16:
        tracer.record_step(
            "M",
            "refuse_num_vertices",
            {"num_vertices": num_vertices},
            refusal_reason="NUM_VERTICES_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize", {"verdict": "UNKNOWN"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "NUM_VERTICES_OUT_OF_BOUNDS",
        }

    # Validate graph G
    valid_g, defect_g = validate_simple_graph(num_vertices, edges_g)
    if not valid_g:
        tracer.record_step("M", "defect_in_g", defect_g)
        tracer.record_step("T", "terminalize", {"verdict": "OUT_OF_SCOPE"})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": defect_g,
        }

    # Validate graph G'
    valid_gp, defect_gp = validate_simple_graph(num_vertices, edges_g_prime)
    if not valid_gp:
        tracer.record_step("M", "defect_in_g_prime", defect_gp)
        tracer.record_step("T", "terminalize", {"verdict": "OUT_OF_SCOPE"})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": defect_gp,
        }

    # Construct SimpleGraph objects
    g = SimpleGraph(num_vertices, edges_g)
    gp = SimpleGraph(num_vertices, edges_g_prime)

    tracer.record_step(
        "I",
        "integrate_graphs",
        {"num_vertices": num_vertices, "edges_g": len(edges_g), "edges_gp": len(edges_g_prime)},
    )

    equiv, seq, witness = decide_local_equivalence(g, gp)

    if equiv is None:
        tracer.record_step("M", "orbit_search_budget_exhausted", witness)
        tracer.record_step("T", "terminalize", {"verdict": "UNKNOWN"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "ORBIT_SEARCH_BUDGET_EXHAUSTED",
            "witness": witness,
        }

    if equiv is True:
        tracer.record_step("E", "equivalent_sequence_verified", {"length": len(seq or [])})
        tracer.record_step("T", "terminalize", {"verdict": "SOLVED", "equivalent": True})
        return {
            "id": case_id,
            "status": "SOLVED",
            "equivalent": True,
            "sequence": seq,
        }
    else:
        tracer.record_step("R", "separating_witness_found", witness)
        tracer.record_step("T", "terminalize", {"verdict": "SOLVED", "equivalent": False})
        return {
            "id": case_id,
            "status": "SOLVED",
            "equivalent": False,
            "witness": witness,
        }


__all__ = [
    "solve",
]
