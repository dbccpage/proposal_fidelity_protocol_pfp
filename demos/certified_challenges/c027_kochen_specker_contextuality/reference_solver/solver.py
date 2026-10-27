# AuthorityEffect: None.
"""
Reference Solver for C027: Kochen-Specker Sets and Contextuality Certificates.

Exposes:
    def solve(case: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .ddc_tracer import DDCTracer
    from .ks_solver import solve_contextuality
    from .orthogonality import compute_orthogonality_graph, enumerate_contexts
    from .ray_merger import parse_and_merge_rays
except (ImportError, ValueError):
    try:
        from c027_kochen_specker_contextuality.reference_solver.ddc_tracer import DDCTracer
        from c027_kochen_specker_contextuality.reference_solver.ks_solver import solve_contextuality
        from c027_kochen_specker_contextuality.reference_solver.orthogonality import compute_orthogonality_graph, enumerate_contexts
        from c027_kochen_specker_contextuality.reference_solver.ray_merger import parse_and_merge_rays
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from ks_solver import solve_contextuality
        from orthogonality import compute_orthogonality_graph, enumerate_contexts
        from ray_merger import parse_and_merge_rays


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decides non-contextual colourability of a set of rays in R^d over Q(sqrt(2)).
    Returns RFC 8785 canonical JSON response.
    """
    cid = case.get("case_id") or case.get("id") or "unknown_case"
    dimension = case.get("dimension")
    raw_vectors = case.get("vectors")

    tracer = DDCTracer(cid)

    # 1. Check vector count limit
    if not isinstance(raw_vectors, list):
        return {
            "id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_vectors_format"},
        }

    if len(raw_vectors) > 60:
        return {
            "id": cid,
            "status": "UNKNOWN",
            "refusal_code": "TOO_MANY_VECTORS",
        }

    # 2. Check dimension and parse rays
    if dimension not in (3, 4):
        return {
            "id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_dimension", "dimension": dimension},
        }

    is_valid, witness, canonical_rays, input_to_ray = parse_and_merge_rays(dimension, raw_vectors)
    if not is_valid:
        return {
            "id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": witness,
        }

    tracer.emit(
        "C",
        {
            "raw_vectors_count": len(raw_vectors),
            "canonical_rays_count": len(canonical_rays),
        },
    )

    # 3. Orthogonality graph and contexts
    adj, edges = compute_orthogonality_graph(canonical_rays)
    contexts = enumerate_contexts(dimension, canonical_rays, adj)

    tracer.emit(
        "I",
        {
            "edges_count": len(edges),
            "contexts_count": len(contexts),
        },
    )

    tracer.emit(
        "R",
        {
            "active_constraints": len(edges) + len(contexts),
            "unassigned_rays": len(canonical_rays),
        },
    )

    # 4. Solve contextuality
    colourable, colouring, cert = solve_contextuality(len(canonical_rays), adj, contexts)
    tracer.emit(
        "D",
        {
            "colourable": colourable,
        },
    )

    if colourable:
        tracer.emit(
            "E",
            {
                "verified_colouring_length": len(colouring) if colouring else 0,
            },
        )
        tracer.emit(
            "T",
            {
                "verdict": "SOLVED_COLOURABLE",
                "head_sha256": tracer.get_head_sha256(),
            },
        )
        return {
            "id": cid,
            "status": "SOLVED",
            "colourable": True,
            "colouring": colouring,
        }
    else:
        tracer.emit(
            "Lambda",
            {
                "certificate_kind": cert["kind"] if cert else "unknown",
            },
        )
        tracer.emit(
            "T",
            {
                "verdict": "SOLVED_UNCOLOURABLE",
                "head_sha256": tracer.get_head_sha256(),
            },
        )
        subset = (
            cert.get("subset", list(range(len(canonical_rays))))
            if cert
            else list(range(len(canonical_rays)))
        )
        return {
            "id": cid,
            "status": "SOLVED",
            "colourable": False,
            "subset": subset,
            "certificate": {
                "kind": cert.get("kind", "refutation") if cert else "refutation",
                "contexts": cert.get("contexts", []) if cert else [],
            },
        }
