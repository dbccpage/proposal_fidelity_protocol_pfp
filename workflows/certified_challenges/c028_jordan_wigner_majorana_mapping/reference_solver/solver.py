# AuthorityEffect: None.
"""
Reference Solver for C028: Fermion-to-Qubit Mappings with Exact CAR Checks.

Exposes:
    def solve(case: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .ddc_tracer import DDCTracer
    from .fermion_term_expander import expand_hamiltonian
    from .majorana_mapper import compute_majorana_operators
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer
    from fermion_term_expander import expand_hamiltonian
    from majorana_mapper import compute_majorana_operators


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves a C028 case.
    """
    case_id = str(case.get("id") or case.get("case_id", "unknown"))
    tracer = DDCTracer(case_id)

    num_modes = case.get("num_modes", 0)
    encoding = case.get("encoding", [])
    terms = case.get("terms", [])

    # Check bounds
    if num_modes > 12:
        tracer.emit("M", {"refusal_code": "TOO_MANY_MODES", "num_modes": num_modes})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "TOO_MANY_MODES",
        }

    tracer.emit(
        "C",
        {
            "num_modes": num_modes,
            "encoding_dim": [len(encoding), len(encoding[0]) if encoding else 0],
            "num_terms": len(terms),
        },
    )

    # Step 1: Compute Majorana operators from encoding matrix M
    tracer.emit("I", {"step": "compute_majoranas"})
    is_valid_m, majoranas, m_witness = compute_majorana_operators(num_modes, encoding)
    if not is_valid_m:
        tracer.emit("R", {"kind": m_witness.get("kind"), "details": m_witness})
        tracer.emit("M", {"status": "OUT_OF_SCOPE", "witness": m_witness})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": m_witness,
        }

    tracer.emit("E", {"majoranas_count": len(majoranas)})

    # Step 2: Expand fermionic Hamiltonian terms into qubit Pauli strings
    tracer.emit("I", {"step": "expand_hamiltonian"})
    is_herm, pauli_terms, h_witness = expand_hamiltonian(num_modes, majoranas, terms)
    if not is_herm:
        tracer.emit("R", {"kind": h_witness.get("kind"), "details": h_witness})
        tracer.emit("M", {"status": "OUT_OF_SCOPE", "witness": h_witness})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": h_witness,
        }

    tracer.emit("D", {"cleared_imaginary_residuals": True})
    tracer.emit("E", {"pauli_terms_count": len(pauli_terms)})
    tracer.emit("T", {"terminal_status": "SOLVED"})

    return {
        "id": case_id,
        "status": "SOLVED",
        "majoranas": majoranas,
        "hamiltonian": [[p, coeff] for p, coeff in pauli_terms],
    }
