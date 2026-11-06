# AuthorityEffect: None.
"""
Exact Checker for C026 (Frustration-Free Projector Hamiltonians).

Verifies candidate answers using exact Q(i) arithmetic:
1. Annihilation: Every kernel basis vector v is annihilated by every extended term P_i (x) I * v = 0.
2. Linear Independence: Basis vectors are linearly independent (rank == kernel_dim).
3. Stacked Rank Equality: kernel_dim == D - rank([P_1 (x) I; ...; P_m (x) I]).
4. Left-Inverse Verification: For frustrated systems, L * [P_1 (x) I; ...; P_m (x) I] == I_D.
5. Typed Refusals:
   - OUT_OF_SCOPE: verified non-projector term witness.
   - UNKNOWN: verified refusal code (e.g. DIMENSION_OUT_OF_BOUNDS).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .schema_guard import validate_certificate

try:
    from ...reference_solver.gaussian_rational import GaussianRat
    from ...reference_solver.kronecker import extend_local_matrix
    from ...reference_solver.linear_algebra import (
        compute_rref_and_kernel,
        mat_mul,
    )
    from ...reference_solver.projector_validator import validate_projector
except (ImportError, ValueError):
    try:
        from c026_frustration_free_projector_hamiltonians.reference_solver.gaussian_rational import GaussianRat
        from c026_frustration_free_projector_hamiltonians.reference_solver.kronecker import extend_local_matrix
        from c026_frustration_free_projector_hamiltonians.reference_solver.linear_algebra import (
            compute_rref_and_kernel,
            mat_mul,
        )
        from c026_frustration_free_projector_hamiltonians.reference_solver.projector_validator import validate_projector
    except (ImportError, ValueError):
        from gaussian_rational import GaussianRat
        from kronecker import extend_local_matrix
        from linear_algebra import (
            compute_rref_and_kernel,
            mat_mul,
        )
        from projector_validator import validate_projector


def verify_exact(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Exact verification of C026 answer against case.
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
        "checker": "exact_checker",
    }

    # Check for invalid inputs requiring refusals
    if not isinstance(local_dims, list) or not isinstance(terms_raw, list):
        expected = {"kind": "malformed_case", "field": "local_dims_or_terms"}
        if ans_status != "OUT_OF_SCOPE" or answer.get("witness") != expected:
            return False, f"Expected OUT_OF_SCOPE witness {expected}, got {answer}", details
        return True, "Malformed case witness verified", details

    total_d = 1
    for d in local_dims:
        if type(d) is not int or d not in (2, 3):
            if ans_status != "UNKNOWN":
                return (
                    False,
                    f"Expected UNKNOWN for invalid local dimension, got {ans_status}",
                    details,
                )
            if answer.get("refusal_code") != "INVALID_LOCAL_DIMENSION":
                return False, "Expected refusal_code INVALID_LOCAL_DIMENSION", details
            return True, "UNKNOWN certified for invalid local dimension", details
        total_d *= d

    if total_d > 64:
        if ans_status != "UNKNOWN":
            return False, f"Expected UNKNOWN for total_d > 64, got {ans_status}", details
        if answer.get("refusal_code") != "DIMENSION_OUT_OF_BOUNDS":
            return (
                False,
                f"Expected refusal_code DIMENSION_OUT_OF_BOUNDS, got {answer.get('refusal_code')}",
                details,
            )
        return True, "DIMENSION_OUT_OF_BOUNDS certified", details

    # Parse and check projector validity
    n_sites = len(local_dims)
    parsed_terms: List[Dict[str, Any]] = []
    has_malformed_projector = False
    malformed_witness = None

    for term_idx, term in enumerate(terms_raw):
        if not isinstance(term, dict):
            expected = {"kind": "malformed_term", "term": term_idx}
            if ans_status != "OUT_OF_SCOPE" or answer.get("witness") != expected:
                return False, f"Expected OUT_OF_SCOPE witness {expected}", details
            return True, "Malformed term witness verified", details
        support = term.get("support", [])
        if not isinstance(support, list) or len(support) > 3:
            if ans_status != "UNKNOWN" or answer.get("refusal_code") != "INVALID_SUPPORT":
                return False, "Expected UNKNOWN refusal_code INVALID_SUPPORT", details
            return True, "INVALID_SUPPORT refusal verified", details
        for s in support:
            if type(s) is not int or s < 0 or s >= n_sites:
                if ans_status != "UNKNOWN":
                    return (
                        False,
                        f"Expected UNKNOWN for invalid site {s}, got {ans_status}",
                        details,
                    )
                if answer.get("refusal_code") != "SITE_OUT_OF_BOUNDS":
                    return False, "Expected refusal_code SITE_OUT_OF_BOUNDS", details
                return True, "UNKNOWN certified for invalid site index", details

        mat_raw = term.get("matrix")
        if not isinstance(mat_raw, list):
            expected = {"kind": "malformed_matrix", "term": term_idx}
            if ans_status != "OUT_OF_SCOPE" or answer.get("witness") != expected:
                return False, f"Expected OUT_OF_SCOPE witness {expected}", details
            return True, "Malformed matrix witness verified", details
        try:
            mat = [[GaussianRat.from_wire(elem) for elem in row] for row in mat_raw]
        except Exception:
            expected = {"kind": "unparseable_matrix", "term": term_idx}
            if ans_status != "OUT_OF_SCOPE" or answer.get("witness") != expected:
                return False, f"Expected OUT_OF_SCOPE witness {expected}", details
            return True, "Unparseable matrix witness verified", details

        is_proj, reason, offending_entry = validate_projector(mat)
        if not is_proj:
            has_malformed_projector = True
            malformed_witness = {"term": term_idx, "reason": reason, "entry": offending_entry}
            break
        parsed_terms.append({"support": support, "matrix": mat})

    if has_malformed_projector:
        if ans_status != "OUT_OF_SCOPE":
            return False, f"Expected OUT_OF_SCOPE for non-projector term, got {ans_status}", details
        wit = answer.get("witness", {})
        if wit != malformed_witness:
            return (
                False,
                f"OUT_OF_SCOPE witness mismatch: expected {malformed_witness}, got {wit}",
                details,
            )
        return True, "OUT_OF_SCOPE certified for non-projector term", details

    # Check solved instances
    if ans_status != "SOLVED":
        return False, f"Expected SOLVED, got {ans_status}", details

    # Compute stacked matrix M = [P_1 (x) I; ...; P_m (x) I]
    stacked_rows: List[List[GaussianRat]] = []
    extended_terms: List[List[List[GaussianRat]]] = []
    for pt in parsed_terms:
        ext = extend_local_matrix(local_dims, pt["support"], pt["matrix"])
        extended_terms.append(ext)
        stacked_rows.extend(ext)

    # Independent check of exact rank and kernel dimension
    _, exact_rank, exact_kernel_basis = compute_rref_and_kernel(stacked_rows)
    expected_kernel_dim = total_d - exact_rank
    is_frustration_free = expected_kernel_dim > 0

    declared_ff = answer.get("frustration_free")
    if declared_ff != is_frustration_free:
        return (
            False,
            f"frustration_free mismatch: expected {is_frustration_free}, got {declared_ff}",
            details,
        )

    if is_frustration_free:
        # Frustration-free case: verify kernel basis
        declared_dim = answer.get("kernel_dim")
        if declared_dim != expected_kernel_dim:
            return (
                False,
                f"kernel_dim mismatch: expected {expected_kernel_dim}, got {declared_dim}",
                details,
            )

        basis_raw = answer.get("kernel_basis")
        if not isinstance(basis_raw, list) or len(basis_raw) != expected_kernel_dim:
            return (
                False,
                f"kernel_basis length mismatch: expected {expected_kernel_dim}, got {len(basis_raw) if isinstance(basis_raw, list) else type(basis_raw)}",
                details,
            )

        # Parse basis vectors
        parsed_basis: List[List[GaussianRat]] = []
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
                return False, f"Failed parsing basis vector {v_idx}: {ex}", details

            # 1. Annihilation: P_i (x) I * v == 0 for all terms
            for t_idx, ext_p in enumerate(extended_terms):
                for row_idx in range(total_d):
                    s = GaussianRat.zero()
                    for col_idx in range(total_d):
                        s = s + (ext_p[row_idx][col_idx] * v[col_idx])
                    if not s.is_zero():
                        return (
                            False,
                            f"Basis vector {v_idx} not annihilated by term {t_idx} at row {row_idx}: {s}",
                            details,
                        )
            parsed_basis.append(v)

        # 2. Linear independence: rank of parsed_basis must equal kernel_dim
        _, basis_rank, _ = compute_rref_and_kernel(parsed_basis)
        if basis_rank != expected_kernel_dim:
            return (
                False,
                f"Kernel basis vectors are linearly dependent: rank {basis_rank} != {expected_kernel_dim}",
                details,
            )

        return (
            True,
            f"Frustration-free certified: kernel_dim {expected_kernel_dim} verified",
            details,
        )

    else:
        # Frustrated case: verify left inverse L * M == I_D
        cert = answer.get("certificate")
        if not isinstance(cert, dict) or cert.get("kind") != "left_inverse":
            return (
                False,
                f"Expected left_inverse certificate for frustrated case, got {cert}",
                details,
            )

        mat_l_raw = cert.get("matrix")
        if not isinstance(mat_l_raw, list) or len(mat_l_raw) != total_d:
            return (
                False,
                f"Left inverse matrix rows mismatch: expected {total_d}, got {len(mat_l_raw) if isinstance(mat_l_raw, list) else type(mat_l_raw)}",
                details,
            )

        try:
            L = [[GaussianRat.from_wire(elem) for elem in row] for row in mat_l_raw]
        except Exception as ex:
            return False, f"Failed parsing left inverse matrix: {ex}", details

        if any(len(row) != len(stacked_rows) for row in L):
            return False, f"Left inverse columns mismatch: expected {len(stacked_rows)}", details

        # Verify L * M == I_D
        LM = mat_mul(L, stacked_rows)
        for i in range(total_d):
            for j in range(total_d):
                expected = GaussianRat.one() if i == j else GaussianRat.zero()
                if LM[i][j] != expected:
                    return (
                        False,
                        f"Left inverse verification failed at ({i}, {j}): {LM[i][j]} != {expected}",
                        details,
                    )

        return True, "Frustrated certified: exact left inverse verified", details
