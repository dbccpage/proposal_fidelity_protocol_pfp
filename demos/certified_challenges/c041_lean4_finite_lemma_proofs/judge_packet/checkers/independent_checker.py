# AuthorityEffect: None.
"""
Independent Second Checker for C041: Lean 4 Proofs of Hidden Finite Lemmas.

1. Clean elaboration of the target proposition on its own, without submission text.
2. The submission is compiled separately and audited from a judge-written file that checks
   the theorem against a judge-written copy of the target and prints its axioms
   (``verify_submission``); the axiom closure must be a subset of {propext, Quot.sound}.
3. Refusals (UNKNOWN, OUT_OF_SCOPE) are never verified: this checker returns False for them
   and reports whether an OUT_OF_SCOPE claim is warranted.

It shares the Lean toolchain wrapper with the exact checker (a known limit of independence).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_pkg_root = Path(__file__).resolve().parent.parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if p.name == "certified_challenges"), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import (  # noqa: E402
    WHITELISTED_AXIOMS,
    compile_lean4_code,
    lean_version,
    verify_submission,
)


def verify_independent(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Independent second verification; True only for a verified PROOF or REFUTATION."""
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
        probe = f"{prelude}\n\ndef _clean_probe : Prop := ({statement})\n"
        res_probe = compile_lean4_code(probe, timeout_sec=10.0, check_banned=False)
        if res_probe.infra_error:
            outcome = "INFRA_ERROR"
        elif res_probe.success:
            outcome = "UNWARRANTED_REFUSAL"
        else:
            outcome = "WARRANTED_REFUSAL"
        return (
            False,
            f"Refusal, not a verified proof ({outcome})",
            {
                "status": status,
                "outcome": outcome,
                "lean_version": lean_version(),
            },
        )

    if status == "UNKNOWN":
        return (
            False,
            "ABSTAINED: independent checker never verifies UNKNOWN",
            {
                "status": status,
                "outcome": "ABSTAINED",
                "code": answer.get("code") or answer.get("refusal_code"),
            },
        )

    kind = answer.get("kind")
    if kind not in {"PROOF", "REFUTATION"}:
        return False, f"Invalid kind: '{kind}'", {"outcome": "REJECTED"}

    proof = answer.get("proof", "")
    if not isinstance(proof, str) or not proof.strip():
        return False, "Empty or non-string proof body in SOLVED answer", {"outcome": "REJECTED"}

    aux_list = answer.get("aux", [])
    if not isinstance(aux_list, list) or any(not isinstance(a, str) for a in aux_list):
        return False, "aux must be a list of strings", {"outcome": "REJECTED"}

    clean_prop_stmt = statement if kind == "PROOF" else f"¬ ({statement})"
    res_spec = compile_lean4_code(
        f"{prelude}\n\ndef ExpectedTargetProp : Prop := {clean_prop_stmt}\n",
        timeout_sec=15.0,
        check_banned=False,
    )
    if res_spec.infra_error:
        return (
            False,
            f"INFRA_ERROR: Lean could not be run: {res_spec.errors}",
            {"outcome": "INFRA_ERROR", "lean_version": lean_version()},
        )
    if not res_spec.success:
        return (
            False,
            f"Target proposition fails clean elaboration: {res_spec.stderr.strip()}",
            {"outcome": "REJECTED"},
        )

    sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(case_id))
    thm_name = f"c41_{sanitized_id}"
    full_target_name = f"Submission.{thm_name}"

    res = verify_submission(prelude, aux_list, thm_name, clean_prop_stmt, proof, timeout_sec=30.0)
    meta: Dict[str, Any] = {"status": status, "lean_version": res.lean_version}
    if res.infra_error:
        meta["outcome"] = "INFRA_ERROR"
        return False, f"INFRA_ERROR: Lean could not be run: {res.errors}", meta
    if not res.success:
        err = res.errors[0] if res.errors else "Independent Lean compilation failed"
        meta.update(outcome="REJECTED", errors=res.errors)
        return False, f"Independent verification failed: {err}", meta

    disallowed_axioms = set(res.axioms) - WHITELISTED_AXIOMS
    if disallowed_axioms:
        meta.update(outcome="REJECTED", axioms=res.axioms)
        return False, f"Independent check found illicit axioms: {sorted(disallowed_axioms)}", meta

    meta.update(outcome=f"VERIFIED_{kind}", axioms=res.axioms, kind=kind, target=full_target_name)
    return (
        True,
        "Independent verification succeeded: judge-file type check and whitelisted axioms",
        meta,
    )
