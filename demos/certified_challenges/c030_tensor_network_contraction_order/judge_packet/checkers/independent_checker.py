# AuthorityEffect: None.
"""
Independent Second Checker for C030: Tensor-Network Contraction Order.

Independent verification engine:
- Uses disjoint-set / tree forest tracking rather than string concatenation.
- Tracks tensor index multiplicity directly.
- Validates step costs, size bounds, and terminal open indices.
- Independently recalculates the optimum for N <= 12 (memoised recursion over
  frozensets of tensor names; no reference-solver imports).
- UNKNOWN (BOUND_NOT_MET) needs, for N > 12, a witness showing that the product of
  the open-leg dimensions exceeds size_bound or cost_bound; for N <= 12 either such
  a witness or the recomputed optimum must show infeasibility.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Set, Tuple

from .schema_guard import validate_certificate

DP_LIMIT = 12


def _independent_optimum(
    tensors: Dict[str, List[str]], dims: Dict[str, int], size_bound: int | None
) -> int | None:
    """Memoised recursion over frozensets of tensor names (no bit masks, no shared code)."""
    names = tuple(sorted(tensors))
    if len(names) == 1:
        return 0

    @lru_cache(maxsize=None)
    def legs(group: frozenset[str]) -> frozenset[str]:
        seen: Dict[str, int] = {}
        for name in group:
            for index in tensors[name]:
                seen[index] = seen.get(index, 0) + 1
        return frozenset(index for index, count in seen.items() if count == 1)

    def size(indices: frozenset[str]) -> int:
        out = 1
        for index in sorted(indices):
            out *= dims[index]
        return out

    @lru_cache(maxsize=None)
    def cost(group: frozenset[str]) -> int | None:
        if len(group) == 1:
            return 0
        if size_bound is not None and size(legs(group)) > size_bound:
            return None
        members = sorted(group)
        anchor, others = members[0], members[1:]
        best: int | None = None
        for pick in range(1 << len(others)):
            left = frozenset([anchor] + [others[i] for i in range(len(others)) if pick >> i & 1])
            right = group - left
            if not right:
                continue
            lc, rc = cost(left), cost(right)
            if lc is None or rc is None:
                continue
            total = lc + rc + size(legs(left) | legs(right))
            if best is None or total < best:
                best = total
        return best

    return cost(frozenset(names))


def _open_leg_product(tensors: Dict[str, List[str]], dims: Dict[str, int]) -> int:
    counts: Dict[str, int] = {}
    for indices in tensors.values():
        for index in indices:
            counts[index] = counts.get(index, 0) + 1
    product = 1
    for index, count in counts.items():
        if count == 1:
            product *= dims[index]
    return product


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
    raise ValueError("invalid bound")


def _validate_network_independent(tensors: Any, dims: Any) -> tuple[bool, dict[str, Any] | None]:
    if not isinstance(tensors, dict) or not isinstance(dims, dict):
        return False, {
            "kind": "malformed_network",
            "details": "tensors and dims must be JSON objects",
        }
    if not 1 <= len(tensors) <= 30:
        return False, {
            "kind": "out_of_bounds",
            "details": f"Tensor count {len(tensors)} must be in [1, 30]",
        }

    index_tensors: Dict[str, List[str]] = {}
    for tensor_name, indices in tensors.items():
        if not isinstance(tensor_name, str) or not tensor_name or tensor_name.startswith("@step:"):
            return False, {
                "kind": "malformed_network",
                "details": "tensor names must be nonempty strings outside the reserved @step: namespace",
            }
        if not isinstance(indices, list) or any(
            not isinstance(index, str) or not index for index in indices
        ):
            return False, {
                "kind": "malformed_network",
                "tensor": tensor_name,
                "details": "tensor indices must be nonempty strings in a JSON array",
            }
        seen: Set[str] = set()
        for index in indices:
            if index in seen:
                return False, {
                    "kind": "duplicate_index_in_tensor",
                    "tensor": tensor_name,
                    "index": index,
                }
            seen.add(index)
            index_tensors.setdefault(index, []).append(tensor_name)

    if any(not isinstance(index, str) or not index for index in dims):
        return False, {
            "kind": "malformed_network",
            "details": "dimension keys must be nonempty strings",
        }
    unused = sorted(set(dims) - set(index_tensors))
    if unused:
        return False, {"kind": "dimension_mismatch", "unused_indices": unused}

    for index, owners in index_tensors.items():
        if index not in dims:
            return False, {
                "kind": "dimension_mismatch",
                "details": f"Index '{index}' not found in dims dictionary",
            }
        dimension = dims[index]
        if type(dimension) is not int or not 2 <= dimension <= 64:
            return False, {
                "kind": "dimension_mismatch",
                "index": index,
                "dim": dimension,
                "details": f"Dimension of '{index}' must be an integer in [2, 64], got {dimension}",
            }
        if len(owners) > 2:
            return False, {
                "kind": "hyperedge",
                "index": index,
                "tensors": sorted(owners),
            }
    return True, None


def verify_independent(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes independent verification of C030 candidate answer.
    """
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}

    status = answer.get("status")
    tensors: Dict[str, List[str]] = case.get("tensors", {})
    dims: Dict[str, int] = case.get("dims", {})
    cost_bound_raw = case.get("cost_bound")
    size_bound_raw = case.get("size_bound")
    try:
        cost_bound = _parse_bound(cost_bound_raw, 0)
    except ValueError:
        expected = {"kind": "invalid_cost_bound", "actual_type": type(cost_bound_raw).__name__}
        return (
            (status == "OUT_OF_SCOPE" and answer.get("witness") == expected),
            "Invalid cost bound checked",
            {},
        )
    try:
        size_bound = _parse_bound(size_bound_raw, 1)
    except ValueError:
        expected = {"kind": "invalid_size_bound", "actual_type": type(size_bound_raw).__name__}
        return (
            (status == "OUT_OF_SCOPE" and answer.get("witness") == expected),
            "Invalid size bound checked",
            {},
        )

    network_ok, topo_witness = _validate_network_independent(tensors, dims)
    if not network_ok:
        assert topo_witness is not None
        if status == "OUT_OF_SCOPE":
            wit = answer.get("witness", {})
            if wit == topo_witness:
                return True, "Independent topology check confirmed OUT_OF_SCOPE", {}
            return False, f"Topology mismatch: expected {topo_witness}, got {wit}", {}
        return (
            False,
            f"Case has topology error ({topo_witness.get('kind')}), must be OUT_OF_SCOPE",
            {},
        )

    if status == "OUT_OF_SCOPE":
        return False, "Case has no topology errors, cannot be OUT_OF_SCOPE", {}

    n = len(tensors)

    if status == "UNKNOWN":
        if answer.get("refusal_code") != "BOUND_NOT_MET":
            return False, "Invalid refusal code for UNKNOWN", {}
        witness = answer.get("witness")
        if witness is not None:
            if not isinstance(witness, dict) or sorted(witness) != ["kind", "open_size"]:
                return False, "Independent check: malformed UNKNOWN witness", {}
            product = _open_leg_product(tensors, dims)
            if witness["open_size"] != str(product):
                return False, "Independent check: witness open_size is not the open-leg product", {}
            if (
                witness["kind"] == "open_legs_exceed_size_bound"
                and size_bound is not None
                and product > size_bound
            ):
                return True, "Independent check confirmed size-bound infeasibility", {}
            if (
                witness["kind"] == "open_legs_exceed_cost_bound"
                and cost_bound is not None
                and product > cost_bound
            ):
                return True, "Independent check confirmed cost-bound infeasibility", {}
            return False, "Independent check: witness does not prove infeasibility", {}
        if n > DP_LIMIT:
            return False, "Independent check: UNKNOWN for N > 12 needs an infeasibility witness", {}
        optimum = _independent_optimum(tensors, dims, size_bound)
        if optimum is not None and (cost_bound is None or optimum <= cost_bound):
            return False, f"Independent DP found feasible cost {optimum} <= {cost_bound}", {}
        return True, "Independent check confirmed UNKNOWN", {}

    if status != "SOLVED":
        return False, f"Unexpected status {status}", {}

    order = answer.get("order", [])
    if len(order) != n - 1:
        return False, f"Expected {n - 1} steps, got {len(order)}", {}

    # Forest mapping: tensor_id -> set of active indices
    forest: Dict[str, Set[str]] = {name: set(idxs) for name, idxs in tensors.items()}
    index_counts: Dict[str, int] = {}
    for indices in tensors.values():
        for index in indices:
            index_counts[index] = index_counts.get(index, 0) + 1
    expected_open = {index for index, count in index_counts.items() if count == 1}
    total_cost = 0
    max_size = 0

    for step_num, pair in enumerate(order):
        if len(pair) != 2:
            return False, f"Step {step_num} is not a 2-element pair", {}
        t1, t2 = pair[0], pair[1]
        if t1 not in forest or t2 not in forest:
            return False, f"Step {step_num}: '{t1}' or '{t2}' not in active forest", {}
        if t1 == t2:
            return False, f"Step {step_num}: self-contraction of '{t1}'", {}

        i1 = forest.pop(t1)
        i2 = forest.pop(t2)

        # Step cost
        step_cost = 1
        for e in i1 | i2:
            step_cost *= dims[e]
        total_cost += step_cost

        # Intermediate size
        out_indices = i1 ^ i2
        step_size = 1
        for e in out_indices:
            step_size *= dims[e]

        if step_size > max_size:
            max_size = step_size

        if size_bound is not None and step_size > size_bound:
            return False, f"Intermediate size {step_size} exceeded size bound {size_bound}", {}

        forest[f"@step:{step_num}"] = out_indices

    if len(forest) != 1 or next(iter(forest.values())) != expected_open:
        return False, "Final tensor does not have the expected open indices", {}

    stated_raw = answer.get("total_cost")
    if type(stated_raw) is not str or stated_raw != str(total_cost):
        return False, f"Stated cost {stated_raw!r} != replayed {total_cost}", {}

    if cost_bound is not None and total_cost > cost_bound:
        return False, f"Total cost {total_cost} > cost bound {cost_bound}", {}

    if answer.get("optimal") is True:
        if n > 12:
            return False, "Optimal claim not permitted for N > 12", {}
        opt_cost = _independent_optimum(tensors, dims, size_bound)
        if opt_cost is None or total_cost != opt_cost:
            return False, f"Optimal claim false: replayed {total_cost} != optimal {opt_cost}", {}

    return (
        True,
        "Independent contraction sequence verified",
        {
            "replayed_cost": total_cost,
            "max_size": max_size,
        },
    )
