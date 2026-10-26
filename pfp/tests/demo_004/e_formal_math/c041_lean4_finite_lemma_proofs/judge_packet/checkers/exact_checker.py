# AuthorityEffect: None.
"""
Exact Checker for C041: Lean 4 Proofs of Hidden Finite Lemmas.

Only a SOLVED answer can be verified. Refusals are scored separately and never count as
verified proofs:

1. Schema: case_id match; status in {SOLVED, UNKNOWN, OUT_OF_SCOPE}.
2. SOLVED: kind in {PROOF, REFUTATION}; the target is `statement` or `¬ (statement)`;
   auxiliary declarations must start with theorem, def or lemma and carry no forbidden
   modifier; the submission is checked by ``verify_submission`` (separate compile, judge-
   written type check and ``#print axioms``); the axiom closure must be a subset of
   {propext, Quot.sound}. Returns True only here.
3. UNKNOWN: an abstention. Returns False with outcome ABSTAINED.
4. OUT_OF_SCOPE: returns False. The outcome is WARRANTED_REFUSAL when the prelude or the
   statement fails to elaborate with a Lean diagnostic, UNWARRANTED_REFUSAL when both
   elaborate, and INFRA_ERROR when Lean could not be run (a missing or timed-out Lean never
   warrants a refusal).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_pkg_root = Path(__file__).resolve().parent.parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import (  # noqa: E402
    WHITELISTED_AXIOMS,
    compile_lean4_code,
    lean_version,
    verify_submission,
)

RECOGNIZED_UNKNOWN_CODES = frozenset(
    {
        "CASE_BUDGET_EXHAUSTED",
        "DECIDE_HEARTBEAT_EXCEEDED",
        "SEARCH_LIMIT_REACHED",
        "TACTIC_BUDGET_EXHAUSTED",
        "UNSUPPORTED_FAMILY",
    }
)


def validate_auxiliary_declarations(aux_list: List[str]) -> Tuple[bool, str]:
    """
    Auxiliary declarations may only use `theorem` and non-`partial`, safe `def`.
    Disallows `axiom`, `opaque`, `unsafe`, `partial`, `instance`, `macro`, `syntax`, etc.
    """
    for idx, decl in enumerate(aux_list):
        if not isinstance(decl, str):
            return False, f"Aux declaration {idx} is not a string."
        cleaned = re.sub(r"--[^\n]*", " ", decl).strip()
        if not cleaned:
            continue
        first_token = cleaned.split()[0] if cleaned.split() else ""
        if first_token not in {"theorem", "def", "lemma"}:
            return (
                False,
                f"Aux declaration {idx} has invalid head command '{first_token}'. Allowed: theorem, def, lemma.",
            )
        if any(bad in decl for bad in ["partial ", "unsafe ", "axiom ", "opaque ", "instance "]):
            return False, f"Aux declaration {idx} contains forbidden declaration modifier."
    return True, ""


def audit_refusal(prelude: str, statement: str) -> Tuple[str, str]:
    """Classifies an OUT_OF_SCOPE claim: WARRANTED_REFUSAL, UNWARRANTED_REFUSAL or INFRA_ERROR."""
    res_prelude = compile_lean4_code(prelude, timeout_sec=10.0, check_banned=False)
    if res_prelude.infra_error:
        return "INFRA_ERROR", f"Lean could not be run: {res_prelude.errors}"
    if not res_prelude.success:
        return "WARRANTED_REFUSAL", "prelude does not elaborate"
    res_stmt = compile_lean4_code(
        f"{prelude}\n#check ({statement})", timeout_sec=10.0, check_banned=False
    )
    if res_stmt.infra_error:
        return "INFRA_ERROR", f"Lean could not be run: {res_stmt.errors}"
    if not res_stmt.success:
        return "WARRANTED_REFUSAL", "statement does not elaborate"
    return "UNWARRANTED_REFUSAL", "prelude and statement elaborate successfully"


def verify_exact(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes exact verification of C041 candidate answer against Lean 4 kernel.
    Returns True only for a kernel-verified PROOF or REFUTATION.
    """
    if not isinstance(case, dict) or not isinstance(answer, dict):
        return False, "Case and answer must be objects", {"outcome": "REJECTED"}
    case_id = case.get("case_id") or case.get("id")
    ans_id = answer.get("case_id") or answer.get("id")
    if ans_id != case_id:
        return (
            False,
            f"ID mismatch: case has '{case_id}', answer has '{ans_id}'",
            {"outcome": "REJECTED"},
        )

    status = answer.get("status")
    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:
        return False, f"Invalid status: '{status}'", {"status": status, "outcome": "REJECTED"}

    prelude = case.get("prelude", "")
    statement = case.get("statement", "")

    if status == "OUT_OF_SCOPE":
        outcome, detail = audit_refusal(prelude, statement)
        return (
            False,
            f"Refusal, not a verified proof ({outcome}: {detail})",
            {
                "status": status,
                "outcome": outcome,
                "lean_version": lean_version(),
            },
        )

    if status == "UNKNOWN":
        code = answer.get("code") or answer.get("refusal_code")
        return (
            False,
            f"ABSTAINED: UNKNOWN ({code!r}) is not a verified proof",
            {
                "status": status,
                "outcome": "ABSTAINED",
                "code": code,
                "code_recognized": code in RECOGNIZED_UNKNOWN_CODES,
            },
        )

    kind = answer.get("kind")
    if kind not in {"PROOF", "REFUTATION"}:
        return (
            False,
            f"Invalid kind for SOLVED: '{kind}'. Expected PROOF or REFUTATION.",
            {"outcome": "REJECTED"},
        )

    proof = answer.get("proof", "")
    if not isinstance(proof, str) or not proof.strip():
        return False, "Empty or non-string proof body in SOLVED answer", {"outcome": "REJECTED"}

    aux_list = answer.get("aux", [])
    if not isinstance(aux_list, list):
        return False, "aux must be a list of declaration strings", {"outcome": "REJECTED"}

    aux_ok, aux_msg = validate_auxiliary_declarations(aux_list)
    if not aux_ok:
        return False, f"Auxiliary validation failure: {aux_msg}", {"outcome": "REJECTED"}

    target_prop = statement if kind == "PROOF" else f"¬ ({statement})"
    sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(case_id))
    thm_name = f"c41_{sanitized_id}"
    full_target_name = f"Submission.{thm_name}"

    res = verify_submission(prelude, aux_list, thm_name, target_prop, proof, timeout_sec=30.0)
    meta: Dict[str, Any] = {"status": status, "lean_version": res.lean_version}
    if res.infra_error:
        meta["outcome"] = "INFRA_ERROR"
        return False, f"INFRA_ERROR: Lean could not be run: {res.errors}", meta
    if not res.success:
        detail = res.errors[0] if res.errors else "Lean compilation failed"
        meta.update(outcome="REJECTED", errors=res.errors)
        return False, f"Lean verification failed: {detail}", meta

    disallowed_axioms = set(res.axioms) - WHITELISTED_AXIOMS
    if disallowed_axioms:
        meta.update(outcome="REJECTED", axioms=res.axioms)
        return False, f"Illicit axioms detected: {sorted(disallowed_axioms)}", meta

    meta.update(outcome=f"VERIFIED_{kind}", axioms=res.axioms, kind=kind, target=full_target_name)
    return True, "Proof kernel-verified with whitelisted axioms", meta
