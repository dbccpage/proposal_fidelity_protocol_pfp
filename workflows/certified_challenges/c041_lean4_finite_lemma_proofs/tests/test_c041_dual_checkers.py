# AuthorityEffect: None.
"""Tests for Exact and Independent Dual Checkers in C041."""

from c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual


def test_dual_evaluator_valid_proof():
    case = {
        "case_id": "test_c_01",
        "statement": "∀ a : Fin 4, a + 0 = a",
        "prelude": "",
    }
    ans = {
        "case_id": "test_c_01",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": [],
        "proof": "by decide",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is True
    assert meta["status"] == "SOLVED"


def test_dual_evaluator_rejects_sorry():
    case = {
        "case_id": "test_c_sorry",
        "statement": "1 + 1 = 3",
        "prelude": "",
    }
    ans = {
        "case_id": "test_c_sorry",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": [],
        "proof": "by sorry",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is False


def test_dual_evaluator_rejects_native_decide():
    case = {
        "case_id": "test_c_native",
        "statement": "1 + 1 = 2",
        "prelude": "",
    }
    ans = {
        "case_id": "test_c_native",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": [],
        "proof": "by native_decide",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is False


def test_dual_evaluator_rejects_illicit_aux():
    case = {
        "case_id": "test_c_aux",
        "statement": "1 + 1 = 2",
        "prelude": "",
    }
    ans = {
        "case_id": "test_c_aux",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": ["axiom illicit_oracle : 1 = 1"],
        "proof": "by decide",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is False


def test_dual_evaluator_rejects_id_mismatch():
    case = {
        "case_id": "test_id_orig",
        "statement": "1 + 1 = 2",
        "prelude": "",
    }
    ans = {
        "case_id": "test_id_other",
        "status": "SOLVED",
        "kind": "PROOF",
        "aux": [],
        "proof": "by decide",
    }
    ok, msg, meta = evaluate_dual(case, ans)
    assert ok is False
