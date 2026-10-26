"""Offline regressions for F01-F03. AuthorityEffect: None."""

from __future__ import annotations
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model

import inspect
import json
import shutil
import socket
import urllib.request
from pathlib import Path

import pytest
import yaml

from omega_engine_pfp.domain.types import EvaluationStatus
from omega_engine_pfp.domain.types import PilotSpec
from omega_engine_pfp.domain.types import PStarPrompt
from omega_engine_pfp.domain.pilots.checker_registry import (
    checker_definition,
    evaluate_candidate,
    strict_json,
)
from omega_engine_pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate
from omega_engine_pfp.infrastructure import pilot_evidence as evidence
from omega_engine_pfp.infrastructure.pilot_runner import grade, materialize_results
from omega_engine_woland.tests.pilots import live_evaluator as live
from omega_engine_woland.tests.pilots.offline_evaluator import ExactLinalgEvaluator

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
RESULTS = ROOT / "omega_engine_woland" / "tests" / "pilots" / "results"
LINALG = "PFP-01-EXACT-LINALG"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network access forbidden in P0 regressions")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("OMEGA_CREDENTIAL_DISCOVERY", "off")


def copy_pilot(tmp_path: Path, *, observed: bool = True) -> Path:
    pilot = tmp_path / "pilot_0000000"
    shutil.copytree(RESULTS / pilot.name, pilot)
    if not observed:
        (pilot / "response.yaml").unlink()
    return pilot


def replace_yaml(path: Path, change) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@pytest.mark.parametrize("checker,expected,payload,status", [
    (LINALG, 3, {"answer": 3.9}, "MALFORMED"),
    (LINALG, 3, {"answer": 3.0}, "MALFORMED"),
    (LINALG, 1, {"answer": True}, "MALFORMED"),
    (LINALG, 3, {"answer": "3"}, "MALFORMED"),
    (LINALG, 3, {}, "MALFORMED"),
    (LINALG, 3, {"answer": None}, "MALFORMED"),
    (LINALG, 3, {"answer": 4}, "WRONG_ANSWER"),
    ("PFP-02-EXACT-PRIMES", [2, 3], {"primes": [2, 3.9]}, "MALFORMED"),
    ("PFP-02-EXACT-PRIMES", [2, 3], {"primes": [2, "3"]}, "MALFORMED"),
    ("PFP-02-EXACT-PRIMES", [1], {"primes": [True]}, "MALFORMED"),
    ("PFP-03-EXACT-FOL-DEDUCTION", {"verdict": "YES", "premise_count": 2},
     {"verdict": "YES", "premise_count": 2.9}, "MALFORMED"),
    ("PFP-03-EXACT-FOL-DEDUCTION", {"verdict": "YES", "premise_count": 2},
     {"verdict": "YES", "premise_count": True}, "MALFORMED"),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL", {"computable": False, "reason": "undefined"}, {}, "MALFORMED"),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL", {"computable": False, "reason": "undefined"},
     {"computable": "false", "reason": "undefined"}, "MALFORMED"),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL", {"computable": False, "reason": "undefined"},
     {"computable": False, "reason": "arbitrary unrelated claim"}, "WRONG_ANSWER"),
    ("PFP-05-EXACT-2X2-DETERMINANT", {"det": 17}, {"det": 1}, "WRONG_ANSWER"),
    ("PFP-05-EXACT-2X2-DETERMINANT", {"det": 17}, {"det": 17}, "ACCEPTED"),
    ("PFP-05-EXACT-2X2-DETERMINANT", {"det": 1}, {"det": 1.9}, "MALFORMED"),
    ("PFP-05-EXACT-2X2-DETERMINANT", {"det": 1}, {"det": True}, "MALFORMED"),
    ("PFP-05-EXACT-2X2-DETERMINANT", {"det": 1}, {"det": "1"}, "MALFORMED"),
    ("UNREGISTERED", 3, {"answer": 3}, "REFUSED"),
])
def test_checker_adversaries_through_both_entry_points(checker, expected, payload, status):
    raw = json.dumps(payload)
    assert live.extract_and_evaluate(checker, expected, raw, payload)[1].value == status
    assert FailClosedRefusalGate.evaluate_candidate_payload(checker, expected, payload).status.value == status


