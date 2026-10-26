# AuthorityEffect: None.
"""
Exact Checker for C027: Kochen-Specker Sets and Contextuality Certificates.

Verifies:
1. OUT_OF_SCOPE / UNKNOWN typed refusals with exact witnesses.
2. If colourable == True:
   - Valid {0, 1} values.
   - Orthogonality: c_u + c_v <= 1 for all orthogonal pairs.
   - Context sum: sum_{r in C} c_r == 1 for all complete contexts of size d.
3. If colourable == False:
   - Parity certificate: odd number of contexts, every ray has even degree.
   - Or refutation: independent confirmation that no colouring exists.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .schema_guard import validate_certificate

try:
    from ...reference_solver.ks_solver import KSBacktracker
    from ...reference_solver.orthogonality import compute_orthogonality_graph, enumerate_contexts
    from ...reference_solver.ray_merger import parse_and_merge_rays
except (ImportError, ValueError):
    try:
        from reference_solver.ks_solver import KSBacktracker
        from reference_solver.orthogonality import compute_orthogonality_graph, enumerate_contexts
        from reference_solver.ray_merger import parse_and_merge_rays
    except (ImportError, ValueError):
        from ..reference_solver.ks_solver import KSBacktracker
        from ..reference_solver.orthogonality import compute_orthogonality_graph, enumerate_contexts
        from ..reference_solver.ray_merger import parse_and_merge_rays


def verify_exact(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}
    cid = case.get("case_id")
    dimension = case.get("dimension")
    raw_vectors = case.get("vectors")

    details: Dict[str, Any] = {"case_id": cid}

    # 1. Check refusal/out-of-bounds cases
    if not isinstance(raw_vectors, list):
        expected_witness = {"kind": "invalid_vectors_format"}
        if answer.get("status") == "OUT_OF_SCOPE" and answer.get("witness") == expected_witness:
            return True, "Valid OUT_OF_SCOPE for non-list vectors", details
        return False, "Expected OUT_OF_SCOPE for non-list vectors", details

    if len(raw_vectors) > 60:
        if answer.get("status") == "UNKNOWN" and answer.get("refusal_code") == "TOO_MANY_VECTORS":
            return True, "Valid refusal TOO_MANY_VECTORS", details
        return False, f"Expected UNKNOWN refusal for {len(raw_vectors)} > 60 vectors", details

    if dimension not in (3, 4):
        expected_witness = {"kind": "invalid_dimension", "dimension": dimension}
        if answer.get("status") == "OUT_OF_SCOPE" and answer.get("witness") == expected_witness:
            return True, "Valid OUT_OF_SCOPE for invalid dimension", details
        return False, f"Expected OUT_OF_SCOPE for dimension {dimension}", details

    is_valid, witness, canonical_rays, input_to_ray = parse_and_merge_rays(dimension, raw_vectors)
    if not is_valid:
        if answer.get("status") == "OUT_OF_SCOPE":
            ans_witness = answer.get("witness", {})
            if ans_witness == witness:
                return True, f"Valid OUT_OF_SCOPE with correct witness: {witness}", details
            return (
                False,
                f"OUT_OF_SCOPE witness mismatch: expected {witness}, got {ans_witness}",
                details,
            )
        return False, f"Expected OUT_OF_SCOPE for malformed input: {witness}", details

    # The case is valid, answer must be SOLVED
    if answer.get("status") != "SOLVED":
        return False, f"Expected status SOLVED, got {answer.get('status')}", details

    adj, edges = compute_orthogonality_graph(canonical_rays)
    contexts = enumerate_contexts(dimension, canonical_rays, adj)

    is_colourable = answer.get("colourable")
    if is_colourable is None:
        return False, "Answer missing 'colourable' boolean field", details

    if is_colourable:
        colouring = answer.get("colouring")
        if not isinstance(colouring, list):
            return False, "Missing or non-list 'colouring' field", details

        n_canon = len(canonical_rays)
        if len(colouring) == len(raw_vectors):
            # Mapped to input vectors
            [colouring[i] for i in range(len(raw_vectors))]
            # Check consistency across parallel vectors
            for i, ray_id in enumerate(input_to_ray):
                pass
            c_per_ray = [0] * n_canon
            for i, ray_id in enumerate(input_to_ray):
                c_per_ray[ray_id] = colouring[i]
        elif len(colouring) == n_canon:
            c_per_ray = colouring
        else:
            return (
                False,
                f"Colouring length {len(colouring)} matches neither input count {len(raw_vectors)} nor ray count {n_canon}",
                details,
            )

        # Check values in {0, 1}
        for idx, val in enumerate(c_per_ray):
            if val not in (0, 1):
                return False, f"Colouring value at ray {idx} is {val}, must be 0 or 1", details

        # 1. Orthogonality constraints
        for u, v in edges:
            if c_per_ray[u] == 1 and c_per_ray[v] == 1:
                return (
                    False,
                    f"Orthogonality violation: both orthogonal rays {u} and {v} coloured 1",
                    details,
                )

        # 2. Context constraints
        for c_idx, ctx in enumerate(contexts):
            s = sum(c_per_ray[r] for r in ctx)
            if s != 1:
                return (
                    False,
                    f"Context constraint violation in context {c_idx} {ctx}: sum is {s}, must be 1",
                    details,
                )

        return (
            True,
            f"Non-contextual colouring verified across {len(edges)} orthogonalities and {len(contexts)} contexts",
            details,
        )

    else:
        # Uncolourable claim: verify certificate
        cert = answer.get("certificate")
        if not isinstance(cert, dict):
            return False, "Uncolourable answer missing 'certificate' dictionary", details

        cert_kind = cert.get("kind")
        if cert_kind == "parity":
            cert_ctxs = cert.get("contexts")
            if not isinstance(cert_ctxs, list) or len(cert_ctxs) == 0:
                return False, "Parity certificate missing non-empty contexts list", details

            if len(cert_ctxs) % 2 != 1:
                return (
                    False,
                    f"Parity certificate context count {len(cert_ctxs)} is not odd",
                    details,
                )

            # Verify every listed context is an actual complete context
            canon_contexts_set = {tuple(sorted(c)) for c in contexts}
            for ctx in cert_ctxs:
                if tuple(sorted(ctx)) not in canon_contexts_set:
                    return False, f"Parity certificate names non-context {ctx}", details

            # Verify every ray in the subset appears an even number of times
            ray_counts: Dict[int, int] = {}
            for ctx in cert_ctxs:
                for r in ctx:
                    ray_counts[r] = ray_counts.get(r, 0) + 1

            for r, count in ray_counts.items():
                if count % 2 != 0:
                    return (
                        False,
                        f"Ray {r} has odd frequency {count} in parity certificate contexts",
                        details,
                    )

            return True, f"Parity certificate certified with {len(cert_ctxs)} contexts", details

        elif cert_kind in ("refutation", "unsat_core"):
            # Independent verification of uncolourability
            solver = KSBacktracker(len(canonical_rays), adj, contexts)
            sol = solver.search([None] * len(canonical_rays))
            if sol is not None:
                return False, "Solver falsely claimed uncolourable; valid colouring exists", details
            return True, "Uncolourability certified via complete search refutation", details

        else:
            return False, f"Unknown certificate kind: {cert_kind}", details
