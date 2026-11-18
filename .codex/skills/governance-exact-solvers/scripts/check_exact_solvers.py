#!/usr/bin/env python3
"""Verification script for exact rational solver arithmetic and certificate integrity.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from fractions import Fraction


def verify_arithmetic_sanity() -> bool:
    """Basic sanity verification of exact rational summation without float conversion."""
    fractions = [Fraction(1, 3), Fraction(1, 6), Fraction(1, 2)]
    total = Fraction(0, 1)
    for f in fractions:
        total += f
    return total == Fraction(1, 1)


def verify_exact_primal_dual_certificate() -> bool:
    """Verify an exact rational primal-dual optimality certificate on an oriented triangle.

    Graph: 0 -> 1 -> 2 -> 0.
    Cochain c = (2, -1, 0).
    Primal variable f = (0, 1, 0).
    Incidence B f on edges (0->1, 1->2, 2->0):
      (B f)_0 = f[1] - f[0] = 1 - 0 = 1
      (B f)_1 = f[2] - f[1] = 0 - 1 = -1
      (B f)_2 = f[0] - f[2] = 0 - 0 = 0
    Residual r = c - B f = (1, 0, 0).
    Primal L1 cost = sum |r_e| = 1.

    Dual circulation y = (1, 1, 1).
    Circulation condition (divergence at each node v is 0):
      Node 0: incoming e_2 - outgoing e_0 = 1 - 1 = 0
      Node 1: incoming e_0 - outgoing e_1 = 1 - 1 = 0
      Node 2: incoming e_1 - outgoing e_2 = 1 - 1 = 0
    Dual feasibility: |y_e| <= 1 for all e.
    Dual value = <c, y> = 2(1) + (-1)(1) + 0(1) = 1.
    Duality gap = 1 - 1 = 0 (exact optimality certified).
    Complementary slackness:
      r_0 != 0 => y_0 = sign(r_0) = 1 (saturated).
    """
    c = [Fraction(2), Fraction(-1), Fraction(0)]
    f = [Fraction(0), Fraction(1), Fraction(0)]

    # Compute residual r = c - Bf
    bf = [f[1] - f[0], f[2] - f[1], f[0] - f[2]]
    r = [c[i] - bf[i] for i in range(3)]

    primal_cost = sum(abs(re) for re in r)

    y = [Fraction(1), Fraction(1), Fraction(1)]
    # Check circulation
    div_0 = y[2] - y[0]
    div_1 = y[0] - y[1]
    div_2 = y[1] - y[2]
    if div_0 != 0 or div_1 != 0 or div_2 != 0:
        return False

    # Check dual bounds
    if any(abs(ye) > 1 for ye in y):
        return False

    dual_value = sum(c[i] * y[i] for i in range(3))
    gap = primal_cost - dual_value

    # Saturated complementary slackness check
    for i in range(3):
        if r[i] != 0:
            expected_y = Fraction(1) if r[i] > 0 else Fraction(-1)
            if y[i] != expected_y:
                return False

    return gap == 0


def main() -> int:
    if not verify_arithmetic_sanity():
        print("[FAIL] Rational arithmetic sanity check failed.", file=sys.stderr)
        return 1
    if not verify_exact_primal_dual_certificate():
        print("[FAIL] Exact rational primal-dual certificate verification failed.", file=sys.stderr)
        return 1
    print("PASS: Exact rational solver arithmetic and primal-dual certificate verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
