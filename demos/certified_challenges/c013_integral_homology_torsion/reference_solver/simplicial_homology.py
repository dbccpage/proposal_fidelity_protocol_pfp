"""Simplicial Complex, Boundary Operators, and Integral Homology over Z.

Builds simplicial complexes from simplex declarations, validates closure under
taking faces, constructs oriented boundary matrices ∂_k, and calculates integral
homology groups H_n(K; Z) = Z^{β_n} ⊕ ⨁ Z/t_i with Smith normal form certificates.

AuthorityEffect: None.
"""

from __future__ import annotations

import itertools
from typing import Any

try:
    from .smith_normal_form import compute_smith_normal_form, identity_matrix, mat_mul
except ImportError:
    from smith_normal_form import (  # type: ignore
        compute_smith_normal_form,
    )


def check_face_closure(
    simplices_raw: list[list[int]],
) -> tuple[bool, dict[str, Any] | None, set[tuple[int, ...]]]:
    """Validates that simplices_raw forms an abstract simplicial complex closed under faces.

    Returns:
        (is_closed, witness_if_not_closed, all_simplices_set)
    """
    simplex_set = set()
    for s in simplices_raw:
        if not isinstance(s, list) or len(s) == 0:
            return False, {"error": "malformed_simplex"}, set()
        # Verify all vertex labels are ints and distinct
        if len(set(s)) != len(s):
            return False, {"error": "duplicate_vertices_in_simplex", "simplex": s}, set()
        simplex_set.add(tuple(sorted(s)))

    # Check that every face of every simplex is in simplex_set
    for s in sorted(simplex_set):
        k = len(s)
        if k > 1:
            for face in itertools.combinations(s, k - 1):
                if face not in simplex_set:
                    witness = {
                        "missing_face": [str(v) for v in face],
                        "of_simplex": [str(v) for v in s],
                    }
                    return False, witness, simplex_set

    return True, None, simplex_set


def build_boundary_matrix(
    k_simplices: list[tuple[int, ...]],
    k_minus_1_simplices: list[tuple[int, ...]],
) -> list[list[int]]:
    """Constructs integer boundary matrix ∂_k: C_k -> C_{k-1}.

    Size: |K_{k-1}| x |K_k|.
    Simplices are assumed sorted in canonical lexicographic order.
    """
    m = len(k_minus_1_simplices)
    n = len(k_simplices)
    if m == 0 or n == 0:
        return []

    idx_map = {s: i for i, s in enumerate(k_minus_1_simplices)}
    mat = [[0 for _ in range(n)] for _ in range(m)]

    for col, sigma in enumerate(k_simplices):
        # ∂_k sigma = sum_{i=0}^k (-1)^i face_i
        for i in range(len(sigma)):
            face = sigma[:i] + sigma[i + 1 :]
            if face in idx_map:
                row = idx_map[face]
                sign = 1 if (i % 2 == 0) else -1
                mat[row][col] += sign

    return mat


def compute_simplicial_integral_homology(
    simplices: set[tuple[int, ...]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Computes integral homology groups and SNF certificates for complex.

    Returns:
        (homology_groups, snf_certificates)
    """
    if not simplices:
        return [], []

    max_dim = max(len(s) - 1 for s in simplices)

    # Group simplices by dimension
    by_dim: dict[int, list[tuple[int, ...]]] = {d: [] for d in range(max_dim + 2)}
    for s in simplices:
        by_dim[len(s) - 1].append(s)

    for d in by_dim:
        by_dim[d].sort()

    boundary_matrices: dict[int, list[list[int]]] = {}
    snf_results: dict[int, Any] = {}

    # Compute boundary matrices and SNF for k = 1 up to max_dim + 1
    for k in range(1, max_dim + 2):
        k_simp = by_dim[k]
        k_minus_1_simp = by_dim[k - 1]
        mat = build_boundary_matrix(k_simp, k_minus_1_simp)
        boundary_matrices[k] = mat

        if mat and len(mat) > 0 and len(mat[0]) > 0:
            d_inv, U, U_inv, V, V_inv = compute_smith_normal_form(mat)
            snf_results[k] = {
                "invariants": d_inv,
                "rank": len(d_inv),
                "U": U,
                "U_inv": U_inv,
                "V": V,
                "V_inv": V_inv,
                "dim_domain": len(mat[0]),
                "dim_codomain": len(mat),
            }
        else:
            snf_results[k] = {
                "invariants": [],
                "rank": 0,
                "U": [],
                "U_inv": [],
                "V": [],
                "V_inv": [],
                "dim_domain": len(k_simp),
                "dim_codomain": len(k_minus_1_simp),
            }

    # Compute Betti numbers and torsion for each degree n = 0, ..., max_dim
    homology = []
    for n in range(max_dim + 1):
        dim_Cn = len(by_dim[n])
        rank_dn = snf_results[n]["rank"] if n in snf_results else 0
        rank_dn_plus_1 = snf_results[n + 1]["rank"] if (n + 1) in snf_results else 0

        betti = dim_Cn - rank_dn - rank_dn_plus_1

        # Torsion comes from invariants > 1 of ∂_{n+1}
        torsion = []
        if (n + 1) in snf_results:
            for factor in snf_results[n + 1]["invariants"]:
                if factor > 1:
                    torsion.append(str(factor))

        homology.append(
            {
                "n": str(n),
                "betti": str(betti),
                "torsion": torsion,
            }
        )

    # Prepare certificates for each non-trivial boundary map
    certificates = []
    for k in range(1, max_dim + 2):
        if (
            k in boundary_matrices
            and len(boundary_matrices[k]) > 0
            and len(boundary_matrices[k][0]) > 0
        ):
            res = snf_results[k]
            certificates.append(
                {
                    "boundary": str(k),
                    "U": [[str(x) for x in row] for row in res["U"]],
                    "U_inv": [[str(x) for x in row] for row in res["U_inv"]],
                    "V": [[str(x) for x in row] for row in res["V"]],
                    "V_inv": [[str(x) for x in row] for row in res["V_inv"]],
                    "D": [str(d) for d in res["invariants"]],
                }
            )

    return homology, certificates
