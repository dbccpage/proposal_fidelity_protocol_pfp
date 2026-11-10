"""Exact checker for C052: Max-Flow with Min-Cut Certificates."""

from typing import Any, Dict, List, Set, Tuple


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result must be a dictionary"

    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"case_id mismatch: expected {case.get('case_id')}, got {result.get('case_id')}",
        )

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    # 1. Check for expected OUT_OF_SCOPE conditions in input case
    is_malformed = False
    malformed_reason = ""
    try:
        n = int(case.get("n", -1))
        s = int(case.get("s", -1))
        t = int(case.get("t", -1))
        arcs = case.get("arcs")
        if not isinstance(arcs, list) or n <= 0 or s < 0 or s >= n or t < 0 or t >= n:
            is_malformed = True
            malformed_reason = "NODE_OUT_OF_BOUNDS_OR_MALFORMED"
        elif s == t:
            is_malformed = True
            malformed_reason = "SOURCE_EQUALS_SINK"
        else:
            for idx, a in enumerate(arcs):
                if not isinstance(a, (list, tuple)) or len(a) != 3:
                    is_malformed = True
                    malformed_reason = "MALFORMED_ARC"
                    break
                u, v, cap = int(a[0]), int(a[1]), int(a[2])
                if u < 0 or u >= n or v < 0 or v >= n:
                    is_malformed = True
                    malformed_reason = "NODE_OUT_OF_BOUNDS"
                    break
                if cap < 0:
                    is_malformed = True
                    malformed_reason = "NEGATIVE_CAPACITY"
                    break
    except Exception as e:
        is_malformed = True
        malformed_reason = f"INPUT_PARSE_ERROR: {e}"

    if is_malformed:
        if status == "OUT_OF_SCOPE":
            return True, f"Correctly identified OUT_OF_SCOPE: {malformed_reason}"
        else:
            return (
                False,
                f"Case was malformed ({malformed_reason}), but solver returned status={status}",
            )

    if status == "OUT_OF_SCOPE":
        return False, "Solver claimed OUT_OF_SCOPE on a valid problem instance"

    if status == "UNKNOWN":
        return False, "Solver returned UNKNOWN status"

    # 2. Check SOLVED certificate
    if "value" not in result or "flow" not in result or "cut_S" not in result:
        return False, "SOLVED result missing required fields ('value', 'flow', 'cut_S')"

    # Validate value format
    val_str = result["value"]
    if not isinstance(val_str, str):
        return False, f"Value must be a canonical decimal string, got {type(val_str)}"
    try:
        val = int(val_str)
        if val < 0 or str(val) != val_str:
            return False, f"Value must be a canonical non-negative integer string, got '{val_str}'"
    except ValueError:
        return False, f"Value '{val_str}' is not a valid integer string"

    # Validate flow list
    flow_list = result["flow"]
    if not isinstance(flow_list, list):
        return False, "Flow must be a list"
    if len(flow_list) != len(arcs):
        return False, f"Flow length {len(flow_list)} does not match arc count {len(arcs)}"

    flows: List[int] = []
    for idx, f_item in enumerate(flow_list):
        if not isinstance(f_item, str):
            return False, f"Arc flow at index {idx} must be a string, got {type(f_item)}"
        try:
            f_val = int(f_item)
            if f_val < 0 or str(f_val) != f_item:
                return False, f"Arc flow at index {idx} '{f_item}' is non-canonical or negative"
        except ValueError:
            return False, f"Arc flow at index {idx} '{f_item}' is not an integer string"

        cap = int(arcs[idx][2])
        if f_val > cap:
            return (
                False,
                f"Arc {idx} ({arcs[idx][0]}->{arcs[idx][1]}) flow {f_val} exceeds capacity {cap}",
            )
        flows.append(f_val)

    # Flow conservation and net balance
    net_flow = [0] * n
    for idx, arc in enumerate(arcs):
        u, v = int(arc[0]), int(arc[1])
        f_val = flows[idx]
        net_flow[u] -= f_val  # outflow
        net_flow[v] += f_val  # inflow

    for node in range(n):
        if node == s:
            if -net_flow[node] != val:
                return (
                    False,
                    f"Net outflow at source {s} is {-net_flow[node]}, expected value {val}",
                )
        elif node == t:
            if net_flow[node] != val:
                return False, f"Net inflow at sink {t} is {net_flow[node]}, expected value {val}"
        else:
            if net_flow[node] != 0:
                return (
                    False,
                    f"Flow conservation violated at internal node {node}: net balance is {net_flow[node]}",
                )

    # Validate cut_S
    cut_S_raw = result["cut_S"]
    if not isinstance(cut_S_raw, list):
        return False, "cut_S must be a list"

    cut_S_set: Set[int] = set()
    for item in cut_S_raw:
        if type(item) is not int:  # strict type checking: rejects bool, float, str
            return False, f"Node in cut_S must be strict int, got {type(item)}: {item}"
        if item < 0 or item >= n:
            return False, f"Node {item} in cut_S is out of range [0, {n - 1}]"
        if item in cut_S_set:
            return False, f"Duplicate node {item} in cut_S"
        cut_S_set.add(item)

    if s not in cut_S_set:
        return False, f"Source node {s} must be in cut_S"
    if t in cut_S_set:
        return False, f"Sink node {t} must not be in cut_S"

    # Validate cut capacity
    cut_cap = 0
    for idx, arc in enumerate(arcs):
        u, v = int(arc[0]), int(arc[1])
        cap = int(arc[2])
        f_val = flows[idx]
        if u in cut_S_set and v not in cut_S_set:
            cut_cap += cap
            # Complementary slackness: forward cut edges must be saturated
            if f_val != cap:
                return (
                    False,
                    f"Forward cut edge {idx} ({u}->{v}) not saturated: flow {f_val} != cap {cap}",
                )
        elif u not in cut_S_set and v in cut_S_set:
            # Complementary slackness: backward cut edges must have zero flow
            if f_val != 0:
                return False, f"Backward cut edge {idx} ({u}->{v}) has non-zero flow: {f_val}"

    if cut_cap != val:
        return False, f"Cut capacity {cut_cap} does not equal flow value {val}"

    return True, f"Valid max-flow min-cut certificate with exact value {val}"
