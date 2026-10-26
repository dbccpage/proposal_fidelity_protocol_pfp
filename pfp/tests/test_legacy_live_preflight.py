"""The retired pilot-directory route cannot dispatch outside bounded PFP."""

from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

import pytest

from omega_engine_woland.tests.pilots import live_evaluator as live
from omega_engine_pfp.domain.types import EvaluationStatus, PilotSpec, PStarPrompt
from omega_engine_pfp.infrastructure import pilot_evidence as evidence
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model

LINALG = "PFP-01-EXACT-LINALG"
REFUSAL = "LEGACY_LIVE_REQUIRES_CANONICAL_PFP"
ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())


def pilot_copy(tmp_path):
    pilot = tmp_path / "pilot_0000000"
    pilot.mkdir()
    source = ROOT / "omega_engine_woland/tests/pilots/results" / pilot.name
    for name in ("spec.yaml", "seed.yaml", "p_star.yaml"):
        shutil.copyfile(source / name, pilot / name)
    return pilot


def capture_network(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"{\\"answer\\":3}"}}]}'

    def send(*args, **kwargs):
        calls.append(1)
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", send)
    return calls


def test_public_legacy_dispatch_refuses_before_network(monkeypatch):
    calls = capture_network(monkeypatch)

    with pytest.raises(ValueError, match=REFUSAL) as refused:
        live.dispatch_live_prompt("unused-secret", "fixture-model", "Solve", "Compute", LINALG)

    assert refused.value.code == REFUSAL
    assert "pfp run-seed" in refused.value.migration_command
    assert "--model" in str(refused.value)
    assert "--output" in str(refused.value)
    assert "unused-secret" not in str(refused.value)
    assert calls == []


def test_new_pilot_observation_refuses_before_credentials_or_attempt_write(tmp_path, monkeypatch):
    from omega_engine_woland.infrastructure.providers import credential_source

    pilot = pilot_copy(tmp_path)
    before = {path.name: path.read_bytes() for path in pilot.iterdir()}
    calls = capture_network(monkeypatch)
    credential_reads = []

    def credential(*args, **kwargs):
        credential_reads.append(1)
        return credential_source.Ok(
            credential_source.ResolvedCredential("fixture", "unused-secret", "fixture")
        )

    monkeypatch.setattr(credential_source, "resolve_credential", credential)

    with pytest.raises(ValueError, match=REFUSAL):
        live.run_live_evaluator(tmp_path, model="fixture-model")

    assert credential_reads == calls == []
    assert {path.name: path.read_bytes() for path in pilot.iterdir()} == before


def test_bound_historical_observation_still_regrades_without_dispatch(tmp_path, monkeypatch):
    pilot = pilot_copy(tmp_path)
    calls = capture_network(monkeypatch)
    spec = load_yaml_model(PilotSpec, pilot / "spec.yaml")
    prompt = load_yaml_model(PStarPrompt, pilot / "p_star.yaml")
    request = live.build_live_request(
        "fixture-model", prompt.system_prompt, prompt.user_prompt, str(spec.host_gate.checker_id)
    )
    binding = evidence.input_binding(pilot, request)
    response = {"choices": [{"message": {"content": '{"answer":3}'}}]}
    observation = evidence.write_once(
        pilot / "observations" / f"{binding['request_sha256']}.json",
        dict(
            schema="pfp.pilot-observation.v2", input_binding=binding, request=request,
            provider_response=response,
            provider_response_sha256=evidence.digest(evidence.canonical_bytes(response)),
        ),
    )
    before = observation.read_bytes()

    report = live.run_live_evaluator(tmp_path, model="fixture-model")[0]

    assert report["status"] == "ACCEPTED"
    assert report["cost_usd"] is None
    assert report["efficacy_eligible"] is False
    assert observation.read_bytes() == before
    assert calls == []
    assert json.loads(observation.read_bytes())["provider_response"] == response


def test_legacy_cli_reports_typed_migration_refusal(tmp_path, monkeypatch, capsys):
    pilot_copy(tmp_path)
    calls = capture_network(monkeypatch)

    assert live.main(["--results-dir", str(tmp_path), "--model", "fixture-model"]) == 2

    report = json.loads(capsys.readouterr().err)
    assert report["status"] == "REFUSED"
    assert report["code"] == REFUSAL
    assert report["migration_command"].startswith("pfp run-seed ")
    assert calls == []


@pytest.mark.parametrize(
    ("raw", "status"),
    [(' {"answer":3} ', EvaluationStatus.ACCEPTED),
     ('{"answer":4}', EvaluationStatus.WRONG_ANSWER),
     ('{"answer":true}', EvaluationStatus.MALFORMED)],
)
def test_historical_raw_grading_keeps_independent_judgments(raw, status):
    _, valid, _, parsed = live.sanitize_raw_reply(raw)
    assert valid
    assert live.extract_and_evaluate(LINALG, 3, raw, parsed)[1] == status
