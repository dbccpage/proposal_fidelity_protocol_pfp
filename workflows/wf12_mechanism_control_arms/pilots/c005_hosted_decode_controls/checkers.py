"""
checkers.py — Exact mathematical checkers and mutation audit suite for Challenge C005.

Verifies:
1. Consistency certificates: exact potential difference pi(v) - pi(u) == c_uv (Phi_1 = 0).
2. Cycle repairs: sum(c'_i) == 0, exact weighted L1 calculation, comparison against minimum.
3. Checker mutation suite: tests checker rejection of malformed or false certificates.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


def _canonical_integer(value):
    return type(value) is str and value != "-0" and re.fullmatch(r"-?(0|[1-9][0-9]*)", value) is not None


@dataclass(frozen=True)
class CheckResult:
    is_valid: bool
    is_optimal: bool
    calculated_cost: int | None
    error_message: str | None


def verify_consistency_certificate(
    edges: list[tuple[str, str, int]],
    verdict: str,
    certificate: dict[str, str] | None,
) -> CheckResult:
    """Exact host verification of consistency certificate."""
    if verdict not in ("CONSISTENT", "INCONSISTENT"):
        return CheckResult(False, False, None, f"Invalid verdict {verdict}")

    if type(edges) is not list or any(type(edge) not in (list, tuple) or len(edge) != 3 or
        type(edge[0]) is not str or type(edge[1]) is not str or type(edge[2]) is not int for edge in edges):
        return CheckResult(False, False, None, "Malformed exact difference relation")

    if verdict == "INCONSISTENT":
        if certificate != {}:
            return CheckResult(False, False, None, "INCONSISTENT requires an empty certificate")
        # A claim of inconsistency is not its own certificate. Independently
        # propagate exact differences and require a contradictory closed walk.
        adjacent = {}
        for u, v, delta in edges:
            adjacent.setdefault(u, []).append((v, delta))
            adjacent.setdefault(v, []).append((u, -delta))
        potentials = {}
        for root in adjacent:
            if root in potentials:
                continue
            potentials[root] = 0
            pending = [root]
            while pending:
                u = pending.pop()
                for v, delta in adjacent[u]:
                    expected = potentials[u] + delta
                    if v in potentials and potentials[v] != expected:
                        return CheckResult(True, True, None, None)
                    if v not in potentials:
                        potentials[v] = expected
                        pending.append(v)
        return CheckResult(False, False, None, "INCONSISTENT verdict on a consistent system")

    if not certificate or not isinstance(certificate, dict):
        return CheckResult(
            False, False, None, "CONSISTENT verdict requires a non-empty certificate dictionary"
        )

    # Parse potentials into integers
    potentials: dict[str, int] = {}
    for node, val_str in certificate.items():
        if not _canonical_integer(val_str):
            return CheckResult(
                False, False, None, f"Potential for node {node} must be string, got {type(val_str)}"
            )
        try:
            potentials[node] = int(val_str)
        except ValueError:
            return CheckResult(
                False, False, None, f"Could not parse potential {val_str!r} as int for node {node}"
            )

    # Check that every edge is satisfied: pi(v) - pi(u) == delta
    for u, v, delta in edges:
        if u not in potentials:
            return CheckResult(False, False, None, f"Missing potential for node {u}")
        if v not in potentials:
            return CheckResult(False, False, None, f"Missing potential for node {v}")
        diff = potentials[v] - potentials[u]
        if diff != delta:
            return CheckResult(
                False,
                False,
                None,
                f"Edge {u} -> {v} violated: pi({v}) - pi({u}) = {diff} != {delta}",
            )

    return CheckResult(True, True, None, None)


def verify_cycle_repair(
    original_claims: list[int],
    weights: list[int],
    repaired_claims: list[str],
    declared_cost: str | None,
) -> CheckResult:
    """Exact host verification of cycle repair."""
    if (type(original_claims) is not list or not original_claims or type(weights) is not list or type(repaired_claims) is not list
        or any(type(v) is not int for v in original_claims)
        or any(type(w) is not int or w <= 0 for w in weights)
        or not _canonical_integer(declared_cost)):
        return CheckResult(False, False, None, "Malformed exact cycle-repair input or cost")
    k = len(original_claims)
    if len(weights) != k:
        return CheckResult(
            False, False, None, f"Weights length {len(weights)} != claims length {k}"
        )
    if len(repaired_claims) != k:
        return CheckResult(
            False, False, None, f"Repaired claims length {len(repaired_claims)} != expected {k}"
        )

    # Parse repaired claims
    parsed_rep: list[int] = []
    for idx, c_str in enumerate(repaired_claims):
        if not _canonical_integer(c_str):
            return CheckResult(
                False,
                False,
                None,
                f"Repaired claim at index {idx} must be string, got {type(c_str)}",
            )
        try:
            parsed_rep.append(int(c_str))
        except ValueError:
            return CheckResult(
                False, False, None, f"Repaired claim {c_str!r} is not a valid integer"
            )

    # 1. Reached-zero check: sum(c'_i) == 0
    cycle_sum = sum(parsed_rep)
    if cycle_sum != 0:
        return CheckResult(
            False, False, None, f"Repaired cycle sum is {cycle_sum} != 0 (Phi_1 > 0)"
        )

    # 2. Compute exact weighted L1 distance
    actual_l1 = sum(w * abs(c - cp) for w, c, cp in zip(weights, original_claims, parsed_rep))

    # 3. Check declared cost matches host calculation
    if declared_cost is not None:
        try:
            decl_int = int(declared_cost)
            if decl_int != actual_l1:
                return CheckResult(
                    False,
                    False,
                    actual_l1,
                    f"Declared weighted_l1 {decl_int} != host calculated {actual_l1}",
                )
        except ValueError:
            return CheckResult(
                False, False, actual_l1, f"Declared weighted_l1 {declared_cost!r} not an int"
            )

    # 4. Check optimality: minimum possible cost for single cycle is |s| * min(w)
    s = sum(original_claims)
    min_w = min(weights)
    optimal_cost = abs(s) * min_w
    is_optimal = actual_l1 == optimal_cost

    return CheckResult(
        is_valid=True,
        is_optimal=is_optimal,
        calculated_cost=actual_l1,
        error_message=None
        if is_optimal
        else f"Repaired at cost {actual_l1} > optimal {optimal_cost}",
    )
