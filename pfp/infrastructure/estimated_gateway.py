"""Compose PFP run accounting around the existing Providers financial policy.

Hard budgets require a transport maximum liability; durable custody never
manufactures that capability. Estimated mode remains explicitly weaker.
"""

import json
import math
import os
import re
import sqlite3
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_pfp.infrastructure.adapters.pfp_campaign import (
    micro,
    snapshot_pricing,
)
from omega_engine_woland.domain.providers.attempt import (
    AdmittedRequest,
    CompletionOutcome,
    ProviderFailure,
    RetryClass,
)
from omega_engine_woland.domain.providers.allowlist import ModelAllowlist
from omega_engine_woland.domain.providers.budget import (
    BUILTIN_OBSERVED_AT_UTC,
    BudgetController,
    GatewayPolicy,
    PriceTable,
    utc_now,
)
from omega_engine_woland.domain.providers.types import (
    Provider,
    ProviderConfigError,
    ProviderError,
    check_reply_bytes,
)
from omega_engine_woland.infrastructure.providers.anthropic_messages import (
    AnthropicTransport,
    parse_anthropic_response,
)
from omega_engine_woland.infrastructure.providers.budget_ledger import SqliteBudgetLedger
from omega_engine_woland.infrastructure.providers.credential_source import resolve_credential
from omega_engine_woland.infrastructure.providers.gateway import (
    OearsLlmGateway,
    fixture_transport,
    unbudgeted_gateway,
)
from omega_engine_woland.infrastructure.providers.generation_reconciler import GenerationReconciler
from omega_engine_woland.infrastructure.providers.openai_compat import (
    OpenAiCompatTransport,
    observe_openai_compat_usage,
)
from omega_engine_woland.infrastructure.providers.openrouter_transport import resolve_openrouter_key
from omega_engine_woland.use_cases.providers.completion import request_digest


def create_accounted_openrouter_gateway(
    model: str, max_output_tokens: int, *, env_file: Path | str | None = None,
    max_cost_microusd: int | None = None, allow_unbounded_cost: bool = False,
    max_estimated_cost_microusd: int | None = None, max_calls: int = 5,
    accounting_path: Path | str | None = None,
    run_id: str | None = None, objective_sha256: str | None = None,
    trace=None, artifact_store=None,
    timeout: float = 60.0,
    transport=None,
    preset: str | None = None,
):
    """Own credential/transport composition while retaining all financial policies."""
    if (trace is None) != (artifact_store is None):
        raise ValueError("TRACE_AND_ARTIFACT_STORE_REQUIRED_TOGETHER")
    if type(model) is not str or not model.strip():
        raise ValueError("an explicit model is required")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("INVALID_PROVIDER_TIMEOUT")
    if type(max_output_tokens) is not int or max_output_tokens < 1:
        raise ValueError("max_output_tokens must be a positive integer")
    if type(allow_unbounded_cost) is not bool:
        raise ValueError("allow_unbounded_cost must be boolean")
    if sum((max_cost_microusd is not None, allow_unbounded_cost,
            max_estimated_cost_microusd is not None)) != 1:
        raise ValueError("choose one explicit financial policy")
    if max_cost_microusd is not None and (type(max_cost_microusd) is not int or max_cost_microusd < 1):
        raise ValueError("max_cost_microusd must be a positive integer")
    estimated_ceiling = ANTHROPIC_RUN_CEILING_MICROUSD if preset is not None else 50000
    if max_estimated_cost_microusd is not None and (
            type(max_estimated_cost_microusd) is not int
            or not 0 < max_estimated_cost_microusd <= estimated_ceiling
            or accounting_path is None or max_output_tokens > 3000):
        raise ValueError("estimated budget requires accounting_path and at most 3000 output tokens")
    # Original bounded C006 sessions include a 40-turn wheel. Retain the hard
    # run contract's limit; estimated sessions still have an explicit call cap,
    # continuing ledger and estimated monetary ceiling.
    call_ceiling = 64 if max_estimated_cost_microusd is not None else 32
    if type(max_calls) is not int or not 0 < max_calls <= call_ceiling:
        raise ValueError(f"max_calls must be an integer from 1 to {call_ceiling}")
    if accounting_path is not None and (max_cost_microusd is not None or max_estimated_cost_microusd is not None):
        if max_cost_microusd is not None:
            _run_scope(run_id, objective_sha256, max_cost_microusd, max_calls)
        elif run_id is not None or objective_sha256 is not None:
            _run_scope(run_id, objective_sha256, max_estimated_cost_microusd, max_calls,
                call_ceiling=64, limit_ceiling=estimated_ceiling)
    elif run_id is not None or objective_sha256 is not None:
        raise ValueError("DURABLE_HARD_BUDGET_REQUIRED")
    key = resolve_openrouter_key(env_file)
    if isinstance(key, Err):
        raise ProviderConfigError(key.error.code)
    if transport is None:
        transport = OpenAiCompatTransport(Provider.OPENROUTER, api_key=key.value,
            max_tokens=max_output_tokens, timeout=timeout)
    observe_key = getattr(transport, "observe_key", None)
    if callable(observe_key):
        observe_key(key.value)
    if trace is not None:
        from omega_engine_pfp.infrastructure.trace.provider_dispatch import DurableDispatchTransport
        transport = DurableDispatchTransport(trace, transport, artifact_store=artifact_store, live=True)
    if allow_unbounded_cost or max_estimated_cost_microusd is not None:
        gateway = unbudgeted_gateway(provider=Provider.OPENROUTER, model=model,
            transport=transport, max_output_tokens=max_output_tokens)
        if max_estimated_cost_microusd is not None:
            gateway = EstimatedBudgetGateway(gateway, model=model,
                price=snapshot_pricing(model, required_parameters=("max_tokens",), text_only=True),
                limit_microusd=max_estimated_cost_microusd, max_calls=max_calls,
                accounting_path=accounting_path, run_id=run_id, objective_sha256=objective_sha256,
                max_output_tokens=max_output_tokens, allow_model_switch=preset is not None)
    else:
        gateway = OearsLlmGateway(
            allowlist=ModelAllowlist.builtin(),
            policy=GatewayPolicy(
                prices=PriceTable.builtin(),
                budget=BudgetController(max_cost_microusd),
                max_output_tokens=max_output_tokens,
                pricing_clock=(lambda: BUILTIN_OBSERVED_AT_UTC) if transport is None or transport is fixture_transport else utc_now,
            ),
            transport=transport or fixture_transport,
        )
        if accounting_path is not None:
            gateway = DurableRunGateway(gateway, accounting_path=accounting_path,
                run_id=run_id, objective_sha256=objective_sha256, max_calls=max_calls)
    if isinstance(gateway, dict):
        gateway["credential_disclosure"] = "[REDACTED]"
    else:
        gateway.credential_disclosure = "[REDACTED]"
    return gateway


ANTHROPIC_COST_BASIS = "anthropic-standard-rated-v1"
# Rated run-wide ceiling for one Anthropic run. Raised from $0.50 for a full Sonnet Retinue, then
# to $4 because an Opus run reserves twice each call's worst case and stops at 80%.
ANTHROPIC_RUN_CEILING_MICROUSD = 4_000_000
# Output bound for one Anthropic call; thinking shares it, so 3000 truncated Opus builders.
ANTHROPIC_MAX_OUTPUT_TOKENS = 16_000


