"""WF1 behavior and decisive counterexamples; all provider replies are fixtures."""

import base64
import json
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

import pytest

from pfp.workflows.tests.gateways import make_gateway
from pfp.workflows.wf0001 import workflow
from pfp.workflows.wf0001.runner import runtime as runner


@pytest.fixture
def spec():
    return json.loads(workflow.resource_text("examples/integer_sum.task.json"))


def reply(spec, answer, **overrides):
    binding = workflow.prepare_task(spec).binding
    value = {key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    value.update(answer=answer, **overrides)
    return json.dumps(value, ensure_ascii=False).encode()


def checked_run(tmp_path, spec, answer):
    root = tmp_path / "run"
    runner.prepare_run(spec, root)
    raw = tmp_path / "reply.json"
    raw.write_bytes(reply(spec, answer))
    return root, runner.check_run(root, raw)


def test_basic_template_reuses_manifest_and_preserves_seed_without_hidden_answers(spec):
    spec["seed_prompt"] += " Preserve Ω and the original spacing."
    # The host-only label is supplied to the generic schema-only path.
    spec["checker"] = "schema_only"
    spec["input"]["expected_answer"] = "HOST_ONLY_SENTINEL"
    turn = workflow.prepare_task(spec)
    public = json.loads(turn.prompt.user)
    assert public["objective"] == spec["seed_prompt"]
    assert public["input"] == {"values": [17, 25, -4]}
    assert "HOST_ONLY_SENTINEL" not in turn.prompt.system + turn.prompt.user
    assert "semantic_policy_manifest:" in turn.prompt.system
    assert "antibody_injections: []" in turn.prompt.system
    assert set(turn.prompt.response_schema["properties"]) == {
        "task_id", "attempt_id", "input_sha256", "answer"}


def test_valid_answer_and_well_typed_wrong_answer_have_different_host_outcomes(spec):
    accepted = workflow.check_reply(spec, reply(spec, {"total": 38}))
    wrong = workflow.check_reply(spec, reply(spec, {"total": 39}))
    assert accepted["status"] == "HOST_ACCEPTED"
    assert wrong["schema_valid"] is True
    assert wrong["status"] == "PROVIDER_COMPLETED" and wrong["failure_class"] == "CERTIFICATE"
    assert accepted["authority_effect"] == wrong["authority_effect"] == "None"


@pytest.mark.parametrize("total", [True, 38.0, "38", None])
def test_wrong_primitive_types_are_not_coerced(spec, total):
    result = workflow.check_reply(spec, reply(spec, {"total": total}))
    assert result["schema_valid"] is False and result["status"] != "HOST_ACCEPTED"


@pytest.mark.parametrize("field,value", [
    ("task_id", "other-task"), ("attempt_id", "attempt-2"), ("input_sha256", "wrong")])
def test_stale_binding_refused(spec, field, value):
    assert workflow.check_reply(spec, reply(spec, {"total": 38}, **{field: value}))["schema_valid"] is False


@pytest.mark.parametrize("raw", [b'{}', b'not JSON', b'{"answer":1,"answer":2}',
                                b'```json\n{}\n```', b'\xff'])
def test_malformed_actual_bytes_are_retained(spec, raw):
    result = workflow.check_reply(spec, raw)
    assert result["schema_valid"] is False
    assert base64.b64decode(result["raw_reply_base64"]) == raw
    assert result["raw_reply_sha256"] == sha256(raw).hexdigest()


def test_schema_only_summary_is_unverified_not_host_accepted():
    source = json.loads(workflow.resource_text("examples/summary.task.json"))
    result = workflow.check_reply(source, reply(source, {
        "summary": "An import points to a moved package.", "next_action": "Inspect the caller."}))
    assert result["schema_valid"] is True
    assert result["status"] == "PROVIDER_COMPLETED" and result["evidence_grade"] == "UNVERIFIED"


@pytest.mark.parametrize("extension", ["agents", "main_stages", "pre_mining", "operad_extraction",
                                     "lggr", "seed_rewrite", "maximum_retries"])
def test_future_workflow_features_are_rejected_before_run_creation(tmp_path, spec, extension):
    spec[extension] = 5
    root = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="WF1_INVALID_TASK_SPECIFICATION"):
        runner.prepare_run(spec, root)
    assert not root.exists()


