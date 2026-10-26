"""Live injected learning checks actual replies and retains the parent's accounting."""

import base64
import json
from types import SimpleNamespace

import pytest

from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnReplyV1
from omega_engine_operads.domain.autopoiesis.learning import (
    CallerContext,
    LearningBlocked,
)
from omega_engine_operads.infrastructure.autopoiesis.agent_learning import (
    call_parent,
)


class BoundExecutor:
    def __init__(self, budget, *, provider="openrouter", wrong_binding=False, bare=False):
        self.budget_controller = budget
        self.provider = provider
        self.calls = []
        self.wrong_binding, self.bare = wrong_binding, bare
        self.raw = ""

    def __call__(self, request):
        self.calls.append(request)
        public = json.loads(request.prompt_text.rsplit("\n\n", 1)[-1])
        assert public["input"]["prompt"] == "Check the source before learning."
        envelope = {key: public[key] for key in ("task_id", "attempt_id", "input_sha256")}
        if self.wrong_binding:
            envelope["input_sha256"] = "0" * 64
        answer = '{"no_change":true}'
        self.raw = json.dumps({"unbound": answer} if self.bare else {**envelope, "answer": answer})
        self.budget_controller.remaining_microusd -= 1
        return SeatTurnReplyV1(self.raw, {}, provider=self.provider, model="chosen-model",
            raw_bytes=b"retained-provider-container", parameters={"temperature": 0}, usage={"tokens": 7})


@pytest.mark.parametrize("provider", ["ide", "openrouter"])
def test_learning_live_turn_is_bound_and_returns_checked_text_with_raw_evidence(provider):
    budget = SimpleNamespace(remaining_microusd=10)
    executor = BoundExecutor(budget, provider=provider)
    context = CallerContext(provider, "chosen-model", "parent", budget)
    reply = call_parent(executor, context, seat="learner", prompt="Check the source before learning.")
    assert reply.reply_text == '{"no_change":true}'
    assert reply.raw_bytes == b"retained-provider-container"
    assert reply.parameters["temperature"] == 0 and reply.usage == {"tokens": 7}
    checked = reply.parameters["pfp"]
    assert checked["schema_valid"] is True and checked["evidence_grade"] == "UNVERIFIED"
    assert base64.b64decode(checked["raw_reply_base64"]).decode() == executor.raw
    assert budget.remaining_microusd == 9 and len(executor.calls) == 1


@pytest.mark.parametrize("wrong_binding,bare", [(True, False), (False, True)])
def test_learning_wrong_binding_or_bare_reply_is_charged_and_refused(wrong_binding, bare):
    budget = SimpleNamespace(remaining_microusd=10)
    executor = BoundExecutor(budget, wrong_binding=wrong_binding, bare=bare)
    context = CallerContext("openrouter", "chosen-model", "parent", budget)
    with pytest.raises(LearningBlocked, match="PFP_LEARNING_REPLY_INVALID") as caught:
        call_parent(executor, context, seat="learner", prompt="Check the source before learning.")
    assert budget.remaining_microusd == 9 and len(executor.calls) == 1
    assert caught.value.reply.raw_bytes == b"retained-provider-container"
    assert base64.b64decode(caught.value.checked["raw_reply_base64"]).decode() == executor.raw


@pytest.mark.parametrize("provider", ["anthropic", "gemini", "local"])
def test_learning_retired_executor_refuses_before_send(provider):
    budget = SimpleNamespace(remaining_microusd=10)
    executor = BoundExecutor(budget, provider=provider)
    context = CallerContext(provider, "chosen-model", "parent", budget)
    with pytest.raises(LearningBlocked, match="LEARNING_EXECUTOR_RETIRED"):
        call_parent(executor, context, seat="learner", prompt="Check the source before learning.")
    assert executor.calls == [] and budget.remaining_microusd == 10
