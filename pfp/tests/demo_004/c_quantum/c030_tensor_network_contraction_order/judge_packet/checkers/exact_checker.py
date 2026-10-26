# AuthorityEffect: None.
"""
Exact Checker for C030: Tensor-Network Contraction Order Under a Cost Bound.

Self-contained: no reference-solver imports. Verifies:
1. Schema conformity and status in {SOLVED, UNKNOWN, OUT_OF_SCOPE}.
2. SOLVED: full pairwise replay in exact integers; stated total_cost equals the
   replayed cost; cost <= cost_bound; every intermediate (including the final
   tensor) has size <= size_bound; an "optimal": true claim needs N <= 12 and the
   replayed cost must equal the exact subset-DP optimum.
3. UNKNOWN (refusal_code BOUND_NOT_MET) is accepted only with a verified reason:
   - N <= 12: the exact subset DP shows that no order meets the bounds (an
     optional witness, if present, must also be valid);
   - N > 12: a witness is required. Every order ends with a step whose output is
     the tensor of all open legs and whose cost includes every open leg, so
       {"kind": "open_legs_exceed_size_bound", "open_size": "<P>"} proves
       infeasibility when P > size_bound, and
       {"kind": "open_legs_exceed_cost_bound", "open_size": "<P>"} proves it when
       P > cost_bound,
     where P is the product of the dimensions of the open indices.
4. OUT_OF_SCOPE: the witness must equal the topology defect this checker finds.
"""

from __future__ import annotations

from typing import Any

from .schema_guard import validate_certificate

EXACT_DP_LIMIT = 12
MAX_TENSORS = 30
WITNESS_KINDS = ("open_legs_exceed_size_bound", "open_legs_exceed_cost_bound")


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


def _canonical_int(value: Any) -> int | None:
    if (
        type(value) is str
        and value.isascii()
        and value.isdigit()
        and (value == "0" or not value.startswith("0"))
    ):
        return int(value)
    return None


def _network_defect(tensors: Any, dims: Any) -> dict[str, Any] | None:
    if not isinstance(tensors, dict) or not isinstance(dims, dict):
        return {"kind": "malformed_network", "details": "tensors and dims must be JSON objects"}
    if not 1 <= len(tensors) <= MAX_TENSORS:
        return {
            "kind": "out_of_bounds",
            "details": f"Tensor count {len(tensors)} must be in [1, 30]",
        }
    owners: dict[str, list[str]] = {}
    for name, indices in tensors.items():
        if not isinstance(name, str) or not name or name.startswith("@step:"):
            return {
                "kind": "malformed_network",
                "details": "tensor names must be nonempty strings outside the reserved @step: namespace",
            }
        if not isinstance(indices, list) or any(not isinstance(i, str) or not i for i in indices):
            return {
                "kind": "malformed_network",
                "tensor": name,
                "details": "tensor indices must be nonempty strings in a JSON array",
            }
        seen: set[str] = set()
        for index in indices:
            if index in seen:
                return {"kind": "duplicate_index_in_tensor", "tensor": name, "index": index}
            seen.add(index)
            owners.setdefault(index, []).append(name)
    if any(not isinstance(i, str) or not i for i in dims):
        return {"kind": "malformed_network", "details": "dimension keys must be nonempty strings"}
    unused = sorted(set(dims) - set(owners))
    if unused:
        return {"kind": "dimension_mismatch", "unused_indices": unused}
    for index, names in owners.items():
        if index not in dims:
            return {
                "kind": "dimension_mismatch",
                "details": f"Index '{index}' not found in dims dictionary",
            }
        dim = dims[index]
        if type(dim) is not int or not 2 <= dim <= 64:
            return {
                "kind": "dimension_mismatch",
                "index": index,
                "dim": dim,
                "details": f"Dimension of '{index}' must be an integer in [2, 64], got {dim}",
            }
        if len(names) > 2:
            return {"kind": "hyperedge", "index": index, "tensors": sorted(names)}
    return None


def _open_indices(tensors: dict[str, list[str]]) -> set[str]:
    counts: dict[str, int] = {}
    for indices in tensors.values():
        for index in indices:
            counts[index] = counts.get(index, 0) + 1
    return {index for index, count in counts.items() if count == 1}