@pytest.mark.parametrize("raw", [
    '{"answer":0,"answer":3}', '{"answer":3,"metadata":{"x":1,"x":2}}',
    '{"answer":NaN}', '{"answer":Infinity}', '{"answer":3,"metadata":1e999}', '[1,', '3', 'null',
    '{"answer":3} trailing', '[' * 2000 + ']' * 2000,
], ids=[f"raw-{index}" for index in range(10)])
def test_strict_raw_ingress(raw):
    assert live.sanitize_raw_reply(raw)[1] is False
    assert live.extract_and_evaluate(LINALG, 3, raw, {"answer": 3})[1] == EvaluationStatus.MALFORMED


@pytest.mark.parametrize("checker", [
    LINALG, "PFP-02-EXACT-PRIMES", "PFP-03-EXACT-FOL-DEDUCTION",
    "PFP-04-EXACT-EPISTEMIC-REFUSAL", "PFP-05-EXACT-2X2-DETERMINANT",
])
def test_hidden_gold_never_enters_outbound_request(checker, monkeypatch):
    captured = []

    def fake_open(*args, **kwargs):
        captured.append(1)
        raise AssertionError("Retired pilot-directory transport must not execute")

    gold = {"answer": 918273}
    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    request = live.build_live_request(
        "fixture-model", "Solve independently", "Compute the requested quantity", checker
    )
    assert str(gold["answer"]).encode() not in evidence.canonical_bytes(request)
    with pytest.raises(live.LegacyLiveMigrationRefusal):
        live.dispatch_live_prompt("fixture-key", "fixture-model", "Solve independently",
                                  "Compute the requested quantity", checker)
    assert captured == []
    assert "expected_answer" not in inspect.signature(live.dispatch_live_prompt).parameters
    assert "const" not in json.dumps(checker_definition(checker).response_schema)


def test_prompt_and_unknown_checker_refused_before_dispatch():
    with pytest.raises(ValueError, match="ANSWER_BEARING"):
        live.build_live_request("m", "s", '{"task":"solve","output":{"answer":3}}', LINALG)
    with pytest.raises(ValueError, match="UNKNOWN_CHECKER"):
        live.dispatch_live_prompt("fixture-key", "m", "s", "u", "unknown")


@pytest.mark.parametrize("edge", [1, 2, 3])
def test_all_tied_triangle_repairs_are_accepted(edge):
    result = grade([{"request_id": "p_req_0", "raw_reply": json.dumps({"answer": edge})}], "p", "graph_repair")
    assert result["results"][0]["status"] == "ACCEPTED"


@pytest.mark.parametrize("payload", [{}, {"answer": None}, {"answer": None, "status": "REFUSED"},
                                     {"answer": None, "status": "REFUSED", "witness": {"remaining": [2.0, 4.0]}}])
def test_refusal_requires_explicit_exact_witness(payload):
    result = grade([{"request_id": "p_req_0", "raw_reply": json.dumps(payload)}], "p", "refusal")
    assert result["results"][0]["status"] != "ACCEPTED"


@pytest.mark.parametrize("remaining", [[2, 4], [4, 2]])
def test_refusal_witness_is_independent_of_candidate_order(remaining):
    payload = {"answer": None, "status": "REFUSED", "witness": {"remaining": remaining}}
    result = grade([{"request_id": "p_req_0", "raw_reply": json.dumps(payload)}], "p", "refusal")
    assert result["results"][0]["status"] == "ACCEPTED"


def test_numeric_reply_to_refusal_task_is_false_certainty():
    result = grade([{"request_id": "p_req_0", "raw_reply": json.dumps({"answer": 2})}], "p", "refusal")
    assert result["results"][0]["status"] == "FALSE_CERTAINTY"


def test_regrading_checks_raw_reply_and_keeps_original_bytes(tmp_path):
    pilot = copy_pilot(tmp_path)
    replace_yaml(pilot / "response.yaml", lambda d: d.update(raw_reply='{"answer":999}'))
    before = (pilot / "response.yaml").read_bytes()
    report = ExactLinalgEvaluator.evaluate_pilot(pilot)
    assert report["status"] == "WRONG_ANSWER"
    assert report["efficacy_eligible"] is False
    assert (pilot / "response.yaml").read_bytes() == before
    receipt = strict_json(Path(report["evaluation_receipt"]).read_text())
    assert receipt["observation_sha256"] == evidence.digest(before)


