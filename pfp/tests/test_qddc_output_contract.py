"""Compiled-host output limits and explicitly nonconforming reply fixtures."""

from __future__ import annotations

import copy
import json
from fractions import Fraction
from itertools import combinations

import pytest
from pydantic import ValidationError

from omega_engine_operating_system.adapters.rust_host.majorana_math import (
    NativeMathRefusal,
    call_native,
)
from omega_engine_operations.domain.rop.result import Ok
from omega_engine_pfp.domain.homology.qddc import (
    DeformationRequest,
    DensityRequest,
    LindbladRequest,
    Operator,
    ProbeRequest,
    QddcState,
    RationalMatrix,
    RetractionRequest,
)
from omega_engine_pfp.infrastructure.adapters.qddc_rust_adapter import NativeQddc


def operator(rows: list[list[str]]) -> Operator:
    n = len(rows)
    return Operator(
        real=RationalMatrix(rows=n, cols=n, data=tuple(tuple(row) for row in rows)),
        imag=RationalMatrix(rows=n, cols=n, data=(("0",) * n,) * n),
    )


def prime_power_denominators() -> tuple[int, ...]:
    values = []
    for prime in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61):
        power = 1
        while (power * prime).bit_length() <= 255:
            power *= prime
        values.append(power)
    return tuple(values)


def assert_native_output_refusal(method: str, request) -> None:
    # These inputs fit both the scalar input gate and the runtime wire budget.
    wire = json.dumps(
        {
            "schema_version": "omega.symbol-game.runtime-request.v1",
            "action": f"qddc_{method}",
            "payload": request.model_dump(mode="json"),
        }
    )
    assert len(wire.encode()) < 65_536
    with pytest.raises(NativeMathRefusal, match="QDDC_OUTPUT_LIMIT") as caught:
        getattr(NativeQddc(), method)(request)
    refusal = caught.value
    assert refusal.code == "NATIVE_MATH_REFUSED"
    assert refusal.outcome["schema_version"] == "omega.symbol-game.runtime-outcome.v1"
    assert refusal.outcome["action"] == f"qddc_{method}"
    assert refusal.outcome["success"] is False
    assert refusal.outcome["result"] is None
    assert refusal.outcome["authority_effect"] == "None"
    assert "8192 bits" in refusal.outcome["error"]


def test_review_density_fixture_refuses_8572_bit_purity_through_compiled_host():
    denominators = prime_power_denominators()
    rows = [[Fraction(int(i == j), 7) for j in range(7)] for i in range(7)]
    for (i, j), denominator in zip(combinations(range(7), 2), denominators):
        rows[i][j] = rows[j][i] = Fraction(1, denominator)
    assert all(rows[i][i] > sum(abs(rows[i][j]) for j in range(7) if i != j) for i in range(7))
    assert sum(rows[i][i] for i in range(7)) == 1
    assert max(x.denominator.bit_length() for row in rows for x in row) == 255
    # Independent closed-form oracle for this symmetric trace-one density.
    purity = Fraction(1, 7) + 2 * sum(Fraction(1, q * q) for q in denominators)
    assert (purity.numerator.bit_length(), purity.denominator.bit_length()) == (8570, 8572)
    assert len(str(purity)) == 5162
    request = DensityRequest(rho=operator([[str(x) for x in row] for row in rows]))
    assert_native_output_refusal("density", request)


def test_lindblad_refuses_8323_bit_derivative_through_compiled_host():
    denominators = prime_power_denominators()
    r = denominators[-1]
    request = LindbladRequest(
        rho=operator([[f"1/{r}", "0"], ["0", f"{r - 1}/{r}"]]),
        hamiltonian=operator([["0", "0"], ["0", "0"]]),
        jumps=tuple(operator([["0", "0"], [f"1/{q}", "0"]]) for q in denominators[:-1]),
    )
    # Each jump transfers 1/(r*q²) from the first diagonal entry to the second.
    transfer = sum(Fraction(1, r * q * q) for q in denominators[:-1])
    assert (transfer.numerator.bit_length(), transfer.denominator.bit_length()) == (7576, 8323)
    assert max(q.bit_length() for q in denominators) == 255
    assert_native_output_refusal("lindblad", request)