@pytest.mark.parametrize("values", [[True], [1.0], (1, 2), []])
def test_sum_input_contract_refuses_coercion(spec, values):
    spec["input"]["values"] = values
    with pytest.raises(ValueError):
        workflow.prepare_task(spec)


def test_external_capture_replays_read_only_without_claiming_provider_usage(tmp_path, spec):
    root, receipt = checked_run(tmp_path, spec, {"total": 38})
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    replayed = runner.replay_run(root)
    assert replayed["replay_verified"] and replayed["status"] == "HOST_ACCEPTED"
    assert replayed["provider_calls_in_this_command"] == 0
    assert receipt["external_provider_calls"] is None and receipt["provider_cost_usd"] is None
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}
    assert (root / "system_prompt.txt").read_text() == workflow.prepare_task(spec).prompt.system


def test_large_valid_reply_replays_when_packaged_receipt_exceeds_reply_limit(tmp_path, spec):
    spec["checker"] = "schema_only"
    spec["answer_schema"] = {"type": "string"}
    root, result = checked_run(tmp_path, spec, "x" * 700_000)
    assert result["check"]["schema_valid"] is True
    assert (root / "response.raw").stat().st_size < 1_048_576
    assert (root / "receipt.json").stat().st_size > 1_048_576
    assert runner.replay_run(root)["check"]["schema_valid"] is True


@pytest.mark.parametrize("member", ["response.raw", "prepared.json", "receipt.json"])
def test_one_byte_tampering_breaks_replay(tmp_path, spec, member):
    root, _ = checked_run(tmp_path, spec, {"total": 38})
    path = root / member
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="RECEIPT_DIGEST_MISMATCH"):
        runner.replay_run(root)


def test_saved_pass_flag_cannot_replace_reexecution_even_after_rehash(tmp_path, spec):
    root, receipt = checked_run(tmp_path, spec, {"total": 39})
    receipt["status"] = receipt["check"]["status"] = "HOST_ACCEPTED"
    (root / "receipt.json").write_text(json.dumps(receipt))
    manifest_path = root / "receipt_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["receipt.json"] = sha256((root / "receipt.json").read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="WF1_REPLAY_CHECK_MISMATCH"):
        runner.replay_run(root)


def test_run_namespace_and_single_response_slot_cannot_be_reused(tmp_path, spec):
    root, _ = checked_run(tmp_path, spec, {"total": 38})
    original = (root / "response.raw").read_bytes()
    with pytest.raises(FileExistsError):
        runner.prepare_run(spec, root)
    raw = tmp_path / "second.json"
    raw.write_bytes(reply(spec, {"total": 39}))
    with pytest.raises(FileExistsError):
        runner.check_run(root, raw)
    assert (root / "response.raw").read_bytes() == original


def test_changed_checker_sources_refuse_historical_replay(tmp_path, spec, monkeypatch):
    root, _ = checked_run(tmp_path, spec, {"total": 38})
    altered = deepcopy(runner.source_identity())
    altered["sources"]["use_cases/pfp_proposal.py"] = "changed"
    monkeypatch.setattr(runner, "source_identity", lambda: altered)
    with pytest.raises(ValueError, match="WF1_IMPLEMENTATION_MISMATCH"):
        runner.replay_run(root)


def test_accounted_runner_sends_one_basic_prompt_and_replays_fixture(tmp_path, spec):
    gateway, provider = make_gateway(tmp_path, max_calls=1, answer={"total": 38})
    root = tmp_path / "live-shaped-fixture"
    result = runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert len(provider.calls) == 1 and result["status"] == "HOST_ACCEPTED"
    assert provider.calls[0].system == workflow.prepare_task(spec).prompt.system
    assert json.loads(provider.calls[0].user)["objective"] == spec["seed_prompt"]
    assert result["provider"]["transport"] == "fixture"
    assert base64.b64decode(result["provider"]["raw_reply_base64"]) == provider.raw
    assert runner.replay_run(root)["status"] == "HOST_ACCEPTED"
    with pytest.raises(ValueError, match="WF1_RUN_ALREADY_ATTEMPTED"):
        runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert len(provider.calls) == 1


def test_larger_gateway_allowance_refused_before_any_send(tmp_path, spec):
    gateway, provider = make_gateway(tmp_path, max_calls=2)
    with pytest.raises(ValueError, match="WF1_ONE_CALL_GATEWAY_REQUIRED"):
        runner.run_accounted(spec, tmp_path / "run", gateway=gateway,
                             model="vendor/model", max_output_tokens=256)
    assert not provider.calls


