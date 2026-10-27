"""Actual Python-to-native QDDC integration and adversarial wire contracts."""

from __future__ import annotations

import copy
import json

import pytest
from pydantic import ValidationError

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operating_system.adapters.rust_host.majorana_math import (
    NativeMathRefusal,
    call_native,
)
from pfp.domain.homology.qddc import (
    DeformationRequest,
    DensityRequest,
    LindbladRequest,
    Operator,
    ProbeRequest,
    QddcState,
    RationalMatrix,
    RetractionRequest,
)
from pfp.infrastructure.adapters.qddc_rust_adapter import NativeQddc


def matrix(rows: list[list[str]], cols: int | None = None) -> dict:
    return {"rows": len(rows), "cols": len(rows[0]) if rows else cols, "data": rows}


def operator(a: str, b: str, c: str, d: str) -> Operator:
    return Operator.model_validate_json(
        json.dumps({"real": matrix([[a, b], [c, d]]), "imag": matrix([["0", "0"], ["0", "0"]])})
    )


def circle() -> QddcState:
    return QddcState.model_validate_json(
        json.dumps(
            {
                "d_prev": matrix([["-1", "1", "0"], ["-1", "0", "1"], ["0", "-1", "1"]]),
                "d_next": matrix([], 3),
                "operator_dim": 2,
                "cochain": [
                    operator("1", "0", "0", "-1").model_dump(mode="json"),
                    operator("-1", "0", "0", "1").model_dump(mode="json"),
                    operator("1", "0", "0", "-1").model_dump(mode="json"),
                ],
            }
        )
    )


def test_hodge_and_finite_deformation_through_native_process():
    port = NativeQddc()
    state = circle()
    result = port.hodge(state)
    assert result.harmonic == state.cochain
    repair = port.repair_projector(state).projector
    assert repair.real.data == (
        ("2/3", "1/3", "-1/3"),
        ("1/3", "2/3", "1/3"),
        ("-1/3", "1/3", "2/3"),
    )
    zero = operator("0", "0", "0", "0")
    assert result.exact == (zero, zero, zero)
    rotated = port.deform(
        DeformationRequest(
            state=state, alpha=(zero, zero, zero), unitary=operator("0", "1", "1", "0")
        )
    )
    assert rotated.cochain[0] == state.cochain[1]
    assert (
        port.hodge(QddcState(**{**dict(state), "cochain": rotated.cochain})).harmonic
        == rotated.cochain
    )


def test_density_generator_retraction_and_selected_probe():
    port = NativeQddc()
    excited = operator("0", "0", "0", "1")
    zero = operator("0", "0", "0", "0")
    derivative = port.lindblad(
        LindbladRequest(rho=excited, hamiltonian=zero, jumps=(operator("0", "1", "0", "0"),))
    )
    assert derivative.derivative == operator("1", "0", "0", "-1")
    ground = operator("1", "0", "0", "0")
    output = port.retract(RetractionRequest(rho=excited, projector=ground, eta="1/3"))
    assert output.rho == operator("1/3", "0", "0", "2/3")
    assert (output.outside_before, output.outside_after) == ("1", "2/3")
    full = port.retract(RetractionRequest(rho=excited, projector=ground, eta="1"))
    assert full.rho == ground
    assert port.density(DensityRequest(rho=ground)).is_pure
    branch = port.probe(ProbeRequest(rho=excited, projector=ground))
    assert branch.probability == "0" and branch.conditional is None
    mixed = operator("1/2", "0", "0", "1/2")
    assert port.density(DensityRequest(rho=mixed)).purity == "1/2"


@pytest.mark.parametrize("value", [True, 1, 0.5, "1/1", "02", "-0", "2/4", "1/0", "0.5", "1e2"])
def test_python_and_native_reject_noncanonical_coefficients(value):
    wire = operator("1", "0", "0", "0").model_dump(mode="json")
    wire["real"]["data"][0][0] = value
    with pytest.raises(ValidationError):
        Operator.model_validate_json(json.dumps(wire))
    with pytest.raises(NativeMathRefusal, match="QDDC_REFUSED"):
        call_native("qddc_density", {"rho": wire})


@pytest.mark.parametrize(
    "field,value", [("rows", True), ("cols", -1), ("rows", 33), ("data", []), ("extra", 1)]
)
def test_shape_and_unknown_fields_fail_closed(field, value):
    wire = operator("1", "0", "0", "0").model_dump(mode="json")
    wire["real"][field] = value
    with pytest.raises(ValidationError):
        Operator.model_validate_json(json.dumps(wire))
    with pytest.raises(NativeMathRefusal):
        call_native("qddc_density", {"rho": wire})


@pytest.mark.parametrize("rho", [("2", "0", "0", "-1"), ("1", "1", "0", "0"), ("1", "0", "0", "1")])
def test_density_shape_is_not_a_mathematical_certificate(rho):
    with pytest.raises(NativeMathRefusal, match="QDDC_REFUSED"):
        NativeQddc().density(DensityRequest(rho=operator(*rho)))


def test_chain_law_is_checked_even_for_zero_cochains():
    wire = circle().model_dump(mode="json")
    wire["d_next"] = matrix([["1", "0", "0"]])
    wire["cochain"] = [operator("0", "0", "0", "0").model_dump(mode="json") for _ in range(3)]
    with pytest.raises(NativeMathRefusal, match="d1\\*d0"):
        NativeQddc().hodge(QddcState.model_validate_json(json.dumps(wire)))


@pytest.mark.parametrize("eta", ["-1", "2", str(2**256)])
def test_step_parameter_and_bit_bound_refusals(eta):
    with pytest.raises(NativeMathRefusal):
        NativeQddc().retract(
            RetractionRequest(
                rho=operator("0", "0", "0", "1"), projector=operator("1", "0", "0", "0"), eta=eta
            )
        )


def test_nested_models_are_immutable_and_unknown_authority_is_refused():
    state = circle()
    with pytest.raises(ValidationError):
        state.operator_dim = 1
    with pytest.raises(TypeError):
        state.d_prev.data[0][0] = "0"
    zero = RationalMatrix(rows=0, cols=0, data=())
    empty = QddcState(d_prev=zero, d_next=zero, operator_dim=1, cochain=())
    assert NativeQddc().hodge(empty).harmonic == ()
    wire = copy.deepcopy(circle().model_dump(mode="json"))
    wire["authority_effect"] = "Admit"
    with pytest.raises(NativeMathRefusal):
        call_native("qddc_hodge", wire)


def test_missing_native_host_has_no_python_solver_fallback(tmp_path):
    port = NativeQddc(RustSymbolGameHost(binary=tmp_path / "absent-native-host"))
    with pytest.raises(NativeMathRefusal):
        port.hodge(circle())