def test_no_observation_is_not_run_and_fixtures_are_separate(tmp_path):
    pilot = copy_pilot(tmp_path, observed=False)
    assert ExactLinalgEvaluator.evaluate_pilot(pilot)["status"] == "NOT_RUN"
    fixture = ExactLinalgEvaluator.create_fixture(pilot)
    assert fixture.parent.name == "fixtures"
    assert strict_json(fixture.read_text())["efficacy_eligible"] is False
    assert ExactLinalgEvaluator.evaluate_pilot(pilot)["status"] == "NOT_RUN"
    assert not (pilot / "response.yaml").exists()


def test_fixture_cannot_replace_failed_observation(tmp_path):
    pilot = copy_pilot(tmp_path)
    replace_yaml(pilot / "response.yaml", lambda d: d.update(raw_reply='{"answer":999}', trial_status="FAILED"))
    before = (pilot / "response.yaml").read_bytes()
    first = ExactLinalgEvaluator.create_fixture(pilot)
    assert ExactLinalgEvaluator.create_fixture(pilot) == first
    assert (pilot / "response.yaml").read_bytes() == before
    assert ExactLinalgEvaluator.evaluate_pilot(pilot)["status"] == "WRONG_ANSWER"


def test_pending_manifest_remains_not_run_without_raw_observation(tmp_path):
    pilot = copy_pilot(tmp_path)
    replace_yaml(pilot / "response.yaml", lambda d: d.update(raw_reply=None, trial_status="NOT_RUN"))
    before = (pilot / "response.yaml").read_bytes()
    assert ExactLinalgEvaluator.evaluate_pilot(pilot)["status"] == "NOT_RUN"
    assert (pilot / "response.yaml").read_bytes() == before


def cached_observation(pilot: Path, raw: str = '{"answer":3}') -> Path:
    spec = load_yaml_model(PilotSpec, pilot / "spec.yaml")
    prompt = load_yaml_model(PStarPrompt, pilot / "p_star.yaml")
    request = live.build_live_request("fixture-model", prompt.system_prompt, prompt.user_prompt, str(spec.host_gate.checker_id))
    binding = evidence.input_binding(pilot, request)
    response = {"choices": [{"message": {"content": raw}}]}
    return evidence.write_once(pilot / "observations" / f"{binding['request_sha256']}.json", {
        "schema": "pfp.pilot-observation.v2", "input_binding": binding, "request": request,
        "provider_response": response, "provider_response_sha256": evidence.digest(evidence.canonical_bytes(response)),
    })


def test_cached_observation_is_regraded_under_changed_oracle_and_checker(tmp_path, monkeypatch):
    pilot = copy_pilot(tmp_path)
    observed = cached_observation(pilot)
    before = observed.read_bytes()
    first = live.run_live_evaluator(tmp_path, model="fixture-model")[0]
    assert first["status"] == "ACCEPTED"
    replace_yaml(pilot / "seed.yaml", lambda d: d["expected_outcome"].update(answer=17))
    second = live.run_live_evaluator(tmp_path, model="fixture-model")[0]
    assert second["status"] == "WRONG_ANSWER"
    assert second["evaluation"] != first["evaluation"]
    monkeypatch.setattr(evidence, "checker_revision", lambda: "changed-checker")
    third = live.run_live_evaluator(tmp_path, model="fixture-model")[0]
    assert third["evaluation"] != second["evaluation"]
    assert observed.read_bytes() == before
    assert third["cost_usd"] is None


@pytest.mark.parametrize("change", ["model", "prompt"])
def test_changed_request_cannot_reuse_observation(tmp_path, change):
    pilot = copy_pilot(tmp_path)
    cached_observation(pilot)
    model = "fixture-model"
    if change == "model":
        model = "different-model"
    else:
        replace_yaml(pilot / "p_star.yaml", lambda d: d.update(user_prompt="A different task"))
    with pytest.raises(ValueError, match="UNBOUND_HISTORICAL"):
        live.run_live_evaluator(tmp_path, model=model)


def test_cache_tampering_and_force_cannot_overwrite(tmp_path):
    pilot = copy_pilot(tmp_path)
    path = cached_observation(pilot)
    with pytest.raises(ValueError, match="ALREADY_OBSERVED"):
        live.run_live_evaluator(tmp_path, model="fixture-model", skip_completed=False)
    content = strict_json(path.read_text())
    content["provider_response"]["choices"][0]["message"]["content"] = '{"answer":999}'
    path.write_bytes(evidence.canonical_bytes(content))
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        live.run_live_evaluator(tmp_path, model="fixture-model")


