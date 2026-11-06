"""The one place a provider is called: estimate, reserve, dispatch, settle, receipt.

AuthorityEffect: None. Order of operations for every call (nothing is sent before step 3 passes):
  1. rate the worst case: input tokens (count_tokens for Anthropic, a byte bound otherwise) plus the
     max_tokens bound at the output rate; thinking tokens are output tokens and max_tokens bounds them;
  2. refuse a Haiku request over the 100K-token tier boundary (the price table is only valid below it);
  3. reserve the worst case in the ledger (BudgetRefused if any weekly or run cap would be exceeded);
  4. dispatch exactly one request;
  5. settle: the rated cost replaces the reservation; an unreported cost on a paid tier keeps the
     worst case; an ambiguous outcome (timeout after send) keeps it as unreconciled spend.
Every outcome appends a redacted receipt row; this is the explicit record that this system, unlike the
historical batches ("external_provider_calls: 0"), calls providers.
"""
from __future__ import annotations

import uuid

from .budget import BudgetRefused, cost_microusd as rate_cost
from .config import HAIKU_LONG_CONTEXT_TOKENS, PRICES
from .llm_common import Redactor, utc_iso
from .providers import CallRequest, CallResult, ProviderError


class Gateway:
    def __init__(self, providers: dict, ledger, *, run_id: str, run_cap_microusd: int, redactor: Redactor | None = None):
        self.providers = providers
        self.ledger = ledger
        self.run_id = run_id
        self.run_cap_microusd = run_cap_microusd
        self.redactor = redactor or Redactor()
        self.receipts: list = []

    # ------------------------------------------------------------------ estimation
    def estimate(self, provider_name: str, req: CallRequest, family: str):
        """(input_tokens, worst_case_microusd). Free tiers rate 0."""
        provider = self.providers[provider_name]
        tokens = provider.estimate_input_tokens(req)
        if family == 'free' or (provider_name, req.model) not in PRICES:
            if family != 'free':
                raise BudgetRefused('NO_PRICE', 'no price on file for %s/%s; a paid call needs one' % (provider_name, req.model))
            return tokens, 0
        pin, pout = PRICES[(provider_name, req.model)]
        if provider_name == 'anthropic' and req.model == 'claude-haiku-5-5' and tokens > HAIKU_LONG_CONTEXT_TOKENS:
            raise BudgetRefused('LONG_CONTEXT_TIER', 'input of %d tokens is above the Haiku 100K price tier' % tokens)
        return tokens, rate_cost(tokens, req.max_tokens, pin, pout)

    # ------------------------------------------------------------------ the call
    def call(self, provider_name: str, req: CallRequest, *, tier_id: int, family: str, attempt_id: str) -> CallResult:
        call_id = '%s:%s' % (attempt_id, uuid.uuid4().hex[:8])
        row = {'call_id': call_id, 'run_id': self.run_id, 'attempt_id': attempt_id, 'tier': tier_id,
               'provider': provider_name, 'model': req.model, 'family': family, 'effort': req.effort,
               'max_tokens': req.max_tokens, 'started_utc': utc_iso(), 'status': 'not_sent'}
        provider = self.providers.get(provider_name)
        if provider is None:
            row.update(error_code='provider_unconfigured')
            self.receipts.append(row)
            raise ProviderError('provider_unconfigured', provider_name)
        try:
            tokens, estimate = self.estimate(provider_name, req, family)
            row.update(estimated_input_tokens=tokens, estimate_microusd=estimate)
            self.ledger.reserve(call_id, run_id=self.run_id, run_cap_microusd=self.run_cap_microusd, family=family,
                                provider=provider_name, model=req.model, estimate_microusd=estimate)
        except BudgetRefused as refusal:
            row.update(status='refused_before_dispatch', error_code=refusal.code, error=refusal.message)
            self.receipts.append(row)
            raise
        except ProviderError as error:
            row.update(status='estimate_failed', error_code=error.code, error=self.redactor.redact(error.message))
            self.receipts.append(row)
            raise
        try:
            result = provider.complete(req)
        except ProviderError as error:
            row.update(status='ambiguous' if error.ambiguous else 'error', error_code=error.code,
                       error=self.redactor.redact(error.message), http_status=error.status,
                       backoff_events=error.backoff_events, retry_after=error.retry_after)
            if error.ambiguous and family != 'free':
                row['retained_microusd'] = self.ledger.retain_unreconciled(call_id)
            else:
                self.ledger.release(call_id)
            self.receipts.append(row)
            raise
        except BaseException:
            self.ledger.release(call_id) if family == 'free' else self.ledger.retain_unreconciled(call_id)
            row.update(status='interrupted')
            self.receipts.append(row)
            raise
        # settle
        cost, source = result.cost_microusd, result.cost_source
        if family != 'free' and (cost is None or source in ('unreported', 'free_tier')):
            cost, source = estimate, 'worst_case_reservation_retained'
        if family == 'free':
            self.ledger.release(call_id)
            self.ledger.count_free_call(provider_name, req.model, result.input_tokens or 0, result.output_tokens or 0)
            cost = 0
        else:
            self.ledger.settle(call_id, cost_microusd=cost, input_tokens=result.input_tokens or 0,
                               output_tokens=result.output_tokens or 0, cost_source=source)
        result.cost_microusd, result.cost_source = cost, source
        row.update(status='refused_by_model' if result.refusal else 'ok', served_model=result.model,
                   input_tokens=result.input_tokens, output_tokens=result.output_tokens, cost_microusd=cost,
                   cost_source=source, request_id=result.request_id, stop_reason=result.stop_reason,
                   stop_category=result.stop_category, truncated=result.truncated, latency_s=result.latency_s,
                   streamed=result.streamed, structured_mode=result.structured_mode, http_status=result.http_status,
                   backoff_events=result.backoff_events)
        self.receipts.append(row)
        return result

    def totals(self) -> dict:
        by_tier = {}
        for row in self.receipts:
            tier = by_tier.setdefault(row['tier'], {'calls': 0, 'sent': 0, 'input_tokens': 0, 'output_tokens': 0,
                                                    'cost_microusd': 0, 'errors': 0, 'refused_before_dispatch': 0})
            tier['calls'] += 1
            if row['status'] in ('ok', 'refused_by_model'):
                tier['sent'] += 1
                tier['input_tokens'] += row.get('input_tokens') or 0
                tier['output_tokens'] += row.get('output_tokens') or 0
                tier['cost_microusd'] += row.get('cost_microusd') or 0
            elif row['status'] == 'refused_before_dispatch':
                tier['refused_before_dispatch'] += 1
            else:
                tier['errors'] += 1
        return by_tier
