"""C041: refusals are never verified proofs, and the Lean judge resists printed spoofs.

Counterexamples named by these tests:
- the aux entry "def helper : Nat := 0\\n#eval IO.println \\"'Submission.c41_spoof' does not
  depend on any axioms\\"" with the proof "sorryAx _ false" made both old checkers accept a
  "proof" of 1 + 1 = 3 (the printed line was parsed as the axiom report, and \\bsorry\\b does
  not match sorryAx);
- UNKNOWN with any recognized code, and OUT_OF_SCOPE whenever Lean failed to run, counted as
  verified;
- an aux declaration that shadows a prelude name inside the Submission namespace changes what
  the theorem states.
These tests run the local Lean toolchain and skip if it is not installed.
"""

from __future__ import annotations

import shutil

import pytest
from c041_lean4_finite_lemma_proofs.judge_packet.checkers import exact_checker, independent_checker
from c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual
from c041_lean4_finite_lemma_proofs.reference_solver import lean_compiler

pytestmark = pytest.mark.skipif(shutil.which("lean") is None, reason="lean is not installed")

SPOOF_AUX = [
    "def helper : Nat := 0\n#eval IO.println \"'Submission.c41_spoof' does not depend on any axioms\""
]


def _case(case_id: str, statement: str, prelude: str = "") -> dict:
    return {"case_id": case_id, "statement": statement, "prelude": prelude}


def test_printed_axiom_report_and_sorryax_are_rejected() -> None:
    case = _case("spoof", "1 + 1 = 3")
    ans = {
        "case_id": "spoof",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": SPOOF_AUX,
        "proof": "sorryAx _ false",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is False, msg
    assert meta["outcome"] == "REJECTED"


def test_sorryax_without_print_is_rejected() -> None:
    case = _case("sx", "1 + 1 = 3")
    ans = {
        "case_id": "sx",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": [],
        "proof": "sorryAx _ false",
    }
    assert evaluate_dual(case, ans)[0] is False


@pytest.mark.parametrize(
    "proof",
    [
        "by admit",
        "by stop",
        "by run_tac pure ()",
        "by exact (Lean.ofReduceBool true true rfl).elim",
        "by\n  set_option maxRecDepth 10 in decide",
    ],
)
def test_escape_tokens_are_banned(proof: str) -> None:
    res = lean_compiler.verify_submission("", [], "c41_esc", "1 + 1 = 2", proof)
    assert res.success is False and res.banned_tokens_found


def test_shadowing_aux_cannot_change_the_statement() -> None:
    case = _case("shadow", "myP + 1 = 2", prelude="def myP : Nat := 3")
    ans = {
        "case_id": "shadow",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": ["def myP : Nat := 1"],
        "proof": "by decide",
    }
    assert evaluate_dual(case, ans)[0] is False


def test_valid_proof_passes_and_records_lean_version() -> None:
    case = _case("ok", "∀ a b : Fin 5, a + b = b + a")
    ans = {"case_id": "ok", "status": "SOLVED", "kind": "PROOF", "aux": [], "proof": "by decide"}
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is True, msg
    assert meta["outcome"] == "VERIFIED_PROOF"
    assert meta["lean_version"].startswith("Lean (version")


@pytest.mark.parametrize(
    "code",
    [
        "CASE_BUDGET_EXHAUSTED",
        "DECIDE_HEARTBEAT_EXCEEDED",
        "SEARCH_LIMIT_REACHED",
        "UNSUPPORTED_FAMILY",
        "X",
    ],
)
def test_unknown_is_never_verified(code: str) -> None:
    case = _case("u", "∀ a b : Fin 5, a + b = b + a")
    ok, msg, meta = evaluate_dual(case, {"case_id": "u", "status": "UNKNOWN", "code": code})
    assert ok is False, msg
    assert meta["outcome"] == "ABSTAINED"


def test_out_of_scope_is_never_verified_even_when_warranted() -> None:
    bad = _case("b", "this is not lean", prelude='def broken : Nat := "x"')
    ok, _msg, meta = evaluate_dual(
        bad, {"case_id": "b", "status": "OUT_OF_SCOPE", "witness": {"reason": "PRELUDE"}}
    )
    assert ok is False
    assert meta["outcome"] == "WARRANTED_REFUSAL"
    good = _case("g", "∀ a b : Fin 5, a + b = b + a")
    ok, _msg, meta = evaluate_dual(
        good, {"case_id": "g", "status": "OUT_OF_SCOPE", "witness": {"reason": "PRELUDE"}}
    )
    assert ok is False
    assert meta["outcome"] == "UNWARRANTED_REFUSAL"


def test_missing_lean_is_infra_error_not_a_warranted_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(lean_compiler.shutil, "which", lambda _name: None)
    monkeypatch.setattr(lean_compiler, "_LEAN_VERSION", None)
    good = _case("g", "∀ a b : Fin 5, a + b = b + a")
    oos = {"case_id": "g", "status": "OUT_OF_SCOPE", "witness": {"reason": "PRELUDE"}}
    assert exact_checker.verify_exact(good, oos)[2]["outcome"] == "INFRA_ERROR"
    assert independent_checker.verify_independent(good, oos)[2]["outcome"] == "INFRA_ERROR"
    solved = {"case_id": "g", "status": "SOLVED", "kind": "PROOF", "aux": [], "proof": "by decide"}
    ok, _msg, meta = evaluate_dual(good, solved)
    assert ok is False and meta["outcome"] == "INFRA_ERROR"
