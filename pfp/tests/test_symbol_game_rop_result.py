"""Unit tests for Railway-Oriented Programming (ROP) in pfp."""

from __future__ import annotations

import pytest

from pfp.controllers.symbol_game_engine import SymbolGameEngine
from pfp.domain.shared_kernel.result import (
    Result,
    ResultError,
    err,
    ok,
)


def test_rop_success_track() -> None:
    res: Result[int, str] = ok(10)
    assert res.is_success
    assert not res.is_failure
    assert res.unwrap() == 10
    assert res.unwrap_or(0) == 10

    # Test map
    mapped = res.map(lambda x: x * 2)
    assert mapped.unwrap() == 20

    # Test bind / and_then
    bound = res.bind(lambda x: ok(f"val: {x}"))
    assert bound.unwrap() == "val: 10"


def test_rop_failure_track() -> None:
    res: Result[int, str] = err("invalid_input")
    assert not res.is_success
    assert res.is_failure
    assert res.unwrap_or(42) == 42

    with pytest.raises(ResultError):
        res.unwrap()

    # Test map skips on failure
    mapped = res.map(lambda x: x * 2)
    assert mapped.is_failure
    assert mapped.unwrap_or(-1) == -1

    # Test map_err
    err_mapped = res.map_err(lambda e: f"error: {e}")
    assert err_mapped.error == "error: invalid_input"


def test_symbol_game_engine_rop_methods() -> None:
    engine = SymbolGameEngine()

    # Test evaluate_proposal_result on valid proposal
    res = engine.evaluate_proposal_result("prop_rop_1", 5.0, 2.0, effort=1.0)
    assert res.is_success
    eval_res = res.unwrap()
    assert eval_res.is_admissible
    assert eval_res.mass_drop == 3.0

    # Test execute_turn_result on valid turn
    turn_res = engine.execute_turn_result("task_rop_1", "Initial problem prompt")
    assert turn_res.is_success
    outcome = turn_res.unwrap()
    assert isinstance(outcome.step_id, str)



def test_rop_failure_keeps_the_typed_refusal_code_and_cause() -> None:
    """Counterexample: ``RustFunctionalRequired`` became ``DomainError(str(exc))``.

    The refusal code ``RUST_FUNCTIONAL_REQUIRED`` and the original exception were
    lost on the failure track, so a caller could not tell a refusal from a bug.
    """
    from pfp.domain.exceptions import TypedRefusalError
    from pfp.functional_boundary import RustFunctionalRequired

    engine = SymbolGameEngine()
    res = engine.solve_problem_result("a problem", task_id="rop_typed")
    assert res.is_failure
    assert type(res.error) is TypedRefusalError
    assert res.error.code == "RUST_FUNCTIONAL_REQUIRED"
    assert isinstance(res.error.cause, RustFunctionalRequired)
    assert res.error.__cause__ is res.error.cause


def test_rop_does_not_turn_a_defect_into_a_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exception without a refusal code is a defect: it propagates."""
    engine = SymbolGameEngine()

    def broken(**kwargs):
        raise KeyError("missing field")

    monkeypatch.setattr(engine, "solve_problem", broken)
    with pytest.raises(KeyError):
        engine.solve_problem_result("a problem")

    def refusing(**kwargs):
        from pfp.domain.exact.errors import ExactRefusal

        raise ExactRefusal("PORT_UNBOUND", "no adapter")

    monkeypatch.setattr(engine, "evaluate_proposal", refusing)
    res = engine.evaluate_proposal_result("p", 1.0, 0.0)
    assert res.is_failure
    assert getattr(res.error, "code", None) == "PORT_UNBOUND"
