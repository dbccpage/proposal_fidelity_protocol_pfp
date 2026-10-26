"""C041 reference portfolio: tell infrastructure failures apart from repeatable timeouts.

Counterexamples named by these tests:
- a cold Lean start made the elaboration probe time out once, and the portfolio answered
  OUT_OF_SCOPE, so the reference label depended on machine warmth;
- after the first fix every timeout became INFRA_ERROR, so c041_base_05 (distributivity over
  Fin 19, whose `decide` times out on every attempt) could never be labelled by a rerun.
A timeout on both attempts is now a budget abstention (TACTIC_BUDGET_EXHAUSTED, or
CASE_BUDGET_EXHAUSTED for the probe); only a Lean that cannot start on the retry is
INFRA_ERROR. Lean is replaced by a stub here; no Lean process runs.
"""

from __future__ import annotations

import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.judge_packet.checkers.exact_checker import verify_exact
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver import lean_compiler, tactic_portfolio


def _ok() -> lean_compiler.LeanCompilationResult:
    return lean_compiler.LeanCompilationResult(
        success=True,
        return_code=0,
        stdout="",
        stderr="",
        axioms=[],
        errors=[],
        warnings=[],
    )


def _timeout() -> lean_compiler.LeanCompilationResult:
    return lean_compiler.LeanCompilationResult(
        success=False,
        return_code=-1,
        stdout="",
        stderr="",
        axioms=[],
        errors=["TIMEOUT: Execution exceeded time limit"],
        warnings=[],
        infra_error=True,
    )


def _no_start() -> lean_compiler.LeanCompilationResult:
    return lean_compiler.LeanCompilationResult(
        success=False,
        return_code=-2,
        stdout="",
        stderr="",
        axioms=[],
        errors=["SYSTEM_ERROR: lean could not start"],
        warnings=[],
        infra_error=True,
    )


def _elab_error() -> lean_compiler.LeanCompilationResult:
    return lean_compiler.LeanCompilationResult(
        success=False,
        return_code=1,
        stdout="",
        stderr="",
        axioms=[],
        errors=["<stdin>:1:0: error: unknown identifier"],
        warnings=[],
    )


CASE = {
    "case_id": "c041_base_05",
    "statement": "∀ a b c : Fin 19, a * (b + c) = a * b + a * c",
    "prelude": "",
}


def _install(monkeypatch: pytest.MonkeyPatch, fn) -> list[str]:
    calls: list[str] = []

    def stub(code, **_kw):
        calls.append(code)
        return fn(code, len(calls))

    monkeypatch.setattr(tactic_portfolio, "compile_lean4_code", stub)
    return calls


def test_every_attempt_times_out_is_a_budget_abstention_not_infra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub Lean that times out on every attempt, probe included."""
    calls = _install(monkeypatch, lambda code, n: _timeout())
    ans = tactic_portfolio.solve_deterministic(CASE)
    assert ans["status"] == "UNKNOWN"
    assert ans["code"] == "CASE_BUDGET_EXHAUSTED"
    assert len(calls) == 2  # the probe and its one retry


def test_heavy_tactic_times_out_on_every_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Probe elaborates; every tactic times out on both attempts (the c041_base_05 pattern)."""
    calls = _install(monkeypatch, lambda code, n: _ok() if "#check" in code else _timeout())
    ans = tactic_portfolio.solve_deterministic(CASE)
    assert ans["status"] == "UNKNOWN"
    assert ans["code"] == "TACTIC_BUDGET_EXHAUSTED"
    tactics = len(tactic_portfolio.CANDIDATE_PROOF_TACTICS) + len(
        tactic_portfolio.CANDIDATE_REFUTATION_TACTICS
    )
    assert len(calls) == 1 + 2 * tactics
    ok, _msg, meta = verify_exact(CASE, ans)
    assert ok is False and meta["outcome"] == "ABSTAINED" and meta["code_recognized"] is True


def test_cold_probe_fails_once_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install(monkeypatch, lambda code, n: _timeout() if n == 1 else _ok())
    ans = tactic_portfolio.solve_deterministic(CASE)
    assert ans["status"] == "SOLVED"
    assert ans["proof"] == "by decide"
    assert len(calls) == 3


def test_lean_that_cannot_start_is_infra_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, lambda code, n: _no_start())
    ans = tactic_portfolio.solve_deterministic(CASE)
    assert ans["status"] == "UNKNOWN"
    assert ans["code"] == "INFRA_ERROR"


def test_timeout_then_start_failure_is_infra_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, lambda code, n: _timeout() if n == 1 else _no_start())
    assert tactic_portfolio.solve_deterministic(CASE)["code"] == "INFRA_ERROR"


def test_genuine_elaboration_failure_is_still_out_of_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, lambda code, n: _elab_error())
    assert tactic_portfolio.solve_deterministic(CASE)["status"] == "OUT_OF_SCOPE"
