# AuthorityEffect: None.
r"""
Independent Second Checker for C025 (Projector Algebra Route).

Validates candidate MUB answers via high-precision numerical embedding of Q(zeta_m)
into complex matrix projector algebra:
1. Projector Hermiticity: Pi^\dagger = Pi
2. Projector Idempotence: Pi^2 = Pi
3. Trace rank one: Tr(Pi) = 1
4. Resolution of Identity: sum_{k=0}^{d-1} Pi_{b, k} = I_d
5. Cross-basis Hilbert-Schmidt inner product: Tr(Pi_{b1, k1} * Pi_{b2, k2}) = 1/d
"""

from __future__ import annotations

import cmath
from fractions import Fraction
from typing import Any, Dict, List, Tuple

import numpy as np

from .exact_checker import verify_exact
from .schema_guard import validate_certificate


def parse_frac_val(s: str) -> float:
    f = Fraction(s)
    return float(f)


def embed_cyclotomic(m: int, coeffs_wire: List[str]) -> complex:
    """Evaluate sum_{k=0}^{m-1} c_k * exp(2*pi*i*k / m)."""
    val = 0.0 + 0.0j
    for k, c_str in enumerate(coeffs_wire):
        c = parse_frac_val(c_str)
        if c != 0.0:
            angle = 2.0 * cmath.pi * k / m
            val += c * cmath.exp(1j * angle)
    return val


