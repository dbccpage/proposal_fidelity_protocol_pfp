"""One synthetic raw-provider fixture for current PFP matrix composition tests.

The original solver sees only the actual public task. Synthetic costs/usage are
explicit response data, never claimed as live model or vendor billing evidence.
"""

import json
from hashlib import sha256
from types import SimpleNamespace

from omega_engine_pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway, DurableRunGateway
from omega_engine_woland.domain.providers.types import Provider
from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway


def make_solver_gateway(tmp_path, solver, cases=(), *, model, max_output_tokens,
                        input_tokens=10, output_tokens=20, cost=0.000001,
                        max_calls=10, raw_content=None, failure=None, hard_budget=False,
                        limit_microusd=50000, liability_microusd=1000):
    fixture = SimpleNamespace(calls=[], raw=[], cases=[], responses=[])
    cases_by_id = {case["case_id"]: case for case in cases}

    def send(provider, selected_model, request):
        fixture.calls.append(request)
        if failure is not None:
            raise failure
        task = json.loads(request.user)
        public = task["input"]["prompt"]
        # complete_pilot_turn also accepts an original messages conversation.
        try:
            conversation = json.loads(public)
        except ValueError:
            conversation = None
        if isinstance(conversation, list):
            public = next(row["content"] for row in reversed(conversation) if row["role"] == "user")
        start = public.find("{")
        if start < 0:
            raise AssertionError("fixture received no public task JSON")
        case, _ = json.JSONDecoder().raw_decode(public[start:])
        if not isinstance(case, dict):
            raise AssertionError("fixture public task is not an object")
        if case.get("case_id") in cases_by_id and case != cases_by_id[case["case_id"]]:
            raise AssertionError("fixture public case differs from original input")
        fixture.cases.append(case)
        reply = {key: task[key] for key in ("task_id", "attempt_id", "input_sha256")}
        reply["answer"] = solver(case)
        response = dict(id=f"synthetic-matrix-{len(fixture.calls)}", model=selected_model,
            choices=[dict(message=dict(role="assistant", content=raw_content
                if raw_content is not None else json.dumps(reply)), finish_reason="stop")],
            usage=dict(prompt_tokens=input_tokens, completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens, cost=cost))
        raw = json.dumps(response, ensure_ascii=True).encode("ascii")
        fixture.responses.append(response)
        fixture.raw.append(raw)
        return raw

    if hard_budget:
        from omega_engine_woland.domain.providers.allowlist import ModelAllowlist
        from omega_engine_woland.domain.providers.budget import (
            BudgetController, GatewayPolicy, PriceTable, fixture_pricing_observation,
        )
        from omega_engine_woland.infrastructure.providers.gateway import OearsLlmGateway

        class SyntheticLiability:
            provenance = "synthetic-matrix-fixture"

            def maximum_liability(self, *args):
                return liability_microusd  # This local fixture cannot charge a vendor account.

            def dispatch(self, admitted):
                return send(admitted.provider, admitted.model, admitted.request)

        provider = OearsLlmGateway(ModelAllowlist.empty().allow(Provider.OPENROUTER, model),
            GatewayPolicy(PriceTable.empty().with_observation(fixture_pricing_observation(model, 1000, 1000)),
                BudgetController(limit_microusd),
                max_output_tokens, pricing_clock=lambda: "2026-10-12T12:00:00.000000Z"),
            SyntheticLiability(), Provider.OPENROUTER, model)
        gateway = DurableRunGateway(provider, accounting_path=tmp_path / "matrix-budget.sqlite3",
            run_id="synthetic-matrix", objective_sha256=sha256(b"synthetic public matrix tasks").hexdigest(),
            max_calls=max_calls)
    else:
        provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model=model,
            transport=send, max_output_tokens=max_output_tokens)
        price = dict(catalog_sha256="synthetic-matrix-price", row=dict(id=model,
            pricing=dict(prompt="0.000000001", completion="0.000000001")))
        gateway = EstimatedBudgetGateway(provider, model=model, price=price,
            limit_microusd=limit_microusd, max_calls=max_calls, accounting_path=tmp_path / "matrix-budget.sqlite3")
    fixture.send = send
    return gateway, fixture
