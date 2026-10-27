# AuthorityEffect: None.
"""
Frozen Solver Entrypoint for C030: Tensor-Network Contraction Order Under a Cost Bound.

Exposes:
    solve(case: dict) -> dict
Adheres to SG-CP v1 (§4) output schema.
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .ddc_tracer import DDCTracer
    from .exact_dp_solver import solve_exact_subset_dp
    from .heuristic_search import solve_heuristic_search
    from .tensor_network import validate_network
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer
    from exact_dp_solver import solve_exact_subset_dp
    from heuristic_search import solve_heuristic_search
    from tensor_network import validate_network


def _parse_bound(value: Any, minimum: int) -> int | None:
    if value is None:
        return None
    if type(value) is int and value >= minimum:
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        if value != "0" and value.startswith("0"):
            raise ValueError("bound is not canonical")
        parsed = int(value)
        if parsed >= minimum:
            return parsed
    raise ValueError("bound must be a canonical non-negative integer")


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finds pairwise contraction order satisfying cost_bound and optional size_bound.
    """
    case_id = case.get("case_id", "c030_case")
    tracer = DDCTracer(case_id)

    tensors = case.get("tensors", {})
    dims = case.get("dims", {})
    cost_bound_raw = case.get("cost_bound")
    size_bound_raw = case.get("size_bound")

    try:
        cost_bound = _parse_bound(cost_bound_raw, 0)
    except ValueError:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_cost_bound", "actual_type": type(cost_bound_raw).__name__},
        }
    try:
        size_bound = _parse_bound(size_bound_raw, 1)
    except ValueError:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_size_bound", "actual_type": type(size_bound_raw).__name__},
        }

    # Step C: Expose problem configuration
    tracer.emit(
        "C",
        {
            "num_tensors": len(tensors),
            "num_indices": len(dims),
            "cost_bound": str(cost_bound) if cost_bound is not None else None,
            "size_bound": str(size_bound) if size_bound is not None else None,
        },
    )

    # Validate tensor network topology and dimensions
    is_valid, witness = validate_network(tensors, dims)
    if not is_valid:
        tracer.emit("M", {"refusal": "OUT_OF_SCOPE", "witness": witness})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": witness,
        }

    n = len(tensors)

    # Every contraction order ends in the tensor of all open legs, and its last step
    # costs at least that tensor's size; either bound can be refuted outright.
    open_counts: Dict[str, int] = {}
    for idx_list in tensors.values():
        for idx in idx_list:
            open_counts[idx] = open_counts.get(idx, 0) + 1
    open_size = 1
    for idx, count in open_counts.items():
        if count == 1:
            open_size *= dims[idx]
    for kind, bound in (
        ("open_legs_exceed_size_bound", size_bound),
        ("open_legs_exceed_cost_bound", cost_bound),
    ):
        if bound is not None and open_size > bound:
            tracer.emit(
                "R", {"refusal": "BOUND_NOT_MET", "witness_kind": kind, "open_size": open_size}
            )
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "BOUND_NOT_MET",
                "witness": {"kind": kind, "open_size": str(open_size)},
            }

    # For small networks (N <= 12), solve exactly via subset DP
    if n <= 12:
        tracer.emit("Lambda", {"method": "exact_subset_dp", "num_tensors": n})
        is_feasible, opt_cost, opt_order = solve_exact_subset_dp(
            tensors, dims, size_bound=size_bound
        )

        if is_feasible and (cost_bound is None or opt_cost <= cost_bound):
            tracer.emit("E", {"optimal_cost": opt_cost, "num_steps": len(opt_order)})
            tracer.emit("T", {"verdict": "SOLVED", "total_cost": opt_cost})
            return {
                "id": case_id,
                "status": "SOLVED",
                "order": opt_order,
                "total_cost": str(opt_cost),
                "optimal": True,
            }
        else:
            tracer.emit(
                "R", {"refusal": "BOUND_NOT_MET", "best_cost": opt_cost, "cost_bound": cost_bound}
            )
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "BOUND_NOT_MET",
            }

    # For larger networks (N > 12), solve via multi-strategy search
    tracer.emit("I", {"method": "heuristic_multi_start", "num_tensors": n})
    meets_bound, best_cost, best_order = solve_heuristic_search(
        tensors, dims, cost_bound=cost_bound, size_bound=size_bound, num_restarts=60
    )

    if meets_bound:
        tracer.emit("E", {"best_cost": best_cost, "num_steps": len(best_order)})
        tracer.emit("T", {"verdict": "SOLVED", "total_cost": best_cost})
        return {
            "id": case_id,
            "status": "SOLVED",
            "order": best_order,
            "total_cost": str(best_cost),
            "optimal": False,
        }
    else:
        tracer.emit(
            "R", {"refusal": "BOUND_NOT_MET", "best_cost": best_cost, "cost_bound": cost_bound}
        )
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "BOUND_NOT_MET",
        }
