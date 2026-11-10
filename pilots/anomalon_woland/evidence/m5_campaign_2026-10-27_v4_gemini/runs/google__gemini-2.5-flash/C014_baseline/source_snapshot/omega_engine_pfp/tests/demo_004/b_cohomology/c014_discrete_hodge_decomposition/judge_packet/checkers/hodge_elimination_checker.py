"""Checker 2: Independent Elimination & Betti Crosscheck for C014.

Recomputes exact Hodge decomposition components independently via alternative
normal equation reduction and asserts uniqueness of flow decomposition:
    g = δ₀ φ, c = W₁⁻¹ δ₁ᵀ ψ, h = f - g - c
and independently certifies Betti 1 rank-nullity:
    b₁ = |E| - rank(δ₀) - rank(δ₁).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from omega_engine_pfp.tests.demo_004.b_cohomology.c014_discrete_hodge_decomposition.judge_packet.checkers.case_model import (
    CaseParseError,
    admissible_refusals,
    check_refusal,
    mat_mul,
    mat_vec,
    parse_answer_natural,
    parse_answer_rational,
    parse_complex,
    rank,
    transpose,
)


def _solve_particular(a: list[list[Fraction]], b: list[Fraction], cols: int) -> list[Fraction]:
    """Particular solution of a consistent exact system A x = b (free variables zero)."""
    aug = [list(row) + [b[i]] for i, row in enumerate(a)]
    pivots: list[int] = []
    r = 0
    for c in range(cols):
        pivot = next((i for i in range(r, len(aug)) if aug[i][c] != 0), None)
        if pivot is None:
            continue
        aug[r], aug[pivot] = aug[pivot], aug[r]
        pv = aug[r][c]
        aug[r] = [x / pv for x in aug[r]]
        for i in range(len(aug)):
            if i != r and aug[i][c] != 0:
                f = aug[i][c]
                aug[i] = [aug[i][j] - f * aug[r][j] for j in range(cols + 1)]
        pivots.append(c)
        r += 1
    if any(aug[i][cols] != 0 for i in range(r, len(aug))):
        raise ArithmeticError("normal equations are inconsistent")
    x = [Fraction(0)] * cols
    for row_idx, col in enumerate(pivots):
        x[col] = aug[row_idx][cols]
    return x


def verify_elimination_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Independently verifies decomposition components and Betti 1 topology."""
    if not isinstance(result, Mapping):
        return False, "FAIL: result is not a mapping"

    status = result.get("status")
    if status == "UNKNOWN":
        return check_refusal(case, result)

    if admissible_refusals(case):
        return False, "FAIL: case violates declared bounds; TASK.md requires UNKNOWN"

    try:
        comp = parse_complex(case)
    except CaseParseError as exc:
        return False, f"FAIL: could not parse case complex: {exc}"

    vertices = comp["vertices"]
    edges = comp["edges"]
    faces = comp["faces"]
    delta0 = comp["delta0"]
    delta1 = comp["delta1"]
    flow = comp["flow"]
    weights = comp["weights"]
    n_V, n_E, n_F = len(vertices), len(edges), len(faces)

    d1_d0 = mat_mul(delta1, delta0, n_E, n_V)
    has_d1_d0_nonzero = any(val != 0 for row in d1_d0 for val in row)

    if status == "OUT_OF_SCOPE":
        witness = result.get("witness")
        if not isinstance(witness, dict):
            return False, "FAIL: OUT_OF_SCOPE missing witness"
        if witness.get("reason") != "D1_D0_NONZERO":
            return False, f"FAIL: unknown OUT_OF_SCOPE reason {witness.get('reason')!r}"
        if not has_d1_d0_nonzero:
            return False, "FAIL: OUT_OF_SCOPE reported but δ₁ · δ₀ == 0"
        f_name = witness.get("face")
        v_name = witness.get("vertex")
        if (
            type(f_name) is not str
            or type(v_name) is not str
            or f_name not in faces
            or v_name not in vertices
        ):
            return False, f"FAIL: unknown face {f_name} or vertex {v_name}"
        if d1_d0[faces.index(f_name)][vertices.index(v_name)] == 0:
            return False, "FAIL: witness cited zero entry in δ₁ · δ₀"
        return True, "VALID_OUT_OF_SCOPE"

    if has_d1_d0_nonzero:
        return False, "FAIL: complex has δ₁ · δ₀ ≠ 0 but solver reported SOLVED"

    if status != "SOLVED":
        return False, f"FAIL: unknown status {status!r}"

    # Independent Betti 1 calculation
    expected_b1 = n_E - rank(delta0, n_V) - rank(delta1, n_E)
    try:
        actual_dim = parse_answer_natural(result.get("harmonic_dim"))
    except ValueError as exc:
        return False, f"FAIL: harmonic_dim is not a canonical non-negative integer: {exc}"
    if actual_dim != expected_b1:
        return (
            False,
            f"FAIL: harmonic_dim {actual_dim} != independently computed Betti 1 {expected_b1}",
        )

    # Independent normal equations solve for unique parts g_ind, c_ind, h_ind
    delta0_T = transpose(delta0, n_V)
    delta1_T = transpose(delta1, n_E)
    w_inv = [Fraction(1) / w for w in weights]

    if n_V > 0 and n_E > 0:
        weighted_d0 = [[delta0[e][v] * weights[e] for v in range(n_V)] for e in range(n_E)]
        l0 = mat_mul(delta0_T, weighted_d0, n_E, n_V)
        rhs0 = mat_vec(delta0_T, [flow[e] * weights[e] for e in range(n_E)])
        g_ind = mat_vec(delta0, _solve_particular(l0, rhs0, n_V))
    else:
        g_ind = [Fraction(0)] * n_E

    if n_F > 0 and n_E > 0:
        winv_d1_T = [[delta1_T[e][f] * w_inv[e] for f in range(n_F)] for e in range(n_E)]
        l2 = mat_mul(delta1, winv_d1_T, n_E, n_F)
        psi_ind = _solve_particular(l2, mat_vec(delta1, flow), n_F)
        d1_T_psi_ind = mat_vec(delta1_T, psi_ind)
        c_ind = [d1_T_psi_ind[e] * w_inv[e] for e in range(n_E)]
    else:
        c_ind = [Fraction(0)] * n_E

    h_ind = [flow[e] - g_ind[e] - c_ind[e] for e in range(n_E)]

    def vector(key: str, index: list[str]) -> list[Fraction]:
        raw = result.get(key, {})
        if not isinstance(raw, dict):
            raise ValueError(f"{key} is not a dictionary")
        if set(raw) - set(index):
            raise ValueError(f"{key} cites unknown keys {sorted(set(raw) - set(index))}")
        return [parse_answer_rational(raw[k]) if k in raw else Fraction(0) for k in index]

    try:
        phi_cand = vector("phi", vertices)
        psi_cand = vector("psi", faces)
        h_cand = vector("h", edges)
    except ValueError as exc:
        return False, f"FAIL: could not parse candidate phi/psi/h: {exc}"

    g_cand = mat_vec(delta0, phi_cand)
    d1_T_psi = mat_vec(delta1_T, psi_cand) if n_F > 0 else [Fraction(0)] * n_E
    c_cand = [d1_T_psi[e] * w_inv[e] for e in range(n_E)]

    # Assert uniqueness of decomposition parts
    for e in range(n_E):
        if g_cand[e] != g_ind[e]:
            return (
                False,
                f"FAIL: gradient flow mismatch on edge {edges[e]}: cand={g_cand[e]} != ind={g_ind[e]}",
            )
        if c_cand[e] != c_ind[e]:
            return (
                False,
                f"FAIL: curl flow mismatch on edge {edges[e]}: cand={c_cand[e]} != ind={c_ind[e]}",
            )
        if h_cand[e] != h_ind[e]:
            return (
                False,
                f"FAIL: harmonic flow mismatch on edge {edges[e]}: cand={h_cand[e]} != ind={h_ind[e]}",
            )

    return True, "VALID_ELIMINATION_CERTIFICATE"