def test_materialization_never_mints_acceptance_or_overwrites(tmp_path):
    artifacts = materialize_results(tmp_path, "p", "linear_algebra")
    response = yaml.safe_load(artifacts["response"].read_text())
    assert response["evaluation"]["status"] == "NOT_RUN"
    before = {name: path.read_bytes() for name, path in artifacts.items()}
    with pytest.raises(FileExistsError):
        materialize_results(tmp_path, "p", "linear_algebra")
    assert before == {name: path.read_bytes() for name, path in artifacts.items()}


def test_immutable_receipt_collision_is_detected(tmp_path):
    path = tmp_path / "receipt.json"
    evidence.write_once(path, {"value": 1})
    with pytest.raises(ValueError, match="IMMUTABLE_ARTIFACT_CONFLICT"):
        evidence.write_once(path, {"value": 2})


def test_registry_schema_is_not_mutable_by_callers():
    first = checker_definition(LINALG)
    first.response_schema["properties"]["answer"]["type"] = "string"
    assert checker_definition(LINALG).response_schema["properties"]["answer"]["type"] == "integer"
    assert evaluate_candidate("unknown", 3, {"answer": 3}).status == EvaluationStatus.REFUSED


@pytest.mark.parametrize("checker,oracle,payload", [
    (LINALG, None, {"answer": 3}),
    (LINALG, True, {"answer": 1}),
    ("PFP-02-EXACT-PRIMES", [True], {"primes": [1]}),
    ("PFP-03-EXACT-FOL-DEDUCTION", {"verdict": "YES", "premise_count": True},
     {"verdict": "YES", "premise_count": 1}),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL", {"computable": False, "reason": None},
     {"computable": False, "reason": "None"}),
    ("PFP-05-EXACT-2X2-DETERMINANT", True, {"det": 1}),
])
def test_invalid_oracle_cannot_certify_candidate(checker, oracle, payload):
    assert evaluate_candidate(checker, oracle, payload).status == EvaluationStatus.REFUSED


@pytest.mark.parametrize("response", [{}, {"choices": []}, {"choices": [None]},
                                     {"choices": [{"message": {"content": 3}}]}])
def test_malformed_provider_envelope_regrades_malformed(tmp_path, response):
    pilot = copy_pilot(tmp_path)
    path = cached_observation(pilot)
    content = strict_json(path.read_text())
    content["provider_response"] = response
    content["provider_response_sha256"] = evidence.digest(evidence.canonical_bytes(response))
    path.write_bytes(evidence.canonical_bytes(content))
    report = live.run_live_evaluator(tmp_path, model="fixture-model")[0]
    assert report["status"] == "MALFORMED"
    assert report["efficacy_eligible"] is False


@pytest.mark.parametrize("field,value,error", [
    ("schema", "unknown", "OBSERVATION_SCHEMA_MISMATCH"),
    ("input_binding", {}, "OBSERVATION_BINDING_MISMATCH"),
    ("request", {}, "REQUEST_DIGEST_MISMATCH"),
])
def test_unbound_cache_rejected_before_dispatch(tmp_path, field, value, error):
    pilot = copy_pilot(tmp_path)
    path = cached_observation(pilot)
    content = strict_json(path.read_text())
    content[field] = value
    path.write_bytes(evidence.canonical_bytes(content))
    with pytest.raises(ValueError, match=error):
        live.run_live_evaluator(tmp_path, model="fixture-model")


def test_interrupted_attempt_is_not_retried(tmp_path, monkeypatch):
    pilot = copy_pilot(tmp_path, observed=False)
    spec = load_yaml_model(PilotSpec, pilot / "spec.yaml")
    prompt = load_yaml_model(PStarPrompt, pilot / "p_star.yaml")
    request = live.build_live_request(
        "fixture-model", prompt.system_prompt, prompt.user_prompt, str(spec.host_gate.checker_id)
    )
    binding = evidence.input_binding(pilot, request)
    marker = pilot / "attempts" / f"{binding['request_sha256']}.json"
    marker.parent.mkdir()
    original = evidence.canonical_bytes(dict(request_id=binding["request_sha256"], input_binding=binding))
    marker.write_bytes(original)
    calls = []

    def interrupted(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("fixture transport interrupted")

    monkeypatch.setattr(live, "dispatch_live_prompt", interrupted)
    for _ in range(2):
        with pytest.raises(live.LegacyLiveMigrationRefusal):
            live.run_live_evaluator(tmp_path, model="fixture-model")
    assert calls == []
    assert marker.read_bytes() == original
    assert not list(pilot.glob("observations/*.json"))