def anthropic_price(pricing_snapshot, model):
    """Select an operator-pinned standard rate; never scrape or claim a bill."""
    try:
        if type(pricing_snapshot) is not dict or set(pricing_snapshot) != {
                "source_url", "observed_at_utc", "rows", "catalog_sha256"}:
            raise ValueError
        content = {key: pricing_snapshot[key] for key in ("source_url", "observed_at_utc", "rows")}
        raw = json.dumps(content, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
        if sha256(raw).hexdigest() != pricing_snapshot["catalog_sha256"]:
            raise ValueError
        if content["source_url"] != "https://platform.claude.com/docs/en/about-claude/pricing":
            raise ValueError
        stamp = content["observed_at_utc"]
        if type(stamp) is not str:
            raise ValueError
        observed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if observed.utcoffset() is None or observed.utcoffset().total_seconds() != 0:
            raise ValueError
        rows = content["rows"]
        if type(rows) is not list or not 1 <= len(rows) <= 128:
            raise ValueError
        identifiers = set()
        for row in rows:
            if (type(row) is not dict or set(row) != {"id", "pricing"}
                    or type(row["id"]) is not str or not row["id"].strip() or row["id"] in identifiers
                    or type(row["pricing"]) is not dict or set(row["pricing"]) != {"prompt", "completion"}):
                raise ValueError
            identifiers.add(row["id"])
            for value in row["pricing"].values():
                if type(value) is not str or not Decimal(value).is_finite() or Decimal(value) <= 0:
                    raise ValueError
        selected = next(row for row in rows if row["id"] == model)
        return dict(row=deepcopy(selected), catalog_sha256=pricing_snapshot["catalog_sha256"],
            source_url=content["source_url"], observed_at_utc=stamp)
    except (KeyError, TypeError, ValueError, ArithmeticError, StopIteration):
        raise ValueError("ANTHROPIC_PRICING_INVALID") from None


def rate_anthropic_usage(body, price):
    """Exact USD estimate from strict standard usage, distinct from vendor cost."""
    try:
        usage = body["usage"]
        permitted = {"input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
            "cache_creation", "server_tool_use", "service_tier", "inference_geo", "output_tokens_details",
            "speed"}
        if type(usage) is not dict or set(usage) - permitted:
            raise ValueError
        for key in ("input_tokens", "output_tokens"):
            if type(usage[key]) is not int or usage[key] < 0:
                raise ValueError
        if "output_tokens_details" in usage:
            details = usage["output_tokens_details"]
            if (type(details) is not dict or set(details) != {"thinking_tokens"}
                    or type(details["thinking_tokens"]) is not int
                    or not 0 <= details["thinking_tokens"] <= usage["output_tokens"]):
                raise ValueError
        for key in ("cache_creation_input_tokens", "cache_read_input_tokens"):
            if key in usage and (type(usage[key]) is not int or usage[key] != 0):
                raise ValueError
        for key, fields in (("cache_creation", {"ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"}),
                            ("server_tool_use", {"web_search_requests", "web_fetch_requests"})):
            extra = usage.get(key)
            if extra is not None and (type(extra) is not dict or set(extra) - fields
                    or any(type(value) is not int or value != 0 for value in extra.values())):
                raise ValueError
        if "service_tier" in usage and usage["service_tier"] not in (None, "standard"):
            raise ValueError
        if "inference_geo" in usage and usage["inference_geo"] not in (None, "global", "not_available"):
            raise ValueError
        # Fast mode is priced differently from the standard rows this rater holds.
        if "speed" in usage and usage["speed"] not in (None, "standard"):
            raise ValueError
        rates = price["row"]["pricing"]
        prompt, completion = Decimal(rates["prompt"]), Decimal(rates["completion"])
        if any(not rate.is_finite() or rate <= 0 for rate in (prompt, completion)):
            raise ValueError
        return format(prompt * usage["input_tokens"] + completion * usage["output_tokens"], "f")
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise ValueError("ANTHROPIC_USAGE_UNRATABLE") from None


def create_accounted_anthropic_gateway(model, max_output_tokens, *, pricing_snapshot,
        max_estimated_cost_microusd, accounting_path, run_id, objective_sha256,
        env_file=None, max_calls=64, timeout=60.0, preset=None):
    """Reuse the Messages sender and existing ledger with explicit rated accounting."""
    price = anthropic_price(pricing_snapshot, model)
    _run_scope(run_id, objective_sha256, max_estimated_cost_microusd, max_calls,
               call_ceiling=64, limit_ceiling=ANTHROPIC_RUN_CEILING_MICROUSD)
    if (accounting_path is None or type(max_output_tokens) is not int
            or not 0 < max_output_tokens <= ANTHROPIC_MAX_OUTPUT_TOKENS):
        raise ValueError("INVALID_ANTHROPIC_OUTPUT_OR_ACCOUNTING")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("INVALID_PROVIDER_TIMEOUT")
    credential = resolve_credential(("ANTHROPIC_API_KEY",), explicit_file=env_file)
    if isinstance(credential, Err):
        raise ProviderConfigError(credential.error.code)
    transport = AnthropicTransport(api_key=credential.value.value, timeout=timeout)
    gateway = unbudgeted_gateway(provider=Provider.ANTHROPIC, model=model,
        transport=transport, max_output_tokens=max_output_tokens)
    return EstimatedBudgetGateway(gateway, provider=Provider.ANTHROPIC, model=model, price=price,
        limit_microusd=max_estimated_cost_microusd, max_calls=max_calls, accounting_path=accounting_path,
        run_id=run_id, objective_sha256=objective_sha256, max_output_tokens=max_output_tokens,
        pricing_snapshot=pricing_snapshot, allow_model_switch=preset is not None)


def _run_scope(run_id, objective_sha256, limit, max_calls, *, call_ceiling=32, limit_ceiling=50000):
    if type(run_id) is not str or not run_id.strip() or len(run_id) > 256:
        raise ValueError("DURABLE_RUN_ID_REQUIRED")
    if type(objective_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", objective_sha256) is None:
        raise ValueError("DURABLE_OBJECTIVE_DIGEST_REQUIRED")
    if type(limit) is not int or not 0 < limit <= limit_ceiling:
        raise ValueError("DURABLE_RUN_CAP_EXCEEDS_50000" if limit_ceiling == 50000 else "INVALID_ANTHROPIC_BUDGET")
    if type(max_calls) is not int or not 0 < max_calls <= call_ceiling:
        raise ValueError("INVALID_CALL_LIMIT")
    return dict(schema="pfp.hard-run.v1", run_id=run_id,
        objective_sha256=objective_sha256, limit_microusd=limit, max_calls=max_calls)


class DurableRunGateway:
    """One immutable run, Providers ledger and persistent action claims.

    Reopening an action never sends it again, even after settlement. Unknown
    sends/costs stop new work. Known completions may continue against retained
    maximum-liability holds; only a trusted generation receipt releases money.
    Raw provider bytes live beside the database, not inside its metadata.
    """

    def __init__(self, gateway, *, accounting_path, run_id, objective_sha256, max_calls=5):
        if not isinstance(gateway, OearsLlmGateway) or gateway.policy is None:
            raise ValueError("DURABLE_HARD_BUDGET_REQUIRED")
        if gateway.policy.budget.spent_microusd or gateway.policy.budget.pending_attempts():
            raise ValueError("DURABLE_BUDGET_ALREADY_USED")
        limit = gateway.policy.budget.limit_microusd
        self.scope = _run_scope(run_id, objective_sha256, limit, max_calls)
        self.path = Path(accounting_path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # A database is one run. Changing run_id cannot select a fresh row and
        # silently reset its allowance.
        self.ledger = _run_ledger(self.path)
        with self.ledger.transaction(limit) as state:
            previous = state.get("run_scope")
            if previous is not None and previous != self.scope:
                raise ValueError("DURABLE_RUN_SCOPE_MISMATCH")
            if previous is None and (state["spent"] or state["attempts"] or state["settlements"]):
                raise ValueError("DURABLE_RUN_SCOPE_MISSING")
            state["run_scope"] = self.scope
            state.setdefault("action_claims", {})
        self.budget = BudgetController(limit, ledger=self.ledger)
        policy = gateway.policy
        self.gateway = replace(gateway, policy=GatewayPolicy(policy.prices, self.budget,
            policy.max_output_tokens, pricing_clock=policy._pricing_clock))
        self.reply_root = self.path.with_name(self.path.name + ".replies")

    @staticmethod
    def read_binding(accounting_path):
        path, state = _read_run_state(accounting_path)
        return {**state["run_scope"], "accounting_path": str(path)}

    @staticmethod
    def read_action(accounting_path, action_id):
        """Inspect existing custody without creating a ledger or seeking credentials."""
        _, state = _read_run_state(accounting_path)
        return deepcopy(state["action_claims"][action_id])

    @staticmethod
    def read_raw_reply(accounting_path, action_id):
        """Validate the original retained wire through a read-only ledger connection."""
        path, state = _read_run_state(accounting_path)
        return _checked_wire(path, action_id, state["action_claims"][action_id])

    @property
    def binding(self):
        return {**self.scope, "accounting_path": str(self.path)}

    def for_action(self, action_id):
        if type(action_id) is not str or not action_id.strip() or len(action_id) > 512:
            raise ValueError("PFP_ACTION_ID_REQUIRED")
        return _ActionGateway(self, action_id)

    def complete_result(self, request, **options):
        return _run_refusal("PFP_ACTION_BINDING_REQUIRED")

    def complete(self, request, **options):
        raise ProviderConfigError("PFP_ACTION_BINDING_REQUIRED")

    def action(self, action_id):
        with self.ledger.transaction(self.scope["limit_microusd"]) as state:
            return deepcopy(state["action_claims"][action_id])

    def _complete_result(self, action_id, request, **options):
        provider = options.get("provider") or self.gateway.default_provider
        model = options.get("model") or (self.gateway.default_model
            if provider == self.gateway.default_provider else self.gateway._resolve_model(provider))
        binding = dict(action_id=action_id, request_digest=request_digest(request),
            provider=provider.value, model=model,
            max_output_tokens=self.gateway.policy.max_output_tokens)
        with self.ledger.transaction(self.scope["limit_microusd"]) as state:
            claims = state["action_claims"]
            if action_id in claims:
                code = ("PFP_ACTION_ALREADY_CLAIMED" if claims[action_id]["binding"] == binding
                    else "PFP_ACTION_BINDING_MISMATCH")
                return _run_refusal(code)
            if any(item["state"] in {"claimed", "dispatched", "outcome_unknown",
                    "cost_unknown", "identity_unavailable", "over_admitted"}
                    for item in claims.values()):
                return _run_refusal("RUN_RECONCILIATION_REQUIRED")
            if len(claims) >= self.scope["max_calls"]:
                return _run_refusal("CALL_ALLOWANCE_EXHAUSTED")
            claims[action_id] = dict(binding=binding, state="claimed")
        captured = replace(self.gateway, transport=_RunTransport(self, action_id, self.gateway.transport))
        try:
            result = captured.complete_result(request, provider=provider, model=model)
        except BaseException:
            self._update_action(action_id, state="outcome_unknown")
            raise
        if isinstance(result, Err):
            observed = result.error.usage_observation
            if observed is not None and observed.generation_id:
                terminal, status = "CompletedPendingSettlement", "completed_pending"
                attempt = self.budget.attempt(result.error.attempt_id)
                if observed.cost_usd is None:
                    terminal, status = "CompletedCostUnknown", "cost_unknown"
                elif micro(observed.cost_usd) > attempt["receipt"]["cost_microusd"]:
                    terminal, status = "CompletedOverAdmittedBudget", "over_admitted"
                with self.ledger.transaction(self.scope["limit_microusd"]) as state:
                    if any(item.get("generation_id") == observed.generation_id
                            for key, item in state["action_claims"].items() if key != action_id):
                        terminal, status = "CompletedAccountingUnavailable", "identity_unavailable"
                    state["action_claims"][action_id].update(state=status,
                        failure_code=result.error.code, provider_attempt_id=result.error.attempt_id,
                        generation_id=observed.generation_id, reported_cost_usd=observed.cost_usd,
                        input_tokens=observed.input_tokens, output_tokens=observed.output_tokens)
                return Err(replace(result.error, attempt_state=terminal))
            self._update_action(action_id,
                state="outcome_unknown" if result.error.attempt_id else "refused_before_dispatch",
                failure_code=result.error.code, provider_attempt_id=result.error.attempt_id)
            return result
        outcome = result.value
        candidate, admitted = outcome.candidate, outcome.admitted
        terminal, state = "CompletedPendingSettlement", "completed_pending"
        if not candidate.generation_id:
            terminal, state = "CompletedAccountingUnavailable", "identity_unavailable"
        elif candidate.cost_usd is None:
            terminal, state = "CompletedCostUnknown", "cost_unknown"
        elif micro(candidate.cost_usd) > admitted.receipt.cost_microusd:
            terminal, state = "CompletedOverAdmittedBudget", "over_admitted"
        with self.ledger.transaction(self.scope["limit_microusd"]) as ledger_state:
            if candidate.generation_id and any(item.get("generation_id") == candidate.generation_id
                    for key, item in ledger_state["action_claims"].items() if key != action_id):
                terminal, state = "CompletedAccountingUnavailable", "identity_unavailable"
            ledger_state["action_claims"][action_id].update(state=state,
                provider_attempt_id=admitted.attempt_id, generation_id=candidate.generation_id,
                reported_cost_usd=candidate.cost_usd)
        return Ok(replace(outcome, state=terminal))

    def _update_action(self, action_id, **values):
        with self.ledger.transaction(self.scope["limit_microusd"]) as state:
            state["action_claims"][action_id].update(values)

    def _record_wire(self, action_id, raw):
        check_reply_bytes(raw)
        raw = bytes(raw)
        self.reply_root.mkdir(exist_ok=True)
        name = sha256(action_id.encode("utf-8")).hexdigest() + ".wire"
        with (self.reply_root / name).open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        self._update_action(action_id, wire_file=name, wire_sha256=sha256(raw).hexdigest(),
            wire_bytes=len(raw))

    def raw_reply(self, action_id):
        return _checked_wire(self.path, action_id, self.action(action_id))

    def recover_result(self, action_id, request, **options):
        """Replay a completed hard-budget action without releasing its reservation."""
        try:
            claim = self.action(action_id)
            binding = claim["binding"]
            provider = options.get("provider") or self.gateway.default_provider
            model = options.get("model") or self.gateway.default_model
            if binding != dict(action_id=action_id, request_digest=request_digest(request),
                    provider=provider.value, model=model,
                    max_output_tokens=self.gateway.policy.max_output_tokens):
                return _run_refusal("PFP_ACTION_BINDING_MISMATCH")
            if claim["state"] not in {"completed_pending", "settled"}:
                return _run_refusal("RUN_RECONCILIATION_REQUIRED")
            raw = self.raw_reply(action_id)
            if claim.get("failure_code"):
                observed = observe_openai_compat_usage(self.gateway._decode_reply(raw),
                    provider=provider, model=model,
                    transport="fixture" if self.gateway.transport is fixture_transport else
                        getattr(self.gateway.transport, "provenance", "custom"))
                return Err(ProviderFailure(claim["failure_code"], "provider.completion",
                    RetryClass.TERMINAL, claim["provider_attempt_id"],
                    ProviderError("retained provider completion was refused"), reply_bytes=raw,
                    usage_observation=observed,
                    attempt_state="CompletedSettled" if claim["state"] == "settled" else
                        "CompletedPendingSettlement"))
            candidate = self.gateway._parse(provider, model, self.gateway._decode_reply(raw))
            if (candidate.model != model or candidate.generation_id != claim["generation_id"]
                    or candidate.cost_usd is None):
                return _run_refusal("PROVIDER_IDENTITY_MISMATCH")
            attempt = self.budget.attempt(claim["provider_attempt_id"])
            from omega_engine_woland.domain.providers.types import BudgetReceipt
            receipt = BudgetReceipt(**attempt["receipt"])
            admitted = AdmittedRequest(claim["provider_attempt_id"], claim["reservation_id"],
                binding["request_digest"], provider, model, request,
                binding["max_output_tokens"], receipt, receipt.cost_microusd)
            return Ok(CompletionOutcome(candidate, admitted,
                state="CompletedPendingSettlement", reply_bytes=raw))
        except (ValueError, KeyError, OSError) as exc:
            return _run_refusal("RUN_RECONCILIATION_REQUIRED:" + type(exc).__name__)

    def settle_generation(self, action_id, api_payload):
        """Settle from caller-supplied trusted generation evidence, never model text."""
        claim = self.action(action_id)
        if not claim.get("provider_attempt_id") or not claim.get("generation_id"):
            raise ValueError("RUN_RECONCILIATION_REQUIRED")
        attempt = self.budget.attempt(claim["provider_attempt_id"])
        result = GenerationReconciler(self.budget).reconcile(api_payload,
            precharge_micro_usd=attempt["receipt"]["cost_microusd"],
            expected_generation_id=claim["generation_id"], provider=claim["binding"]["provider"],
            attempt_id=claim["provider_attempt_id"])
        if result.status == "RECONCILED":
            self._update_action(action_id, state="settled")
        return result


def _read_run_state(accounting_path):
    path = Path(accounting_path).resolve(strict=True)
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
            rows = connection.execute("SELECT state FROM provider_budget").fetchall()
    except sqlite3.Error:
        raise ValueError("DURABLE_RUN_SCOPE_MISSING") from None
    if len(rows) != 1:
        raise ValueError("DURABLE_RUN_SCOPE_MISSING")
    state = json.loads(rows[0][0])
    if not isinstance(state.get("run_scope"), dict):
        raise ValueError("DURABLE_RUN_SCOPE_MISSING")
    return path, state


def _checked_wire(path, action_id, record):
    expected_name = sha256(action_id.encode("utf-8")).hexdigest() + ".wire"
    if record.get("wire_file") != expected_name:
        raise ValueError("DURABLE_WIRE_MISMATCH")
    raw = (path.with_name(path.name + ".replies") / expected_name).read_bytes()
    if len(raw) != record["wire_bytes"] or sha256(raw).hexdigest() != record["wire_sha256"]:
        raise ValueError("DURABLE_WIRE_MISMATCH")
    return raw


def _run_refusal(code):
    return Err(ProviderFailure(code, "pfp.run_budget", RetryClass.TERMINAL))


@dataclass(frozen=True)
class _ActionGateway:
    owner: DurableRunGateway
    action_id: str

    def complete_result(self, request, **options):
        return self.owner._complete_result(self.action_id, request, **options)

    def recover_result(self, request, **options):
        return self.owner.recover_result(self.action_id, request, **options)

    def complete(self, request, **options):
        result = self.complete_result(request, **options)
        if isinstance(result, Err):
            raise ProviderConfigError(result.error.code)
        if result.value.state in {"CompletedCostUnknown", "CompletedAccountingUnavailable",
                "CompletedOverAdmittedBudget", "CompletedOverEstimatedBudget"}:
            error = ProviderConfigError(result.value.state)
            error.outcome = result.value
            raise error
        return result.value.candidate, result.value.admitted.receipt


class _RunTransport:
    def __init__(self, owner, action_id, delegate):
        self.owner, self.action_id, self.delegate = owner, action_id, delegate
        self.provenance = "fixture" if delegate is fixture_transport else getattr(delegate, "provenance", "custom")

    def maximum_liability(self, provider, model, request, limit, quote):
        if self.delegate is fixture_transport:
            return quote.cost_microusd
        maximum = getattr(self.delegate, "maximum_liability", None)
        if not callable(maximum) or not callable(getattr(self.delegate, "dispatch", None)):
            return None
        return maximum(provider, model, request, limit, quote)

    def dispatch(self, admitted):
        self.owner._update_action(self.action_id, state="dispatched",
            provider_attempt_id=admitted.attempt_id, reservation_id=admitted.reservation_id)
        try:
            send = getattr(self.delegate, "dispatch", None)
            raw = send(admitted) if callable(send) else self.delegate(
                admitted.provider, admitted.model, admitted.request)
        except BaseException as exc:
            retained = getattr(exc, "reply_bytes", None)
            if type(retained) is bytes and retained:
                self.owner._record_wire(self.action_id, retained)
            raise
        self.owner._record_wire(self.action_id, raw)
        return raw


def _run_ledger(path):
    # New modes share one row, including concurrent first construction. Existing
    # sole run rows retain their identity; missing scopes never receive backfill.
    budget_id = "pfp-hard-run-v1"
    if path.exists():
        with closing(sqlite3.connect(path)) as connection:
            table = connection.execute("SELECT 1 FROM sqlite_master WHERE name='provider_budget'").fetchone()
            rows = connection.execute("SELECT id FROM provider_budget").fetchall() if table else []
            if rows:
                if len(rows) != 1 or rows[0][0] not in {"pfp-hard-run-v1", "woland-pfp-estimated"}:
                    raise ValueError("DURABLE_RUN_FINANCIAL_POLICY_MISMATCH")
                budget_id = rows[0][0]
    return SqliteBudgetLedger(path, budget_id=budget_id)


class EstimatedBudgetGateway(DurableRunGateway):
    """Conservative FUZZY accounting in the existing run ledger, never a vendor cap.

    Input bytes plus framing are a conservative token estimate, not a tokenizer
    measurement. Model-specific observed rates, maximum output and 2x headroom
    are reserved before send. Stop at 80% of the original allowance. Unknown
    outcomes retain their reservation. Action claims and raw custody are reused
    from DurableRunGateway; changing a model never creates another allowance.
    """

    def __init__(self, gateway, *, model, price, limit_microusd, max_calls, accounting_path,
                 run_id=None, objective_sha256=None, max_output_tokens=None, provider=Provider.OPENROUTER,
                 pricing_snapshot=None, allow_model_switch=False):
        if type(provider) is not Provider or provider not in (Provider.OPENROUTER, Provider.ANTHROPIC):
            raise ValueError("ESTIMATED_PROVIDER_UNSUPPORTED")
        anthropic = provider == Provider.ANTHROPIC
        if anthropic and (not isinstance(gateway, OearsLlmGateway) or gateway.default_provider != provider
                or run_id is None or objective_sha256 is None):
            raise ValueError("ANTHROPIC_ACCOUNTED_SCOPE_REQUIRED")
        limit_ceiling = ANTHROPIC_RUN_CEILING_MICROUSD if (anthropic or allow_model_switch) else 50000
        if type(limit_microusd) is not int or not 0 < limit_microusd <= limit_ceiling:
            raise ValueError("INVALID_ESTIMATED_BUDGET")
        if type(max_calls) is not int or not 0 < max_calls <= 64:
            raise ValueError("INVALID_CALL_LIMIT")
        if isinstance(gateway, OearsLlmGateway) and gateway.policy is not None:
            raise ValueError("ESTIMATED_GATEWAY_REQUIRES_UNBUDGETED_PROVIDER")
        self.gateway, self.model, self.price = gateway, model, deepcopy(price)
        self.provider = provider
        self._pricing_snapshot = deepcopy(pricing_snapshot)
        self._allow_model_switch = bool(allow_model_switch)
        self._price_cache = {model: deepcopy(price)}
        self.limit, self.max_calls = limit_microusd, max_calls
        self.max_output_tokens = (max_output_tokens if max_output_tokens is not None
            else getattr(gateway, "unbudgeted_max_output_tokens", 512))
        output_ceiling = ANTHROPIC_MAX_OUTPUT_TOKENS if anthropic else 3000
        if type(self.max_output_tokens) is not int or not 0 < self.max_output_tokens <= output_ceiling:
            raise ValueError("INVALID_OUTPUT_TOKEN_LIMIT")
        if isinstance(gateway, OearsLlmGateway) and gateway.unbudgeted_max_output_tokens != self.max_output_tokens:
            raise ValueError("OUTPUT_LIMIT_BINDING_MISMATCH")
        run_id = "legacy-estimated" if run_id is None else run_id
        objective_sha256 = sha256(b"legacy-estimated").hexdigest() if objective_sha256 is None else objective_sha256
        # Same identity/cap validation, with the existing estimated 64-call limit.
        _run_scope(run_id, objective_sha256, limit_microusd, max_calls, call_ceiling=64, limit_ceiling=limit_ceiling)
        self.scope = dict(schema="pfp.fuzzy-run.v1", run_id=run_id,
            objective_sha256=objective_sha256, limit_microusd=limit_microusd,
            max_calls=max_calls, safety_multiplier=2, stop_percent=80,
            estimate_basis="utf8-bytes-plus-256-framing-v1")
        if anthropic:
            if (price["row"]["id"] != model or type(price.get("catalog_sha256")) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", price["catalog_sha256"]) is None):
                raise ValueError("ANTHROPIC_PRICING_INVALID")
            rate_anthropic_usage({"usage": {"input_tokens": 0, "output_tokens": 0}}, price)
            self.scope.update(schema="pfp.anthropic-rated-run.v1", provider=provider.value,
                cost_basis=ANTHROPIC_COST_BASIS, pricing_sha256=price["catalog_sha256"])
        self.path = Path(accounting_path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = _run_ledger(self.path)
        with self.ledger.transaction(self.limit) as state:
            previous = state.get("run_scope")
            if previous is not None and previous != self.scope:
                raise ValueError("DURABLE_RUN_SCOPE_MISMATCH")
            if previous is None and (state["spent"] or state["attempts"]):
                raise ValueError("DURABLE_RUN_SCOPE_MISSING")
            state["run_scope"] = self.scope
            state.setdefault("action_claims", {})
        self.reply_root = self.path.with_name(self.path.name + ".replies")

    def complete_result(self, request, **options):
        # Compatibility for direct callers; production role callers bind actions.
        return self._complete_result("legacy:" + uuid4().hex, request, **options)

    def _price_for(self, model):
        if model == self.model:
            return self.price
        if not self._allow_model_switch:
            raise ValueError("PRICING_MODEL_MISMATCH")
        if model not in self._price_cache:
            if self.provider == Provider.ANTHROPIC:
                self._price_cache[model] = anthropic_price(self._pricing_snapshot, model)
            else:
                self._price_cache[model] = snapshot_pricing(
                    model, required_parameters=("max_tokens",), text_only=True
                )
        return self._price_cache[model]

    def _binding(self, action_id, request, options):
        provider = options.get("provider", self.provider)
        model = options.get("model", self.model)
        if provider != self.provider or (model != self.model and not self._allow_model_switch):
            raise ValueError("PRICING_MODEL_MISMATCH")
        return dict(action_id=action_id, request_digest=request_digest(request),
            provider=provider.value, model=model, max_output_tokens=self.max_output_tokens)

    def _quote(self, request, *, model=None):
        active_model = self.model if model is None else model
        price = self._price_for(active_model)
        if price["row"]["id"] != active_model or active_model.endswith(":online"):
            raise ValueError("PRICING_MODEL_MISMATCH")
        rates = price["row"]["pricing"]
        for key, value in rates.items():
            if key == "overrides" and isinstance(value, list):
                continue
            rate = Decimal(str(value))
            if not rate.is_finite() or rate < 0:
                raise ValueError("INVALID_PRICING")
            if key not in (
                "prompt", "completion", "input_cache_read", "input_cache_write",
                "web_search", "input_cache_write_1h", "internal_reasoning",
                "image", "audio", "input_audio_cache",
            ) and rate:
                raise ValueError("UNSUPPORTED_SURCHARGE")
        request.check_payload_ceiling()
        tokens = request.estimated_payload_bytes() + 256
        reserve = 2 * micro(max(Decimal(str(rates.get(key, 0))) for key in ("prompt", "input_cache_read", "input_cache_write")) * tokens
            + Decimal(str(rates["completion"])) * self.max_output_tokens)
        return reserve, tokens

    def _complete_result(self, action_id, request, **options):
        try:
            binding = self._binding(action_id, request, options)
            active_model = binding["model"]
            active_price = self._price_for(active_model)
            reserve, tokens = self._quote(request, model=active_model)
            with self.ledger.transaction(self.limit) as state:
                claims = state["action_claims"]
                if action_id in claims:
                    return _run_refusal("PFP_ACTION_ALREADY_CLAIMED" if claims[action_id]["binding"] == binding
                        else "PFP_ACTION_BINDING_MISMATCH")
                if any(item["state"] != "settled" for item in state["attempts"].values()):
                    return _run_refusal("UNRECONCILED_ATTEMPT")
                if len(state["attempts"]) >= self.max_calls:
                    return _run_refusal("CALL_ALLOWANCE_EXHAUSTED")
                if state["spent"] + reserve > self.limit:
                    return _run_refusal("ESTIMATED_BUDGET_EXCEEDED")
                if state["spent"] + reserve > self.limit * self.scope["stop_percent"] // 100:
                    return _run_refusal("FUZZY_BUDGET_MILESTONE_REACHED")
                state["spent"] += reserve
                entry = dict(state="reserved", reserved=reserve, model=active_model,
                    pricing_sha256=active_price["catalog_sha256"], pricing=deepcopy(active_price),
                    input_token_estimate=tokens, max_output_tokens=self.max_output_tokens)
                if self.provider == Provider.ANTHROPIC:
                    entry.update(cost_basis=ANTHROPIC_COST_BASIS, rated_cost_usd=None,
                        rated_microusd=None, pricing_sha256=active_price["catalog_sha256"])
                state["attempts"][action_id] = entry
                claims[action_id] = dict(entry, binding=binding)
        except (ValueError, KeyError, ArithmeticError) as exc:
            return _run_refusal(str(exc))
        # Real gateway dispatch passes through the existing raw-custody seam.
        gateway = (replace(self.gateway,
            allowlist=self.gateway.allowlist.allow(self.provider, active_model) if self._allow_model_switch else self.gateway.allowlist,
            transport=_RunTransport(self, action_id, self.gateway.transport))
            if isinstance(self.gateway, OearsLlmGateway) else self.gateway)
        try:
            result = gateway.complete_result(request, **options)
        except BaseException:
            self._update_action(action_id, state="outcome_unknown")
            raise
        if isinstance(result, Err):
            self._update_action(action_id, state="outcome_unknown", failure_code=result.error.code,
                provider_attempt_id=result.error.attempt_id)
            return self._finish_refused(action_id, result.error)
        return self._finish(action_id, result.value)

    def _finish(self, action_id, outcome):
        if self.provider == Provider.ANTHROPIC:
            return self._finish_anthropic(action_id, outcome)
        candidate = outcome.candidate
        usage_available = True
        if isinstance(self.gateway, OearsLlmGateway):
            decoded = self.gateway._decode_reply(outcome.reply_bytes)
            usage = decoded.get("usage", {})
            usage_available = all(key in usage for key in ("prompt_tokens", "completion_tokens"))
            candidate = replace(candidate, content=decoded["choices"][0]["message"]["content"])
            outcome = replace(outcome, candidate=candidate)
        terminal, reserve = self._settle_usage(action_id, candidate,
            provider_attempt_id=outcome.admitted.attempt_id, usage_available=usage_available)
        return Ok(replace(outcome, state=terminal, admitted=replace(outcome.admitted,
            reservation_id=action_id, estimated_microusd=reserve)))

    def _finish_refused(self, action_id, failure):
        """Settle known refused-answer usage without manufacturing a candidate.

        The refusal remains Err and its raw content remains untouched. Only the
        real gateway's retained bounded body may supply financial observations.
        """
        if (not isinstance(self.gateway, OearsLlmGateway) or not failure.attempt_id
                or failure.reply_truncated):
            return Err(failure)
        try:
            claim = self.action(action_id)
            raw = self.raw_reply(action_id)
            if failure.reply_bytes is not None and raw != failure.reply_bytes:
                raise ProviderError("refused billing body differs from retained wire")
            decoded = self.gateway._decode_reply(raw)
            usage = observe_openai_compat_usage(decoded, provider=Provider.OPENROUTER,
                model=claim["binding"]["model"],
                transport="fixture" if self.gateway.transport is fixture_transport else
                    getattr(self.gateway.transport, "provenance", "custom"))
            terminal, _ = self._settle_usage(action_id, usage,
                provider_attempt_id=failure.attempt_id, usage_available=True)
        except (ValueError, KeyError, OSError):
            return Err(replace(failure, attempt_state="CompletedAccountingUnavailable"))
        return Err(replace(failure, usage_observation=usage, attempt_state=terminal))

    def _settle_usage(self, action_id, observation, *, provider_attempt_id, usage_available):
        actual = micro(observation.cost_usd) if observation.cost_usd is not None else None
        with self.ledger.transaction(self.limit) as state:
            entry = state["attempts"][action_id]
            claim = state["action_claims"][action_id]
            reserve = entry["reserved"]
            charged = entry.get("charged", reserve)
            generation = observation.generation_id
            duplicate = generation and any(item.get("generation_id") == generation
                for key, item in state["attempts"].items() if key != action_id)
            if (not generation or duplicate or not usage_available
                    or observation.input_tokens > entry["input_token_estimate"]
                    or observation.output_tokens > entry["max_output_tokens"]):
                terminal, status = "CompletedAccountingUnavailable", "identity_unavailable"
                liability = max(charged, reserve, actual or 0)
                state["spent"] += liability - charged
                charged = liability
            elif actual is None:
                terminal, status = "CompletedCostUnknown", "cost_unknown"
            elif entry["state"] in {"settled", "over_estimate"}:
                terminal, status = (("CompletedSettled", "settled") if entry["state"] == "settled"
                    else ("CompletedOverEstimatedBudget", "over_estimate"))
            else:
                state["spent"] += actual - charged
                charged = actual
                over = actual > reserve or state["spent"] > self.limit
                terminal, status = ("CompletedOverEstimatedBudget", "over_estimate") if over else ("CompletedSettled", "settled")
            updates = dict(state=status, actual=actual, charged=charged, generation_id=generation,
                provider_attempt_id=provider_attempt_id, input_tokens=observation.input_tokens,
                output_tokens=observation.output_tokens, reported_cost_usd=observation.cost_usd)
            entry.update(updates)
            claim.update(updates)
        return terminal, reserve

    def _finish_anthropic(self, action_id, outcome):
        rated, refusal = None, None
        candidate = outcome.candidate
        try:
            claim = self.action(action_id)
            active_model = claim["binding"]["model"]
            active_price = claim.get("pricing") or self._price_for(active_model)
            body = self.gateway._decode_reply(outcome.reply_bytes)
            if (type(body.get("id")) is not str or not body["id"]
                    or body.get("model") != active_model):
                raise ValueError("ANTHROPIC_REPLY_IDENTITY_UNAVAILABLE")
            candidate = parse_anthropic_response(body, fallback_model=active_model,
                transport=candidate.transport)
            rated = rate_anthropic_usage(body, active_price)
        except (KeyError, TypeError, ValueError) as exc:
            refusal = str(exc)
        amount = micro(rated) if rated is not None else None
        with self.ledger.transaction(self.limit) as state:
            entry, claim = state["attempts"][action_id], state["action_claims"][action_id]
            reserve, charged = entry["reserved"], entry.get("charged", entry["reserved"])
            generation = candidate.generation_id
            duplicate = generation and any(item.get("generation_id") == generation
                for key, item in state["attempts"].items() if key != action_id)
            if (refusal is not None or not generation or duplicate
                    or candidate.input_tokens > entry["input_token_estimate"]
                    or candidate.output_tokens > entry["max_output_tokens"]):
                terminal, status = "CompletedAccountingUnavailable", "identity_unavailable"
                liability = max(charged, reserve, amount or 0)
                state["spent"] += liability - charged
                charged = liability
            elif entry["state"] in {"settled", "over_estimate"}:
                terminal, status = (("CompletedRatedEstimate", "settled") if entry["state"] == "settled"
                    else ("CompletedOverEstimatedBudget", "over_estimate"))
            else:
                state["spent"] += amount - charged
                charged = amount
                over = amount > reserve or state["spent"] > self.limit
                terminal, status = ("CompletedOverEstimatedBudget", "over_estimate") if over else ("CompletedRatedEstimate", "settled")
            updates = dict(state=status, actual=None, charged=charged, generation_id=generation,
                rated_cost_usd=rated, rated_microusd=amount, cost_basis=ANTHROPIC_COST_BASIS,
                pricing_sha256=self.price["catalog_sha256"], rating_refusal=refusal,
                provider_attempt_id=outcome.admitted.attempt_id)
            entry.update(updates)
            claim.update(updates)
        return Ok(replace(outcome, candidate=candidate, state=terminal,
            admitted=replace(outcome.admitted, reservation_id=action_id, estimated_microusd=reserve)))

    def recover_result(self, action_id, request, **options):
        """Decode only the original retained wire; never send a claimed action again."""
        try:
            claim = self.action(action_id)
            if claim["binding"] != self._binding(action_id, request, options):
                return _run_refusal("PFP_ACTION_BINDING_MISMATCH")
            raw = self.raw_reply(action_id)
            recoverable = {"reserved", "dispatched", "outcome_unknown", "settled"}
            if self.provider == Provider.ANTHROPIC:
                recoverable.add("identity_unavailable")
            if claim["state"] not in recoverable:
                return _run_refusal("RUN_RECONCILIATION_REQUIRED")
            provider = Provider(claim["binding"]["provider"])
            decoded = self.gateway._decode_reply(raw)
            try:
                candidate = self.gateway._parse(provider, claim["binding"]["model"], decoded)
            except ProviderError as exc:
                failure = ProviderFailure(claim.get("failure_code", "PROVIDER_REFUSED"),
                    "provider.completion", RetryClass.TERMINAL,
                    claim.get("provider_attempt_id", ""), exc, reply_bytes=raw)
                return self._finish_refused(action_id, failure)
            if candidate.model != claim["binding"]["model"]:
                return _run_refusal("PROVIDER_IDENTITY_MISMATCH")
            admitted = AdmittedRequest(claim.get("provider_attempt_id", ""), action_id,
                claim["binding"]["request_digest"], provider, candidate.model, request,
                claim["binding"]["max_output_tokens"], None, claim["reserved"])
            return self._finish(action_id, CompletionOutcome(candidate, admitted, reply_bytes=raw))
        except (ValueError, KeyError, OSError) as exc:
            return _run_refusal("RUN_RECONCILIATION_REQUIRED:" + type(exc).__name__)

    def complete(self, request, **options):
        result = self.complete_result(request, **options)
        if isinstance(result, Err):
            raise ProviderConfigError(result.error.code)
        if result.value.state != ("CompletedRatedEstimate" if self.provider == Provider.ANTHROPIC else "CompletedSettled"):
            error = ProviderConfigError(result.value.state)
            error.outcome = result.value
            raise error
        return result.value.candidate, result.value.admitted.receipt

def native_anthropic_request(prepared, *, model, max_tokens=768, structured=False):
    request = dict(model=model, max_tokens=max_tokens, system=prepared.prompt.system,
        messages=[dict(role="user", content=prepared.prompt.user)])
    if structured:
        def wire_schema(value):
            if isinstance(value, list):
                return [wire_schema(item) for item in value]
            if not isinstance(value, dict):
                return value
            out = {key: wire_schema(item) for key, item in value.items()
                if key not in {"$id", "minLength", "pattern"}}
            if "const" in out:
                out["enum"] = [out.pop("const")]
            return out
        request["output_config"] = dict(format=dict(type="json_schema",
            schema=wire_schema(prepared.prompt.response_schema)))
    return request


class NativeAnthropicCampaign:
    """Sequential native Messages calls sharing the existing continuing ledger.

    The Rust host supplies the quote and preserves raw bytes. A reservation is
    durable before dispatch; an ambiguous outcome stays charged and halts sends.
    Stage ceilings are partitions of the one campaign allowance, not new budgets.
    """

    def __init__(self, *, transport, accounting_path, run_id, registration,
                 limit_microusd=2_000_000, stage_caps=None, clock=None, sleep=None,
                 registration_amendment=None):
        import time
        self.transport = transport
        self.limit = limit_microusd
        self.stage_caps = dict(stage_caps or {"P0": 0, "P1": 200000, "P2": 600000, "P3": 800000, "P4": 400000})
        if (type(limit_microusd) is not int or not 0 < limit_microusd <= 2_000_000
                or set(self.stage_caps) != {"P0", "P1", "P2", "P3", "P4"}
                or any(type(cap) is not int or cap < 0 for cap in self.stage_caps.values())
                or sum(self.stage_caps.values()) != limit_microusd):
            raise ValueError("CAMPAIGN_CAP_INVALID")
        self._clock, self._sleep = clock or time.time, sleep or time.sleep
        self.registration_digest = sha256(json.dumps(registration, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        self.ledger = SqliteBudgetLedger(Path(accounting_path), budget_id="native-anthropic:" + run_id)
        self.stage_call_limits = registration.get("stage_call_limits")
        self.quote_bounds = registration.get("quote_bounds")
        self.request_byte_limit = registration.get("max_request_bytes", 16384)
        scope = dict(schema="pfp.native-anthropic-campaign.v1", registration_sha256=self.registration_digest,
            limit=limit_microusd, stage_caps=self.stage_caps)
        with self.ledger.transaction(self.limit) as state:
            original = state.setdefault("campaign_scope", scope)
            active = state.get("campaign_registration_sha256", original["registration_sha256"])
            if original["limit"] != self.limit or original["stage_caps"] != self.stage_caps:
                raise ValueError("CAMPAIGN_SCOPE_MISMATCH")
            if active != self.registration_digest:
                amendment = registration_amendment
                if not isinstance(amendment, dict):
                    raise ValueError("CAMPAIGN_SCOPE_MISMATCH")
                if (amendment.get("schema") != "pfp.native-anthropic-amendment.v1"
                        or amendment.get("predecessor_registration_sha256") != active
                        or amendment.get("successor_registration_sha256") != self.registration_digest
                        or amendment.get("accounting_sha256") != self._digest(state)
                        or not self._authorized_reference(amendment.get("authorization_reference"))
                        or not self._authorized_reference(amendment.get("reason"))
                        or not isinstance(amendment.get("source_changes"), dict)):
                    raise ValueError("CAMPAIGN_AMENDMENT_INVALID")
                state.setdefault("registration_amendments", []).append(deepcopy(amendment))
                state["campaign_registration_sha256"] = self.registration_digest
            elif registration_amendment is not None:
                if registration_amendment not in state.get("registration_amendments", []):
                    raise ValueError("CAMPAIGN_AMENDMENT_INVALID")
            state.setdefault("stage_spent", {stage: 0 for stage in self.stage_caps})
            state.setdefault("last_dispatch", None)

    @staticmethod
    def _digest(value):
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False).encode()).hexdigest()

    @staticmethod
    def _authorized_reference(value):
        # This is an explicit operator decision reference, not authentication or
        # a model-generated admission. The calling workflow obtains the decision.
        return type(value) is str and bool(value.strip()) and len(value.encode("utf-8")) <= 2048

    def reconcile_ambiguous(self, attempt_id, *, authorization_reference,
                            expected_snapshot_sha256, expected_request_sha256):
        """Keep the full reserved charge and unknown usage after explicit review.

        Neither a receipt nor a reply is fabricated. The old attempt is never
        retried: replay returns its original unknown outcome. The append-only
        decision allows *other* registered attempts to use the remaining budget.
        """
        if not self._authorized_reference(authorization_reference):
            raise ValueError("RECONCILIATION_AUTHORIZATION_REQUIRED")
        with self.ledger.transaction(self.limit) as state:
            entry = state["attempts"].get(attempt_id)
            if entry is None or entry["request_sha256"] != expected_request_sha256:
                raise ValueError("RECONCILIATION_BINDING_MISMATCH")
            existing = entry.get("conservative_reconciliation")
            if existing is not None:
                if existing["authorization_reference"] != authorization_reference:
                    raise ValueError("RECONCILIATION_BINDING_MISMATCH")
                return deepcopy(existing)
            if self._digest(state) != expected_snapshot_sha256:
                raise ValueError("RECONCILIATION_SNAPSHOT_MISMATCH")
            if entry["state"] not in {"reserved", "dispatched", "unknown"}:
                raise ValueError("AMBIGUOUS_ATTEMPT_REQUIRED")
            actual = entry.get("actual_microusd")
            if actual is not None and (type(actual) is not int or not 0 <= actual <= entry["reserved_microusd"]):
                raise ValueError("RECONCILIATION_RESERVE_INSUFFICIENT")
            event = dict(basis="CONSERVATIVE_RESERVED_CHARGE", attempt_id=attempt_id,
                prior_entry_sha256=self._digest(entry), accounting_sha256=expected_snapshot_sha256,
                prior_state=entry["state"], request_sha256=expected_request_sha256,
                charged_microusd=entry["reserved_microusd"], actual_microusd=entry.get("actual_microusd"),
                authorization_reference=authorization_reference)
            entry["conservative_reconciliation"] = event
            entry["state"] = "conservatively_charged"
            entry["charged_microusd"] = entry["reserved_microusd"]
            state.setdefault("reconciliations", []).append(deepcopy(event))
            return deepcopy(event)

    def snapshot(self):
        with self.ledger.transaction(self.limit) as state:
            return deepcopy(state)

    def settle_retained_reply(self, attempt_id, *, request, expected_snapshot_sha256):
        """Settle a hash-bound retained reply using native metering, without sending."""
        before=self.snapshot()
        entry=before['attempts'].get(attempt_id)
        if entry is None or entry['request_sha256']!=self._digest(request):
            raise ValueError('RETAINED_SETTLEMENT_BINDING_MISMATCH')
        if entry.get('metered_reconciliation') is not None:
            return deepcopy(entry['metered_reconciliation'])
        if self._digest(before)!=expected_snapshot_sha256:
            raise ValueError('RETAINED_SETTLEMENT_SNAPSHOT_MISMATCH')
        original=entry.get('outcome') or {}
        raw=original.get('raw')
        if (entry['state']!='unknown' or original.get('dispatch')!='REPLIED'
                or not 200<=original.get('status',0)<300 or not raw):
            raise ValueError('RETAINED_REPLY_REQUIRED')
        from omega_engine_pfp.infrastructure.seat_transport.anthropic_messages import read_retained_reply
        data=read_retained_reply(raw,original['status'])
        if sha256(data).hexdigest()!=raw['sha256'].removeprefix('sha256:') or len(data)!=raw['bytes']:
            raise ValueError('REPLAY_RAW_MISMATCH')
        replay=self.transport.replay(request,raw=raw,status=original['status'])
        if isinstance(replay,Err): raise ValueError(replay.error.code)
        observed=replay.value
        actual=observed.get('metered_cost_microusd')
        if (observed.get('dispatch')!='REPLIED' or observed.get('status')!=original['status']
                or observed.get('raw')!=raw or observed.get('response')!=original.get('response')
                or (observed.get('response') or {}).get('model')!=request['model']
                or type(actual) is not int or not 0<=actual<=entry['reserved_microusd']):
            raise ValueError('RETAINED_SETTLEMENT_UNVERIFIABLE')
        event=dict(basis='NATIVE_RETAINED_USAGE_RATED_ESTIMATE',attempt_id=attempt_id,
            request_sha256=entry['request_sha256'],accounting_sha256=expected_snapshot_sha256,
            registration_sha256=self.registration_digest,original_outcome=deepcopy(original),
            actual_microusd=actual,provider_calls=0,invoice_cost='UNOBSERVED')
        with self.ledger.transaction(self.limit) as state:
            if self._digest(state)!=expected_snapshot_sha256:
                raise ValueError('RETAINED_SETTLEMENT_SNAPSHOT_MISMATCH')
            current=state['attempts'][attempt_id]
            release=current.get('charged_microusd',current['reserved_microusd'])-actual
            state['spent']-=release
            state['stage_spent'][current['stage']]-=release
            current.update(state='settled',actual_microusd=actual,charged_microusd=actual,
                outcome={**original,'metered_cost_microusd':actual},metered_reconciliation=event)
            state.setdefault('metered_reconciliations',[]).append(deepcopy(event))
        return deepcopy(event)

    def complete_prepared(self, prepared, *, model, stage, attempt_id, raw_dir,
                          max_tokens=768, structured=False):
        request = native_anthropic_request(prepared,model=model,max_tokens=max_tokens,structured=structured)
        outcome = self.send(request, stage=stage, attempt_id=attempt_id, raw_dir=raw_dir)
        response = outcome.get("response") or {}
        checked = prepared.check_completion(response.get("text", "")) if outcome.get("dispatch") == "REPLIED" else None
        return dict(outcome=outcome, checked=checked, request=request,
            binding=prepared.binding, model=response.get("model"), usage=response.get("usage"),
            cost_microusd=outcome.get("metered_cost_microusd"),
            cost_basis="METERED_ESTIMATE" if outcome.get("metered_cost_microusd") is not None else "UNKNOWN")

    def send(self, request, *, stage, attempt_id, raw_dir):
        if stage not in self.stage_caps or stage == "P0":
            raise ValueError("PAID_STAGE_REQUIRED")
        if type(attempt_id) is not str or not attempt_id:
            raise ValueError("ATTEMPT_ID_REQUIRED")
        request_digest = sha256(json.dumps(request, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        if len(json.dumps(request,ensure_ascii=True,separators=(",", ":")).encode()) > self.request_byte_limit:
            return dict(dispatch="NOT_SENT",refusal=dict(code="CAMPAIGN_REQUEST_BOUND"),authority_effect="None")
        raw_name = sha256(attempt_id.encode()).hexdigest()
        options = dict(raw_dir=str(Path(raw_dir).resolve()), raw_name=raw_name)
        with self.ledger.transaction(self.limit) as state:
            previous = state["attempts"].get(attempt_id)
            if previous:
                if previous["request_sha256"] != request_digest or previous["stage"] != stage:
                    raise ValueError("ATTEMPT_BINDING_MISMATCH")
                if previous["state"] in {"settled", "not_sent", "conservatively_charged"}:
                    outcome = deepcopy(previous.get("outcome") or dict(dispatch="OUTCOME_UNKNOWN",
                        refusal=dict(code="HISTORICAL_AMBIGUOUS_CHARGED"), authority_effect="None"))
                    raw = outcome.get("raw")
                    if raw:
                        data = Path(raw["path"]).read_bytes()
                        if sha256(data).hexdigest() != raw["sha256"].removeprefix("sha256:") or len(data) != raw["bytes"]:
                            raise ValueError("REPLAY_RAW_MISMATCH")
                        if outcome.get('dispatch') == 'REPLIED':
                            body=json.loads(data)
                            blocks=body['content']
                            observed=dict(id=body['id'],model=body['model'],stop_reason=body['stop_reason'],
                                usage=body['usage'],assistant_message=dict(role='assistant',content=blocks),
                                text=''.join(block['text'] for block in blocks if block.get('type')=='text'),
                                container_id=(body.get('container') or {}).get('id'))
                            if outcome.get('response') != observed:
                                raise ValueError('REPLAY_RESPONSE_MISMATCH')
                    elif outcome.get('dispatch') == 'REPLIED':
                        raise ValueError('REPLAY_RAW_MISSING')
                    return outcome
                raise ValueError("UNRECONCILED_ATTEMPT")
            if any(row["state"] not in {"settled", "not_sent", "conservatively_charged"} for row in state["attempts"].values()):
                raise ValueError("UNRECONCILED_ATTEMPT")
        quoted = self.transport.send(request, **options, ceiling_microusd=0, quote_only=True)
        if isinstance(quoted, Err):
            raise ValueError(quoted.error.code)
        quote = quoted.value.get("quote_microusd")
        if type(quote) is not int or quote <= 0:
            raise ValueError("NATIVE_QUOTE_REQUIRED")
        if self.quote_bounds is not None:
            key=f'{stage}:{request["model"]}:{int("output_config" in request)}'
            bound=self.quote_bounds.get(key)
            if bound is None or quote>bound['quote_microusd']:
                return dict(dispatch="NOT_SENT",refusal=dict(code="QUOTE_SCOPE_EXCEEDED"),
                    quote_microusd=quote,authority_effect="None")
        with self.ledger.transaction(self.limit) as state:
            if (state["spent"] + quote > self.limit
                    or state["stage_spent"][stage] + quote > self.stage_caps[stage]
                    or self.stage_call_limits is not None and sum(row["stage"]==stage for row in state["attempts"].values()) >= self.stage_call_limits[stage]):
                return dict(dispatch="NOT_SENT", refusal=dict(code="BUDGET_CENSORED"),
                    quote_microusd=quote, authority_effect="None")
            state["spent"] += quote
            state["stage_spent"][stage] += quote
            state["attempts"][attempt_id] = dict(state="reserved", stage=stage,
                request_sha256=request_digest, reserved_microusd=quote, actual_microusd=None)
            last = state["last_dispatch"]
        if last is not None:
            self._sleep(max(0, 2 - (self._clock() - last)))
        with self.ledger.transaction(self.limit) as state:
            state["last_dispatch"] = self._clock()
            state["attempts"][attempt_id]["state"] = "dispatched"
        try:
            result = self.transport.send(request, **options, ceiling_microusd=quote)
            outcome = (dict(dispatch="OUTCOME_UNKNOWN", refusal=dict(code=result.error.code), authority_effect="None")
                if isinstance(result, Err) else dict(result.value))
        except BaseException:
            with self.ledger.transaction(self.limit) as state:
                state["attempts"][attempt_id]["state"] = "unknown"
            raise
        with self.ledger.transaction(self.limit) as state:
            entry = state["attempts"][attempt_id]
            dispatch, actual = outcome.get("dispatch"), outcome.get("metered_cost_microusd")
            if dispatch == "NOT_SENT":
                charge, status = 0, "not_sent"
            elif (dispatch == "REPLIED" and type(actual) is int and 0 <= actual <= quote
                    and (outcome.get("response") or {}).get("model") == request["model"]):
                charge, status = actual, "settled"
            else:
                charge, status = quote, "unknown"
            state["spent"] -= quote - charge
            state["stage_spent"][stage] -= quote - charge
            entry.update(state=status, actual_microusd=actual, charged_microusd=charge, outcome=outcome)
        return outcome
