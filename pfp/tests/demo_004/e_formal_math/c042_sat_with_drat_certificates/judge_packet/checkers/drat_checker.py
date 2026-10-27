# AuthorityEffect: None.
"""
DRAT Resolution Proof Checker for C042.
Checks:
1. Exact SHA-256 binding between judge's canonical CNF and submitted cnf_sha256.
2. Step-by-step RAT / RUP verification using drat_engine.
3. Terminal empty clause derivation.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.drat_engine import (
    compute_sha256,
    verify_drat_certificate,
)
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.family_solvers import (
    encode_coloring,
    encode_latin_square,
    encode_php,
    encode_tiling,
    encode_tseitin,
)
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.solver import (
    format_dimacs_cnf,
)


def get_canonical_cnf(case: Dict[str, Any]) -> Tuple[str, str]:
    """Retrieves or builds canonical CNF text and its SHA-256."""
    if "cnf_text" in case:
        cnf_text = case["cnf_text"]
        return cnf_text, compute_sha256(cnf_text)

    fam = case.get("family")
    if fam == "coloring":
        num_vars, clauses, _ = encode_coloring(case["n"], case["k"], case["edges"])
    elif fam == "php":
        num_vars, clauses, _ = encode_php(case["pigeons"], case["holes"], case.get("blocked"))
    elif fam == "latin_square":
        num_vars, clauses, _ = encode_latin_square(case["order"], case.get("prefilled", []))
    elif fam == "tseitin":
        num_vars, clauses, _ = encode_tseitin(case["vertices"], case["edges"], case["charges"])
    elif fam == "tiling":
        num_vars, clauses, _ = encode_tiling(
            case["rows"], case["cols"], case["tiles"], case.get("blocked")
        )
    else:
        raise ValueError(f"Unknown family: {fam}")

    cnf_text = format_dimacs_cnf(num_vars, clauses)
    return cnf_text, compute_sha256(cnf_text)


def _parse_dimacs(cnf_text: str) -> list[list[int]]:
    clauses: list[list[int]] = []
    for line in cnf_text.splitlines():
        line = line.strip()
        if not line or line.startswith(("c", "p")):
            continue
        lits = [int(tok) for tok in line.split()]
        if not lits or lits[-1] != 0:
            raise ValueError(f"DIMACS clause not terminated by 0: {line!r}")
        clauses.append(lits[:-1])
    return clauses


def trivial_refutation_reason(cnf_text: str) -> str | None:
    """EMPTY_CLAUSE or UNIT_PROPAGATION when the CNF is refuted without search, else None.

    For such a formula the one-line proof "0" is a valid DRAT refutation, so a verified
    UNSAT certificate on it is not evidence of solving anything.
    """
    clauses = _parse_dimacs(cnf_text)
    if any(len(c) == 0 for c in clauses):
        return "EMPTY_CLAUSE"
    assign: dict[int, bool] = {}
    changed = True
    while changed:
        changed = False
        for clause in clauses:
            if any(assign.get(abs(lit)) == (lit > 0) for lit in clause if abs(lit) in assign):
                continue
            free = [lit for lit in clause if abs(lit) not in assign]
            if not free:
                return "UNIT_PROPAGATION"
            if len(free) == 1:
                assign[abs(free[0])] = free[0] > 0
                changed = True
    return None


def check_drat_submission(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Checks an UNSAT DRAT certificate against the judge's canonical CNF."""
    proof_fmt = answer.get("proof_format")
    if proof_fmt != "DRAT":
        return False, f"Invalid proof_format: '{proof_fmt}'. Expected 'DRAT'.", {}

    submitted_hash = answer.get("cnf_sha256")
    cnf_text, expected_hash = get_canonical_cnf(case)

    if submitted_hash != expected_hash:
        return (
            False,
            f"CNF hash mismatch: submitted '{submitted_hash}', expected '{expected_hash}'",
            {},
        )

    proof_text = answer.get("proof_text", "")
    if not isinstance(proof_text, str) or not proof_text.strip():
        return False, "DRAT proof_text is empty or not string", {}

    # Verify proof against canonical CNF
    ok, msg = verify_drat_certificate(cnf_text, proof_text)
    if not ok:
        return False, f"DRAT verification failure: {msg}", {}

    meta: Dict[str, Any] = {"cnf_sha256": expected_hash, "drat_valid": True}
    trivial = trivial_refutation_reason(cnf_text)
    if trivial is not None:
        meta["trivial_refutation"] = trivial
    return True, f"DRAT proof verified: {msg}", meta
