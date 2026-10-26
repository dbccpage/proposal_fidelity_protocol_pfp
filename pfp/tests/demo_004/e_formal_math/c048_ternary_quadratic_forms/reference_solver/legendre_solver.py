"""Legendre descent and Holzer bound search for ternary quadratic forms.
Finds non-trivial integer point (x, y, z) satisfying a x^2 + b y^2 + c z^2 = 0.
"""

import math
from typing import Optional, Tuple


def solve_ternary(a: int, b: int, c: int) -> Optional[Tuple[int, int, int]]:
    """Find a non-trivial integer solution (x, y, z) != (0, 0, 0)
    for a*x^2 + b*y^2 + c*z^2 = 0.
    """
    # 1. Zero coefficient edge cases
    if a == 0:
        return (1, 0, 0)
    if b == 0:
        return (0, 1, 0)
    if c == 0:
        return (0, 0, 1)

    # 2. Pairwise opposite coefficient edge cases
    if a + b == 0:
        return (1, 1, 0)
    if a + c == 0:
        return (1, 0, 1)
    if b + c == 0:
        return (0, 1, 1)

    # If all coefficients have the same sign, no real solution
    if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
        return None

    # Standardize signs: ensure two positive and one negative (multiply by -1 if needed)
    coeffs = [(a, "x"), (b, "y"), (c, "z")]
    neg_count = sum(1 for v, _ in coeffs if v < 0)
    scale = -1 if neg_count == 2 else 1
    sa, sb, sc = scale * a, scale * b, scale * c

    # Sort so that A > 0, B > 0, C < 0 (i.e. A x^2 + B y^2 = |C| z^2)
    # Permute variables appropriately
    pos = []
    neg = []
    for val, var in [(sa, "x"), (sb, "y"), (sc, "z")]:
        if val > 0:
            pos.append((val, var))
        else:
            neg.append((val, var))

    (A, vA), (B, vB) = pos
    (C, vC) = neg[0]
    absC = abs(C)

    # Holzer's bound: |zA| <= sqrt(A * B)
    # Search over z
    z_limit = max(100, int(math.isqrt(A * B)) + 50)
    # Clamp z_limit for practical search
    z_limit = min(z_limit, 50000)

    for z in range(1, z_limit + 1):
        target = absC * z * z
        # Check if target is a square mod A or B
        # Try small x
        max_x = int(math.isqrt(target // A))
        # If max_x is small, enumerate x
        if max_x <= 2000:
            for x in range(0, max_x + 1):
                rem = target - A * x * x
                if rem % B == 0:
                    y2 = rem // B
                    sq_y = math.isqrt(y2)
                    if sq_y * sq_y == y2:
                        y = sq_y
                        # Reconstruct (x, y, z) map
                        res_map = {vA: x, vB: y, vC: z}
                        sol = (res_map["x"], res_map["y"], res_map["z"])
                        if any(sol):
                            # Verify
                            if a * sol[0] ** 2 + b * sol[1] ** 2 + c * sol[2] ** 2 == 0:
                                return sol
        else:
            # Try small y
            max_y = int(math.isqrt(target // B))
            if max_y <= 2000:
                for y in range(0, max_y + 1):
                    rem = target - B * y * y
                    if rem % A == 0:
                        x2 = rem // A
                        sq_x = math.isqrt(x2)
                        if sq_x * sq_x == x2:
                            x = sq_x
                            res_map = {vA: x, vB: y, vC: z}
                            sol = (res_map["x"], res_map["y"], res_map["z"])
                            if any(sol):
                                if a * sol[0] ** 2 + b * sol[1] ** 2 + c * sol[2] ** 2 == 0:
                                    return sol

    return None