def test_unknown_billing_does_not_become_success_and_cannot_be_replaced_manually(tmp_path, spec):
    gateway, provider = make_gateway(tmp_path, max_calls=1, answer={"total": 38}, cost=None)
    root = tmp_path / "unknown-cost-fixture"
    result = runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert len(provider.calls) == 1
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["provider"]["cost_usd"] is None
    assert runner.replay_run(root)["status"] == "INFRASTRUCTURE_ERROR"
    raw = tmp_path / "replacement.json"
    raw.write_bytes(reply(spec, {"total": 38}))
    with pytest.raises(ValueError, match="WF1_ACCOUNTED_RUN_NEEDS_OWN_RESPONSE"):
        runner.check_run(root, raw)


def test_malformed_accounted_reply_is_not_repaired_or_retried(tmp_path, spec):
    gateway, provider = make_gateway(tmp_path, max_calls=1, raw_content="not JSON")
    root = tmp_path / "bad-reply-fixture"
    result = runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert len(provider.calls) == 1 and not result["check"]["schema_valid"]
    assert (root / "response.raw").read_bytes() == b"not JSON"
    assert runner.replay_run(root)["check"]["schema_valid"] is False


def test_served_model_identity_mismatch_cannot_be_a_success(tmp_path, spec, monkeypatch):
    from operations.domain.rop.result import Ok

    gateway, provider = make_gateway(tmp_path, max_calls=1, answer={"total": 38})
    original = provider.complete_result

    def substituted_model(*args, **kwargs):
        result = original(*args, **kwargs)
        return Ok(replace(result.value, candidate=replace(result.value.candidate, model="other/model")))

    monkeypatch.setattr(provider, "complete_result", substituted_model)
    root = tmp_path / "identity-mismatch"
    result = runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["failure_class"] == "WF1_PROVIDER_IDENTITY_MISMATCH"
    assert runner.replay_run(root)["status"] == "INFRASTRUCTURE_ERROR"
    assert len(provider.calls) == 1


def test_shipped_control_is_explicitly_a_fixture_and_bound_to_example(tmp_path, spec):
    root = tmp_path / "shipped-control"
    runner.prepare_run(spec, root)
    fixture = tmp_path / "fixture.json"
    fixture.write_text(workflow.resource_text("examples/integer_sum.reply.fixture.json"), encoding="utf-8")
    result = runner.check_run(root, fixture, fixture=True)
    assert result["origin"] == "HAND_AUTHORED_FIXTURE"
    assert result["status"] == "HOST_ACCEPTED"
    assert result["external_provider_calls"] == result["provider_cost_usd"] == 0


def test_provider_failure_retains_wire_without_forging_a_reply(tmp_path, spec, monkeypatch):
    from operations.domain.rop.result import Err
    from adversary.domain.providers.attempt import ProviderFailure, RetryClass

    gateway, provider = make_gateway(tmp_path, max_calls=1)
    raw = b'{"error":"fixture rejection"}'
    failure = ProviderFailure("FIXTURE_REJECTED", "fixture", RetryClass.TERMINAL,
                              reply_bytes=raw)
    monkeypatch.setattr(provider, "complete_result", lambda *a, **k: Err(failure))
    root = tmp_path / "provider-rejected"
    result = runner.run_accounted(spec, root, gateway=gateway, model="vendor/model", max_output_tokens=256)
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert not (root / "response.raw").exists()
    assert not (root / "receipt.json").exists()
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == raw


def test_public_cli_prepare_check_and_replay(tmp_path, spec, capsys):
    task = tmp_path / "task.json"
    task.write_text(json.dumps(spec))
    root = tmp_path / "cli"
    assert runner.main(["prepare", str(task), "--output", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["provider_calls"] == 0
    raw = tmp_path / "reply.json"
    raw.write_bytes(reply(spec, {"total": 38}))
    assert runner.main(["check", str(root), str(raw)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "HOST_ACCEPTED"
    assert runner.main(["replay", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["replay_verified"] is True


def test_profile_is_wf1_only():
    profile = json.loads(workflow.resource_text("workflow.json"))
    assert profile["workflow_id"] == "WF1"
    assert profile["agent_count"] == profile["main_stages"] == profile["maximum_provider_calls"] == 1
    assert profile["maximum_retries"] == 0
    assert all(profile[key] is False for key in (
        "operad_extraction", "pre_mining", "lggr", "seed_rewrite"))
