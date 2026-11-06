"""Checker 2 (Independent Elimination & Topological Invariant Certifier) for C013.

Independent second checker verifying:
1. Independent integer echelon and gcd-based invariant factor calculation.
2. Euler-Poincaré formula: χ(K) = ∑ (-1)^n β_n = ∑ (-1)^n |K_n|.
3. Universal Coefficient Theorem bounds: β_n(K; F_2) >= β_n(K; Z).
4. Independent verification of missing-face out-of-scope witnesses and refusal conditions.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

SOLVED_ALLOWED_KEYS = frozenset({"id", "status", "homology", "snf"})
HOMOLOGY_ALLOWED_KEYS = frozenset({"n", "betti", "torsion"})

CLOSED_REFUSAL_ENUM = frozenset(
    {
        "SIMPLEX_COUNT_OUT_OF_BOUNDS",
        "DIMENSION_OUT_OF_BOUNDS",
        "MALFORMED_INPUT",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_CASE_STRUCTURE",
    }
)


def _is_canonical_int_str(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    if s == "0":
        return True
    if s.startswith("-"):
        val = s[1:]
        return val.isdigit() and val != "0" and not val.startswith("0")
    return s.isdigit() and not s.startswith("0")


def _independent_gcd_elimination_invariants(M_in: list[list[int]]) -> list[int]:
    """Independent integer reduction to diagonal form using gcd steps."""
    if not M_in or not M_in[0]:
        return []
    M = [list(r) for r in M_in]
    rows = len(M)
    cols = len(M[0])
    p = 0
    min_dim = min(rows, cols)

    while p < min_dim:
        while True:
            # Find non-zero entry with smallest absolute value
            best_val = None
            best_r, best_c = -1, -1
            for r in range(p, rows):
                for c in range(p, cols):
                    v = abs(M[r][c])
                    if v != 0 and (best_val is None or v < best_val):
                        best_val = v
                        best_r, best_c = r, c

            if best_val is None:
                break

            # Swap to pivot
            M[p], M[best_r] = M[best_r], M[p]
            for r in range(rows):
                M[r][p], M[r][best_c] = M[r][best_c], M[r][p]

            if M[p][p] < 0:
                for c in range(cols):
                    M[p][c] = -M[p][c]

            pivot_val = M[p][p]

            # Clear col
            col_clean = True
            for r in range(p + 1, rows):
                if M[r][p] != 0:
                    q = M[r][p] // pivot_val
                    for c in range(cols):
                        M[r][c] -= q * M[p][c]
                    if M[r][p] != 0:
                        col_clean = False
                        break
            if not col_clean:
                continue

            # Clear row
            row_clean = True
            for c in range(p + 1, cols):
                if M[p][c] != 0:
                    q = M[p][c] // pivot_val
                    for r in range(rows):
                        M[r][c] -= q * M[r][p]
                    if M[p][c] != 0:
                        row_clean = False
                        break
            if not row_clean:
                continue

            # Check divisibility in remaining submatrix
            divisible = True
            for r in range(p + 1, rows):
                for c in range(p + 1, cols):
                    if M[r][c] % pivot_val != 0:
                        for j in range(cols):
                            M[p][j] += M[r][j]
                        divisible = False
                        break
                if not divisible:
                    break

            if divisible:
                break

        if best_val is None:
            break
        p += 1

    invariants = []
    for i in range(p):
        v = abs(M[i][i])
        if v > 0:
            invariants.append(v)

    # Sort divisibility chain if needed
    for i in range(len(invariants)):
        for j in range(i + 1, len(invariants)):
            g = math.gcd(invariants[i], invariants[j])
            l = (invariants[i] * invariants[j]) // g
            invariants[i] = g
            invariants[j] = l

    return invariants


def _compute_f2_rank(M_in: list[list[int]]) -> int:
    """Computes matrix rank over field F_2 using Gaussian elimination."""
    if not M_in or not M_in[0]:
        return 0
    M = [[val % 2 for val in r] for r in M_in]
    rows = len(M)
    cols = len(M[0])
    p = 0
    for c in range(cols):
        if p >= rows:
            break
        pivot_r = None
        for r in range(p, rows):
            if M[r][c] == 1:
                pivot_r = r
                break
        if pivot_r is None:
            continue
        M[p], M[pivot_r] = M[pivot_r], M[p]
        for r in range(rows):
            if r != p and M[r][c] == 1:
                for j in range(c, cols):
                    M[r][j] ^= M[p][j]
        p += 1
    return p


def _verify_refusal_warranted(case: Any, refusal: str) -> tuple[bool, str]:
    if refusal not in CLOSED_REFUSAL_ENUM:
        return False, f"FAIL: refusal {refusal!r} not in closed refusal enum"

    if not isinstance(case, Mapping):
        return (
            (True, "VALID_REFUSAL_MALFORMED_CASE_STRUCTURE")
            if refusal == "MALFORMED_CASE_STRUCTURE"
            else (False, "FAIL: wrong refusal on non-mapping")
        )

    simplices = case.get("simplices")
    if not isinstance(simplices, list):
        return (
            (True, "VALID_REFUSAL_MALFORMED_CASE_STRUCTURE")
            if refusal == "MALFORMED_CASE_STRUCTURE"
            else (False, "FAIL: wrong refusal on non-list simplices")
        )

    if refusal == "SIMPLEX_COUNT_OUT_OF_BOUNDS":
        if len(simplices) < 1 or len(simplices) > 1000:
            return True, "VALID_REFUSAL_SIMPLEX_COUNT_OUT_OF_BOUNDS"
        return False, f"FAIL: refused SIMPLEX_COUNT_OUT_OF_BOUNDS on valid count {len(simplices)}"

    if refusal == "DIMENSION_OUT_OF_BOUNDS":
        has_dim_oob = any(
            isinstance(s, list) and (len(s) - 1 > 3 or len(s) - 1 < 0) for s in simplices
        )
        if has_dim_oob:
            return True, "VALID_REFUSAL_DIMENSION_OUT_OF_BOUNDS"
        return False, "FAIL: refused DIMENSION_OUT_OF_BOUNDS on complex with dimension <= 3"

    if refusal == "COEFFICIENT_BOUND_EXCEEDED":
        has_coeff_oob = any(
            isinstance(s, list) and any(isinstance(v, int) and abs(v) > 10_000 for v in s)
            for s in simplices
        )
        if has_coeff_oob:
            return True, "VALID_REFUSAL_COEFFICIENT_BOUND_EXCEEDED"
        return False, "FAIL: refused COEFFICIENT_BOUND_EXCEEDED on bounded vertices"

    if refusal == "MALFORMED_INPUT":
        has_malformed = any(
            not isinstance(s, list)
            or len(s) == 0
            or any(not isinstance(v, int) for v in s)
            or len(set(s)) != len(s)
            for s in simplices
        )
        if has_malformed:
            return True, "VALID_REFUSAL_MALFORMED_INPUT"
        return False, "FAIL: refused MALFORMED_INPUT on valid simplices"

    return False, f"FAIL: unhandled refusal {refusal}"


def _verify_oos_warranted(case: Any, witness: Any) -> tuple[bool, str]:
    if not isinstance(witness, Mapping):
        return False, "FAIL: OUT_OF_SCOPE witness is not a mapping"

    missing = witness.get("missing_face")
    parent = witness.get("of_simplex")
    if not isinstance(missing, list) or not isinstance(parent, list):
        return False, "FAIL: OUT_OF_SCOPE witness missing required keys"

    # Independently reject malformed witness labels before using them as set keys.
    for name, vertices in (("missing_face", missing), ("of_simplex", parent)):
        if any(
            type(x) is not int and (not _is_canonical_int_str(x) or not x.isascii())
            for x in vertices
        ):
            return False, f"FAIL: OUT_OF_SCOPE {name} contains a non-integer vertex"

    missing_set = set(int(x) if isinstance(x, str) else x for x in missing)
    parent_set = set(int(x) if isinstance(x, str) else x for x in parent)

    if (
        not missing_set.issubset(parent_set)
        or len(missing_set) == 0
        or len(missing_set) >= len(parent_set)
    ):
        return False, f"FAIL: missing face {missing} not a proper face of {parent}"

    simplices = case.get("simplices", [])
    existing_set = set(tuple(sorted(int(x) for x in s)) for s in simplices if isinstance(s, list))
    if tuple(sorted(parent_set)) not in existing_set:
        return False, f"FAIL: parent simplex {parent} not in input"
    if tuple(sorted(missing_set)) in existing_set:
        return False, f"FAIL: missing face {missing} actually present in input"

    return True, "VALID_OOS_NOT_CLOSED_UNDER_FACES"


def verify_elimination_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Total parsing verifier for Checker 2 (Independent Elimination & Topological Invariants)."""
    if not isinstance(case, Mapping):
        return False, "FAIL: case is not a mapping"
    if not isinstance(result, Mapping):
        return False, "FAIL: result is not a mapping"

    status = result.get("status")
    if status == "UNKNOWN":
        refusal = result.get("refusal") or result.get("refusal_code")
        if not isinstance(refusal, str):
            return False, "FAIL: UNKNOWN status missing string refusal code"
        return _verify_refusal_warranted(case, refusal)

    if status == "OUT_OF_SCOPE":
        witness = result.get("witness")
        return _verify_oos_warranted(case, witness)

    if status != "SOLVED":
        return False, f"FAIL: unknown status {status!r}"

    for k in result:
        if k not in SOLVED_ALLOWED_KEYS:
            return False, f"FAIL: unexpected extra phantom key {k!r} in result"

    raw_simplices = case.get("simplices")
    if not isinstance(raw_simplices, list):
        return False, "FAIL: case simplices not a list"

    simplex_set = set(tuple(sorted(s)) for s in raw_simplices)
    max_dim = max(len(s) - 1 for s in simplex_set)

    by_dim: dict[int, list[tuple[int, ...]]] = {d: [] for d in range(max_dim + 2)}
    for s in simplex_set:
        by_dim[len(s) - 1].append(s)
    for d in by_dim:
        by_dim[d].sort()

    # Build canonical boundary matrices independently
    ranks: dict[int, int] = {}
    f2_ranks: dict[int, int] = {}
    invariants: dict[int, list[int]] = {}

    for k in range(1, max_dim + 2):
        m = len(by_dim[k - 1])
        n = len(by_dim[k])
        mat = [[0 for _ in range(n)] for _ in range(m)]
        if m > 0 and n > 0:
            idx_map = {s: i for i, s in enumerate(by_dim[k - 1])}
            for col, sigma in enumerate(by_dim[k]):
                for i in range(len(sigma)):
                    face = sigma[:i] + sigma[i + 1 :]
                    if face in idx_map:
                        sign = 1 if (i % 2 == 0) else -1
                        mat[idx_map[face]][col] += sign

        # Independent integer elimination
        inv = _independent_gcd_elimination_invariants(mat)
        ranks[k] = len(inv)
        invariants[k] = inv
        f2_ranks[k] = _compute_f2_rank(mat)

    # 1. Euler Characteristic Theorem
    # χ(K) = ∑ (-1)^n |K_n|
    expected_euler_from_simplices = sum(((-1) ** n) * len(by_dim[n]) for n in range(max_dim + 1))

    raw_homology = result.get("homology")
    if not isinstance(raw_homology, list) or len(raw_homology) != max_dim + 1:
        return False, "FAIL: homology list length mismatch"

    actual_betti_list: list[int] = []
    for n in range(max_dim + 1):
        h = raw_homology[n]
        if not isinstance(h, Mapping):
            return False, f"FAIL: homology[{n}] is not a mapping"
        betti_str = h.get("betti")
        if not _is_canonical_int_str(betti_str):
            return False, f"FAIL: non-canonical betti number at degree {n}"
        b = int(betti_str)
        actual_betti_list.append(b)

        # Independent Betti check
        dim_Cn = len(by_dim[n])
        rk_dn = ranks.get(n, 0)
        rk_dn_plus_1 = ranks.get(n + 1, 0)
        exp_b = dim_Cn - rk_dn - rk_dn_plus_1
        if b != exp_b:
            return False, f"FAIL: degree {n} betti {b} != independently eliminated {exp_b}"

        # Independent Torsion check
        exp_torsion = [str(t) for t in invariants.get(n + 1, []) if t > 1]
        act_torsion = h.get("torsion")
        if act_torsion != exp_torsion:
            return (
                False,
                f"FAIL: degree {n} torsion {act_torsion} != independently computed {exp_torsion}",
            )

        # 2. Universal Coefficient Theorem / Universal Rank Inequality:
        # dim H_n(K; F_2) = dim C_n - rk_F2(∂_n) - rk_F2(∂_{n+1})
        f2_betti = dim_Cn - f2_ranks.get(n, 0) - f2_ranks.get(n + 1, 0)
        if f2_betti < b:
            return False, f"FAIL: UCT violation at degree {n}: F_2 Betti {f2_betti} < Z Betti {b}"

    # Verify Euler-Poincaré identity
    computed_euler_from_betti = sum(((-1) ** n) * actual_betti_list[n] for n in range(max_dim + 1))
    if computed_euler_from_betti != expected_euler_from_simplices:
        return False, (
            f"FAIL: Euler-Poincaré theorem violated: ∑(-1)^n β_n ({computed_euler_from_betti}) != "
            f"∑(-1)^n |K_n| ({expected_euler_from_simplices})"
        )

    return True, "VALID_ELIMINATION_CERTIFICATE"
