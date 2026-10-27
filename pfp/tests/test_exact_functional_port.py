"""The Symbol Game reaches Phi1/Gamma2 only through the native functional port.

No test here computes a named functional in Python. The scripted host checks the
adapter's refusal paths without a binary; the live checks skip when the native
host is not built, like the rest of the seam suite.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from operations.domain.rop.result import Ok
from operating_system.adapters.rust_host.ffi import locate_host_binary
from pfp.domain.exact.errors import ExactError
from pfp.domain.value_objects.functional_receipt import FunctionalReceipt
from pfp.fixtures.gate11_residual_dual import (
    frozen_fixtures,
    host_verify_self,
    k0_d0,
    k0_d1,
)
from pfp.infrastructure.adapters.exact_rust_adapter import (
    RustExactEngineAdapter,
)

_DIGEST = "41e19d465ffca9dd0195682314ffba74f7abf11ad9c832c358fad96b8b4fa8b4"


def _receipt(**changes: Any) -> FunctionalReceipt:
    base = FunctionalReceipt(
        input_digest=_DIGEST,
        phi1=Fraction(2),
        gamma2=Fraction(0),
        diagnostic_class="ClosedResidual",
        dual_witness=(Fraction(0), Fraction(1)),
        primal_residual=(Fraction(1), Fraction(1)),
        second_stage_repairs="none",
    )
    return replace(base, **changes)


def test_receipt_equality_is_exact_type_equality() -> None:
    class Relabelled(FunctionalReceipt):
        __slots__ = ()

    a, b = _receipt(), _receipt()
    assert a == b and hash(a) == hash(b)
    assert a != Relabelled(**{f: getattr(a, f) for f in a.__dataclass_fields__})


@pytest.mark.parametrize(
    "changes",
    [
        {"phi1": 2.0},
        {"gamma2": Fraction(-1)},
        {"input_digest": "not-a-digest"},
        {"diagnostic_class": "Green"},
        {"second_stage_repairs": "some"},
        {"authority_effect": "Granted"},
        {"dual_witness": [Fraction(0)]},
    ],
)
def test_receipt_refuses_values_the_host_never_issues(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        _receipt(**changes)


class _ScriptedHost:
    """Records calls; answers with a fixed native outcome."""

    def __init__(self, outcome: dict[str, Any]) -> None:
        self.calls: list[Any] = []
        self._outcome = outcome

    def functional_evaluate(self, payload: Any) -> Ok:
        self.calls.append(payload)
        return Ok(self._outcome)


def test_a_native_refusal_reaches_the_caller_with_its_code() -> None:
    host = _ScriptedHost({"success": False, "error": "CHAIN_LAW_VIOLATED: d1 * d0 != 0"})
    with pytest.raises(ExactError) as caught:
        RustExactEngineAdapter(host=host).evaluate(k0_d0(), k0_d1(), [Fraction(0)] * 5)
    assert caught.value.code == "CHAIN_LAW_VIOLATED"


def test_a_float_is_refused_before_the_host_is_asked() -> None:
    host = _ScriptedHost({"success": True, "result": {}})
    with pytest.raises(ExactError) as caught:
        RustExactEngineAdapter(host=host).evaluate(k0_d0(), k0_d1(), [0.0, 0, 1, 1, 0])
    assert caught.value.code == "THEORY_REQUEST_NOT_EXACT"
    assert host.calls == []


def test_a_missing_binary_is_a_typed_refusal_with_its_reason(monkeypatch) -> None:
    def absent() -> Any:
        raise FileNotFoundError("HOST_BINARY_NOT_FOUND: not built")

    monkeypatch.setattr("pfp.ffi.get_default_host", absent)
    adapter = RustExactEngineAdapter()
    with pytest.raises(ExactError) as caught:
        adapter.evaluate(k0_d0(), k0_d1(), [Fraction(0)] * 5)
    assert caught.value.code == "HOST_UNAVAILABLE"
    assert "HOST_BINARY_NOT_FOUND" in caught.value.detail


def test_a_wiring_defect_is_not_swallowed_as_a_missing_host(monkeypatch) -> None:
    def broken() -> Any:
        raise RuntimeError("defect")

    monkeypatch.setattr("pfp.ffi.get_default_host", broken)
    with pytest.raises(RuntimeError):
        RustExactEngineAdapter()


def test_the_boundary_law_is_never_granted_to_an_unchecked_object() -> None:
    with pytest.raises(ExactError) as caught:
        RustExactEngineAdapter(host=object()).verify_boundary_law(42)
    assert caught.value.code == "INVALID_COMPLEX_DESCRIPTOR"


def _live_adapter() -> RustExactEngineAdapter:
    located = locate_host_binary()
    if located.is_err:
        pytest.skip(f"native host not built: {located.error.code}")
    return RustExactEngineAdapter()


def test_live_k0_fixtures_are_classified_by_core_functional() -> None:
    adapter = _live_adapter()
    expected = {
        "Exact": "ExactRepair",
        "StabilizedSurvivor": "ClosedResidual",
        "OpenObstruction": "ActiveClosureFailure",
    }
    for fixture in frozen_fixtures():
        receipt = adapter.evaluate(k0_d0(), k0_d1(), fixture.omega)
        assert receipt.diagnostic_class == expected[fixture.name]
        assert (receipt.phi1, receipt.gamma2) == (fixture.phi, fixture.gamma)


def test_live_gate11_self_replays_every_fixture(tmp_path: Path) -> None:
    from pfp.entrypoints.cli.symbol_game import main

    record = host_verify_self(_live_adapter())
    assert record["overall_passed"] is True
    assert record["functional_owner"] == "engine/crates_rs/core_functional"
    assert main(["gate11-self", "--out-dir", str(tmp_path)]) == 0
    assert (tmp_path / "host_record.json").exists()
