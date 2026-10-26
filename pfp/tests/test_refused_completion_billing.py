"""A charged unusable answer is not an unknown send or an accepted proposal."""

import base64
import json
from copy import deepcopy
from hashlib import sha256

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
from omega_engine_woland.domain.providers.types import CandidateRequest, Provider
from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway

REQUEST = CandidateRequest("System", "Original task")


def payload():
    return dict(id="known-generation", model="vendor/model",
        choices=[dict(message=dict(content=None), finish_reason="length")],
        usage=dict(prompt_tokens=10, completion_tokens=8, cost="0.000001"))


def bind(tmp_path, value=None, *, transport=None):
    sends = []
    raw = json.dumps(payload() if value is None else value).encode()

    def sender(*args):
        sends.append(args)
        return transport(*args) if transport else raw

    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model="vendor/model",
        transport=sender, max_output_tokens=64)
    price = dict(catalog_sha256="synthetic-price-v1", row=dict(id="vendor/model",
        pricing={"prompt": "0.0000001", "completion": "0.0000002"}))
    bound = EstimatedBudgetGateway(provider, model="vendor/model", price=price,
        limit_microusd=50000, max_calls=6, accounting_path=tmp_path / "refused.sqlite3",
        run_id="one-original-run", objective_sha256=sha256(b"original objective").hexdigest(),
        max_output_tokens=64)
    return bound, sends, raw


def send(bound, action="first"):
    return bound.for_action(action).complete_result(REQUEST,
        provider=Provider.OPENROUTER, model="vendor/model")


def test_known_empty_completion_settles_without_becoming_a_candidate(tmp_path):
    bound, sends, raw = bind(tmp_path)
    result = send(bound)
    assert isinstance(result, Err) and result.error.code == "PROVIDER_REFUSED"
    assert result.error.attempt_state == "CompletedSettled"
    metadata = result.error.response_metadata()
    assert metadata["input_tokens"] == 10 and metadata["output_tokens"] == 8
    assert metadata["cost_usd"] == 0.000001 and metadata["generation_id"] == "known-generation"
    assert base64.b64decode(metadata["raw_reply_base64"]) == raw
    assert json.loads(bound.raw_reply("first"))["choices"][0]["message"]["content"] is None
    assert bound.action("first")["state"] == "settled"
    assert bound.action("first")["actual"] == 1
    assert not hasattr(result.error.usage_observation, "content")
    reopened, replacement, _ = bind(tmp_path)
    assert send(reopened).error.code == "PFP_ACTION_ALREADY_CLAIMED"
    for _ in range(2):
        recovered = reopened.for_action("first").recover_result(REQUEST,
            provider=Provider.OPENROUTER, model="vendor/model")
        assert isinstance(recovered, Err) and recovered.error.attempt_state == "CompletedSettled"
        assert recovered.error.reply_bytes == raw
        with reopened.ledger.transaction(50000) as state:
            assert state["spent"] == 1
    assert len(sends) == 1 and not replacement


def test_known_refusal_keeps_call_spend_and_allows_explicit_new_action(tmp_path):
    value = payload()
    count = 0

    def sender(*args):
        nonlocal count
        count += 1
        changed = deepcopy(value)
        changed["id"] = "generation-" + str(count)
        if count == 2:
            changed["choices"][0]["message"]["content"] = "original valid answer"
        return json.dumps(changed).encode()

    bound, sends, _ = bind(tmp_path, transport=sender)
    assert isinstance(send(bound), Err)
    second = send(bound, "second")
    assert isinstance(second, Ok) and second.value.state == "CompletedSettled"
    with bound.ledger.transaction(50000) as state:
        assert state["spent"] == 2 and len(state["attempts"]) == 2
    assert len(sends) == 2


@pytest.mark.parametrize("fault", ["missing_cost", "missing_usage", "bool_count", "bool_cost",
    "foreign_model", "missing_identity", "output_overrun", "input_overrun", "duplicate_json"])
