# AuthorityEffect: None.
"""
Dual Evaluator for C042 SAT & DRAT Certificates.
Enforces 100% consensus between exact checkers and independent verification.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .drat_checker import check_drat_submission, get_canonical_cnf
from .sat_checker import check_sat_submission


def evaluate_dual(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates participant answer across dual checking seams.
    Returns: (consensus_pass, verdict_message, metadata)
    """
    status = answer.get("status")

    if status == "OUT_OF_SCOPE":
        # Warranted only when the judge cannot build the case's canonical CNF.
        witness = answer.get("witness")
        if not isinstance(witness, dict) or not witness.get("reason"):
            return False, "OUT_OF_SCOPE missing valid witness dict with 'reason'", {}
        try:
            get_canonical_cnf(case)
        except (KeyError, TypeError, ValueError):
            return (
                True,
                f"OUT_OF_SCOPE warranted: the case has no canonical CNF ({witness['reason']})",
                {"witness": witness},
            )
        return False, "OUT_OF_SCOPE on a well-formed case with a canonical CNF", {}

    elif status == "UNKNOWN":
        # An abstention is never a verified answer; it is reported separately.
        return (
            False,
            f"ABSTAINED: UNKNOWN ({answer.get('code', '')!r}) is not a verified answer",
            {"abstained": True},
        )

    elif status == "SOLVED":
        kind = answer.get("kind")
        if kind == "SAT":
            ok, msg, meta = check_sat_submission(case, answer)
            if not ok:
                return False, f"REJECTED by SAT checker: {msg}", meta
            return True, f"CONSENSUS_PASS: SAT certificate verified: {msg}", meta

        elif kind == "UNSAT":
            ok, msg, meta = check_drat_submission(case, answer)
            if not ok:
                return False, f"REJECTED by DRAT checker: {msg}", meta
            if meta.get("trivial_refutation"):
                # Correct, but "0" refutes this formula; never count it as evidence of solving.
                return (
                    True,
                    f"CONSENSUS_PASS (TRIVIAL {meta['trivial_refutation']}): UNSAT DRAT certificate verified: {msg}",
                    meta,
                )
            return True, f"CONSENSUS_PASS: UNSAT DRAT certificate verified: {msg}", meta

        else:
            return False, f"Invalid SOLVED kind: '{kind}'. Expected 'SAT' or 'UNSAT'.", {}

    else:
        return (
            False,
            f"Invalid status: '{status}'. Expected 'SOLVED', 'OUT_OF_SCOPE', or 'UNKNOWN'.",
            {},
        )
