"""Real process integration for all three tests; no mocked solver, no skips."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err, Ok
from pfp.infrastructure.normal_forms.qm_classical import evaluate, verify

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "engine/crates_rs/tests/core_symbol_game/data/qm_classical.json"


def examples():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def result(outcome):
    assert isinstance(outcome, Ok), outcome
    assert outcome.value["success"], outcome.value
    return outcome.value["result"]


@pytest.mark.parametrize("name", list(examples()))
def test_each_experiment_replays_and_normalizes_idempotently(name):
    host = RustSymbolGameHost(timeout_seconds=60)
    experiment = examples()[name]
    certificate = result(evaluate(experiment, host=host))
    assert certificate["normal_form"] == experiment
    assert result(evaluate(certificate["normal_form"], host=host)) == certificate
    assert result(verify(experiment, certificate, host=host))["verified"] is True


def test_exact_obstructions_and_controls():
    host = RustSymbolGameHost(timeout_seconds=60)
    f = examples()
    report = result(evaluate(f["report_collision"], host=host))["result"]
    assert report["answers"] == ["1", "49/625"]
    assert report["witness"]["verdict"] == "report_collision"
    bell = result(evaluate(f["bell_nonlocal"], host=host))["result"]
    assert bell["chsh"] == "14/5" and bell["no_signalling"] is True
    assert bell["witness"]["verdict"] == "no_positive_joint_extension"
    sector = result(evaluate(f["central_mixture"], host=host))["result"]
    assert sector["central_purity_ceiling"] == "1/2"
    assert sector["central_trace_distance_floor"] == "1/2"
    quantum = result(evaluate(f["quantum_purification"], host=host))["result"]
    assert quantum["available_ancilla_max_purity"] == "1"


def test_tampered_or_wrong_problem_certificate_is_a_native_refusal():
    host = RustSymbolGameHost(timeout_seconds=60)
    f = examples()
    c = result(evaluate(f["central_mixture"], host=host))
    bad = copy.deepcopy(c)
    bad["result"]["central_purity_ceiling"] = "1"
    for experiment, certificate in [(f["central_mixture"], bad), (f["quantum_purification"], c)]:
        outcome = verify(experiment, certificate, host=host)
        assert isinstance(outcome, Ok)
        assert outcome.value["success"] is False
        assert outcome.value["result"] is None


@pytest.mark.parametrize("invalid", [True, 0.25, "1/0", "2/8", "-1/4"])
def test_exact_wire_refuses_invalid_probability(invalid):
    experiment = examples()["bell_local"]
    experiment["test"]["probabilities"][0] = invalid
    outcome = evaluate(experiment, host=RustSymbolGameHost(timeout_seconds=60))
    assert isinstance(outcome, Ok)
    assert outcome.value["success"] is False


def test_missing_host_is_not_a_python_mathematical_fallback(tmp_path):
    outcome = evaluate(examples()["bell_local"], host=RustSymbolGameHost(binary=tmp_path / "absent"))
    assert isinstance(outcome, Err)
