# AuthorityEffect: None.
"""
Tensor network validation, contraction math, and replay simulator for C030.

Definitions:
- Input: up to 30 tensors; each tensor has a list of index names.
- Each index has an integer dimension in [2, 64].
- Every index appears in exactly 1 tensor (open) or 2 tensors (bond).
- Hyperedges (degree >= 3) are not allowed (typed refusal OUT_OF_SCOPE).
- Step cost: prod_{e in I union J} dim(e).
- Resulting indices: I symmetric_difference J.
- Intermediate size: prod_{e in I symmetric_difference J} dim(e).
- All arithmetic in exact arbitrary-precision integers (Python int).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


def validate_network(
    tensors: Dict[str, List[str]],
    dims: Dict[str, int],
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validates tensor network structure.
    Checks:
    - Index dimensions exist and are integers >= 2.
    - No hyperedges (each index appears in at most 2 tensors).
    - Tensor count <= 30.
    Returns:
        (is_valid, refusal_witness)
    """
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

    # Count index occurrences
    index_tensors: Dict[str, List[str]] = {}
    for t_name, idx_list in tensors.items():
        if not isinstance(t_name, str) or not t_name or t_name.startswith("@step:"):
            return False, {
                "kind": "malformed_network",
                "details": "tensor names must be nonempty strings outside the reserved @step: namespace",
            }
        if not isinstance(idx_list, list) or any(
            not isinstance(idx, str) or not idx for idx in idx_list
        ):
            return False, {
                "kind": "malformed_network",
                "tensor": t_name,
                "details": "tensor indices must be nonempty strings in a JSON array",
            }
        seen_in_t: Set[str] = set()
        for idx in idx_list:
            if idx in seen_in_t:
                return False, {
                    "kind": "duplicate_index_in_tensor",
                    "tensor": t_name,
                    "index": idx,
                }
            seen_in_t.add(idx)
            index_tensors.setdefault(idx, []).append(t_name)

    if any(not isinstance(idx, str) or not idx for idx in dims):
        return False, {
            "kind": "malformed_network",
            "details": "dimension keys must be nonempty strings",
        }

    unused_dims = sorted(set(dims) - set(index_tensors))
    if unused_dims:
        return False, {
            "kind": "dimension_mismatch",
            "unused_indices": unused_dims,
        }

    # Check dimensions and hyperedges.
    for idx, t_list in index_tensors.items():
        if idx not in dims:
            return False, {
                "kind": "dimension_mismatch",
                "details": f"Index '{idx}' not found in dims dictionary",
            }
        dim = dims[idx]
        if isinstance(dim, bool) or not isinstance(dim, int) or not 2 <= dim <= 64:
            return False, {
                "kind": "dimension_mismatch",
                "index": idx,
                "dim": dim,
                "details": f"Dimension of '{idx}' must be an integer in [2, 64], got {dim}",
            }
        if len(t_list) > 2:
            return False, {
                "kind": "hyperedge",
                "index": idx,
                "tensors": sorted(t_list),
            }

    return True, None


def compute_step_cost_and_size(
    indices_a: Set[str],
    indices_b: Set[str],
    dims: Dict[str, int],
) -> Tuple[int, int, Set[str]]:
    """
    Computes exact integer cost, resulting intermediate size, and resulting indices
    for contracting tensor A with tensor B.
    Cost = prod_{e in I union J} dim(e)
    Resulting indices = I Delta J
    Size = prod_{e in I Delta J} dim(e)
    """
    union_idx = indices_a | indices_b
    sym_diff_idx = indices_a ^ indices_b

    cost = 1
    for idx in union_idx:
        cost *= dims[idx]

    size = 1
    for idx in sym_diff_idx:
        size *= dims[idx]

    return cost, size, sym_diff_idx


def replay_contraction_order(
    tensors: Dict[str, List[str]],
    dims: Dict[str, int],
    order: List[List[str]],
    cost_bound: Optional[int] = None,
    size_bound: Optional[int] = None,
) -> Tuple[bool, int, int, str]:
    """
    Replays a pairwise contraction order and computes total exact cost and max intermediate size.
    Validates:
    - Order has exactly n - 1 steps.
    - Each step names two currently live tensors.
    - Output tensor names use the reserved collision-free ``@step:N`` namespace.
    - Exactly 1 tensor remains, with open indices matching theoretical open indices.
    - Total cost <= cost_bound (if given).
    - Every intermediate tensor size <= size_bound (if given).
    Returns:
        (is_valid, total_cost, max_size, message)
    """
    n = len(tensors)
    if n == 0:
        return False, 0, 0, "Empty tensor network is outside the admitted domain"
    if n == 1:
        if len(order) == 0:
            return True, 0, 0, "Single tensor, 0 contractions"
        return False, 0, 0, "Single tensor must have empty order"

    if len(order) != n - 1:
        return False, 0, 0, f"Expected {n - 1} contraction steps, got {len(order)}"

    # Determine open indices
    all_indices: Dict[str, int] = {}
    for idx_list in tensors.values():
        for idx in idx_list:
            all_indices[idx] = all_indices.get(idx, 0) + 1
    expected_open = {idx for idx, count in all_indices.items() if count == 1}

    # Live tensors: name -> Set[str] of active indices
    live_tensors: Dict[str, Set[str]] = {name: set(indices) for name, indices in tensors.items()}

    total_cost = 0
    max_size = 0

    for step_idx, step in enumerate(order):
        if not isinstance(step, (list, tuple)) or len(step) != 2:
            return False, 0, 0, f"Step {step_idx} must be a pair of tensor names, got {step}"

        t1, t2 = step[0], step[1]
        if t1 not in live_tensors:
            return False, 0, 0, f"Step {step_idx}: Tensor '{t1}' is not currently live"
        if t2 not in live_tensors:
            return False, 0, 0, f"Step {step_idx}: Tensor '{t2}' is not currently live"
        if t1 == t2:
            return False, 0, 0, f"Step {step_idx}: Cannot contract tensor '{t1}' with itself"

        idx1 = live_tensors.pop(t1)
        idx2 = live_tensors.pop(t2)

        step_cost, step_size, new_idx = compute_step_cost_and_size(idx1, idx2, dims)
        total_cost += step_cost
        if step_size > max_size:
            max_size = step_size

        if size_bound is not None and step_size > size_bound:
            return (
                False,
                total_cost,
                max_size,
                (f"Step {step_idx} intermediate size {step_size} exceeds size_bound {size_bound}"),
            )

        new_name = f"@step:{step_idx}"
        if new_name in live_tensors:
            return False, total_cost, max_size, f"Internal tensor identifier collision: {new_name}"
        live_tensors[new_name] = new_idx

    if len(live_tensors) != 1:
        return False, total_cost, max_size, f"Expected 1 remaining tensor, got {len(live_tensors)}"

    final_name, final_indices = next(iter(live_tensors.items()))
    if final_indices != expected_open:
        return (
            False,
            total_cost,
            max_size,
            (
                f"Final tensor indices {final_indices} do not match expected open indices {expected_open}"
            ),
        )

    if cost_bound is not None and total_cost > cost_bound:
        return (
            False,
            total_cost,
            max_size,
            (f"Total cost {total_cost} exceeds cost_bound {cost_bound}"),
        )

    return True, total_cost, max_size, "Contraction sequence valid"
