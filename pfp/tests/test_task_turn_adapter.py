"""Real prepare/check boundaries, without provider calls."""

import base64
from hashlib import sha256
import json

import pytest

from omega_engine_pfp.infrastructure.task_turn import (
    PfpTurnRefusal,
    complete_task_turn,
    prepare_task_turn,
)


def reply(turn, answer):
    fields = turn.prompt.response_schema["properties"]
    return json.dumps({key: fields[key]["const"] for key in (
        "task_id", "attempt_id", "input_sha256"
    )} | {"answer": answer}).encode()


def test_prepare_check_and_offline_replay_bind_task_candidate_checker_and_raw():
    turn = prepare_task_turn(system="Solve the task", user="Input", task_id="task",
        attempt_id="attempt", context={"candidate": "original"}, checker_id="checker-v1")
    raw = reply(turn, "proposal")
    result = turn.check(raw)
    assert result["answer"] == "proposal" and result["schema_valid"]
    assert result["evidence_grade"] == "UNVERIFIED"
    assert turn.replay(result)["answer"] == "proposal"
    assert base64.b64decode(result["raw_reply_base64"]) == raw
    for changed in (
        dict(task_id="wrong"), dict(context={"candidate": "changed"}),
        dict(checker_id="checker-v2"),
    ):
        options = dict(system="Solve the task", user="Input", task_id="task",
            attempt_id="attempt", context={"candidate": "original"}, checker_id="checker-v1")
        options.update(changed)
        with pytest.raises(ValueError, match="REPLAY_BINDING_MISMATCH"):
            prepare_task_turn(**options).replay(result)
    tampered = dict(result, raw_reply_base64=base64.b64encode(raw + b" ").decode())
    with pytest.raises(ValueError, match="REPLAY_RAW_MISMATCH"):
        turn.replay(tampered)


def test_wrong_finite_answer_never_becomes_host_accepted():
    turn = prepare_task_turn(system="Add", user="2+2", task_id="addition", attempt_id="one",
        answer_schema={"type": "integer"}, checker_id="sum-v1")
    judge = (("sum-v1", lambda case, answer: answer == 4),)
    wrong = turn.check(reply(turn, 5), judges=judge, require_checker=True)
    assert wrong["schema_valid"] and wrong["status"] == "PROVIDER_COMPLETED"
    assert wrong["failure_class"] == "CERTIFICATE"
    assert turn.check(reply(turn, 4), judges=judge)["status"] == "HOST_ACCEPTED"


def test_malformed_and_wrong_task_keep_exact_bytes():
    turn = prepare_task_turn(system="Write", user="brief", task_id="task", attempt_id="one")
    for raw in (b"not JSON", reply(turn, "proposal").replace(b'"task"', b'"other"')):
        result = turn.check(raw)
        assert not result["schema_valid"] and result["failure_class"] == "TASK_ENVELOPE"
        assert base64.b64decode(result["raw_reply_base64"]) == raw


def test_complete_facade_actually_prepares_and_checks_around_existing_gateway():
    from omega_engine_woland.domain.providers.types import (
        CandidateRequest,
        CandidateResponse,
        DecodingParamsV1,
    )

    calls = []
    class Gateway:
        malformed = False
        def complete(self, request):
            calls.append(request)
            public = json.loads(request.user)
            raw = json.dumps({key: public[key] for key in (
                "task_id", "attempt_id", "input_sha256")} | {"answer": "proposal"})
            return CandidateResponse("plain bypass" if self.malformed else raw,
                "model", "openrouter", cost_usd=None, transport="live"), None
    gateway = Gateway()
    original = CandidateRequest("System", "Task", decoding=DecodingParamsV1(temperature=0.2,
        response_format={"type": "json_schema", "json_schema": {"name": "old", "schema": {"type": "integer"}}}))
    candidate, receipt, checked = complete_task_turn(gateway, original,
        task_id="task", attempt_id="one")
    assert candidate.content == "proposal" and candidate.cost_usd is None
    assert receipt is None and checked["evidence_grade"] == "UNVERIFIED"
    assert "untrusted proposal" in calls[0].system
    assert calls[0].decoding.temperature == 0.2
    assert calls[0].decoding.response_format["json_schema"]["name"] == "pfp_task_turn"
    gateway.malformed = True
    with pytest.raises(PfpTurnRefusal) as rejected:
        complete_task_turn(gateway, CandidateRequest("System", "Task"), task_id="task", attempt_id="two")
    assert base64.b64decode(rejected.value.checked["raw_reply_base64"]) == b"plain bypass"


def test_unsettled_estimated_reply_is_retained_and_not_sent_again():
    from types import SimpleNamespace

    from omega_engine_woland.domain.providers.types import (
        CandidateRequest,
        CandidateResponse,
        ProviderConfigError,
    )

    calls = []

    class Gateway:
        def complete(self, request, **options):
            calls.append(request)
            public = json.loads(request.user)
            body = json.dumps({key: public[key] for key in (
                "task_id", "attempt_id", "input_sha256")} | {"answer": "kept"}).encode()
            candidate = CandidateResponse(body.decode(), "model", "openrouter",
                cost_usd=None, transport="live")
            error = ProviderConfigError("CompletedCostUnknown")
            error.outcome = SimpleNamespace(
                state="CompletedCostUnknown", candidate=candidate, reply_bytes=body,
                admitted=SimpleNamespace(receipt={"spent_microusd": 12}))
            raise error

    with pytest.raises(PfpTurnRefusal) as rejected:
        complete_task_turn(Gateway(), CandidateRequest("System", "Task"),
            task_id="task", attempt_id="cost")
    assert len(calls) == 1
    refusal = rejected.value
    assert refusal.code == "CompletedCostUnknown" and refusal.attempt_state == "CompletedCostUnknown"
    assert refusal.checked["schema_valid"] and refusal.checked["answer"] == "kept"
    assert base64.b64decode(refusal.checked["raw_reply_base64"]) == refusal.candidate.content.encode()
    assert refusal.budget_receipt == {"spent_microusd": 12}
    assert isinstance(refusal.__cause__, ProviderConfigError)


