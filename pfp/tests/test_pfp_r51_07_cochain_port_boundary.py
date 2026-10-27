"""Architecture and literal transport controls; fixture replies prove no native math."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

import pfp.domain.cochain as cochain_domain
import pfp.ffi as ffi
from operations.domain.rop.result import Err, Ok, Refusal
from pfp.infrastructure.finite_qm_cochain_judge import NativeCochainJudge


class RecordingPort:
    """Literal transport reply, deliberately not a solver or certificate verifier."""

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def evaluate_prompt_cochain(self, **kwargs):
        self.calls.append(kwargs)
        return self.reply


class FalseyPort(RecordingPort):
    def __bool__(self):
        return False


def wire_complex():
    return {"c0_dim": 2, "c1_dim": 1, "c2_dim": 0, "d0": [["-1", "1"]], "d1": []}


def exact_reply():
    return {"result": {"disposition": "ExactCoboundary", "phi1": "0", "gamma2": "0",
                       "potential": ["0", "1"], "dual_witness": ["0"]}}


def test_domain_has_no_concrete_process_adapter_import() -> None:
    """Original architecture red uses existing API/source, with no new imports."""
    tree = ast.parse(Path(cochain_domain.__file__).read_text(encoding="utf-8"))
    modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert "pfp.ffi" not in modules
    assert not any(module and "operating_system.adapters" in module for module in modules)


def test_real_domain_import_does_not_load_concrete_host() -> None:
    script = (
        "import sys;import pfp.domain.cochain;"
        "assert 'pfp.ffi' not in sys.modules;"
        "assert 'operating_system.adapters.rust_host.ffi' not in sys.modules;"
        "print('DOMAIN_IMPORT_ONLY')"
    )
    result = subprocess.run(
        [sys.executable, "-E", "-B", "-c", script],
        cwd=Path(cochain_domain.__file__).resolve().parents[2],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout.strip() == b"DOMAIN_IMPORT_ONLY"


def test_injected_port_gets_literal_exact_wire_and_triad() -> None:
    port = RecordingPort(Ok(exact_reply()))
    complex_value = cochain_domain.PromptCellComplex(
        v_count=2, e_count=1, f_count=0,
        d0_matrix=((Fraction(-1), Fraction(1)),),
    )
    triad = cochain_domain.PrimeTriadContext(
        source_bytes="literal source", expected_source_hash="literal hash",
        protected_answers={"q": "a"}, candidate_answers={"q": "a"}, remaining_budget=3,
    )
    result = cochain_domain.evaluate_prompt_cochain(
        complex=complex_value, cochain=[Fraction(1, 2)],
        primal_potential=[0, Fraction(1, 2)], dual_witness=[0],
        triad_context=triad, host=port,
    )
    assert port.calls == [{
        "complex": {"c0_dim": 2, "c1_dim": 1, "c2_dim": 0,
                    "d0": [["-1", "1"]], "d1": [],
                    "source_bytes_hash": None},
        "cochain": ["1/2"], "primal_potential": ["0", "1/2"], "dual_witness": ["0"],
        "triad_context": {"source_bytes": "literal source", "expected_source_hash": "literal hash",
                          "protected_answers": {"q": "a"}, "candidate_answers": {"q": "a"}, "remaining_budget": 3},
    }]
    assert isinstance(result, cochain_domain.ExactCoboundary)
    assert result.phi1 == Fraction(0)


@pytest.mark.parametrize(
    ("potential", "dual", "omitted"),
    [
        (None, None, ["primal_potential", "dual_witness"]),
        (None, (), ["primal_potential"]),
        ((), None, ["dual_witness"]),
    ],
    ids=["both", "potential", "dual"],
)
def test_omitted_witness_is_a_refusal_not_an_empty_vector(potential, dual, omitted) -> None:
    port = RecordingPort(Ok(exact_reply()))
    result = cochain_domain.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=[], primal_potential=potential,
        dual_witness=dual, host=port,
    )
    assert isinstance(result, cochain_domain.CochainRefusal)
    assert result.reason == "OMITTED_COCHAIN_WITNESS"
    assert result.receipt["omitted"] == omitted
    assert port.calls == []


def test_explicit_empty_witnesses_still_forward() -> None:
    port = RecordingPort(Ok(exact_reply()))
    cochain_domain.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=[], primal_potential=(),
        dual_witness=(), host=port,
    )
    assert port.calls == [{"complex": wire_complex(), "cochain": [],
                           "primal_potential": [], "dual_witness": [], "triad_context": None}]


@pytest.mark.parametrize("value", [True, 1.5], ids=["bool", "float"])
def test_invalid_rational_never_calls_injected_port(value) -> None:
    port = RecordingPort(Ok(exact_reply()))
    with pytest.raises(TypeError, match="Invalid rational type"):
        cochain_domain.evaluate_prompt_cochain(complex=wire_complex(), cochain=[value], host=port)
    assert port.calls == []


def test_domain_requires_host_keyword() -> None:
    with pytest.raises(TypeError, match="host"):
        cochain_domain.evaluate_prompt_cochain(complex=wire_complex(), cochain=[])


def test_domain_explicit_none_is_not_an_adapter_default() -> None:
    with pytest.raises(TypeError, match="requires an injected host"):
        cochain_domain.evaluate_prompt_cochain(complex=wire_complex(), cochain=[], host=None)


@pytest.mark.parametrize(
    ("payload", "expected_type", "attributes"),
    [
        ({"result": {"disposition": "ExactCoboundary", "phi1": "0", "gamma2": "0",
                     "potential": ["0", "1"], "dual_witness": ["0"]}},
         cochain_domain.ExactCoboundary, {"phi1": Fraction(0), "gamma2": Fraction(0), "potential": (Fraction(0), Fraction(1))}),
        ({"result": {"disposition": "ClosedNonExactClass", "phi1": "1", "gamma2": "0",
                     "potential": ["0", "0"], "dual_witness": ["1"], "cohomology_class": ["4"]}},
         cochain_domain.ClosedNonExactClass, {"phi1": Fraction(1), "cohomology_class_vec": (Fraction(4),)}),
        ({"result": {"disposition": "NonClosedEdgeData", "phi1": "1", "gamma2": "2", "face_defect": ["2"]}},
         cochain_domain.NonClosedEdgeData, {"phi1": Fraction(1), "gamma2": Fraction(2), "defect_vector": (Fraction(2),)}),
        ({"result": {"disposition": "Refusal", "code": "PHI1_CERTIFICATE_INVALID", "message": "literal refusal"}},
         cochain_domain.CochainRefusal, {"reason": "PHI1_CERTIFICATE_INVALID", "detail": "literal refusal"}),
        ({"disposition": "other"}, cochain_domain.CochainRefusal, {"reason": "UNRECOGNIZED_DISPOSITION"}),
        ({"error": "literal unavailable"}, cochain_domain.CochainRefusal, {"reason": "HOST_ERROR", "detail": "literal unavailable"}),
    ],
    ids=["exact", "closed", "nonclosed", "refusal", "unknown", "host-error"],
)
def test_literal_reply_decoding_preserved(payload, expected_type, attributes) -> None:
    port = RecordingPort(Ok(payload))
    result = cochain_domain.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=[], primal_potential=[], dual_witness=[], host=port,
    )
    assert type(result) is expected_type
    assert result.receipt is payload.get("result", payload)
    for key, expected in attributes.items():
        assert getattr(result, key) == expected
    assert len(port.calls) == 1


def test_transport_refusal_stays_a_refusal() -> None:
    refusal = Refusal("HOST_TIMEOUT", "literal timeout")
    port = RecordingPort(Err(refusal))
    result = cochain_domain.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=[], primal_potential=[], dual_witness=[], host=port,
    )
    assert isinstance(result, cochain_domain.CochainRefusal)
    assert result.reason == "HOST_TIMEOUT"
    assert result.detail == "literal timeout"
    assert "raw_refusal" in result.receipt
    assert len(port.calls) == 1


def test_port_exception_is_not_relabelled_as_math_success() -> None:
    class RaisingPort:
        def evaluate_prompt_cochain(self, **kwargs):
            raise RuntimeError("literal transport exception")

    with pytest.raises(RuntimeError, match="literal transport exception"):
        cochain_domain.evaluate_prompt_cochain(
            complex=wire_complex(), cochain=[], primal_potential=[], dual_witness=[], host=RaisingPort(),
        )


def test_adapter_default_precedes_serialization(monkeypatch) -> None:
    events = []
    port = RecordingPort(Ok(exact_reply()))

    def default():
        events.append("default")
        return port

    class ComplexInput:
        def to_dict(self):
            events.append("serialize")
            return wire_complex()

    monkeypatch.setattr(ffi, "get_default_host", default)
    result = ffi.evaluate_prompt_cochain_disposition(
        complex=ComplexInput(), cochain=[], primal_potential=[], dual_witness=[],
    )
    assert events == ["default", "serialize"]
    assert isinstance(result, cochain_domain.ExactCoboundary)
    assert len(port.calls) == 1


def test_falsey_explicit_host_suppresses_default(monkeypatch) -> None:
    def forbidden_default():
        raise AssertionError("explicit host must suppress default")

    monkeypatch.setattr(ffi, "get_default_host", forbidden_default)
    port = FalseyPort(Ok(exact_reply()))
    result = ffi.evaluate_prompt_cochain_disposition(
        complex=wire_complex(), cochain=[], primal_potential=[], dual_witness=[], host=port,
    )
    assert isinstance(result, cochain_domain.ExactCoboundary)
    assert len(port.calls) == 1


def test_adapter_default_error_precedes_malformed_input(monkeypatch) -> None:
    def unavailable():
        raise FileNotFoundError("HOST_BINARY_NOT_FOUND: literal unavailable")

    monkeypatch.setattr(ffi, "get_default_host", unavailable)
    with pytest.raises(FileNotFoundError, match="HOST_BINARY_NOT_FOUND"):
        ffi.evaluate_prompt_cochain_disposition(complex=wire_complex(), cochain=[1.5])


def test_existing_raw_ffi_function_keeps_complete_result_identity() -> None:
    crossing = Err(Refusal("HOST_TIMEOUT", "literal raw timeout"))
    port = RecordingPort(crossing)
    received = ffi.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=["1"], budget=7,
        source_bytes="literal source", expected_source_hash="literal hash",
        protected_answers={"q": "a"}, host=port,
    )
    assert received is crossing
    assert port.calls == [{"complex": wire_complex(), "cochain": ["1"],
                           "primal_potential": None, "dual_witness": None, "triad_context": None,
                           "budget": 7, "source_bytes": "literal source", "expected_source_hash": "literal hash",
                           "protected_answers": {"q": "a"}}]


def judge_inputs():
    case = {"prompt": json.dumps({"operad_slots": {"slot_m1_layer0_ambient_carrier": {
        "coefficient_ring": "Q", "public_input": {"complex": wire_complex(), "cochain": ["1"]},
    }}})}
    answer = {"potential": [{"num": 0, "den": 1}, {"num": 1, "den": 1}],
              "dual_witness": [{"num": 0, "den": 1}],
              "phi1": {"num": 0, "den": 1}, "gamma2": {"num": 0, "den": 1}}
    return case, answer


@pytest.mark.parametrize("transport_error", [False, True], ids=["certificate-refusal", "unavailable"])
def test_judge_preserves_certificate_vs_availability(transport_error) -> None:
    payload = {"result": {"disposition": "Refusal", "code": "PHI1_CERTIFICATE_INVALID", "message": "literal invalid"}}
    crossing = Err(Refusal("HOST_TIMEOUT", "literal timeout")) if transport_error else Ok(payload)
    judge = NativeCochainJudge(RecordingPort(crossing))
    case, answer = judge_inputs()
    if transport_error:
        with pytest.raises(RuntimeError, match="NATIVE_CHECK_UNAVAILABLE:HOST_TIMEOUT"):
            judge(case, answer)
    else:
        assert judge(case, answer) == (False, "NATIVE_CERTIFICATE_REFUSED:PHI1_CERTIFICATE_INVALID")
    assert len(judge.receipts) == 1


def test_judge_none_uses_adapter_convenience(monkeypatch) -> None:
    port = RecordingPort(Ok(exact_reply()))
    defaults = []

    def default():
        defaults.append("called")
        return port

    monkeypatch.setattr(ffi, "get_default_host", default)
    judge = NativeCochainJudge(None)
    case, answer = judge_inputs()
    assert judge(case, answer) == (True, "NATIVE_CERTIFICATE_CHECKED_ON_SUPPLIED_COMPLEX")
    assert defaults == ["called"]
    assert judge.receipts == [port.reply.unwrap()["result"]]
