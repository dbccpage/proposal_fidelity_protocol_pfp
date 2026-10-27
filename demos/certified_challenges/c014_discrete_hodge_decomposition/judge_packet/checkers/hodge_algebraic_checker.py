"""Checker 1: Exact Algebraic & Orthogonality Hodge Verifier for C014.

Verifies:
1. Exact discrete Hodge decomposition identity:
   f = δ₀ φ + W₁⁻¹ δ₁ᵀ ψ + h
2. Exact curl-free condition on harmonic part:
   δ₁ h = 0
3. Exact co-closed condition on harmonic part:
   δ₀ᵀ W₁ h = 0
4. Exact pairwise orthogonality under ⟨·, ·⟩_W₁:
   ⟨g, c⟩_W₁ = 0, ⟨g, h⟩_W₁ = 0, ⟨c, h⟩_W₁ = 0
5. Harmonic basis validity, independence, and dimension match b₁.
6. OUT_OF_SCOPE witness verification: (δ₁ δ₀)_{f, v} ≠ 0.
7. Refusal verification against closed enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from c014_discrete_hodge_decomposition.judge_packet.checkers.case_model import (
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

SOLVED_ALLOWED_KEYS = frozenset(
    {"id", "status", "phi", "psi", "h", "harmonic_dim", "harmonic_basis"}
)


def _parse_vector(raw: Any, index: list[str], label: str) -> list[Fraction]:
    if not isinstance(raw, dict):
        raise ValueError(f"{label} is not a dictionary")
    unknown = set(raw) - set(index)
    if unknown:
        raise ValueError(f"{label} cites unknown keys {sorted(unknown)}")
    return [parse_answer_rational(raw[k]) if k in raw else Fraction(0) for k in index]


def verify_algebraic_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Verifies candidate result against algebraic and orthogonality constraints."""
    if not isinstance(result, Mapping):
        return False, "FAIL: result is not a mapping"

    status = result.get("status")
    if status == "UNKNOWN":
        return check_refusal(case, result)

    out_of_bounds = admissible_refusals(case)
    if out_of_bounds:
        return (
            False,
            f"FAIL: case violates declared bounds {sorted(out_of_bounds)}; TASK.md requires UNKNOWN",
        )

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
            return False, "FAIL: OUT_OF_SCOPE missing witness dictionary"
        reason = witness.get("reason")
        if reason != "D1_D0_NONZERO":
            return False, f"FAIL: unknown OUT_OF_SCOPE reason {reason!r}"
        if not has_d1_d0_nonzero:
            return False, "FAIL: OUT_OF_SCOPE declared but δ₁ · δ₀ == 0"
        f_name = witness.get("face")
        v_name = witness.get("vertex")
        if (
            type(f_name) is not str
            or type(v_name) is not str
            or f_name not in faces
            or v_name not in vertices
        ):
            return False, f"FAIL: witness cites unknown face {f_name!r} or vertex {v_name!r}"
        if d1_d0[faces.index(f_name)][vertices.index(v_name)] == 0:
            return False, f"FAIL: witness cited entry ({f_name}, {v_name}) is zero in δ₁ · δ₀"
        return True, "VALID_OUT_OF_SCOPE"

    if has_d1_d0_nonzero:
        return (
            False,
            "FAIL: complex has δ₁ · δ₀ ≠ 0 but solver reported SOLVED instead of OUT_OF_SCOPE",
        )

    if status != "SOLVED":
        return False, f"FAIL: unknown status {status!r}"

    for k in result:
        if k not in SOLVED_ALLOWED_KEYS:
            return False, f"FAIL: unexpected extra phantom key {k!r} in result"

    try:
        phi_vec = _parse_vector(result.get("phi", {}), vertices, "phi")
        psi_vec = _parse_vector(result.get("psi", {}), faces, "psi")
        h_vec = _parse_vector(result.get("h", {}), edges, "h")
    except ValueError as exc:
        return False, f"FAIL: could not parse phi/psi/h: {exc}"

    g_vec = mat_vec(delta0, phi_vec)
    delta1_T = transpose(delta1, n_E)
    d1_T_psi = mat_vec(delta1_T, psi_vec) if n_F > 0 else [Fraction(0)] * n_E
    c_vec = [d1_T_psi[e] / weights[e] for e in range(n_E)]

    # 1. Verify decomposition: f == g + c + h exactly
    for e in range(n_E):
        rhs = g_vec[e] + c_vec[e] + h_vec[e]
        if flow[e] != rhs:
            return False, (
                f"FAIL: Hodge decomposition identity violated on edge {edges[e]}: "
                f"flow={flow[e]} != g({g_vec[e]}) + c({c_vec[e]}) + h({h_vec[e]}) = {rhs}"
            )

    delta0_T = transpose(delta0, n_V)

    def harmonic_defect(vec: list[Fraction]) -> str | None:
        if any(val != 0 for val in mat_vec(delta1, vec)):
            return "not closed: δ₁ h ≠ 0"
        weighted = [vec[e] * weights[e] for e in range(n_E)]
        if any(val != 0 for val in mat_vec(delta0_T, weighted)):
            return "not co-closed: δ₀ᵀ W₁ h ≠ 0"
        return None

    # 2-3. Verify the harmonic part is closed and co-closed
    defect = harmonic_defect(h_vec)
    if defect:
        return False, f"FAIL: harmonic flow h is {defect}"

    # 4. Verify exact pairwise orthogonality under ⟨·, ·⟩_W₁
    for name, a, b in (
        ("gradient and curl", g_vec, c_vec),
        ("gradient and harmonic", g_vec, h_vec),
        ("curl and harmonic", c_vec, h_vec),
    ):
        dot = sum((weights[e] * a[e] * b[e] for e in range(n_E)), Fraction(0))
        if dot != 0:
            return False, f"FAIL: orthogonality violated between {name}: ⟨·, ·⟩_W₁ = {dot}"

    # 5. Verify harmonic dimension equals b₁ and the basis spans the harmonic space
    try:
        harm_dim = parse_answer_natural(result.get("harmonic_dim"))
    except ValueError as exc:
        return False, f"FAIL: harmonic_dim is not a canonical non-negative integer: {exc}"
    b1 = n_E - rank(delta0, n_V) - rank(delta1, n_E)
    if harm_dim != b1:
        return False, f"FAIL: harmonic_dim {harm_dim} != b₁ = |E| - rank δ₀ - rank δ₁ = {b1}"

    raw_basis = result.get("harmonic_basis")
    if not isinstance(raw_basis, list) or len(raw_basis) != harm_dim:
        return (
            False,
            f"FAIL: harmonic_basis length {len(raw_basis) if isinstance(raw_basis, list) else None} != harmonic_dim {harm_dim}",
        )

    basis_vectors: list[list[Fraction]] = []
    for idx, b_dict in enumerate(raw_basis):
        try:
            b_vec = _parse_vector(b_dict, edges, f"harmonic_basis[{idx}]")
        except ValueError as exc:
            return False, f"FAIL: could not parse basis vector {idx}: {exc}"
        defect = harmonic_defect(b_vec)
        if defect:
            return False, f"FAIL: basis vector {idx} is {defect}"
        basis_vectors.append(b_vec)

    if harm_dim > 0 and rank(basis_vectors, n_E) != harm_dim:
        return False, f"FAIL: harmonic_basis vectors are linearly dependent (dimension {harm_dim})"

    return True, "VALID_ALGEBRAIC_CERTIFICATE"
