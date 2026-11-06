"""Reference solver interface for C052: Max-Flow with Min-Cut Certificates."""

from typing import Any, Dict, List

from .max_flow import DinicMaxFlow


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "mf_unknown")

    # 1. Schema and field presence check
    if not isinstance(case, dict):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    if "n" not in case or "s" not in case or "t" not in case or "arcs" not in case:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    try:
        n = int(case["n"])
        s = int(case["s"])
        t = int(case["t"])
        arcs = case["arcs"]
    except (ValueError, TypeError):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    # Node bounds check
    if n <= 0 or s < 0 or s >= n or t < 0 or t >= n:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "NODE_OUT_OF_BOUNDS"},
        }

    # Source equals sink check
    if s == t:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "SOURCE_EQUALS_SINK"},
        }

    if not isinstance(arcs, list):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    # Arc validation check
    parsed_arcs: List[List[int]] = []
    for arc_idx, arc in enumerate(arcs):
        if not isinstance(arc, (list, tuple)) or len(arc) != 3:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "MALFORMED_INPUT", "arc": arc_idx},
            }
        try:
            u = int(arc[0])
            v = int(arc[1])
            cap = int(arc[2])
        except (ValueError, TypeError):
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "MALFORMED_INPUT", "arc": arc_idx},
            }

        if u < 0 or u >= n or v < 0 or v >= n:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "NODE_OUT_OF_BOUNDS", "arc": arc_idx},
            }

        if cap < 0:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "NEGATIVE_CAPACITY", "arc": arc_idx},
            }

        parsed_arcs.append([u, v, cap])

    # Execute exact solver
    dinic = DinicMaxFlow(n, s, t, parsed_arcs)
    flow_val, arc_flows, cut_S = dinic.compute_max_flow()

    return {
        "case_id": case_id,
        "status": "SOLVED",
        "value": str(flow_val),
        "flow": [str(f) for f in arc_flows],
        "cut_S": cut_S,
    }
