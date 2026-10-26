"""Route legacy pilot turns through PFP and the existing accounted provider boundary."""

import base64
import json
import time
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err
from omega_engine_pfp.infrastructure.estimated_gateway import (
    DurableRunGateway,
    EstimatedBudgetGateway,
    create_accounted_openrouter_gateway,
    create_accounted_anthropic_gateway,
)
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_woland.domain.providers.types import (
    CandidateRequest,
    DecodingParamsV1,
    Provider,
    thaw_json,
)
from omega_engine_woland.infrastructure.providers.openai_compat import build_openai_compat_body
from omega_engine_woland.infrastructure.providers.anthropic_messages import build_anthropic_body


def _output_bound(gateway):
    inner = gateway.gateway
    policy = getattr(inner, "policy", None)
    return (policy.max_output_tokens if policy is not None
        else getattr(inner, "unbudgeted_max_output_tokens", None))


def _scope(gateway, model, max_tokens=None, *, provider=Provider.OPENROUTER):
    if not isinstance(gateway, (EstimatedBudgetGateway, DurableRunGateway)):
        raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
    if isinstance(gateway, EstimatedBudgetGateway):
        if gateway.model != model or gateway.provider != provider:
            raise ValueError("PRICING_MODEL_MISMATCH")
        limit, calls, run = gateway.limit, gateway.max_calls, None
        if provider == Provider.ANTHROPIC:
            run = json.dumps(gateway.scope, sort_keys=True)
    else:
        if provider != Provider.OPENROUTER:
            raise ValueError("PFP_ANTHROPIC_ESTIMATED_PROFILE_REQUIRED")
        limit, calls = gateway.scope["limit_microusd"], gateway.scope["max_calls"]
        run = json.dumps(gateway.scope, sort_keys=True)
    output = _output_bound(gateway)
    if type(output) is not int or output < 1:
        raise ValueError("PFP_OUTPUT_BOUND_REQUIRED")
    if max_tokens is not None and (type(max_tokens) is not int or max_tokens != output):
        raise ValueError("PFP_OUTPUT_BOUND_MISMATCH")
    with gateway.ledger.transaction(limit) as state:
        original = state.setdefault("pilot_max_calls", calls)
        if original != calls:
            raise ValueError("PFP_CALL_ALLOWANCE_MISMATCH")
    return Path(gateway.ledger.path).resolve(), gateway.ledger.budget_id, limit, calls, run


def validate_pilot_gateways(gateways, model_ids, *, max_tokens=None, provider=Provider.OPENROUTER):
    """All model wrappers in a sweep must share one continuing allowance."""
    scopes = []
    for model in model_ids:
        if model not in gateways:
            raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
        scopes.append(_scope(gateways[model], model, max_tokens, provider=provider))
    if not scopes:
        raise ValueError("NO_MODEL_SELECTED")
    if any(scope != scopes[0] for scope in scopes[1:]):
        raise ValueError("PFP_SHARED_ACCOUNTING_REQUIRED")


def make_pilot_gateways(model_ids, *, max_output_tokens,
    max_estimated_cost_microusd, max_calls, accounting_path, env_file=None,
    run_id=None, objective_sha256=None, provider=Provider.OPENROUTER, pricing_snapshot=None):
    """Compose the existing gateway factory; no pilot-specific sender or ledger."""
    model_ids = tuple(model_ids)
    if provider not in (Provider.OPENROUTER, Provider.ANTHROPIC):
        raise ValueError("PFP_PROVIDER_UNSUPPORTED")
    factory = create_accounted_anthropic_gateway if provider == Provider.ANTHROPIC else create_accounted_openrouter_gateway
    pricing = {"pricing_snapshot": pricing_snapshot} if provider == Provider.ANTHROPIC else {}
    gateways = {model: factory(model, max_output_tokens,
        max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_calls,
        accounting_path=accounting_path, env_file=env_file,
        run_id=run_id, objective_sha256=objective_sha256, **pricing) for model in model_ids}
    validate_pilot_gateways(gateways, model_ids, max_tokens=max_output_tokens, provider=provider)
    return gateways


def _wire(raw):
    return dict(raw_reply_base64=base64.b64encode(raw).decode("ascii"),
        raw_reply_sha256=sha256(raw).hexdigest(), raw_reply_bytes=len(raw))


