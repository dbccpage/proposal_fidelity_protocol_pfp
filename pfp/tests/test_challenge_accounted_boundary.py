"""New synthetic bound replies exercise original challenge judges, never old verdicts."""

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from omega_engine_operations.domain.rop.result import Ok
from omega_engine_pfp.infrastructure import challenge_live as live
from omega_engine_pfp.tests.test_pilot_matrix_pfp import make_gateway


def inputs():
    source = live.ROOT / "omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning/live/c050_dev_typed_witness_v3"
    config = json.loads((source / "config.json").read_bytes())
    wire = json.loads((source / "stage_1/provider_response.json").read_bytes())
    return config["row"], json.loads(wire["choices"][0]["message"]["content"])


def fixture_gateway(tmp_path, answers, *, cost=0.000001, raw_content=None, wrong_model=False):
    gateway, provider = make_gateway(tmp_path, answer=answers[0], cost=cost,
        max_output_tokens=256, raw_content=raw_content)
    original = provider.complete_result
    def complete(request, **options):
        result = original(request, **options)
        wire = json.loads(provider.raw)
        wire["model"] = "wrong-model" if wrong_model else "vendor/model"
        wire["id"] = result.value.candidate.generation_id
        wire["usage"].update(prompt_tokens=12, completion_tokens=8, total_tokens=20)
        if raw_content is None:
            reply = json.loads(wire["choices"][0]["message"]["content"])
            reply["answer"] = answers[min(len(provider.calls) - 1, len(answers) - 1)]
            wire["choices"][0]["message"]["content"] = json.dumps(reply)
        provider.raw = json.dumps(wire).encode()
        candidate = replace(result.value.candidate, content=wire["choices"][0]["message"]["content"])
        return Ok(replace(result.value, candidate=candidate, reply_bytes=provider.raw))
    provider.complete_result = complete
    return gateway, provider


def execute(row, output, gateway):
    return live.live_run(row, output, "vendor/model", "typed_witness", gateway=gateway,
        max_output_tokens=256, max_provider_calls=4)


def test_missing_gateway_refuses_before_output(tmp_path):
    row, _ = inputs()
    with pytest.raises(ValueError, match="PFP_ACCOUNTED_GATEWAY_REQUIRED"):
        live.live_run(row, tmp_path / "new", "vendor/model", "baseline", gateway=None,
            max_output_tokens=256, max_provider_calls=4)
    assert not (tmp_path / "new").exists()


def test_original_judges_and_trusted_second_stage_then_zero_send_replay(tmp_path):
    row, good = inputs()
    bad = deepcopy(good)
    bad["answer"]["steps"] = []
    gateway, provider = fixture_gateway(tmp_path, [bad, good])
    records = execute(row, tmp_path / "new", gateway)
    assert len(records) == len(provider.calls) == 2
    assert "response_format" not in json.loads((tmp_path / "new/stage_1/request.json").read_bytes())
    assert records[0]["result"]["status"] == "PROVIDER_COMPLETED"
    assert records[1]["result"]["status"] == "HOST_ACCEPTED"
    from omega_engine_pfp.use_cases.pfp_proposal import REPAIR_RULES
    second = json.loads(provider.calls[1].user)
    assert REPAIR_RULES[records[0]["result"]["failure_class"]] in second["input"]["prompt"]
    assert live.replay_live(tmp_path / "new") == 2
    assert len(provider.calls) == 2
    receipt = tmp_path / "new/stage_1/receipt.json"
    original_receipt = receipt.read_bytes()
    value = json.loads(original_receipt)
    value["result"]["status"] = "HOST_ACCEPTED"
    receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="REPLAY_"):
        live.replay_live(tmp_path / "new")
    receipt.write_bytes(original_receipt)
    exchange_file = tmp_path / "new/stage_1/exchange.json"
    original_exchange = exchange_file.read_bytes()
    exchange = json.loads(original_exchange)
    exchange["attempted"] = False
    exchange_file.write_text(json.dumps(exchange))
    with pytest.raises(ValueError, match="REPLAY_ATTEMPT_MISMATCH"):
        live.replay_live(tmp_path / "new")
    exchange_file.write_bytes(original_exchange)
    config_file = tmp_path / "new/config.json"
    config = json.loads(config_file.read_bytes())
    config["sources"].pop(next(path for path in config["sources"] if path.endswith("judge_packet/exact_checker.py")))
    config_file.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="REPLAY_SOURCE_MANIFEST_MISMATCH"):
        live.replay_live(tmp_path / "new")


def test_inner_spk_failure_keeps_original_envelope_feedback(tmp_path):
    row, good = inputs()
    gateway, provider = fixture_gateway(tmp_path, [{"not": "SPK-001"}, good])
    records = execute(row, tmp_path / "new", gateway)
    assert len(records) == len(provider.calls) == 2
    assert records[0]["result"]["failure_class"] == "ENVELOPE"
    from omega_engine_pfp.use_cases.pfp_proposal import REPAIR_RULES
    assert REPAIR_RULES["ENVELOPE"] in json.loads(provider.calls[1].user)["input"]["prompt"]
    assert records[1]["result"]["status"] == "HOST_ACCEPTED"


@pytest.mark.parametrize("kind", ["malformed", "wrong-binding", "unknown-cost", "wrong-model"])
def test_invalid_turn_retains_raw_and_stops_before_original_judge(tmp_path, monkeypatch, kind):
    row, good = inputs()
    raw = "not-json" if kind == "malformed" else (
        '{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":{}}'
        if kind == "wrong-binding" else None)
    gateway, provider = fixture_gateway(tmp_path, [good], raw_content=raw,
        cost=None if kind == "unknown-cost" else 0.000001, wrong_model=kind == "wrong-model")
    monkeypatch.setattr(live, "isolated", lambda *a, **k: pytest.fail("bad turn reached judge"))
    records = execute(row, tmp_path / "new", gateway)
    assert len(provider.calls) == len(records) == 1
    assert records[0]["result"]["status"] == "INFRASTRUCTURE_ERROR"
    assert (tmp_path / "new/stage_1/provider_response.json").read_bytes() == provider.raw
    assert records[0]["cost_microusd"] is None if kind == "unknown-cost" else True
    assert live.replay_live(tmp_path / "new") == 1


def test_occupied_output_preserves_bytes_without_sends(tmp_path):
    row, good = inputs()
    gateway, provider = fixture_gateway(tmp_path, [good])
    output = tmp_path / "new"
    output.mkdir()
    (output / "old").write_bytes(b"retained")
    with pytest.raises(ValueError, match="RUN_ALREADY_EXISTS"):
        execute(row, output, gateway)
    assert not provider.calls and (output / "old").read_bytes() == b"retained"


def test_escaped_surrogate_is_retained_as_a_replayable_typed_refusal(tmp_path):
    row, _ = inputs()
    gateway, provider = fixture_gateway(tmp_path, ["\ud800"])
    records = execute(row, tmp_path / "new", gateway)
    assert len(records) == len(provider.calls) == 1
    assert records[0]["result"]["status"] == "INFRASTRUCTURE_ERROR"
    assert records[0]["result"]["failure_class"] == "INVALID_COMPLETION_UNICODE"
    assert (tmp_path / "new/stage_1/provider_response.json").read_bytes() == provider.raw
    exchange = json.loads((tmp_path / "new/stage_1/exchange.json").read_bytes())
    assert exchange["content"] == "\ud800"
    assert live.replay_live(tmp_path / "new") == 1
    assert len(provider.calls) == 1