def verify_independent(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Independent projector algebra verification.
    Returns (passed: bool, message: str, details: dict).
    """
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}
    case_id = case.get("case_id")
    d = case.get("dimension")
    k = case.get("num_bases")
    fixed_b0 = case.get("fixed_first_basis")

    ans_status = answer.get("status")
    details: Dict[str, Any] = {
        "case_id": case_id,
        "dimension": d,
        "num_bases": k,
        "status": ans_status,
        "checker": "independent_projector_algebra",
    }

    if ans_status != "SOLVED":
        return verify_exact(case, answer)

    # Case 1: Out of scope request
    if k > d + 1:
        if ans_status != "OUT_OF_SCOPE":
            return False, f"Expected OUT_OF_SCOPE, got {ans_status}", details
        return True, "OUT_OF_SCOPE verified independently", details

    # Case 2: Open problem (d = 6, k >= 4)
    if d == 6 and k >= 4:
        if ans_status != "UNKNOWN":
            return False, f"CRITICAL: Claimed {ans_status} for open problem d=6", details
        if answer.get("refusal_code") != "OPEN_PROBLEM":
            return False, "Expected refusal_code OPEN_PROBLEM", details
        return True, "OPEN_PROBLEM refusal verified independently", details

    # Case 3: Solved instance
    if ans_status != "SOLVED":
        return False, f"Expected SOLVED, got {ans_status}", details

    m = answer.get("cyclotomic_order")
    if not isinstance(m, int) or m < 1:
        return False, f"Invalid cyclotomic_order: {m}", details

    bases = answer.get("bases")
    if not isinstance(bases, list) or len(bases) != k:
        return (
            False,
            f"Expected {k} bases, got {len(bases) if isinstance(bases, list) else type(bases)}",
            details,
        )

    tol = 1e-9
    eye_d = np.eye(d, dtype=complex)
    all_projectors: List[List[np.ndarray]] = []

    for b_idx, base in enumerate(bases):
        if not isinstance(base, list) or len(base) != d:
            return False, f"Basis {b_idx} must have {d} vectors", details

        basis_projs: List[np.ndarray] = []
        basis_id_sum = np.zeros((d, d), dtype=complex)

        for v_idx, vec in enumerate(base):
            if not isinstance(vec, dict):
                return False, f"Vector B{b_idx}[{v_idx}] must be dict", details

            try:
                norm2_declared = parse_frac_val(vec.get("norm2", "0"))
                if norm2_declared <= 0:
                    return False, f"Non-positive norm2: {norm2_declared}", details
            except Exception as ex:
                return False, f"Invalid norm2 in B{b_idx}[{v_idx}]: {ex}", details

            entries_raw = vec.get("entries")
            if not isinstance(entries_raw, list) or len(entries_raw) != d:
                return False, f"Vector B{b_idx}[{v_idx}] entries must have length {d}", details

            # Embed entries into complex vector
            v_vec = np.zeros(d, dtype=complex)
            for idx, c_wire in enumerate(entries_raw):
                if not isinstance(c_wire, list) or len(c_wire) != m:
                    return False, f"Invalid coordinate length in B{b_idx}[{v_idx}]", details
                try:
                    v_vec[idx] = embed_cyclotomic(m, c_wire)
                except Exception as ex:
                    return (
                        False,
                        f"Invalid cyclotomic coordinate in B{b_idx}[{v_idx}]: {ex}",
                        details,
                    )

            # Check norm
            computed_norm = np.vdot(v_vec, v_vec).real
            if abs(computed_norm - norm2_declared) > tol:
                return (
                    False,
                    f"Norm mismatch in B{b_idx}[{v_idx}]: {computed_norm} vs {norm2_declared}",
                    details,
                )

            # Form projector Pi = |v><v| / <v|v>
            proj = np.outer(v_vec, np.conj(v_vec)) / computed_norm

            # 1. Hermiticity: Pi^\dagger = Pi
            if np.max(np.abs(proj - np.conj(proj.T))) > tol:
                return False, f"Projector Hermiticity failed in B{b_idx}[{v_idx}]", details

            # 2. Idempotence: Pi^2 = Pi
            proj_sq = proj @ proj
            if np.max(np.abs(proj_sq - proj)) > tol:
                return False, f"Projector idempotence failed in B{b_idx}[{v_idx}]", details

            # 3. Trace rank one: Tr(Pi) = 1
            tr = np.trace(proj).real
            if abs(tr - 1.0) > tol:
                return False, f"Projector trace != 1 in B{b_idx}[{v_idx}]: {tr}", details

            basis_projs.append(proj)
            basis_id_sum += proj

        # 4. Resolution of Identity in basis: sum Pi = I_d
        if np.max(np.abs(basis_id_sum - eye_d)) > tol:
            return False, f"Resolution of identity failed in basis {b_idx}", details

        all_projectors.append(basis_projs)

    # 5. Cross-basis unbiasedness: Tr(Pi_{b1, k1} * Pi_{b2, k2}) = 1/d
    expected_overlap = 1.0 / d
    for b1 in range(k):
        for b2 in range(b1 + 1, k):
            for i in range(d):
                p1 = all_projectors[b1][i]
                for j in range(d):
                    p2 = all_projectors[b2][j]
                    overlap = np.trace(p1 @ p2).real
                    if abs(overlap - expected_overlap) > tol:
                        return (
                            False,
                            f"Cross-basis overlap failed between B{b1}[{i}] and B{b2}[{j}]: {overlap} vs {expected_overlap}",
                            details,
                        )

    # 6. Fixed B_0 check if required
    if fixed_b0 is not None:
        m_b0 = len(fixed_b0[0]["entries"][0])
        b0_projs = []
        for v in fixed_b0:
            v_vec = np.zeros(d, dtype=complex)
            for idx, c_wire in enumerate(v["entries"]):
                v_vec[idx] = embed_cyclotomic(m_b0, c_wire)
            p = np.outer(v_vec, np.conj(v_vec)) / np.vdot(v_vec, v_vec).real
            b0_projs.append(p)

        matched_b0 = False
        for b_idx in range(k):
            cand_projs = all_projectors[b_idx]
            # check if set of projectors matches b0_projs up to permutation
            used = [False] * d
            match_cnt = 0
            for cp in cand_projs:
                for target_idx, tp in enumerate(b0_projs):
                    if not used[target_idx] and np.max(np.abs(cp - tp)) < tol:
                        used[target_idx] = True
                        match_cnt += 1
                        break
            if match_cnt == d:
                matched_b0 = True
                break

        if not matched_b0:
            return False, "Projector set does not contain fixed_first_basis projectors", details

    return True, f"Independent projector algebra verified for {k} bases in dimension {d}", details
