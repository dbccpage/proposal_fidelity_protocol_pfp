"""Negative controls: the retraction turn loop refuses instead of bluffing.

Each test removes or breaks one measurement or judge and checks that the loop
reports a refusal, never a zero obstruction, a silent fallback, or a
convergence it did not reach. Fake ports stand in for the native host, so the
file runs without a Rust build.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pytest

from pfp.domain.bridge.sbe import SBEAnalyzer
from pfp.domain.models import StepVerdict, SymbolGameEnvelope
from pfp.domain.ports import exact_ports
from pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    Delta,
    Holds,
    NewInst,
    RegimeK,
    compute_obstruction_score,
    execute_retraction_turn,
    host,
    kinds,
    run_retraction_loop,
)
from pfp.domain.solvers.errors import SolverRefusal
from pfp.use_cases.symbol_turn_service import SymbolGameExecutionService


@dataclass(frozen=True)
class _FunctionalReq:
    """A requirement only the functional port can measure."""

    rid: str
    d0: tuple[int, ...] = (1,)
    d1: tuple[int, ...] = (1,)
    residual: tuple[int, ...] = (1,)


class _RaisingFunctionalPort:
    def evaluate(self, d0: object, d1: object, residual: object) -> object:
        raise RuntimeError("native functional crashed")


class _FakeRetractionPort:
    """Retraction judge whose answers the test controls."""

    def __init__(
        self,
        *,
        turn: Mapping[str, Any] | Exception | None = None,
        loop: Mapping[str, Any] | Exception | None = None,
    ) -> None:
        self._turn = turn if turn is not None else {"admitted": True}
        self._loop = loop
        self.loop_calls: list[dict[str, Any]] = []

    def retraction_turn(
        self,
        before: Mapping[str, int],
        after: Mapping[str, int],
        candidate: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if isinstance(self._turn, Exception):
            raise self._turn
        return self._turn

    def retraction_loop(
        self,
        intake: Mapping[str, int],
        candidates: Sequence[Mapping[str, Any]],
        open_obligations: int = 0,
    ) -> Mapping[str, Any]:
        self.loop_calls.append(
            {"intake": dict(intake), "candidates": list(candidates), "open": open_obligations}
        )
        if isinstance(self._loop, Exception):
            raise self._loop
        if self._loop is not None:
            return self._loop
        # Default: count strict descents the way the native engine does.
        current = (intake["gamma_2"], intake["phi_1"], intake["defect_count"])
        admitted = 0
        for c in candidates:
            t = c["triad"]
            nxt = (t["gamma_2"], t["phi_1"], t["defect_count"])
            if all(a <= b for a, b in zip(nxt, current)) and nxt != current:
                current = nxt
                admitted += 1
        return {"admitted": admitted}


@pytest.fixture(autouse=True)
def _no_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test with no functional or retraction port registered."""
    monkeypatch.setattr(kinds, "_GLOBAL_FUNCTIONAL_PORT", None)
    monkeypatch.setattr(kinds, "_GLOBAL_HOMOLOGY_PORT", kinds._UnboundHomologyPort())
    monkeypatch.setattr(kinds, "_GLOBAL_HOLONOMY_PORT", kinds._UnboundHolonomyPort())
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", None)


def _two_holds_state() -> RegimeK:
    return host(
        base_history=(AdmitDatum(0), AdmitDatum(1)),
        claim_forms=frozenset(),
        reqs=(Holds("r1", (0, (0,))), Holds("r2", (1, (1,)))),
        witness_forms=((1, ()), (1, ())),
    )


_D1: Delta = (NewInst(0, (0,)),)
_D2: Delta = (NewInst(1, (1,)),)


def _functional_state() -> RegimeK:
    return host(
        base_history=(AdmitDatum(0),),
        claim_forms=frozenset(),
        reqs=(_FunctionalReq("f1"),),  # type: ignore[arg-type]
    )


def test_missing_functional_port_refuses_instead_of_scoring_zero() -> None:
    with pytest.raises(SolverRefusal) as exc:
        compute_obstruction_score(_functional_state())
    assert exc.value.code == "FUNCTIONAL_PORT_REQUIRED"
    assert "f1" in exc.value.detail