def _product(indices: set[str], dims: dict[str, int]) -> int:
    out = 1
    for index in indices:
        out *= dims[index]
    return out


def _replay(
    tensors: dict[str, list[str]], dims: dict[str, int], order: Any, size_bound: int | None
) -> tuple[bool, int, str]:
    n = len(tensors)
    if not isinstance(order, list) or len(order) != n - 1:
        return False, 0, f"order must list exactly {n - 1} contraction steps"
    live: dict[str, set[str]] = {name: set(indices) for name, indices in tensors.items()}
    total = 0
    for step_no, step in enumerate(order):
        if not isinstance(step, list) or len(step) != 2 or not all(type(x) is str for x in step):
            return False, total, f"step {step_no} must be a pair of tensor names"
        a, b = step
        if a == b or a not in live or b not in live:
            return (
                False,
                total,
                f"step {step_no}: {a!r} and {b!r} must be two distinct live tensors",
            )
        ia, ib = live.pop(a), live.pop(b)
        total += _product(ia | ib, dims)
        out = ia ^ ib
        if size_bound is not None and _product(out, dims) > size_bound:
            return False, total, f"step {step_no} intermediate size exceeds size_bound {size_bound}"
        live[f"@step:{step_no}"] = out
    if len(live) != 1 or next(iter(live.values())) != _open_indices(tensors):
        return False, total, "final tensor does not carry exactly the open indices"
    return True, total, "replayed"


def _dp_optimum(
    tensors: dict[str, list[str]], dims: dict[str, int], size_bound: int | None
) -> int | None:
    """Exact minimum total cost over all contraction trees; None when no tree meets size_bound."""
    names = sorted(tensors)
    n = len(names)
    if n == 1:
        return 0
    legs = [set(tensors[name]) for name in names]
    full = (1 << n) - 1
    open_legs: list[set[str]] = [set() for _ in range(full + 1)]
    for mask in range(1, full + 1):
        low = mask & -mask
        open_legs[mask] = open_legs[mask ^ low] ^ legs[low.bit_length() - 1]
    best: list[int | None] = [None] * (full + 1)
    for i in range(n):
        best[1 << i] = 0
    for mask in range(1, full + 1):
        if mask & (mask - 1) == 0:
            continue
        if size_bound is not None and _product(open_legs[mask], dims) > size_bound:
            continue
        low = mask & -mask
        rest = mask ^ low
        sub = rest
        candidate: int | None = None
        while True:
            left = sub | low
            right = mask ^ left
            if right and best[left] is not None and best[right] is not None:
                cost = best[left] + best[right] + _product(open_legs[left] | open_legs[right], dims)
                if candidate is None or cost < candidate:
                    candidate = cost
            if sub == 0:
                break
            sub = (sub - 1) & rest
        best[mask] = candidate
    return best[full]


def _check_unknown_witness(
    witness: Any,
    tensors: dict[str, list[str]],
    dims: dict[str, int],
    cost_bound: int | None,
    size_bound: int | None,
) -> tuple[bool, str]:
    if not isinstance(witness, dict) or set(witness) != {"kind", "open_size"}:
        return False, "UNKNOWN witness must be {'kind', 'open_size'}"
    kind = witness["kind"]
    claimed = _canonical_int(witness["open_size"])
    actual = _product(_open_indices(tensors), dims)
    if kind not in WITNESS_KINDS:
        return False, f"unknown UNKNOWN witness kind {kind!r}"
    if claimed != actual:
        return (
            False,
            f"witness open_size {witness['open_size']!r} != product of open-leg dimensions {actual}",
        )
    if kind == "open_legs_exceed_size_bound":
        if size_bound is None or actual <= size_bound:
            return False, f"open-leg size {actual} does not exceed size_bound {size_bound}"
        return True, "final tensor necessarily exceeds size_bound"
    if cost_bound is None or actual <= cost_bound:
        return False, f"open-leg size {actual} does not exceed cost_bound {cost_bound}"
    return True, "final contraction step necessarily exceeds cost_bound"


