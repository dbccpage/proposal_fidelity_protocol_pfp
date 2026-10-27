"""Discrete Hodge Decomposition and Harmonic Forms over Q.

Computes exact Helmholtz-Hodge-Eckmann decomposition:
    f = δ₀ φ + W₁⁻¹ δ₁ᵀ ψ + h
where:
    g = δ₀ φ (gradient / exact cochain)
    c = W₁⁻¹ δ₁ᵀ ψ (curl / co-exact cochain)
    h ∈ H¹ (harmonic cochain, δ₁ h = 0 and δ₀ᵀ W₁ h = 0)
under the inner product ⟨a, b⟩_W₁ = aᵀ W₁ b.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

try:
    from .rational_linear_algebra import (
        exact_solve,
        format_fraction,
        mat_mul,
        mat_vec_mul,
        nullspace_basis,
        parse_fraction,
        rref_and_rank,
        transpose,
    )
except ImportError:
    from rational_linear_algebra import (  # type: ignore
        exact_solve,
        format_fraction,
        mat_mul,
        mat_vec_mul,
        nullspace_basis,
        rref_and_rank,
        transpose,
    )


def compute_discrete_hodge_decomposition(
    vertices: list[str],
    edges: list[str],
    faces: list[str],
    delta0: list[list[Fraction]],  # |E| x |V|
    delta1: list[list[Fraction]],  # |F| x |E|
    flow: list[Fraction],  # |E|
    weights: list[Fraction],  # |E|
) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None]:
    """Computes exact discrete Hodge decomposition over Q.

    Returns:
        (is_valid_complex, witness_if_invalid, solution_dict)
    """
    n_V = len(vertices)
    n_E = len(edges)
    n_F = len(faces)

    assert len(delta0) == n_E and (n_E == 0 or len(delta0[0]) == n_V)
    assert len(delta1) == n_F and (n_F == 0 or len(delta1[0]) == n_E)
    assert len(flow) == n_E
    assert len(weights) == n_E

    # 1. Verify coboundary chain complex condition: δ₁ · δ₀ == 0
    if n_F > 0 and n_E > 0 and n_V > 0:
        d1_d0 = mat_mul(delta1, delta0)
        for r_idx in range(n_F):
            for c_idx in range(n_V):
                if d1_d0[r_idx][c_idx] != 0:
                    witness = {
                        "reason": "D1_D0_NONZERO",
                        "face": faces[r_idx],
                        "vertex": vertices[c_idx],
                        "value": format_fraction(d1_d0[r_idx][c_idx]),
                    }
                    return False, witness, None

    # Edge weight diagonal matrix and inverse
    # W1 = diag(w_e), W1_inv = diag(1 / w_e)
    W1_diag = weights
    W1_inv_diag = [Fraction(1, 1) / w for w in weights]

    # Transposes
    delta0_T = transpose(delta0)  # |V| x |E|
    delta1_T = transpose(delta1)  # |E| x |F|

    # 2. Gradient potential φ: solve δ₀ᵀ · W₁ · δ₀ φ = δ₀ᵀ · W₁ · f
    # W1 · delta0 has row e scaled by w_e
    W1_delta0 = [[delta0[e][v] * W1_diag[e] for v in range(n_V)] for e in range(n_E)]
    L0 = mat_mul(delta0_T, W1_delta0)  # |V| x |V|

    # RHS: δ₀ᵀ · (W₁ · f)
    W1_f = [flow[e] * W1_diag[e] for e in range(n_E)]
    rhs_L0 = mat_vec_mul(delta0_T, W1_f) if n_E > 0 else [Fraction(0, 1) for _ in range(n_V)]

    if n_V > 0:
        ok_grad, phi_vec = exact_solve(L0, rhs_L0)
        assert ok_grad, "Gradient normal equation L0 φ = δ₀ᵀ W₁ f must always be consistent"
    else:
        phi_vec = []

    # Gradient flow: g = δ₀ · φ
    g_vec = (
        mat_vec_mul(delta0, phi_vec)
        if n_V > 0 and n_E > 0
        else [Fraction(0, 1) for _ in range(n_E)]
    )

    # 3. Curl potential ψ: solve δ₁ · W₁⁻¹ · δ₁ᵀ ψ = δ₁ · f
    if n_F > 0 and n_E > 0:
        W1_inv_delta1_T = [
            [delta1_T[e][f] * W1_inv_diag[e] for f in range(n_F)] for e in range(n_E)
        ]
        L2 = mat_mul(delta1, W1_inv_delta1_T)  # |F| x |F|
        rhs_L2 = mat_vec_mul(delta1, flow)
        ok_curl, psi_vec = exact_solve(L2, rhs_L2)
        assert ok_curl, "Curl normal equation L2 ψ = δ₁ f must always be consistent"
        # Curl flow: c = W₁⁻¹ · δ₁ᵀ · ψ
        delta1_T_psi = mat_vec_mul(delta1_T, psi_vec)
        c_vec = [delta1_T_psi[e] * W1_inv_diag[e] for e in range(n_E)]
    else:
        psi_vec = [Fraction(0, 1) for _ in range(n_F)]
        c_vec = [Fraction(0, 1) for _ in range(n_E)]

    # 4. Harmonic flow: h = f - g - c
    h_vec = [flow[e] - g_vec[e] - c_vec[e] for e in range(n_E)]

    # Exact harmonicity verification:
    # a. δ₁ · h == 0 (curl-free / closed)
    if n_F > 0 and n_E > 0:
        d1_h = mat_vec_mul(delta1, h_vec)
        assert all(val == 0 for val in d1_h), f"Harmonic flow h is not closed: δ₁ h = {d1_h}"

    # b. δ₀ᵀ · W₁ · h == 0 (co-closed / divergence-free)
    if n_E > 0 and n_V > 0:
        W1_h = [h_vec[e] * W1_diag[e] for e in range(n_E)]
        d0_T_W1_h = mat_vec_mul(delta0_T, W1_h)
        assert all(val == 0 for val in d0_T_W1_h), (
            f"Harmonic flow h is not co-closed: δ₀ᵀ W₁ h = {d0_T_W1_h}"
        )

    # 5. Harmonic space H¹ and basis:
    # H¹ = ker(δ₁) ∩ ker(δ₀ᵀ W₁)
    # System: [ δ₁ ] x = 0  and  [ δ₀ᵀ W₁ ] x = 0
    # Combined matrix M_harm: (|F| + |V|) x |E|
    rows_M: list[list[Fraction]] = []
    if n_F > 0:
        rows_M.extend([[delta1[f][e] for e in range(n_E)] for f in range(n_F)])
    if n_V > 0 and n_E > 0:
        # δ₀ᵀ W₁ has row v: [ delta0[e][v] * w_e for e ]
        rows_M.extend([[delta0[e][v] * W1_diag[e] for e in range(n_E)] for v in range(n_V)])

    if rows_M and n_E > 0:
        harm_basis_raw = nullspace_basis(rows_M)
    elif n_E > 0:
        # No faces and no vertices (isolated edges)
        harm_basis_raw = [[Fraction(1 if e == i else 0) for e in range(n_E)] for i in range(n_E)]
    else:
        harm_basis_raw = []

    # Cross-check dimension with Betti 1: b1 = |E| - rank(δ₀) - rank(δ₁)
    _, _, rank_d0 = rref_and_rank(delta0) if n_E > 0 and n_V > 0 else (None, None, 0)
    _, _, rank_d1 = rref_and_rank(delta1) if n_F > 0 and n_E > 0 else (None, None, 0)
    expected_b1 = n_E - rank_d0 - rank_d1
    assert len(harm_basis_raw) == expected_b1, (
        f"Harmonic basis count {len(harm_basis_raw)} != expected Betti 1 {expected_b1} "
        f"(|E|={n_E}, rank(δ₀)={rank_d0}, rank(δ₁)={rank_d1})"
    )

    # Format output dictionaries (omitting zero values per spec §4 or including non-zero)
    phi_dict = {vertices[v]: format_fraction(phi_vec[v]) for v in range(n_V) if phi_vec[v] != 0}
    psi_dict = {faces[f]: format_fraction(psi_vec[f]) for f in range(n_F) if psi_vec[f] != 0}
    h_dict = {edges[e]: format_fraction(h_vec[e]) for e in range(n_E) if h_vec[e] != 0}

    basis_formatted = []
    for vec in harm_basis_raw:
        vec_dict = {edges[e]: format_fraction(vec[e]) for e in range(n_E) if vec[e] != 0}
        basis_formatted.append(vec_dict)

    solution = {
        "status": "SOLVED",
        "phi": phi_dict,
        "psi": psi_dict,
        "h": h_dict,
        "harmonic_dim": str(expected_b1),
        "harmonic_basis": basis_formatted,
    }

    return True, None, solution
