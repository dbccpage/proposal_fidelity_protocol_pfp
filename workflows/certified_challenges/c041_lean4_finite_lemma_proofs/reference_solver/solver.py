# AuthorityEffect: None.
"""
Frozen Reference Solver for C041: Lean 4 Proofs of Hidden Finite Lemmas.

API Contract:
  def solve(case: Dict[str, Any]) -> Dict[str, Any]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if p.name == "certified_challenges"), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c041_lean4_finite_lemma_proofs.reference_solver.ddc_tracer import LeanProofDdcTracer
from c041_lean4_finite_lemma_proofs.reference_solver.tactic_portfolio import solve_deterministic


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves a C041 Lean 4 finite lemma case, maintaining DDC trace.
    """
    case_id = case.get("case_id") or case.get("id")
    tracer = LeanProofDdcTracer(case_id=case_id)

    # Step C: Context initialization
    tracer.record(
        letter="C",
        action="initialize_case_context",
        phi1=1,
        active_count=0,
        details={"case_id": case_id, "has_prelude": bool(case.get("prelude"))},
    )

    # Step I: Initial deterministic portfolio proposal
    tracer.record(
        letter="I",
        action="propose_tactic_portfolio",
        phi1=1,
        active_count=0,
    )

    # Execute deterministic solve
    ans = solve_deterministic(case)
    status = ans.get("status")

    if status == "SOLVED":
        tracer.record(
            letter="D",
            action="tactic_descent",
            phi1=0,
            active_count=0,
            details={"kind": ans.get("kind"), "tactic": ans.get("proof")},
        )
        tracer.record(
            letter="E",
            action="exact_closure_verified",
            phi1=0,
            active_count=0,
        )
        tracer.record(
            letter="T",
            action="terminal_commitment",
            phi1=0,
            active_count=0,
        )
    elif status == "OUT_OF_SCOPE":
        tracer.record(
            letter="M",
            action="refusal_out_of_scope",
            phi1=1,
            active_count=0,
            details=ans.get("witness", {}),
        )
        tracer.record(
            letter="T",
            action="terminal_commitment",
            phi1=1,
            active_count=0,
        )
    else:  # UNKNOWN
        tracer.record(
            letter="M",
            action="refusal_budget_or_heartbeat_exhausted",
            phi1=1,
            active_count=0,
            details={"code": ans.get("code")},
        )
        tracer.record(
            letter="T",
            action="terminal_commitment",
            phi1=1,
            active_count=0,
        )

    ans["ddc_trace"] = tracer.get_trace_string()
    return ans
