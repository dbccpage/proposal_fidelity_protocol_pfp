"""Reference Solver for C015: Persistent Homology Barcodes with Reduction Certificates.

Input:
A filtered simplicial complex with up to 2000 simplices of dimension <= 3.
Simplices must be face-compatible and non-decreasing in filtration value.

Output:
status SOLVED with index pairs, essential classes, value barcodes, and sparse R/V certificates,
or OUT_OF_SCOPE with witness of face violation,
or UNKNOWN refusal.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any

from .ddc_tracer import DDCTracer
from .persistence_reduction import extract_pairing_and_barcodes, reduce_boundary_matrix


def parse_fraction(val: Any) -> Fraction | None:
    try:
        return Fraction(str(val))
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def solve(case: dict[str, Any]) -> tuple[dict[str, Any], DDCTracer]:
    tracer = DDCTracer()
    case_id = str(case.get("id", "c015_unknown"))
    tracer.record_step("E", "init_solver", payload={"case_id": case_id})

    # Validate simplices list
    raw_simplices = case.get("simplices")
    if not isinstance(raw_simplices, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "simplices must be a list",
        }
        tracer.record_step(
            "M", "refusal_missing_simplices", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    n = len(raw_simplices)
    if n > 2000:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "SIMPLEX_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "SIMPLEX_COUNT_OUT_OF_BOUNDS",
            "count": n,
        }
        tracer.record_step(
            "M",
            "refusal_simplex_count",
            payload=refusal,
            refusal_reason="SIMPLEX_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse and validate each simplex
    parsed_simplices: list[dict[str, Any]] = []
    seen_simplices: dict[tuple[int, ...], int] = {}
    prev_val: Fraction | None = None

    for idx, s in enumerate(raw_simplices):
        if not isinstance(s, dict):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"simplex {idx} is not a dict",
            }
            tracer.record_step(
                "M", "refusal_simplex_dict", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        dim = s.get("dim")
        raw_verts = s.get("vertices")
        raw_val = s.get("val")

        if dim is None or raw_verts is None or raw_val is None:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"simplex {idx} missing dim, vertices, or val",
            }
            tracer.record_step(
                "M", "refusal_simplex_fields", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        try:
            dim_int = int(dim)
        except (ValueError, TypeError):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
            }
            tracer.record_step(
                "M", "refusal_dim_type", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if dim_int > 3 or dim_int < 0:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "DIMENSION_OUT_OF_BOUNDS",
                "refusal_code": "DIMENSION_OUT_OF_BOUNDS",
                "dimension": dim_int,
            }
            tracer.record_step(
                "M", "refusal_dim_bound", payload=refusal, refusal_reason="DIMENSION_OUT_OF_BOUNDS"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if not isinstance(raw_verts, (list, tuple)) or len(raw_verts) != dim_int + 1:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"vertices length {len(raw_verts) if isinstance(raw_verts, list) else None} != dim+1 for simplex {idx}",
            }
            tracer.record_step(
                "M", "refusal_verts_length", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        try:
            verts = tuple(sorted(int(v) for v in raw_verts))
        except (ValueError, TypeError):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
            }
            tracer.record_step(
                "M", "refusal_vert_values", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if len(set(verts)) != len(verts):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"duplicate vertices in simplex {idx}",
            }
            tracer.record_step(
                "M", "refusal_duplicate_verts", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        val_frac = parse_fraction(raw_val)
        if val_frac is None:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"invalid rational filtration value {raw_val!r}",
            }
            tracer.record_step(
                "M", "refusal_val_fraction", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        # Check non-decreasing filtration values
        if prev_val is not None and val_frac < prev_val:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "NON_MONOTONIC_FILTRATION",
                "refusal_code": "NON_MONOTONIC_FILTRATION",
                "details": f"filtration value decreased at simplex {idx}: {val_frac} < {prev_val}",
            }
            tracer.record_step(
                "M",
                "refusal_monotonicity",
                payload=refusal,
                refusal_reason="NON_MONOTONIC_FILTRATION",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        prev_val = val_frac

        # Check face compatibility: every codimension-1 face must appear earlier
        if dim_int > 0:
            for face_verts in itertools.combinations(verts, dim_int):
                if face_verts not in seen_simplices:
                    # Face missing earlier! OUT_OF_SCOPE with witness
                    s_id = str(s.get("id", idx))
                    face_str = "[" + ", ".join(str(v) for v in face_verts) + "]"
                    out_of_scope = {
                        "id": case_id,
                        "status": "OUT_OF_SCOPE",
                        "witness": {
                            "simplex": s_id,
                            "missing_earlier_face": face_str,
                        },
                    }
                    tracer.record_step(
                        "I",
                        "face_compatibility_failure",
                        payload=out_of_scope,
                    )
                    tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
                    return out_of_scope, tracer

        seen_simplices[verts] = idx
        parsed_simplices.append(
            {
                "id": idx,
                "dim": dim_int,
                "vertices": verts,
                "val": str(val_frac),
            }
        )

    tracer.record_step("C", "simplices_validated", payload={"count": n})

    # Construct boundary matrix D over F2
    D_cols: list[set[int]] = []
    for j, s in enumerate(parsed_simplices):
        col_j: set[int] = set()
        dim_j = s["dim"]
        if dim_j > 0:
            for face_verts in itertools.combinations(s["vertices"], dim_j):
                face_idx = seen_simplices[face_verts]
                col_j.add(face_idx)
        D_cols.append(col_j)

    tracer.record_step("I", "boundary_matrix_constructed", payload={"n": n})

    # Perform matrix reduction R = D * V over F2
    R_cols, V_cols, low_map = reduce_boundary_matrix(D_cols, n)
    tracer.record_step(
        "D", "reduction_completed", payload={"unreduced_count": 0, "pairs_found": len(low_map)}
    )

    # Extract pairs, essential classes, and value barcodes
    pairs, essential, barcode = extract_pairing_and_barcodes(
        parsed_simplices, low_map, n, R_cols, D_cols
    )

    # Format certificate columns (sparse lists of row indices as strings)
    r_cols_json = {str(k): [str(r) for r in sorted(R_cols[k])] for k in sorted(R_cols.keys())}
    v_cols_json = {str(k): [str(r) for r in sorted(V_cols[k])] for k in sorted(V_cols.keys())}

    result = {
        "id": case_id,
        "status": "SOLVED",
        "pairs": pairs,
        "essential": essential,
        "barcode": barcode,
        "R_columns": r_cols_json,
        "V_columns": v_cols_json,
    }

    tracer.record_step("T", "terminal_pass", payload=result)
    return result, tracer