def test_unavailable_or_invalid_refused_billing_retains_hold_across_restart(tmp_path, fault):
    value = payload()
    if fault == "missing_cost":
        value["usage"].pop("cost")
    elif fault == "missing_usage":
        value["usage"].pop("prompt_tokens")
    elif fault == "bool_count":
        value["usage"]["prompt_tokens"] = True
    elif fault == "bool_cost":
        value["usage"]["cost"] = True
    elif fault == "foreign_model":
        value["model"] = "foreign/model"
    elif fault == "missing_identity":
        value["id"] = ""
    elif fault == "output_overrun":
        value["usage"]["completion_tokens"] = 65
    elif fault == "input_overrun":
        value["usage"]["prompt_tokens"] = 1000000
    transport = (lambda *args: b'{"model":"vendor/model","model":"vendor/model"}') if fault == "duplicate_json" else None
    bound, sends, raw = bind(tmp_path, value, transport=transport)
    refused = send(bound)
    assert isinstance(refused, Err) and refused.error.attempt_state != "CompletedSettled"
    assert bound.action("first")["state"] != "settled"
    retained = bound.raw_reply("first")
    if transport is None:
        assert retained == raw
    restarted, replacement, _ = bind(tmp_path)
    assert send(restarted, "second").error.code == "UNRECONCILED_ATTEMPT"
    assert len(sends) == 1 and not replacement


def test_refused_over_estimate_retains_actual_bill_and_blocks_future_send(tmp_path):
    value = payload()
    value["usage"]["cost"] = "0.001"
    bound, sends, raw = bind(tmp_path, value)
    refused = send(bound)
    assert isinstance(refused, Err) and refused.error.attempt_state == "CompletedOverEstimatedBudget"
    assert refused.error.response_metadata()["cost_usd"] == 0.001
    with bound.ledger.transaction(50000) as state:
        assert state["spent"] == 1000 and state["attempts"]["first"]["actual"] == 1000
    assert send(bound, "second").error.code == "UNRECONCILED_ATTEMPT"
    assert bound.raw_reply("first") == raw and len(sends) == 1


def test_refused_wire_survives_crash_and_explicit_recovery_never_resends(tmp_path, monkeypatch):
    bound, sends, raw = bind(tmp_path)

    def interrupt(*args):
        raise KeyboardInterrupt("after wire custody, before accounting")

    monkeypatch.setattr(bound, "_finish_refused", interrupt)
    with pytest.raises(KeyboardInterrupt):
        send(bound)
    reopened, replacement, _ = bind(tmp_path)
    recovered = reopened.for_action("first").recover_result(REQUEST,
        provider=Provider.OPENROUTER, model="vendor/model")
    assert isinstance(recovered, Err) and recovered.error.attempt_state == "CompletedSettled"
    assert recovered.error.reply_bytes == raw and len(sends) == 1 and not replacement
    with reopened.ledger.transaction(50000) as state:
        assert state["spent"] == 1


def test_hard_mode_keeps_refused_usage_pending_until_trusted_receipt(tmp_path):
    from omega_engine_pfp.tests.test_durable_run_budget import (
        SyntheticTransport,
        generation_payload,
    )
    from omega_engine_pfp.tests.test_durable_run_budget import (
        bind as hard_bind,
    )
    from omega_engine_pfp.tests.test_durable_run_budget import (
        send as hard_send,
    )

    class EmptyTransport(SyntheticTransport):
        def dispatch(self, admitted):
            wire = json.loads(super().dispatch(admitted))
            wire["choices"][0]["message"]["content"] = None
            return json.dumps(wire).encode()

    bound, transport = hard_bind(tmp_path, EmptyTransport())
    refused = hard_send(bound, "first")
    assert isinstance(refused, Err) and refused.error.attempt_state == "CompletedPendingSettlement"
    assert refused.error.response_metadata()["cost_usd"] == 0.001
    assert bound.budget.spent_microusd == 10000
    # This is separate caller-supplied trusted receipt evidence, not model text.
    assert bound.settle_generation("first", generation_payload(bound, "first")).status == "RECONCILED"
    assert bound.budget.spent_microusd == 1000
    recovered = bound.for_action("first").recover_result(CandidateRequest("System", "Solve the original task"),
        provider=Provider.OPENROUTER, model=bound.action("first")["binding"]["model"])
    assert isinstance(recovered, Err) and recovered.error.code == "PROVIDER_REFUSED"
    assert recovered.error.attempt_state == "CompletedSettled"
    assert json.loads(recovered.error.reply_bytes)["choices"][0]["message"]["content"] is None
    assert len(transport.calls) == 1