def test_failing_functional_port_refuses_instead_of_scoring_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(kinds, "_GLOBAL_FUNCTIONAL_PORT", _RaisingFunctionalPort())
    with pytest.raises(SolverRefusal) as exc:
        compute_obstruction_score(_functional_state())
    assert exc.value.code == "FUNCTIONAL_EVALUATION_FAILED"
    assert "native functional crashed" in exc.value.detail


def test_retraction_port_error_is_a_refusal_not_a_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    port = _FakeRetractionPort(turn=RuntimeError("host died"))
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    state = _two_holds_state()
    out = execute_retraction_turn(
        task_id="t", turn_index=0, state=state, candidate_delta=_D1, stage=BASE
    )
    # The local check alone would have admitted this descent.
    assert out.new_score.strictly_improves(out.prior_score)
    assert out.verdict == StepVerdict.REFUSAL
    assert out.child_state is None
    assert "Retraction port failed: host died" in out.details


def test_retraction_port_refusal_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _FakeRetractionPort(turn={"admitted": False, "refusal": "LYAPUNOV_VIOLATION"})
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    out = execute_retraction_turn(
        task_id="t", turn_index=0, state=_two_holds_state(), candidate_delta=_D1, stage=BASE
    )
    assert out.verdict == StepVerdict.REFUSAL
    assert out.child_state is None
    assert "LYAPUNOV_VIOLATION" in out.details


def test_truthy_non_bool_admission_is_not_admission(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _FakeRetractionPort(turn={"admitted": "yes"})
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    out = execute_retraction_turn(
        task_id="t", turn_index=0, state=_two_holds_state(), candidate_delta=_D1, stage=BASE
    )
    assert out.verdict == StepVerdict.REFUSAL


def test_partial_descent_is_not_convergence() -> None:
    result = run_retraction_loop(
        task_id="partial", initial_state=_two_holds_state(), stage=BASE, candidate_deltas=(_D1,)
    )
    assert result.total_descent_steps == 1
    assert result.final_score.active_count == 1
    assert result.converged is False
    assert result.is_exact is False
    assert result.native_check == "NOT_RUN"


def test_loop_agrees_with_port_and_converges(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _FakeRetractionPort()
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    result = run_retraction_loop(
        task_id="full", initial_state=_two_holds_state(), stage=BASE, candidate_deltas=(_D1, _D2)
    )
    assert result.native_check == "AGREED"
    assert result.converged is True
    assert result.is_exact is True
    # Every triad shares one scale, and the port saw every turn.
    (call,) = port.loop_calls
    assert call["intake"]["defect_count"] == 2
    assert [c["triad"]["defect_count"] for c in call["candidates"]] == [1, 0]


def test_loop_disagreement_withholds_exactness(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _FakeRetractionPort(loop={"admitted": 1})
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    result = run_retraction_loop(
        task_id="disagree", initial_state=_two_holds_state(), stage=BASE, candidate_deltas=(_D1, _D2)
    )
    assert result.final_score.is_exact is True
    assert result.native_check.startswith("DISAGREED")
    assert result.converged is False
    assert result.is_exact is False


def test_loop_port_error_withholds_exactness(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _FakeRetractionPort(loop=RuntimeError("replay crashed"))
    monkeypatch.setattr(exact_ports, "_GLOBAL_RETRACTION_PORT", port)
    result = run_retraction_loop(
        task_id="err", initial_state=_two_holds_state(), stage=BASE, candidate_deltas=(_D1, _D2)
    )
    assert result.native_check == "REFUSED: replay crashed"
    assert result.converged is False
    assert result.is_exact is False


def test_text_purity_never_certifies_a_turn() -> None:
    service = SymbolGameExecutionService(SBEAnalyzer())
    outcome = service.execute_symbol_turn(
        SymbolGameEnvelope(task_id="purity_task", initial_input="retract discrete cochain")
    )
    # A single text is a pure state, so purity is 1.0; that is not exactness.
    assert outcome.purity > 0.5
    assert outcome.is_exact is False
    assert outcome.verdict == StepVerdict.HOLD
