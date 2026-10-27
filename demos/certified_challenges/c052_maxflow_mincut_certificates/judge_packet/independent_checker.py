"""Independent second checker for C052: Max-Flow Min-Cut Certificates.
Uses residual graph reachability and dual cut-partition boundary verification.
"""

from typing import Any, Dict, List, Set, Tuple


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict) or not isinstance(case, dict):
        return False, "Case and result must be dictionaries"

    if result.get("case_id") != case.get("case_id"):
        return False, "Mismatched case_id"

    # 1. Independent evaluation of whether case is malformed / out of scope
    is_invalid = False
    try:
        n = case["n"]
        s = case["s"]
        t = case["t"]
        arcs = case["arcs"]
        if (
            not isinstance(n, int)
            or not isinstance(s, int)
            or not isinstance(t, int)
            or not isinstance(arcs, list)
        ):
            is_invalid = True
        elif n <= 0 or s < 0 or s >= n or t < 0 or t >= n or s == t:
            is_invalid = True
        else:
            for arc in arcs:
                if not isinstance(arc, (list, tuple)) or len(arc) != 3:
                    is_invalid = True
                    break
                u, v, cap = int(arc[0]), int(arc[1]), int(arc[2])
                if u < 0 or u >= n or v < 0 or v >= n or cap < 0:
                    is_invalid = True
                    break
    except Exception:
        is_invalid = True

    status = result.get("status")
    if is_invalid:
        if status == "OUT_OF_SCOPE":
            return True, "Valid OUT_OF_SCOPE rejection"
        return False, f"Expected OUT_OF_SCOPE for malformed input, got {status}"

    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"

    # Check fields
    if "value" not in result or "flow" not in result or "cut_S" not in result:
        return False, "Missing mandatory fields"

    val_str = result["value"]
    flow_list = result["flow"]
    cut_S_list = result["cut_S"]

    if (
        not isinstance(val_str, str)
        or not isinstance(flow_list, list)
        or not isinstance(cut_S_list, list)
    ):
        return False, "Type mismatch on result fields"

    if len(flow_list) != len(arcs):
        return False, "Flow vector length mismatch"

    try:
        val = int(val_str)
        if val < 0 or str(val) != val_str:
            return False, "Value string is non-canonical"
    except ValueError:
        return False, "Value string is not an integer"

    # Build residual adjacency and verify capacities
    residual_adj: List[List[Tuple[int, int]]] = [
        [] for _ in range(n)
    ]  # (neighbor, residual_capacity)
    inflow = [0] * n
    outflow = [0] * n

    for idx, (a, f_str) in enumerate(zip(arcs, flow_list)):
        if not isinstance(f_str, str):
            return False, f"Flow item at index {idx} not a string"
        try:
            f = int(f_str)
            if f < 0 or str(f) != f_str:
                return False, f"Flow item at index {idx} not canonical non-negative integer"
        except ValueError:
            return False, f"Flow item at index {idx} is invalid integer"

        u, v, cap = int(a[0]), int(a[1]), int(a[2])
        if f > cap:
            return False, f"Flow {f} exceeds capacity {cap} on arc {idx}"

        outflow[u] += f
        inflow[v] += f

        # Forward residual capacity
        rem_fwd = cap - f
        if rem_fwd > 0:
            residual_adj[u].append((v, rem_fwd))
        # Backward residual capacity
        if f > 0:
            residual_adj[v].append((u, f))

    # Check flow conservation
    for i in range(n):
        if i == s:
            if outflow[s] - inflow[s] != val:
                return False, f"Source net balance {outflow[s] - inflow[s]} != stated value {val}"
        elif i == t:
            if inflow[t] - outflow[t] != val:
                return False, f"Sink net balance {inflow[t] - outflow[t]} != stated value {val}"
        else:
            if inflow[i] != outflow[i]:
                return (
                    False,
                    f"Node {i} flow conservation failure: inflow {inflow[i]} != outflow {outflow[i]}",
                )

    # Check cut_S
    S_set: Set[int] = set()
    for node in cut_S_list:
        if type(node) is not int:  # strict int
            return False, f"cut_S member {node} is not strict int"
        if node < 0 or node >= n:
            return False, f"cut_S member {node} out of graph range"
        if node in S_set:
            return False, f"Duplicate node {node} in cut_S"
        S_set.add(node)

    if s not in S_set:
        return False, f"Source {s} missing from cut_S"
    if t in S_set:
        return False, f"Sink {t} present in cut_S"

    # Check that in residual graph, no residual edge leaves S into V \ S
    for u in S_set:
        for v, rem in residual_adj[u]:
            if v not in S_set and rem > 0:
                return (
                    False,
                    f"Residual arc from {u} in S to {v} not in S has positive capacity {rem}",
                )

    # Check cut capacity equals value
    computed_cut_cap = 0
    for a in arcs:
        u, v, cap = int(a[0]), int(a[1]), int(a[2])
        if u in S_set and v not in S_set:
            computed_cut_cap += cap

    if computed_cut_cap != val:
        return False, f"Cut capacity {computed_cut_cap} != flow value {val}"

    return True, f"Independent verification confirmed: flow={val}, cut_cap={computed_cut_cap}"
