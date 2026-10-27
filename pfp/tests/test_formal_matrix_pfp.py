"""Formal-math matrix migration through actual PFP checks and accounted fixtures.

Scripted provider replies are deterministic controls, not model experiments.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import json
import urllib.request

import pytest

from pfp.infrastructure import formal_matrix as matrix


def gateway(tmp_path, **options):
    from pfp.tests.test_pilot_matrix_pfp import make_gateway

    return make_gateway(tmp_path, **options)


def call(accounted, **options):
    return matrix.call_openrouter("unused-key", "vendor/model",
        [{"role": "system", "content": "public system"},
         {"role": "user", "content": "public task"}],
        gateway=accounted, task_id="formal-public-task", attempt_id="case-0",
        max_tokens=256, **options)


def run(tmp_path, monkeypatch, gateways, *, cases=None, models=None, evaluate=None):
    folder = tmp_path / "matrix-run"
    monkeypatch.setattr(matrix, "run_folder", lambda *_args: folder)
    folder.mkdir()
    monkeypatch.setattr(matrix, "require_api_key", lambda *_args: pytest.fail("raw key lookup"))
    return matrix.run_model_matrix(challenge_id="C044", models=models or [{"id": "vendor/model"}],
        cases=cases or [{"case_id": "PRIVATE-CASE", "data": 3}], system_prompt="public system",
        evaluate=evaluate or (lambda _case, answer: (answer["value"] == 1, "independent check")),
        gateways=gateways, max_tokens=256, pause_sec=0)


def test_direct_call_without_accounted_gateway_refuses_before_raw_transport(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: pytest.fail("raw transport reached"))
    result = matrix.call_openrouter("unused-key", "vendor/model", [{"role": "user", "content": "x"}])
    assert result["ok"] is False and result["stop"] is True
    assert result["error"] == "PFP_ACCOUNTED_GATEWAY_REQUIRED"


def test_direct_call_checks_bound_answer_and_retains_exact_wire(tmp_path):
    accounted, provider = gateway(tmp_path, answer={"value": 1})
    result = call(accounted)
    assert result["ok"] is True and json.loads(result["content"]) == {"value": 1}
    assert result["pfp"]["schema_valid"] is True
    assert len(provider.calls) == 1
    request = provider.calls[0]
    assert all(key in request.user for key in ("task_id", "attempt_id", "input_sha256"))
    assert "public task" in request.user and "public system" in request.user
    wire = base64.b64decode(result["provider_wire"]["raw_reply_base64"], validate=True)
    assert wire == provider.raw
    assert sha256(wire).hexdigest() == result["provider_wire"]["raw_reply_sha256"]
    assert wire.decode("utf-8") == result["raw_body"]


@pytest.mark.parametrize("extra", [{"messages": []}, {"model": "other/model"},
    {"max_tokens": 1}, {"response_format": {"type": "json_object"}}, {"unknown": True}])
def test_unknown_or_prompt_overriding_controls_refuse_before_dispatch(tmp_path, extra):
    accounted, provider = gateway(tmp_path)
    result = call(accounted, extra=extra)
    assert result["ok"] is False and result["stop"] is True
    assert "UNSUPPORTED" in result["error"]
    assert provider.calls == []


def test_supported_controls_reach_accounted_request_without_prompt_overwrite(tmp_path):
    accounted, provider = gateway(tmp_path, answer={"value": 1})
    result = call(accounted, temperature=0.1, extra={"seed": 7, "top_p": 0.9,
        "provider": {"allow_fallbacks": False, "require_parameters": True}})
    assert result["ok"] is True
    assert provider.calls[0].decoding.seed == 7
    assert provider.calls[0].decoding.top_p == 0.9
    assert provider.calls[0].decoding.allow_fallbacks is False


def test_matrix_injected_gateway_hides_private_ids_and_judges_only_checked_answer(tmp_path, monkeypatch):
    accounted, provider = gateway(tmp_path, answer={"value": 1})
    judged = []

    def evaluate(case, answer):
        judged.append((case, answer))
        return answer == {"case_id": "PRIVATE-CASE", "value": 1}, "independent check"

    folder = run(tmp_path, monkeypatch, {"vendor/model": accounted},
        cases=[{"case_id": "PRIVATE-CASE", "category": "PRIVATE-CATEGORY",
                "expected_value": "PRIVATE-ANSWER", "data": 3}], evaluate=evaluate)
    record = json.loads((folder / "run_record.json").read_bytes())
    row = record["models"]["vendor/model"]["records"][0]
    assert row["outcome"] == "VERIFIED" and len(judged) == 1
    assert row["pfp"]["schema_valid"] is True and row["provider_wire"]
    assert not any(secret in provider.calls[0].user for secret in
                   ("PRIVATE-CASE", "PRIVATE-CATEGORY", "PRIVATE-ANSWER"))


def test_invalid_pfp_never_becomes_reasoning_answer_or_reaches_judge(tmp_path, monkeypatch):
    accounted, provider = gateway(tmp_path, raw_content='{"value":1}')
    folder = run(tmp_path, monkeypatch, {"vendor/model": accounted},
        cases=[{"case_id": "PRIVATE-1"}, {"case_id": "PRIVATE-2"}],
        evaluate=lambda *_args: pytest.fail("unbound answer reached judge"))
    rows = json.loads((folder / "run_record.json").read_bytes())["models"]["vendor/model"]["records"]
    assert len(provider.calls) == 2
    assert all(row["outcome"] == matrix.INFRA_ERROR for row in rows)
    assert all(row["pfp"]["schema_valid"] is False for row in rows)


def test_unknown_cost_stops_remaining_cases_and_models_retaining_reply(tmp_path, monkeypatch):
    first, provider = gateway(tmp_path, cost=None, answer={"value": 1})
    second, other = gateway(tmp_path, model="vendor/other", answer={"value": 1})
    folder = run(tmp_path, monkeypatch, {"vendor/model": first, "vendor/other": second},
        models=[{"id": "vendor/model"}, {"id": "vendor/other"}],
        cases=[{"case_id": "PRIVATE-1"}, {"case_id": "PRIVATE-2"}],
        evaluate=lambda *_args: pytest.fail("unsettled answer reached judge"))
    record = json.loads((folder / "run_record.json").read_bytes())
    assert len(provider.calls) == 1 and other.calls == []
    row = record["models"]["vendor/model"]["records"][0]
    assert row["outcome"] == matrix.INFRA_ERROR and row["stop"] is True
    assert row["provider_wire"] and record["stop_reason"]
    assert row["usage"]["cost"] is None


def test_matrix_validates_all_gateways_share_accounting_before_send(tmp_path, monkeypatch):
    first, provider = gateway(tmp_path)
    second, other = gateway(tmp_path, model="vendor/other", accounting_name="different.sqlite3")
    with pytest.raises(ValueError):
        run(tmp_path, monkeypatch, {"vendor/model": first, "vendor/other": second},
            models=[{"id": "vendor/model"}, {"id": "vendor/other"}])
    assert provider.calls == [] and other.calls == []


def test_original_per_model_output_bound_is_not_silently_shrunk(tmp_path, monkeypatch):
    first, provider = gateway(tmp_path)
    second, other = gateway(tmp_path, model="vendor/other")
    with pytest.raises(ValueError, match="PFP_OUTPUT_BOUND_MISMATCH"):
        run(tmp_path, monkeypatch, {"vendor/model": first, "vendor/other": second},
            models=[{"id": "vendor/model"}, {"id": "vendor/other", "max_tokens": 4096}])
    assert provider.calls == [] and other.calls == []


@pytest.mark.parametrize("status,outcome", [("SOLVED", "REJECTED"), ("UNKNOWN", "ABSTAINED")])
def test_original_independent_rejection_classification_is_preserved(tmp_path, monkeypatch, status, outcome):
    accounted, provider = gateway(tmp_path, answer={"status": status, "value": 1})
    folder = run(tmp_path, monkeypatch, {"vendor/model": accounted}, evaluate=lambda *_args: (False, "counterexample"))
    row = json.loads((folder / "run_record.json").read_bytes())["models"]["vendor/model"]["records"][0]
    assert row["outcome"] == outcome and len(provider.calls) == 1


def test_original_privacy_parsing_summary_and_antibody_arm_isolation():
    assert matrix.participant_view({"case_id": "private", "expected_result": 1, "data": 2}, "q1") == {"case_id": "q1", "data": 2}
    assert matrix.extract_json_object("no actual answer") is None
    assert matrix.summarize([{"outcome": "VERIFIED"}, {"outcome": matrix.INFRA_ERROR}])["answered"] == 1
    first, second = matrix.ArmAntibodyStore("A"), matrix.ArmAntibodyStore("B")
    first.mint("case", {}, "actual counterexample")
    assert len(first.active("case")) == 1 and second.active("case") == []
