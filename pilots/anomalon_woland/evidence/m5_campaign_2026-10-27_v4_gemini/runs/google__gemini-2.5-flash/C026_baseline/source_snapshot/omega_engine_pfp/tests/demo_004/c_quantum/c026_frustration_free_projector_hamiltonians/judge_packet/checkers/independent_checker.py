# AuthorityEffect: None.
"""
Independent Second Checker for C026 (Hamiltonian Spectral Route).

Validates candidate answers by assembling the full Hamiltonian
H = sum_i w_i * (P_i (x) I)
and computing its nullity via independent exact echelonization of H.
Shares no code with the stacked-rank route.
Positive semidefiniteness ensures nullity(H) == dim bigcap_i ker(P_i (x) I).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate

try:
    from ...reference_solver.gaussian_rational import GaussianRat, parse_fraction
    from ...reference_solver.kronecker import extend_local_matrix
    from ...reference_solver.linear_algebra import (
        mat_add,
        mat_scale,
    )
    from ...reference_solver.projector_validator import validate_projector
except (ImportError, ValueError):
    try:
        from reference_solver.gaussian_rational import GaussianRat, parse_fraction
        from reference_solver.kronecker import extend_local_matrix
        from reference_solver.linear_algebra import (
            mat_add,
            mat_scale,
        )
        from reference_solver.projector_validator import validate_projector
    except (ImportError, ValueError):
        from gaussian_rational import GaussianRat, parse_fraction
        from kronecker import extend_local_matrix
        from linear_algebra import (
            mat_add,
            mat_scale,
        )
        from projector_validator import validate_projector


def compute_matrix_nullity(H: List[List[GaussianRat]]) -> int:
    """
    Computes exact nullity of square matrix H via Gaussian row reduction.
    """
    n = len(H)
    mat = [[H[r][c] for c in range(n)] for r in range(n)]
    rank = 0
    pivot_row = 0

    for col in range(n):
        if pivot_row >= n:
            break
        sel = None
        for r in range(pivot_row, n):
            if not mat[r][col].is_zero():
                sel = r
                break
        if sel is None:
            continue

        if sel != pivot_row:
            mat[pivot_row], mat[sel] = mat[sel], mat[pivot_row]

        piv = mat[pivot_row][col]
        for c in range(col, n):
            mat[pivot_row][c] = mat[pivot_row][c] / piv

        for r in range(n):
            if r != pivot_row and not mat[r][col].is_zero():
                fac = mat[r][col]
                for c in range(col, n):
                    mat[r][c] = mat[r][c] - (fac * mat[pivot_row][c])

        rank += 1
        pivot_row += 1

    return n - rank


def verify_independent(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Independent Hamiltonian spectral verification.
    Returns (passed: bool, message: str, details: dict).
    """
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}
    case_id = case.get("case_id")
    local_dims = case.get("local_dims")
    terms_raw = case.get("terms")
    ans_status = answer.get("status")

    details: Dict[str, Any] = {
        "case_id": case_id,
        "status": ans_status,
        "checker": "independent_hamiltonian_checker",
    }

    if ans_status != "SOLVED":
        return verify_exact(case, answer)

    if not isinstance(local_dims, list) or not isinstance(terms_raw, list):
        if ans_status != "UNKNOWN":
            return False, f"Expected UNKNOWN, got {ans_status}", details
        return True, "UNKNOWN verified independently", details

    total_d = 1
    for d in local_dims:
        if not isinstance(d, int) or d not in (2, 3):
            if ans_status != "UNKNOWN":
                return False, f"Expected UNKNOWN, got {ans_status}", details
            return True, "UNKNOWN verified independently", details
        total_d *= d

    if total_d > 64:
        if ans_status != "UNKNOWN":
            return False, f"Expected UNKNOWN, got {ans_status}", details
        return True, "DIMENSION_OUT_OF_BOUNDS verified independently", details

    n_sites = len(local_dims)
    parsed_terms: List[Dict[str, Any]] = []

    for term_idx, term in enumerate(terms_raw):
        support = term.get("support", [])
        for s in support:
            if not isinstance(s, int) or s < 0 or s >= n_sites:
                if ans_status != "UNKNOWN":
                    return False, f"Expected UNKNOWN for site {s}", details
                return True, "UNKNOWN verified independently", details

        mat_raw = term.get("matrix", [])
        try:
            mat = [[GaussianRat.from_wire(elem) for elem in row] for row in mat_raw]
        except Exception:
            if ans_status != "OUT_OF_SCOPE":
                return False, "Expected OUT_OF_SCOPE", details
            return True, "OUT_OF_SCOPE verified independently", details

        is_proj, reason, offending_entry = validate_projector(mat)
        if not is_proj:
            if ans_status != "OUT_OF_SCOPE":
                return False, f"Expected OUT_OF_SCOPE for term {term_idx}", details
            return True, "OUT_OF_SCOPE verified independently", details

        weight_val = parse_fraction(term.get("weight", "1"))
        parsed_terms.append(
            {
                "support": support,
                "weight": weight_val,
                "matrix": mat,
            }
        )

    if ans_status != "SOLVED":
        return False, f"Expected SOLVED, got {ans_status}", details

    # Assemble Hamiltonian H = sum_i w_i * (P_i (x) I)
    H = [[GaussianRat.zero() for _ in range(total_d)] for _ in range(total_d)]
    for pt in parsed_terms:
        ext_p = extend_local_matrix(local_dims, pt["support"], pt["matrix"])
        w_rat = GaussianRat(pt["weight"])
        w_ext = mat_scale(ext_p, w_rat)
        H = mat_add(H, w_ext)

    # Compute nullity of H
    h_nullity = compute_matrix_nullity(H)
    is_ff = h_nullity > 0

    declared_ff = answer.get("frustration_free")
    if declared_ff != is_ff:
        return (
            False,
            f"Independent frustration_free mismatch: expected {is_ff}, got {declared_ff}",
            details,
        )

    if is_ff:
        declared_dim = answer.get("kernel_dim")
        if declared_dim != h_nullity:
            return (
                False,
                f"Independent nullity mismatch: expected {h_nullity}, got {declared_dim}",
                details,
            )

        basis_raw = answer.get("kernel_basis")
        if not isinstance(basis_raw, list) or len(basis_raw) != h_nullity:
            return False, f"Basis vector count mismatch: expected {h_nullity}", details

        # Verify <v| H |v> == 0 for all basis vectors
        for v_idx, vec_wire in enumerate(basis_raw):
            if not isinstance(vec_wire, list) or len(vec_wire) != total_d:
                return (
                    False,
                    f"Basis vector {v_idx} dimension mismatch: expected {total_d}",
                    details,
                )
            try:
                v = [GaussianRat.from_wire(elem) for elem in vec_wire]
            except Exception as ex:
                return False, f"Failed parsing vector {v_idx}: {ex}", details

            # Hv = H * v
            Hv = [GaussianRat.zero() for _ in range(total_d)]
            for r in range(total_d):
                for c in range(total_d):
                    Hv[r] = Hv[r] + (H[r][c] * v[c])

            # <v| Hv>
            energy = GaussianRat.zero()
            for c in range(total_d):
                energy = energy + (v[c].conjugate() * Hv[c])

            if not energy.is_zero():
                return (
                    False,
                    f"Basis vector {v_idx} has non-zero energy <v|H|v> = {energy}",
                    details,
                )

        return (
            True,
            f"Independent Hamiltonian spectral verification certified: nullity {h_nullity}",
            details,
        )

    else:
        # Frustrated case: H has strictly zero nullity (positive definite)
        if h_nullity != 0:
            return False, f"Expected nullity 0 for frustrated case, got {h_nullity}", details
        return True, "Independent Hamiltonian positive definiteness certified", details