def test_pre_dispatch_provider_refusal_has_no_reply_to_retain():
    from omega_engine_woland.domain.providers.types import CandidateRequest, ProviderConfigError

    class Gateway:
        def complete(self, request, **options):
            raise ProviderConfigError("ESTIMATED_BUDGET_EXCEEDED")

    with pytest.raises(ProviderConfigError, match="ESTIMATED_BUDGET_EXCEEDED"):
        complete_task_turn(Gateway(), CandidateRequest("System", "Task"),
            task_id="task", attempt_id="blocked")


@pytest.mark.parametrize("invalid_unicode", [False, True])
def test_unknown_cost_checks_actual_completion_and_retains_distinct_provider_wire(tmp_path, invalid_unicode):
    from omega_engine_pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
    from omega_engine_woland.domain.providers.types import CandidateRequest, Provider, ProviderConfigError
    from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway

    sent = []

    def wire(provider, model, request):
        public = json.loads(request.user)
        completion = "\ud800" if invalid_unicode else json.dumps({
            key: public[key] for key in ("task_id", "attempt_id", "input_sha256")
        } | {"answer": "preserved proposal"})
        raw = json.dumps({
            "id": "synthetic-generation", "model": model,
            "choices": [{"message": {"content": completion}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10},
        }).encode()
        sent.append((raw, completion))
        return raw

    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model="fixture/task",
        transport=wire, max_output_tokens=256)
    price = dict(catalog_sha256="synthetic-price-snapshot", row=dict(id="fixture/task",
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    gateway = EstimatedBudgetGateway(provider, model="fixture/task", price=price,
        limit_microusd=50000, max_calls=2, accounting_path=tmp_path / "budget.sqlite3")
    request = CandidateRequest("System", "Task")
    with pytest.raises(PfpTurnRefusal) as rejected:
        complete_task_turn(gateway, request, task_id="task", attempt_id="unknown-cost",
            provider=Provider.OPENROUTER, model="fixture/task")
    refusal = rejected.value
    assert refusal.code == "CompletedCostUnknown" and len(sent) == 1
    raw_wire, completion = sent[0]
    checked = refusal.checked
    retained_completion = base64.b64decode(checked["raw_reply_base64"])
    assert retained_completion == completion.encode("utf-8", errors="surrogatepass")
    assert retained_completion != raw_wire
    assert checked["raw_reply_sha256"] == sha256(retained_completion).hexdigest()
    assert base64.b64decode(checked["provider_wire"]["raw_reply_base64"]) == raw_wire
    assert checked["provider_wire"]["raw_reply_sha256"] == sha256(raw_wire).hexdigest()
    assert checked["provider_wire"]["raw_reply_bytes"] == len(raw_wire)
    assert checked["schema_valid"] is not invalid_unicode
    if invalid_unicode:
        assert checked["reason"] == "INVALID_COMPLETION_UNICODE"
        assert checked["raw_reply_encoding"] == "utf-8-surrogatepass"
    else:
        assert checked["answer"] == "preserved proposal"
    assert checked["status"] == "PROVIDER_COMPLETED"
    assert checked["evidence_grade"] == "UNVERIFIED"
    with pytest.raises(ProviderConfigError, match="UNRECONCILED_ATTEMPT"):
        complete_task_turn(gateway, request, task_id="task", attempt_id="second-attempt",
            provider=Provider.OPENROUTER, model="fixture/task")
    assert len(sent) == 1


def test_actual_provider_parser_lone_surrogate_becomes_typed_task_refusal():
    from omega_engine_woland.domain.providers.types import CandidateRequest, Provider
    from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway

    sends = []

    def wire(provider, model, request):
        sends.append(request)
        return json.dumps({"id": "synthetic-unicode", "model": model,
            "choices": [{"message": {"content": "\ud800"}}]}).encode()

    gateway = unbudgeted_gateway(provider=Provider.OPENROUTER, model="fixture/task",
        transport=wire, max_output_tokens=256)
    with pytest.raises(PfpTurnRefusal) as rejected:
        complete_task_turn(gateway, CandidateRequest("System", "Task"),
            task_id="task", attempt_id="unicode", provider=Provider.OPENROUTER, model="fixture/task")
    checked = rejected.value.checked
    assert len(sends) == 1 and rejected.value.code == "PFP_TASK_ENVELOPE"
    assert checked["schema_valid"] is False and checked["evidence_grade"] == "UNVERIFIED"
    assert checked["reason"] == "INVALID_COMPLETION_UNICODE"
    assert checked["raw_reply_encoding"] == "utf-8-surrogatepass"
    assert base64.b64decode(checked["raw_reply_base64"]) == b"\xed\xa0\x80"