@pytest.mark.parametrize(
    "value",
    [str(2**8191), str(-(2**8191)), f"1/{2**8191}"],
    ids=("positive_numerator", "negative_numerator", "denominator"),
)
def test_python_accepts_inclusive_output_bit_limit(value):
    assert operator([[value]]).real.data == ((value,),)


@pytest.mark.parametrize(
    "value",
    [str(2**8192), f"1/{2**8192}", "1" * 6001],
    ids=("numerator_bits", "denominator_bits", "text_length"),
)
def test_python_rejects_outputs_above_bit_or_text_limit(value):
    with pytest.raises(ValidationError, match="output.*bound"):
        operator([[value]])


@pytest.fixture(
    scope="module",
    params=("hodge", "repair_projector", "deform", "density", "lindblad", "retract", "probe"),
)
def native_case(request):
    """Small valid replies obtained from the actual compiled native process."""
    ground = operator([["1", "0"], ["0", "0"]])
    zero = operator([["0", "0"], ["0", "0"]])
    mixed = operator([["1/2", "0"], ["0", "1/2"]])
    state = QddcState(
        d_prev=RationalMatrix(rows=1, cols=1, data=(("1",),)),
        d_next=RationalMatrix(rows=0, cols=1, data=()),
        operator_dim=2,
        cochain=(ground,),
    )
    method = request.param
    inputs = {
        "hodge": state,
        "repair_projector": state,
        "deform": DeformationRequest(
            state=state, alpha=(zero,), unitary=operator([["1", "0"], ["0", "1"]])
        ),
        "density": DensityRequest(rho=mixed),
        "lindblad": LindbladRequest(rho=mixed, hamiltonian=zero, jumps=(ground,)),
        "retract": RetractionRequest(rho=mixed, projector=ground, eta="1/3"),
        "probe": ProbeRequest(rho=mixed, projector=ground),
    }
    value = inputs[method]
    reply = call_native(f"qddc_{method}", value.model_dump(mode="json"))
    return method, value, reply


def test_all_actions_accept_valid_compiled_host_results(native_case):
    method, request, reply = native_case
    result = getattr(NativeQddc(), method)(request)
    assert result.model_dump(mode="json") == dict(reply)
    if method == "probe":
        assert result.probability == "1/2"
        assert result.conditional == operator([["1", "0"], ["0", "0"]])


class NonconformingReplyHost:
    """Fixture for a broken success-reply producer, not native execution evidence."""

    def __init__(self, outcome):
        self.outcome = outcome

    def invoke_runtime(self, action, payload):
        assert action == self.outcome["action"]
        assert payload
        return Ok(self.outcome)


def replace_first_scalar(value, replacement: str) -> bool:
    if isinstance(value, dict):
        entries = value.items()
    elif isinstance(value, list):
        entries = enumerate(value)
    else:
        return False
    for key, item in entries:
        if isinstance(item, str):
            value[key] = replacement
            return True
        if replace_first_scalar(item, replacement):
            return True
    return False


@pytest.mark.parametrize(
    "defect", ["oversized_numerator", "oversized_denominator", "missing_fields"]
)
def test_output_schema_refusal_preserves_complete_fixture_outcome(native_case, defect):
    method, request, reply = native_case
    outcome = copy.deepcopy(dict(reply.outcome))
    if defect == "missing_fields":
        outcome["result"] = {}
    else:
        value = str(2**8192) if defect == "oversized_numerator" else f"1/{2**8192}"
        assert replace_first_scalar(outcome["result"], value)
    outcome["fixture_marker"] = {"kind": "nonconforming success", "retained": [1, 2, 3]}
    port = NativeQddc(NonconformingReplyHost(outcome))
    with pytest.raises(NativeMathRefusal) as caught:
        getattr(port, method)(request)
    refusal = caught.value
    assert refusal.code == "QDDC_OUTPUT_SCHEMA"
    assert isinstance(refusal.__cause__, ValidationError)
    assert dict(refusal.outcome) == outcome
    assert refusal.outcome["result"] is outcome["result"]
    assert refusal.outcome["success"] is True
    assert refusal.outcome["authority_effect"] == "None"
