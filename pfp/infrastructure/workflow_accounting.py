"""Workflow batch admission over the canonical durable estimated ledger.

No financial arithmetic or provider transport is reimplemented here. Atomic
batch reservation extends the existing single-action gateway. AuthorityEffect: None.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from threading import Barrier
from time import perf_counter

from operations.domain.rop.result import Err, Ok
from adversary.domain.providers.types import Provider
from adversary.infrastructure.providers.gateway import OearsLlmGateway
from pfp.infrastructure.estimated_gateway import (
    EstimatedBudgetGateway as CanonicalEstimatedBudgetGateway,
    _RunTransport,
    _read_run_state as _read_run_state,
    _run_refusal,
    create_accounted_openrouter_gateway as canonical_gateway,
)


class EstimatedBudgetGateway(CanonicalEstimatedBudgetGateway):
    def complete_batch_result(self, requests, *, provider, model):
        """Atomically reserve a finite concurrent batch, then send each action once.

        An unrelated pending/unknown action still blocks admission. Every member
        is charged before any worker starts; partial batches are never admitted.
        This is estimated accounting, not a provider-enforced dollar ceiling.
        """
        try:
            if type(requests) is not dict or not 1 <= len(requests) <= 64:
                raise ValueError("INVALID_ESTIMATED_BATCH")
            requests = dict(requests)
            options = dict(provider=provider, model=model)
            entries = {}
            for action_id, request in requests.items():
                if type(action_id) is not str or not action_id:
                    raise ValueError("INVALID_BATCH_ACTION_ID")
                binding = self._binding(action_id, request, options)
                reserve, tokens = self._quote(request, model=model)
                entry = dict(state="reserved", reserved=reserve, model=model,
                    pricing_sha256=self._price_for(model)["catalog_sha256"],
                    pricing=deepcopy(self._price_for(model)), input_token_estimate=tokens,
                    max_output_tokens=self.max_output_tokens)
                if provider != Provider.OPENROUTER:
                    raise ValueError("ESTIMATED_BATCH_REQUIRES_OPENROUTER")
                entries[action_id] = (entry, binding)
            with self.ledger.transaction(self.limit) as state:
                if any(key in state["action_claims"] for key in requests):
                    raise ValueError("PFP_ACTION_ALREADY_CLAIMED")
                if any(item["state"] != "settled" for item in state["attempts"].values()):
                    raise ValueError("UNRECONCILED_ATTEMPT")
                if len(state["attempts"]) + len(entries) > self.max_calls:
                    raise ValueError("CALL_ALLOWANCE_EXHAUSTED")
                liability = state["spent"] + sum(row[0]["reserved"] for row in entries.values())
                if liability > self.limit:
                    raise ValueError("ESTIMATED_BUDGET_EXCEEDED")
                if liability > self.limit * self.scope["stop_percent"] // 100:
                    raise ValueError("FUZZY_BUDGET_MILESTONE_REACHED")
                for action_id, (entry, binding) in entries.items():
                    state["attempts"][action_id] = entry
                    state["action_claims"][action_id] = dict(entry, binding=binding)
                state["spent"] = liability
        except (ValueError, KeyError, ArithmeticError) as exc:
            return _run_refusal(str(exc))
        barrier = Barrier(len(requests))

        def send(action_id, request):
            barrier.wait(timeout=30)
            started = perf_counter()
            try:
                result = self._dispatch_reserved(action_id, request, model, options)
            except Exception:
                self._update_action(action_id, state="outcome_unknown")
                result = _run_refusal("BATCH_DISPATCH_OUTCOME_UNKNOWN")
            return dict(outcome=result, started=started, ended=perf_counter())

        with ThreadPoolExecutor(max_workers=len(requests), thread_name_prefix="pfp-batch") as pool:
            futures = {key: pool.submit(send, key, request) for key, request in requests.items()}
            return Ok({key: future.result() for key, future in futures.items()})

    def _dispatch_reserved(self, action_id, request, active_model, options):
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

def create_accounted_openrouter_gateway(model, max_output_tokens, **options):
    """Keep canonical credential/pricing composition and the original ledger scope."""
    bound = canonical_gateway(model, max_output_tokens, **options)
    if not isinstance(bound, CanonicalEstimatedBudgetGateway):
        return bound
    return EstimatedBudgetGateway(
        bound.gateway, model=bound.model, price=bound.price,
        limit_microusd=bound.limit, max_calls=bound.max_calls,
        accounting_path=options["accounting_path"],
        run_id=bound.scope["run_id"],
        objective_sha256=bound.scope["objective_sha256"],
        max_output_tokens=bound.max_output_tokens,
    )
