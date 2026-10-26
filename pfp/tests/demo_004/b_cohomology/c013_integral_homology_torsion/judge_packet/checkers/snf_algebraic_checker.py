"""Checker 1 (Exact Algebraic & Unimodular SNF Certifier) for C013.

Verifies:
1. Matrix unimodularity: U·U_inv = I and V·V_inv = I over Z.
2. SNF identity: U·∂_k·V = diag(D_k).
3. Divisibility chain: d_1 | d_2 | ... | d_r >= 1.
4. Exact Betti rank-nullity: β_n = dim C_n - rank ∂_n - rank ∂_{n+1}.
5. Torsion factors: invariant factors of ∂_{n+1} strictly greater than 1.
6. Closed refusal and out-of-scope witness validity.

AuthorityEffect: None.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from typing import Any

SOLVED_ALLOWED_KEYS = frozenset({"id", "status", "homology", "snf"})
HOMOLOGY_ALLOWED_KEYS = frozenset({"n", "betti", "torsion"})
SNF_ALLOWED_KEYS = frozenset({"boundary", "U", "U_inv", "V", "V_inv", "D"})

CLOSED_REFUSAL_ENUM = frozenset(
    {
        "SIMPLEX_COUNT_OUT_OF_BOUNDS",
        "DIMENSION_OUT_OF_BOUNDS",
        "MALFORMED_INPUT",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_CASE_STRUCTURE",
    }
)

CLOSED_OUT_OF_SCOPE_ENUM = frozenset(
    {
        "NOT_CLOSED_UNDER_FACES",
    }
)


def _is_canonical_int_str(s: Any) -> bool:
    """Checks if s is a canonical integer string."""
    if not isinstance(s, str):
        return False
    if s == "0":
        return True
    if s.startswith("-"):
        val = s[1:]
        return val.isdigit() and val != "0" and not val.startswith("0")
    return s.isdigit() and not s.startswith("0")


def _mat_mul_int(A: list[list[int]], B: list[list[int]]) -> list[list[int]]:
    m = len(A)
    k = len(A[0]) if m > 0 else 0
    n = len(B[0]) if B and len(B) > 0 else 0
    res = [[0 for _ in range(n)] for _ in range(m)]
    for i in range(m):
        for p in range(k):
            if A[i][p] != 0:
                for j in range(n):
                    res[i][j] += A[i][p] * B[p][j]
    return res


def _is_identity_int(A: list[list[int]], n: int) -> bool:
    if len(A) != n:
        return False
    for i in range(n):
        if len(A[i]) != n:
            return False
        for j in range(n):
            expected = 1 if i == j else 0
            if A[i][j] != expected:
                return False
    return True


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
        has_coeff_oob = False
        for s in simplices:
            if isinstance(s, list):
                for v in s:
                    if isinstance(v, int) and abs(v) > 10_000:
                        has_coeff_oob = True
        if has_coeff_oob:
            return True, "VALID_REFUSAL_COEFFICIENT_BOUND_EXCEEDED"
        return False, "FAIL: refused COEFFICIENT_BOUND_EXCEEDED on bounded vertices"

    if refusal == "MALFORMED_INPUT":
        has_malformed = False
        for s in simplices:
            if not isinstance(s, list) or len(s) == 0:
                has_malformed = True
            else:
                for v in s:
                    if not isinstance(v, int):
                        has_malformed = True
                if len(set(s)) != len(s):
                    has_malformed = True
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
        return False, "FAIL: OUT_OF_SCOPE witness missing 'missing_face' or 'of_simplex' list"

    # Validate untrusted vertices before conversion or hashing (nested lists are
    # not vertex labels, even when an empty missing face would later be rejected).
    for name, vertices in (("missing_face", missing), ("of_simplex", parent)):
        if any(
            type(x) is not int and (not _is_canonical_int_str(x) or not x.isascii())
            for x in vertices
        ):
            return False, f"FAIL: OUT_OF_SCOPE {name} contains a non-integer vertex"

    missing_set = set(int(x) if isinstance(x, str) else x for x in missing)
    parent_set = set(int(x) if isinstance(x, str) else x for x in parent)

    # missing must be a strict non-empty subset of parent
    if (
        not missing_set.issubset(parent_set)
        or len(missing_set) == 0
        or len(missing_set) >= len(parent_set)
    ):
        return False, f"FAIL: missing_face {missing} is not a valid proper face of {parent}"

    # Verify parent is indeed in case, and missing face is NOT in case
    simplices = case.get("simplices", [])
    if not isinstance(simplices, list):
        return False, "FAIL: case simplices not a list"

    existing_set = set(tuple(sorted(int(x) for x in s)) for s in simplices if isinstance(s, list))
    parent_tuple = tuple(sorted(parent_set))
    missing_tuple = tuple(sorted(missing_set))

    if parent_tuple not in existing_set:
        return False, f"FAIL: parent simplex {parent} does not exist in case"
    if missing_tuple in existing_set:
        return False, f"FAIL: claimed missing face {missing} actually exists in case"

    return True, "VALID_OOS_NOT_CLOSED_UNDER_FACES"


def verify_algebraic_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Total parsing verifier for Checker 1 (Exact Algebraic & Unimodular SNF Certifier)."""
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

    # 1. Whitelist dictionary keys in result
    for k in result:
        if k not in SOLVED_ALLOWED_KEYS:
            return False, f"FAIL: unexpected extra phantom key {k!r} in result"

    raw_simplices = case.get("simplices")
    if not isinstance(raw_simplices, list):
        return False, "FAIL: case simplices not a list"

    # Reconstruct simplicial complex
    simplex_set: set[tuple[int, ...]] = set()
    for s in raw_simplices:
        if not isinstance(s, list) or len(s) == 0:
            return False, "FAIL: invalid simplex in case"
        s_tuple = tuple(sorted(s))
        simplex_set.add(s_tuple)

    # Check closure
    for s in simplex_set:
        k = len(s)
        if k > 1:
            for face in itertools.combinations(s, k - 1):
                if face not in simplex_set:
                    return (
                        False,
                        f"FAIL: complex not closed under faces: missing face {face} of {s}",
                    )

    max_dim = max(len(s) - 1 for s in simplex_set)
    by_dim: dict[int, list[tuple[int, ...]]] = {d: [] for d in range(max_dim + 2)}
    for s in simplex_set:
        by_dim[len(s) - 1].append(s)
    for d in by_dim:
        by_dim[d].sort()

    # Build canonical boundary matrices
    canonical_boundaries: dict[int, list[list[int]]] = {}
    for k in range(1, max_dim + 2):
        k_simp = by_dim[k]
        k_minus_1_simp = by_dim[k - 1]
        m = len(k_minus_1_simp)
        n = len(k_simp)
        mat = [[0 for _ in range(n)] for _ in range(m)]
        if m > 0 and n > 0:
            idx_map = {s: i for i, s in enumerate(k_minus_1_simp)}
            for col, sigma in enumerate(k_simp):
                for i in range(len(sigma)):
                    face = sigma[:i] + sigma[i + 1 :]
                    if face in idx_map:
                        sign = 1 if (i % 2 == 0) else -1
                        mat[idx_map[face]][col] += sign
        canonical_boundaries[k] = mat

    # Verify SNF certificates
    raw_snf = result.get("snf")
    if not isinstance(raw_snf, list):
        return False, "FAIL: snf is not a list"

    snf_by_boundary: dict[int, dict[str, Any]] = {}
    for item in raw_snf:
        if not isinstance(item, Mapping):
            return False, "FAIL: snf item is not a mapping"
        for k in item:
            if k not in SNF_ALLOWED_KEYS:
                return False, f"FAIL: unexpected key {k!r} in snf item"
        b_str = item.get("boundary")
        if not _is_canonical_int_str(b_str):
            return False, f"FAIL: non-canonical boundary index {b_str!r}"
        b_idx = int(b_str)
        if b_idx in snf_by_boundary:
            return False, f"FAIL: duplicate snf certificate for boundary {b_idx}"
        snf_by_boundary[b_idx] = item

    ranks: dict[int, int] = {}
    invariants: dict[int, list[int]] = {}

    for k in range(1, max_dim + 2):
        orig_mat = canonical_boundaries[k]
        m = len(orig_mat)
        n = len(orig_mat[0]) if m > 0 else 0

        if m == 0 or n == 0:
            ranks[k] = 0
            invariants[k] = []
            continue

        if k not in snf_by_boundary:
            return False, f"FAIL: missing SNF certificate for non-trivial boundary map ∂_{k}"

        cert = snf_by_boundary[k]
        U_raw = cert.get("U")
        U_inv_raw = cert.get("U_inv")
        V_raw = cert.get("V")
        V_inv_raw = cert.get("V_inv")
        D_raw = cert.get("D")

        if not isinstance(U_raw, list) or len(U_raw) != m:
            return (
                False,
                f"FAIL: boundary {k} U row dimension {len(U_raw) if isinstance(U_raw, list) else None} != {m}",
            )
        if not isinstance(U_inv_raw, list) or len(U_inv_raw) != m:
            return False, f"FAIL: boundary {k} U_inv row dimension != {m}"
        if not isinstance(V_raw, list) or len(V_raw) != n:
            return False, f"FAIL: boundary {k} V row dimension != {n}"
        if not isinstance(V_inv_raw, list) or len(V_inv_raw) != n:
            return False, f"FAIL: boundary {k} V_inv row dimension != {n}"
        if not isinstance(D_raw, list):
            return False, f"FAIL: boundary {k} D is not a list"

        # Parse integer matrices
        try:
            U = [[int(x) for x in row] for row in U_raw]
            U_inv = [[int(x) for x in row] for row in U_inv_raw]
            V = [[int(x) for x in row] for row in V_raw]
            V_inv = [[int(x) for x in row] for row in V_inv_raw]
            D = [int(x) for x in D_raw]
        except (ValueError, TypeError) as exc:
            return False, f"FAIL: boundary {k} non-integer matrix or diagonal entry: {exc}"

        # 1. Unimodularity checks: U·U_inv == I_m and V·V_inv == I_n
        if not _is_identity_int(_mat_mul_int(U, U_inv), m):
            return False, f"FAIL: boundary {k} U·U_inv != I_{m} (U is not unimodular)"
        if not _is_identity_int(_mat_mul_int(U_inv, U), m):
            return False, f"FAIL: boundary {k} U_inv·U != I_{m} (U_inv is not valid inverse)"
        if not _is_identity_int(_mat_mul_int(V, V_inv), n):
            return False, f"FAIL: boundary {k} V·V_inv != I_{n} (V is not unimodular)"
        if not _is_identity_int(_mat_mul_int(V_inv, V), n):
            return False, f"FAIL: boundary {k} V_inv·V != I_{n} (V_inv is not valid inverse)"

        # 2. Check U · ∂_k · V == diag(D)
        U_d_V = _mat_mul_int(_mat_mul_int(U, orig_mat), V)
        for r in range(m):
            for c in range(n):
                expected = D[r] if (r == c and r < len(D)) else 0
                if U_d_V[r][c] != expected:
                    return (
                        False,
                        f"FAIL: boundary {k} U·∂·V != D at ({r}, {c}): {U_d_V[r][c]} != {expected}",
                    )

        # 3. Check divisibility chain
        for idx, d in enumerate(D):
            if d <= 0:
                return False, f"FAIL: boundary {k} invariant factor D[{idx}] = {d} <= 0"
            if idx > 0 and d % D[idx - 1] != 0:
                return (
                    False,
                    f"FAIL: boundary {k} divisibility violated: D[{idx - 1}]={D[idx - 1]} does not divide D[{idx}]={d}",
                )

        ranks[k] = len(D)
        invariants[k] = D

    # Verify Homology
    raw_homology = result.get("homology")
    if not isinstance(raw_homology, list) or len(raw_homology) != max_dim + 1:
        return (
            False,
            f"FAIL: homology list length {len(raw_homology) if isinstance(raw_homology, list) else None} != {max_dim + 1}",
        )

    for n in range(max_dim + 1):
        h_spec = raw_homology[n]
        if not isinstance(h_spec, Mapping):
            return False, f"FAIL: homology[{n}] is not a mapping"
        for key in h_spec:
            if key not in HOMOLOGY_ALLOWED_KEYS:
                return False, f"FAIL: unexpected key {key!r} in homology[{n}]"

        n_str = h_spec.get("n")
        betti_str = h_spec.get("betti")
        torsion_list = h_spec.get("torsion")

        if not _is_canonical_int_str(n_str) or int(n_str) != n:
            return False, f"FAIL: homology[{n}] degree mismatch {n_str!r} != {n}"
        if not _is_canonical_int_str(betti_str):
            return False, f"FAIL: homology[{n}] non-canonical betti number {betti_str!r}"
        if not isinstance(torsion_list, list):
            return False, f"FAIL: homology[{n}] torsion is not a list"

        dim_Cn = len(by_dim[n])
        rank_dn = ranks.get(n, 0)
        rank_dn_plus_1 = ranks.get(n + 1, 0)
        expected_betti = dim_Cn - rank_dn - rank_dn_plus_1

        if int(betti_str) != expected_betti:
            return False, f"FAIL: degree {n} betti number {betti_str} != expected {expected_betti}"

        expected_torsion = [str(t) for t in invariants.get(n + 1, []) if t > 1]
        if torsion_list != expected_torsion:
            return False, f"FAIL: degree {n} torsion {torsion_list} != expected {expected_torsion}"

    return True, "VALID_ALGEBRAIC_CERTIFICATE"
