"""Reference Solver for C018: Frustration Index of Signed Graphs."""

from __future__ import annotations

from typing import Any

from .ddc_tracer import DdcOperationalTracer
from .graph_blocks import (
    count_negative_edges,
    find_biconnected_components,
    find_negative_cycle_packing,
    local_search_switching,
    parse_graph,
    solve_exhaustive,
)


def solve(case: dict[str, Any]) -> tuple[dict[str, Any], DdcOperationalTracer]:
    """Solve C018 case returning certificate or honest UNKNOWN with bounds."""
    tracer = DdcOperationalTracer(challenge_id=case.get("id", "c018"))
    tracer.record("C", "INIT", "Parsed signed graph case", case_id=case.get("id"))

    # 1. Validation
    try:
        vertices, edges, edge_dict = parse_graph(case)
    except ValueError as e:
        msg = str(e)
        if msg.startswith("SELF_LOOP:"):
            v = msg.split(":")[1]
            tracer.record("M", "REFUSAL", "Self loop detected", vertex=v)
            res = {
                "id": case.get("id", "unknown"),
                "status": "OUT_OF_SCOPE",
                "witness": {"edge": [v, v], "reason": "SELF_LOOP"},
            }
            tracer.record("T", "TERMINAL", "Terminated with OUT_OF_SCOPE")
            return res, tracer
        elif msg.startswith("INVALID_SIGN:"):
            tracer.record("M", "REFUSAL", "Invalid sign detected")
            res = {
                "id": case.get("id", "unknown"),
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "INVALID_SIGN"},
            }
            tracer.record("T", "TERMINAL", "Terminated with OUT_OF_SCOPE")
            return res, tracer
        else:
            raise

    # 2. Block decomposition (Lambda in DDC)
    tracer.record(
        "Lambda",
        "DECOMPOSE",
        "Decomposing graph into 2-connected blocks",
        num_vertices=len(vertices),
        num_edges=len(edges),
    )
    find_biconnected_components(vertices, edges)

    # If small graph (|V| <= 20), solve exhaustively
    if len(vertices) <= 20:
        opt_l, switching = solve_exhaustive(vertices, edges)
        tracer.record("E", "EXHAUSTIVE", "Exhaustive search exact optimum certified", opt_l=opt_l)
        neg_count, deleted = count_negative_edges(edges, switching)
        res = {
            "id": case.get("id", "unknown"),
            "status": "SOLVED",
            "l": str(opt_l),
            "switching": {k: ("+1" if v == 1 else "-1") for k, v in switching.items() if v != 1},
            "deleted": deleted,
            "lower_bound": {"kind": "exhaustive"},
        }
        tracer.record("T", "TERMINAL", "Terminated with exact SOLVED certificate")
        return res, tracer

    # 3. For larger graphs, use local search + cycle packing
    # Upper bound via local switching
    best_l, switching = local_search_switching(vertices, edges)
    tracer.record("D", "LOCAL_SEARCH", "Found switching upper bound", upper=best_l)
    neg_count, deleted = count_negative_edges(edges, switching)

    # Lower bound via negative cycle packing
    packing = find_negative_cycle_packing(vertices, edges)
    lower_bound = len(packing)
    tracer.record(
        "I", "LOWER_BOUND", "Computed negative cycle packing lower bound", packing_count=lower_bound
    )

    # Check if balanced (l == 0)
    if best_l == 0:
        res = {
            "id": case.get("id", "unknown"),
            "status": "SOLVED",
            "l": "0",
            "switching": {k: ("+1" if v == 1 else "-1") for k, v in switching.items() if v != 1},
            "deleted": [],
            "lower_bound": {"kind": "packing", "cycles": []},
        }
        tracer.record("T", "TERMINAL", "Terminated with balanced SOLVED certificate")
        return res, tracer

    if lower_bound == best_l:
        # Certified optimal via packing!
        res = {
            "id": case.get("id", "unknown"),
            "status": "SOLVED",
            "l": str(best_l),
            "switching": {k: ("+1" if v == 1 else "-1") for k, v in switching.items() if v != 1},
            "deleted": deleted,
            "lower_bound": {"kind": "packing", "cycles": packing},
        }
        tracer.record("T", "TERMINAL", "Terminated with packing-certified SOLVED")
        return res, tracer

    # Otherwise, return honest UNKNOWN with bounds
    tracer.record(
        "M", "REFUSAL", "Optimality uncertified, returning bounds", upper=best_l, lower=lower_bound
    )
    res = {
        "id": case.get("id", "unknown"),
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": str(best_l),
        "lower": str(lower_bound),
        "switching": {k: ("+1" if v == 1 else "-1") for k, v in switching.items() if v != 1},
        "lower_bound": {"kind": "packing", "cycles": packing},
    }
    tracer.record("T", "TERMINAL", "Terminated with UNKNOWN bounds")
    return res, tracer