def verify_exact(case: dict[str, Any], answer: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """Executes exact verification of a C030 candidate answer."""
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}

    status = answer.get("status")
    tensors = case.get("tensors", {})
    dims = case.get("dims", {})
    cost_bound_raw = case.get("cost_bound")
    size_bound_raw = case.get("size_bound")
    try:
        cost_bound = _parse_bound(cost_bound_raw, 0)
    except ValueError:
        expected = {"kind": "invalid_cost_bound", "actual_type": type(cost_bound_raw).__name__}
        if status == "OUT_OF_SCOPE" and answer.get("witness") == expected:
            return True, "Invalid cost bound witness verified", {"witness": expected}
        return False, "Invalid cost bound requires its exact OUT_OF_SCOPE witness", {}
    try:
        size_bound = _parse_bound(size_bound_raw, 1)
    except ValueError:
        expected = {"kind": "invalid_size_bound", "actual_type": type(size_bound_raw).__name__}
        if status == "OUT_OF_SCOPE" and answer.get("witness") == expected:
            return True, "Invalid size bound witness verified", {"witness": expected}
        return False, "Invalid size bound requires its exact OUT_OF_SCOPE witness", {}

    defect = _network_defect(tensors, dims)
    if status == "OUT_OF_SCOPE":
        if defect is None:
            return False, "Case is valid, cannot refuse as OUT_OF_SCOPE", {}
        if answer.get("witness") != defect:
            return (
                False,
                f"Witness mismatch: expected {defect}, got {answer.get('witness')}",
                {"expected": defect},
            )
        return True, "OUT_OF_SCOPE refusal witness verified", {"witness": defect}
    if defect is not None:
        return (
            False,
            f"Case is invalid ({defect.get('kind')}), must return OUT_OF_SCOPE",
            {"witness": defect},
        )

    n = len(tensors)
    if status == "UNKNOWN":
        if answer.get("refusal_code") != "BOUND_NOT_MET":
            return False, f"Unknown refusal code: {answer.get('refusal_code')!r}", {}
        if "witness" in answer:
            ok, msg = _check_unknown_witness(
                answer["witness"], tensors, dims, cost_bound, size_bound
            )
            if not ok:
                return False, f"UNKNOWN witness rejected: {msg}", {}
            return True, f"UNKNOWN verified: {msg}", {}
        if n > EXACT_DP_LIMIT:
            return (
                False,
                f"UNKNOWN for N = {n} > {EXACT_DP_LIMIT} requires a verifiable infeasibility witness",
                {},
            )
        optimum = _dp_optimum(tensors, dims, size_bound)
        if optimum is not None and (cost_bound is None or optimum <= cost_bound):
            return (
                False,
                f"Case is feasible with optimal cost {optimum} <= {cost_bound}, cannot refuse as UNKNOWN",
                {"opt_cost": optimum},
            )
        return True, "UNKNOWN verified by exact subset DP", {}

    stated = _canonical_int(answer.get("total_cost"))
    if stated is None:
        return False, "SOLVED answer needs a canonical total_cost string", {}
    ok, replayed, msg = _replay(tensors, dims, answer.get("order"), size_bound)
    if not ok:
        return False, f"Contraction replay failed: {msg}", {"replayed_cost": replayed}
    if stated != replayed:
        return (
            False,
            f"Stated cost {stated} does not match replayed cost {replayed}",
            {"replayed_cost": replayed},
        )
    if cost_bound is not None and replayed > cost_bound:
        return (
            False,
            f"Replayed cost {replayed} exceeds cost_bound {cost_bound}",
            {"replayed_cost": replayed},
        )
    optimal = answer.get("optimal")
    if type(optimal) is not bool:
        return False, "optimal must be a JSON boolean", {}
    if optimal:
        if n > EXACT_DP_LIMIT:
            return False, f"Optimality claims forbidden for N > {EXACT_DP_LIMIT} (N={n})", {"n": n}
        optimum = _dp_optimum(tensors, dims, size_bound)
        if optimum is None or replayed != optimum:
            return (
                False,
                f"Suboptimal order claimed as optimal: replayed {replayed} != optimal {optimum}",
                {},
            )
    return (
        True,
        "Contraction sequence verified and within declared bounds",
        {
            "total_cost": replayed,
            "optimal": optimal,
        },
    )
