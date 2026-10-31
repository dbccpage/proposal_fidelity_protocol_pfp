"""Scripted fixture gateways only; never counted as live model calls. AuthorityEffect: None."""

import json
from dataclasses import replace
from operations.domain.rop.result import Err, Ok
from pfp.infrastructure.workflow_accounting import EstimatedBudgetGateway
from adversary.domain.providers.attempt import AdmittedRequest, CompletionOutcome
from adversary.domain.providers.types import CandidateRequest, CandidateResponse, Provider

class Gateway:
    def __init__(self, content, *, failure=None, raw=False):
        self.content, self.failure, self.calls, self.raw = content, failure, [], raw
        self.bound_actions = []

    def for_action(self, action_id):
        self.bound_actions.append(action_id)
        return self

    def complete_result(self, request, **kwargs):
        self.calls.append((request, kwargs))
        if self.failure is not None:
            return Err(self.failure)
        sequence = len(self.calls)
        admitted = AdmittedRequest(f"attempt-{sequence}", "", "sha256:request", Provider.OPENROUTER,
            "vendor/model", request, 512, None, None)
        content = self.content
        if not self.raw:
            public, _end = json.JSONDecoder().raw_decode(request.user)
            answer = json.loads(content) if content.lstrip().startswith("{") else content
            content = json.dumps({key: public[key] for key in ("task_id", "attempt_id", "input_sha256")}
                | {"answer": answer})
        candidate = CandidateResponse(content, "vendor/model", "openrouter",
            input_tokens=20, output_tokens=10, generation_id=f"generation-{sequence}", transport="synthetic-unit")
        wire = json.dumps({"choices": [{"message": {"content": content}}],
            "model": candidate.model, "usage": {"prompt_tokens": 20, "completion_tokens": 10}}).encode()
        return Ok(CompletionOutcome(candidate, admitted, reply_bytes=wire))

def gateway(tmp_path, *, cost=0.000010, limit=100, max_calls=2, generation=True):
    class ProviderGateway(Gateway):
        def complete_result(self, request, **options):
            outcome = super().complete_result(request, **options).value
            self.returned_wire = outcome.reply_bytes
            return Ok(replace(outcome, candidate=replace(outcome.candidate,
                cost_usd=cost, generation_id=f"generation-{len(self.calls)}" if generation else "")))
    provider = ProviderGateway("raw", raw=True)
    price = dict(catalog_sha256="snapshot", row=dict(id="vendor/model",
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    return EstimatedBudgetGateway(provider, model="vendor/model", price=price,
        limit_microusd=limit, max_calls=max_calls, accounting_path=tmp_path / "budget.sqlite3"), provider

def make_gateway(tmp_path, *, model="vendor/model", cost=0.000001, answer=None,
    raw_content=None, max_calls=4, accounting_name="budget.sqlite3", max_output_tokens=256):
    class ScriptedProvider:
        unbudgeted_max_output_tokens = max_output_tokens

        def __init__(self):
            self.calls = []
            self.raw = b""

        def complete_result(self, request, **options):
            # The host reservation exists before the provider receives the turn.
            with bound.ledger.transaction(bound.limit) as state:
                assert any(row["state"] == "reserved" for row in state["attempts"].values())
            self.calls.append(request)
            prepared = json.loads(request.user)
            reply = {key: prepared[key] for key in ("task_id", "attempt_id", "input_sha256")}
            reply["answer"] = answer if answer is not None else {"case_id": "case_01", "value": 1}
            content = raw_content if raw_content is not None else json.dumps(reply)
            self.raw = json.dumps({"choices": [{"message": {"content": content},
                "finish_reason": "stop"}], "usage": {"cost": cost}, "extra": "retained α"},
                ensure_ascii=False).encode("utf-8")
            candidate = CandidateResponse(content, model, "openrouter", input_tokens=12,
                output_tokens=8, transport="fixture", generation_id=f"{model}-{len(self.calls)}",
                cost_usd=cost)
            admitted = AdmittedRequest(f"attempt-{model}-{len(self.calls)}", "", "request",
                Provider.OPENROUTER, model, request, max_output_tokens, None, None)
            return Ok(CompletionOutcome(candidate, admitted, reply_bytes=self.raw))

    provider = ScriptedProvider()
    price = dict(catalog_sha256="fixture-price", row=dict(id=model,
        pricing={"prompt": "0.000000001", "completion": "0.000000001"}))
    bound = EstimatedBudgetGateway(provider, model=model, price=price, limit_microusd=4999,
        max_calls=max_calls, accounting_path=tmp_path / accounting_name)
    return bound, provider
