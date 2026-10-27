# AuthorityEffect: None.
"""
Deterministic Tactic Portfolio (Arm E) for C041.

Executes a sequence of non-LLM, standard Lean 4 tactics:
1. `by decide` for PROOF.
2. `by decide` for REFUTATION.
3. `by rfl` for PROOF.
4. `by omega` for PROOF.
5. `by intro h; revert h; decide` for implication refutations.
6. Scripted bounded range-splitter tactics.

Returns structured candidate answer dict:
{
    "case_id": ...,
    "status": "SOLVED" | "UNKNOWN" | "OUT_OF_SCOPE",
    "kind": "PROOF" | "REFUTATION",
    "aux": [...],
    "proof": "...",
    "code": "..." (if UNKNOWN)
}

Every Lean run that times out or cannot start is retried once, and the pair of attempts is
classified:
- the retry runs: the first failure was a cold start or a transient fault; use the retry;
- both attempts time out: the tactic (or elaboration) needs more than its time limit. This is
  repeatable, so it is a budget abstention: UNKNOWN with code TACTIC_BUDGET_EXHAUSTED (tactics)
  or CASE_BUDGET_EXHAUSTED (the elaboration probe), never verified and never OUT_OF_SCOPE;
- otherwise (Lean could not start on the retry): UNKNOWN with code INFRA_ERROR and the
  diagnostics in "infra_errors". A rerun can recover this; it is not a property of the case.
The time limits are kept (5 s probe, 6 s per tactic); they are not raised, because a longer
wall-clock limit would still depend on the machine and would only move the boundary.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import (  # noqa: E402
    WHITELISTED_AXIOMS,
    LeanCompilationResult,
    compile_lean4_code,
)

INFRA_ERROR_CODE = "INFRA_ERROR"
TACTIC_BUDGET_CODE = "TACTIC_BUDGET_EXHAUSTED"
PROBE_BUDGET_CODE = "CASE_BUDGET_EXHAUSTED"

RAN = "RAN"
REPEATED_TIMEOUT = "REPEATED_TIMEOUT"
INFRA = "INFRA"


def _is_timeout(res: LeanCompilationResult) -> bool:
    return res.infra_error and res.return_code == -1


def _compile_with_retry(code: str, **kwargs: Any) -> Tuple[LeanCompilationResult, str]:
    """compile_lean4_code with one retry; returns the result and RAN, REPEATED_TIMEOUT or INFRA."""
    first = compile_lean4_code(code, **kwargs)
    if not first.infra_error:
        return first, RAN
    second = compile_lean4_code(code, **kwargs)
    if not second.infra_error:
        return second, RAN
    if _is_timeout(first) and _is_timeout(second):
        return second, REPEATED_TIMEOUT
    return second, INFRA


def _infra_answer(case_id: Any, errors: List[str]) -> Dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": INFRA_ERROR_CODE,
        "infra_errors": errors,
    }


CANDIDATE_PROOF_TACTICS = [
    "by decide",
    "by rfl",
    "by omega",
    "by simp",
    "by intro h; cases h <;> decide",
    "by intro; decide",
    "by intros; decide",
]

CANDIDATE_REFUTATION_TACTICS = [
    "by decide",
    "by intro h; revert h; decide",
    "by intro h; cases h <;> decide",
]


def test_candidate_tactic(
    case_id: str,
    prelude: str,
    statement: str,
    kind: str,
    proof_str: str,
    aux_list: Optional[List[str]] = None,
    timeout_sec: float = 8.0,
    infra_errors: Optional[List[str]] = None,
    timeouts: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Tests whether a candidate tactic closes the goal within the axiom whitelist.
    After one retry, an infrastructure failure is appended to ``infra_errors`` and a
    repeated timeout (the tactic's budget is exhausted) to ``timeouts``.
    """
    if aux_list is None:
        aux_list = []

    sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(case_id))
    thm_name = f"c41_{sanitized_id}"
    full_target_name = f"Submission.{thm_name}"

    target_prop = statement if kind == "PROOF" else f"¬ ({statement})"
    aux_block = "\n\n".join(aux_list)

    code = (
        f"{prelude}\n\n"
        f"namespace Submission\n"
        f"{aux_block}\n\n"
        f"theorem {thm_name} : {target_prop} := {proof_str}\n\n"
        f"#print axioms {thm_name}\n"
        f"end Submission\n"
    )

    res, outcome = _compile_with_retry(
        code, target_name=full_target_name, timeout_sec=timeout_sec, check_banned=True
    )
    if outcome == REPEATED_TIMEOUT:
        if timeouts is not None:
            timeouts.append(f"{kind}: {proof_str}")
        return False, []
    if outcome == INFRA:
        if infra_errors is not None:
            infra_errors.extend(res.errors)
        return False, []
    if res.success:
        disallowed = set(res.axioms) - WHITELISTED_AXIOMS
        if not disallowed:
            return True, res.axioms
    return False, []


def solve_deterministic(case: Dict[str, Any], timeout_per_tactic: float = 6.0) -> Dict[str, Any]:
    """
    Arm E deterministic solver. Searches tactic portfolio to prove or refute the case.
    """
    case_id = case.get("case_id") or case.get("id")
    statement = case.get("statement", "")
    prelude = case.get("prelude", "")

    # Quick syntax / prelude check
    probe = f"{prelude}\n#check ({statement})"
    res_probe, probe_outcome = _compile_with_retry(probe, timeout_sec=5.0, check_banned=False)
    if probe_outcome == REPEATED_TIMEOUT:
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": PROBE_BUDGET_CODE,
            "timed_out": ["elaboration probe"],
        }
    if probe_outcome == INFRA:
        return _infra_answer(case_id, res_probe.errors)
    if not res_probe.success:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "PRELUDE_OR_STATEMENT_DOES_NOT_ELABORATE"},
        }

    infra_errors: List[str] = []
    timeouts: List[str] = []

    # 1. Test candidate proof tactics
    for tactic in CANDIDATE_PROOF_TACTICS:
        ok, axioms = test_candidate_tactic(
            case_id=case_id,
            prelude=prelude,
            statement=statement,
            kind="PROOF",
            proof_str=tactic,
            timeout_sec=timeout_per_tactic,
            infra_errors=infra_errors,
            timeouts=timeouts,
        )
        if ok:
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "PROOF",
                "aux": [],
                "proof": tactic,
            }

    # 2. Test candidate refutation tactics
    for tactic in CANDIDATE_REFUTATION_TACTICS:
        ok, axioms = test_candidate_tactic(
            case_id=case_id,
            prelude=prelude,
            statement=statement,
            kind="REFUTATION",
            proof_str=tactic,
            timeout_sec=timeout_per_tactic,
            infra_errors=infra_errors,
            timeouts=timeouts,
        )
        if ok:
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "REFUTATION",
                "aux": [],
                "proof": tactic,
            }

    # 3. If standard tactics fail, return UNKNOWN. A tactic that could not run at all makes the
    #    result an infrastructure failure; a tactic that timed out on both attempts is a
    #    budget abstention.
    if infra_errors:
        return _infra_answer(case_id, infra_errors)
    if timeouts:
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": TACTIC_BUDGET_CODE,
            "timed_out": timeouts,
        }
    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": "DECIDE_HEARTBEAT_EXCEEDED",
    }
