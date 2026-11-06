"""Reference solver for C053: Bareiss Fraction-Free Matrix Inversion."""

from fractions import Fraction
from typing import Any, Dict, List

from .bareiss import (
    bareiss_determinant,
    compute_adjugate,
    find_null_vector,
    format_fraction,
    parse_fraction,
)


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "bf_unknown")

    # 1. Input schema validation
    if not isinstance(case, dict):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    matrix_raw = case.get("matrix")
    if not isinstance(matrix_raw, list):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MALFORMED_INPUT"},
        }

    n = len(matrix_raw)
    if n == 0:
        return {"case_id": case_id, "status": "OUT_OF_SCOPE", "witness": {"reason": "EMPTY_MATRIX"}}

    parsed_mat: List[List[Fraction]] = []
    for r_idx, row in enumerate(matrix_raw):
        if not isinstance(row, list) or len(row) != n:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "NOT_SQUARE", "row": r_idx},
            }
        parsed_row: List[Fraction] = []
        for c_idx, val in enumerate(row):
            try:
                parsed_row.append(parse_fraction(val))
            except Exception:
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"reason": "NON_NUMERIC_ENTRY", "row": r_idx, "col": c_idx},
                }
        parsed_mat.append(parsed_row)

    # 2. Compute exact determinant via Bareiss algorithm
    det = bareiss_determinant(parsed_mat)

    if det != 0:
        # Invertible
        adj = compute_adjugate(parsed_mat)
        inv = [[adj[r][c] / det for c in range(n)] for r in range(n)]

        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "INVERTIBLE",
            "det": format_fraction(det),
            "adjugate": [[format_fraction(val) for val in row] for row in adj],
            "inverse": [[format_fraction(val) for val in row] for row in inv],
        }
    else:
        # Singular: compute non-zero null vector
        null_vec = find_null_vector(parsed_mat)
        if null_vec is None:
            # Fallback trivial if all zero or edge case
            null_vec = [Fraction(1, 1)] + [Fraction(0, 1)] * (n - 1)

        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "SINGULAR",
            "det": "0",
            "null_vector": [format_fraction(val) for val in null_vec],
        }
