# AuthorityEffect: None.
"""
Frozen Reference Solver for C042 SAT Encodings with DRAT Certificates.
Exposes:
  def solve(case: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from c042_sat_with_drat_certificates.reference_solver.ddc_tracer import DDCTracer
from c042_sat_with_drat_certificates.reference_solver.drat_engine import compute_sha256, parse_dimacs_cnf
from c042_sat_with_drat_certificates.reference_solver.family_solvers import (
    decode_coloring,
    decode_latin_square,
    decode_php,
    decode_tiling,
    decode_tseitin,
    encode_coloring,
    encode_latin_square,
    encode_php,
    encode_tiling,
    encode_tseitin,
)
from c042_sat_with_drat_certificates.reference_solver.sat_solver import solve_cnf


def validate_case_boundaries(case: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detects poisoned / out-of-scope test cases."""
    fam = case.get("family")
    case_id = case.get("case_id", "unknown")

    # Check DIMACS header if cnf_text provided
    if "cnf_text" in case:
        cnf_text = case["cnf_text"]
        lines = [
            line.strip()
            for line in cnf_text.splitlines()
            if line.strip() and not line.startswith("c")
        ]
        for idx, line in enumerate(lines, 1):
            if line.startswith("p cnf"):
                parts = line.split()
                if len(parts) >= 4:
                    expected_c = int(parts[3])
                    actual_c = sum(
                        1 for l in lines[idx:] if not l.startswith("c") and not l.startswith("p")
                    )
                    if expected_c != actual_c:
                        return {
                            "case_id": case_id,
                            "status": "OUT_OF_SCOPE",
                            "witness": {
                                "field": "cnf_header",
                                "reason": "CLAUSE_COUNT_MISMATCH",
                                "line": idx,
                            },
                        }
                break

    valid_fams = {"coloring", "php", "latin_square", "tseitin", "tiling"}
    if fam not in valid_fams:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "family", "reason": f"UNSUPPORTED_FAMILY_{fam}"},
        }

    # Family-specific boundary checks
    if fam == "coloring":
        n = case.get("n", 0)
        edges = case.get("edges", [])
        for e_idx, edge in enumerate(edges):
            if not isinstance(edge, list) or len(edge) != 2:
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"edges[{e_idx}]", "reason": "MALFORMED_EDGE"},
                }
            u, v = edge
            if u < 0 or u >= n or v < 0 or v >= n:
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"edges[{e_idx}]", "reason": "VERTEX_OUT_OF_RANGE"},
                }

    elif fam == "php":
        p = case.get("pigeons", 0)
        h = case.get("holes", 0)
        if p <= 0 or h <= 0:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"field": "pigeons_holes", "reason": "NON_POSITIVE_DIMENSION"},
            }

    elif fam == "tseitin":
        v_count = case.get("vertices", 0)
        edges = case.get("edges", [])
        for e_idx, edge in enumerate(edges):
            if not isinstance(edge, list) or len(edge) != 2:
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"edges[{e_idx}]", "reason": "MALFORMED_EDGE"},
                }
            u, v = edge
            if u < 0 or u >= v_count or v < 0 or v >= v_count:
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"edges[{e_idx}]", "reason": "VERTEX_OUT_OF_RANGE"},
                }

    elif fam == "tiling":
        tiles = case.get("tiles", [])
        for t_idx, tile in enumerate(tiles):
            if not isinstance(tile, list):
                return {
                    "case_id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"tiles[{t_idx}]", "reason": "MALFORMED_TILE"},
                }

    return None


def format_dimacs_cnf(num_vars: int, clauses: List[List[int]]) -> str:
    """Formats CNF clauses into standard DIMACS string."""
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for c in clauses:
        lines.append(" ".join(map(str, c)) + " 0")
    return "\n".join(lines)


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main frozen solver entrypoint.
    Returns RFC 8785 conforming dictionary.
    """
    case_id = case.get("case_id", "unknown")
    tracer = DDCTracer(case_id)
    tracer.record("C", "Problem case and canonical specification loaded")

    # 1. Scope and sanity validation
    oos = validate_case_boundaries(case)
    if oos is not None:
        tracer.record("M", "Case rejected as out of scope")
        oos["ddc_trace"] = tracer.trace_letters()
        return oos

    tracer.record("I", "Case invariants checked and verified valid")
    fam = case.get("family")

    # 2. Encode to canonical CNF
    tracer.record("Λ", f"Lifting problem into canonical CNF for family {fam}")
    num_vars = 0
    clauses: List[List[int]] = []
    decoder_meta: Any = None

    if "cnf_text" in case:
        num_vars, clauses, cnf_sha256 = parse_dimacs_cnf(case["cnf_text"])
    else:
        if fam == "coloring":
            num_vars, clauses, var_map = encode_coloring(case["n"], case["k"], case["edges"])
            decoder_meta = var_map
        elif fam == "php":
            num_vars, clauses, var_map = encode_php(
                case["pigeons"], case["holes"], case.get("blocked")
            )
            decoder_meta = var_map
        elif fam == "latin_square":
            num_vars, clauses, var_map = encode_latin_square(
                case["order"], case.get("prefilled", [])
            )
            decoder_meta = var_map
        elif fam == "tseitin":
            num_vars, clauses, edge_map = encode_tseitin(
                case["vertices"], case["edges"], case["charges"]
            )
            decoder_meta = edge_map
        elif fam == "tiling":
            num_vars, clauses, tile_var = encode_tiling(
                case["rows"], case["cols"], case["tiles"], case.get("blocked")
            )
            decoder_meta = tile_var
        else:
            return {"case_id": case_id, "status": "UNKNOWN", "code": f"UNSUPPORTED_FAMILY_{fam}"}

        cnf_text = format_dimacs_cnf(num_vars, clauses)
        cnf_sha256 = compute_sha256(cnf_text)

    # 3. Solve CNF
    tracer.record("D", f"Solving CNF with {num_vars} variables and {len(clauses)} clauses")
    is_sat, model, drat_proof = solve_cnf(num_vars, clauses)

    if is_sat and model is not None:
        tracer.record("E", "Satisfying assignment found; decoding to problem domain")
        if fam == "coloring":
            sol = decode_coloring(case["n"], case["k"], model, decoder_meta)
        elif fam == "php":
            sol = decode_php(case["pigeons"], case["holes"], model, decoder_meta)
        elif fam == "latin_square":
            sol = decode_latin_square(case["order"], model, decoder_meta)
        elif fam == "tseitin":
            sol = decode_tseitin(len(case["edges"]), model)
        elif fam == "tiling":
            sol = decode_tiling(len(case["tiles"]), model)
        else:
            sol = {"raw_model": [model.get(i, 0) for i in range(1, num_vars + 1)]}

        tracer.record("T", "Terminal verification complete")
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "SAT",
            "solution": sol,
            "ddc_trace": tracer.trace_letters(),
        }

    else:
        tracer.record("E", "Formula proved unsatisfiable; DRAT certificate generated")
        tracer.record("T", "Terminal verification complete")
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "UNSAT",
            "proof_format": "DRAT",
            "proof_text": drat_proof,
            "cnf_sha256": cnf_sha256,
            "ddc_trace": tracer.trace_letters(),
        }
