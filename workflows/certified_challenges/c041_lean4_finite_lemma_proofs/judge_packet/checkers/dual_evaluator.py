# AuthorityEffect: None.
"""
Dual Evaluator for C041: Lean 4 Proofs of Hidden Finite Lemmas.

Passes (returns True) only when both checkers verify the same SOLVED kind (PROOF or
REFUTATION). Refusals are scored separately and never pass; the metadata carries an
``outcome`` in {VERIFIED_PROOF, VERIFIED_REFUTATION, ABSTAINED, WARRANTED_REFUSAL,
UNWARRANTED_REFUSAL, INFRA_ERROR, REJECTED, DIVERGENCE} and the ``lean --version`` in use.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_pkg_root = Path(__file__).resolve().parent.parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if p.name == "certified_challenges"), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from c041_lean4_finite_lemma_proofs.judge_packet.checkers.exact_checker import verify_exact  # noqa: E402
from c041_lean4_finite_lemma_proofs.judge_packet.checkers.independent_checker import verify_independent  # noqa: E402
from c041_lean4_finite_lemma_proofs.reference_solver.lean_compiler import lean_version  # noqa: E402

REFUSAL_OUTCOMES = frozenset({"ABSTAINED", "WARRANTED_REFUSAL", "UNWARRANTED_REFUSAL"})


def evaluate_dual(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Evaluates candidate answer against both checkers and enforces consensus."""
    exact_ok, exact_msg, exact_meta = verify_exact(case, answer)
    indep_ok, indep_msg, indep_meta = verify_independent(case, answer)
    status = answer.get("status") if isinstance(answer, dict) else None
    base = {
        "status": status,
        "lean_version": lean_version(),
        "exact": {"ok": exact_ok, "msg": exact_msg, "meta": exact_meta},
        "independent": {"ok": indep_ok, "msg": indep_msg, "meta": indep_meta},
    }
    exact_outcome = exact_meta.get("outcome")
    indep_outcome = indep_meta.get("outcome")

    if "INFRA_ERROR" in (exact_outcome, indep_outcome):
        return (
            False,
            "INFRA_ERROR: Lean could not be run; nothing was verified",
            {**base, "outcome": "INFRA_ERROR"},
        )

    if exact_ok != indep_ok:
        return (
            False,
            f"DIVERGENCE: exact={exact_ok} ('{exact_msg}') vs independent={indep_ok} ('{indep_msg}')",
            {
                **base,
                "outcome": "DIVERGENCE",
            },
        )

    if not exact_ok:
        if exact_outcome in REFUSAL_OUTCOMES:
            outcome = exact_outcome if exact_outcome == indep_outcome else "UNWARRANTED_REFUSAL"
            return (
                False,
                f"NOT VERIFIED (refusal scored separately): {exact_msg}",
                {**base, "outcome": outcome},
            )
        return False, f"REJECTED by both checkers: {exact_msg}", {**base, "outcome": "REJECTED"}

    if exact_meta.get("kind") != indep_meta.get("kind"):
        return (
            False,
            f"KIND_MISMATCH: exact={exact_meta.get('kind')} vs independent={indep_meta.get('kind')}",
            {
                **base,
                "outcome": "DIVERGENCE",
            },
        )

    return (
        True,
        "CONSENSUS_PASS: Both checkers verified the submission",
        {
            **base,
            "outcome": exact_outcome,
            "exact_meta": exact_meta,
            "indep_meta": indep_meta,
        },
    )