def complete_pilot_turn(gateway, request: CandidateRequest, *, model, task_id,
    attempt_id, max_tokens=None, answer_schema=None, provider=Provider.OPENROUTER):
    """Check the actual bound reply before exposing an answer to the original judge.

    PFP shape/binding is not mathematical acceptance. Unknown accounting stops
    the sweep; a malformed but settled reply may be recorded before continuing.
    """
    started = time.monotonic()
    record = dict(ok=False, content=None, reasoning=None, usage={}, elapsed=0,
        raw_body=None, error=None, stop=True, request={}, pfp=None,
        provider_wire=None, attempt_state=None)
    try:
        _scope(gateway, model, max_tokens, provider=provider)
        decoding = request.decoding or DecodingParamsV1()
        if decoding is not None and (decoding.allow_fallbacks or not decoding.require_parameters):
            raise ValueError("PFP_EXPLICIT_DECODING_REQUIRED")
        user = request.user
        if request.messages:
            user = json.dumps([dict(role=item.role, content=item.content)
                for item in request.messages], ensure_ascii=False)
        requested_schema = answer_schema
        if answer_schema is None:
            answer_schema = {"anyOf": [{"type": "object"}, {"type": "array"},
                {"type": "string", "minLength": 1}]}
        declared = None
        if decoding.response_format is not None:
            response_format = thaw_json(decoding.response_format)
            if response_format.get("type") == "json_schema":
                declared = response_format.get("json_schema")
                if type(declared) is not dict or type(declared.get("schema")) is not dict:
                    raise ValueError("PFP_DECLARED_ANSWER_SCHEMA_REQUIRED")
                if requested_schema is not None and requested_schema != declared["schema"]:
                    raise ValueError("PFP_ANSWER_SCHEMA_CONFLICT")
                answer_schema = declared["schema"]
            elif requested_schema is not None:
                raise ValueError("PFP_ANSWER_SCHEMA_CONFLICT")
        turn = prepare_task_turn(system=request.system or
            "Solve the supplied conversation task; put its JSON proposal in answer.",
            user=user, task_id=task_id, attempt_id=attempt_id,
            answer_schema=answer_schema, checker_id="pilot-original-judge-pending-v1")
        if decoding is not None and decoding.response_format is not None:
            decoding = replace(decoding, response_format={"type": "json_schema",
                "json_schema": {**(declared if declared is not None
                    else {"name": "pfp_pilot_turn", "strict": True}),
                    "schema": turn.prompt.response_schema}})
        mediated = replace(request, system=turn.prompt.system, user=turn.prompt.user,
            messages=(), decoding=decoding)
        record["request"] = (build_anthropic_body(mediated, model=model, max_tokens=_output_bound(gateway))
            if provider == Provider.ANTHROPIC else build_openai_compat_body(mediated, model=model,
                max_tokens=_output_bound(gateway), provider=provider))
        bound = gateway.for_action(attempt_id)
        result = bound.complete_result(mediated, provider=provider, model=model)
        if provider == Provider.ANTHROPIC:
            try:
                claim = gateway.action(attempt_id)
            except KeyError:
                claim = {}
            if claim.get("cost_basis") == "anthropic-standard-rated-v1":
                record.update({key: claim.get(key) for key in
                    ("rated_cost_usd", "cost_basis", "pricing_sha256")})
        if isinstance(result, Err):
            record["error"] = result.error.code
            wire = result.error.response_metadata()
            if wire:
                record["provider_wire"] = wire
                record["raw_body"] = base64.b64decode(wire["raw_reply_base64"]).decode(
                    "utf-8", errors="replace")
            return record
        outcome = result.value
        candidate = outcome.candidate
        record.update(attempt_state=outcome.state, model=candidate.model, provider_wire=_wire(outcome.reply_bytes),
            raw_body=outcome.reply_bytes.decode("utf-8", errors="replace"),
            usage=dict(prompt_tokens=candidate.input_tokens, completion_tokens=candidate.output_tokens,
                cost=candidate.cost_usd, generation_id=candidate.generation_id))
        checked = turn.check_completion(candidate.content)
        record["pfp"] = checked
        accepted_states = ({"CompletedRatedEstimate"} if provider == Provider.ANTHROPIC
            else {"CompletedSettled", "CompletedPendingSettlement"})
        if outcome.state not in accepted_states:
            record["error"] = outcome.state
            return record
        record["stop"] = False
        if not checked["schema_valid"] or checked["failure_class"] != "NONE":
            record["error"] = "PFP_" + checked["failure_class"]
            return record
        answer = checked["answer"]
        record.update(ok=True, content=answer if isinstance(answer, str)
            else json.dumps(answer, ensure_ascii=False))
        return record
    except Exception as exc:
        record["error"] = str(exc) if isinstance(exc, ValueError) else "PFP_ADAPTER_ERROR_" + type(exc).__name__
        return record
    finally:
        record["elapsed"] = time.monotonic() - started
