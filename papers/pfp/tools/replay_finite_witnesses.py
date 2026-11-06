"""Exact arithmetic checks of displayed finite witnesses, not a native solver."""
import json
from fractions import Fraction as Q


def triangle_certificate(claims, weights, potential, flow):
    rows = (claims, weights, potential, flow)
    if any(len(row) != 3 for row in rows):
        return False
    if any(type(value) not in (int, Q) for row in rows for value in row):
        return False
    if any(weight <= 0 for weight in weights):
        return False
    gradient = (potential[1] - potential[0], potential[2] - potential[1], potential[0] - potential[2])
    residual = tuple(c - d for c, d in zip(claims, gradient))
    cost = sum(w * abs(r) for w, r in zip(weights, residual))
    balance = (-flow[0] + flow[2], flow[0] - flow[1], flow[1] - flow[2])
    return all(value == 0 for value in balance) and all(abs(y) <= w for y, w in zip(flow, weights)) and cost == sum(c * y for c, y in zip(claims, flow))


def main():
    if not __debug__:
        raise RuntimeError("Run this assertion-based replay without Python -O")
    claims, weights = (Q(1), Q(1), Q(1)), (Q(1), Q(2), Q(3))
    assert sum(weights) == 6
    assert triangle_certificate(claims, weights, (Q(0), Q(-2), Q(-1)), (Q(1),) * 3)
    # Equal displayed primal/dual objectives are insufficient without balance.
    assert not triangle_certificate((1, 0, 0), (1, 1, 1), (0, 0, 0), (1, 0, 0))
    # Zero objectives cannot excuse an over-capacity circulation.
    assert not triangle_certificate((0, 0, 0), weights, (0, 0, 0), (2, 2, 2))
    assert not triangle_certificate(claims, (0, 2, 3), (0, -2, -1), (1, 1, 1))
    assert not triangle_certificate(claims, weights, (0.0, -2, -1), (1, 1, 1))
    assert triangle_certificate((-2, 1, 1), weights, (0, -2, -1), (0, 0, 0))
    # A uniform four-cycle has multiple optimal residuals despite cycle rank one.
    tied = [(Q(4), Q(0), Q(0), Q(0)), (Q(0), Q(4), Q(0), Q(0)), (Q(1),) * 4]
    assert all(sum(r) == sum(abs(v) for v in r) == 4 for r in tied)
    costs = [Q(1, 2**t) for t in range(20)]
    assert all(a > b > 0 for a, b in zip(costs, costs[1:]))
    print(json.dumps({"status": "PASS", "triangle_initial_cost": "6", "triangle_optimum": "3", "dual_objective": "3", "invalid_witnesses_rejected": ["unbalanced_equal_objective", "over_capacity_equal_objective", "zero_weight", "floating_point_potential"], "tied_cycle_examples": len(tied), "positive_strict_descent_terms": len(costs), "scope": "Displayed finite arithmetic and certificate checks; no native runtime or convergence claim", "AuthorityEffect": "None"}, indent=2))


if __name__ == "__main__":
    main()
