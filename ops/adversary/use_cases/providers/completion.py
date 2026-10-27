"""Single provider admission/dispatch use case. AuthorityEffect: None."""

import hashlib
import json
from collections.abc import Callable

from operations.domain.rop.result import Err, Ok, Result
from adversary.domain.providers.attempt import (
    AdmittedRequest,
    CompletionOutcome,
    ProviderFailure,
    RetryClass,
    TransportFailure,
)
from adversary.domain.providers.budget import GatewayPolicy, PriceQuoteV1
from adversary.domain.providers.types import (
    MAX_PROVIDER_REPLY_BYTES,
    BudgetEnforcementUnavailable,
    BudgetExceeded,
    CandidateRequest,
    ModelNotAllowed,
    Provider,
    ProviderError,
    thaw_json,
)


def request_digest(request: CandidateRequest) -> str:
    # An unset effort is omitted so digests recorded before the field existed still match.
    decoding = None if request.decoding is None else {
        k: thaw_json(v) for k, v in vars(request.decoding).items()
        if not (k == "effort" and v is None)
    }
    # Fractions are serialized as exact numerator/denominator pairs.
    wire = json.dumps({"messages": [vars(m) for m in request.conversation()], "decoding": decoding},
                      sort_keys=True, separators=(",", ":"), default=lambda f: [f.numerator, f.denominator])
    return "sha256:" + hashlib.sha256(wire.encode("utf-8")).hexdigest()


class CompletionService:
    def __init__(self, *, allowlist, policy: GatewayPolicy | None, dispatch: Callable,
                 decode: Callable, parse: Callable, new_id: Callable[[], str],
                 maximum_liability: Callable, validate_capabilities: Callable,
                 max_output_tokens: int = 1024, observe_failure: Callable | None = None) -> None:
        self.allowlist, self.policy = allowlist, policy
        self.dispatch, self.decode, self.parse = dispatch, decode, parse
        self.new_id, self.maximum_liability = new_id, maximum_liability
        self.validate_capabilities = validate_capabilities
        self.max_output_tokens = max_output_tokens
        self.observe_failure = observe_failure

    def admit(self, provider: Provider, model: str, request: CandidateRequest) -> AdmittedRequest:
        request.check_payload_ceiling()
        self.allowlist.check(provider, model)
        limit = self.policy.max_output_tokens if self.policy is not None else self.max_output_tokens
        self.validate_capabilities(provider, model, request, limit)
        if self.policy is None:
            # Explicit unbudgeted clients promise no maximum spend. They still
            # share request admission, capability validation and reply parsing.
            return AdmittedRequest(self.new_id(), "", request_digest(request), provider, model, request, limit, None, None)
        quote = self.policy.quote_for_request(model, request)
        liability = self.maximum_liability(provider, model, request, limit, quote)
        if liability is None:
            raise BudgetEnforcementUnavailable()
        if type(liability) is not int or liability < 0:
            raise ProviderError("invalid maximum liability")
        attempt_id = self.new_id()
        identity = {"attempt_id": attempt_id, "reservation_id": attempt_id,
                    "request_digest": request_digest(request), "provider": provider.value,
                    "model": model, "max_output_tokens": limit, "estimated_microusd": quote.cost_microusd}
        receipt = self.policy.budget.reserve(identity, PriceQuoteV1(quote.observation, liability))
        return AdmittedRequest(attempt_id, attempt_id, identity["request_digest"], provider, model,
                               request, limit, receipt, quote.cost_microusd)

    def complete(self, provider: Provider, model: str, request: CandidateRequest) -> Result[CompletionOutcome, ProviderFailure]:
        admitted = None
        pending = False
        raw = None
        decoded = None
        try:
            admitted = self.admit(provider, model, request)
            # Persist before invoking any user-supplied transport. A crash in
            # this window is conservatively an ambiguous dispatched attempt.
            if self.policy is not None:
                self.policy.budget.record_attempt(admitted.attempt_id, "Dispatched")
            raw = self.dispatch(admitted)
            decoded = self.decode(raw)
            candidate = self.parse(provider, model, decoded)
            if candidate.model != model:
                raise ProviderError("provider reply model differs from the admitted deployment")
            if self.policy is not None:
                self.policy.budget.record_attempt(admitted.attempt_id, "CompletedPendingSettlement",
                    generation_id=candidate.generation_id, wire_sha256=hashlib.sha256(raw).hexdigest(),
                    reported_cost_usd=candidate.cost_usd)
            pending = True
            return Ok(CompletionOutcome(candidate, admitted, reply_bytes=bytes(raw)))
        except ProviderError as exc:
            code = getattr(exc, "code", None) or (
                "BUDGET_EXCEEDED" if isinstance(exc, BudgetExceeded) else
                "MODEL_NOT_ALLOWED" if isinstance(exc, ModelNotAllowed) else "PROVIDER_REFUSED")
            retry = exc.retry if isinstance(exc, TransportFailure) else RetryClass.TERMINAL
            retained, truncated = None, False
            if isinstance(raw, (bytes, bytearray, memoryview)):
                octets = memoryview(raw).cast("B")
                retained = bytes(octets[:MAX_PROVIDER_REPLY_BYTES + 1])
                truncated = octets.nbytes > MAX_PROVIDER_REPLY_BYTES
            usage_observation, attempt_state = None, None
            if decoded is not None and self.observe_failure is not None:
                try:
                    usage_observation = self.observe_failure(provider, model, decoded)
                except ProviderError:
                    pass
            if usage_observation is not None:
                attempt_state = ("CompletedCostUnknown" if usage_observation.cost_usd is None
                    else "CompletedPendingSettlement")
                if not usage_observation.generation_id:
                    attempt_state = "CompletedAccountingUnavailable"
                elif self.policy is not None:
                    # The answer was refused, but the vendor returned identifiable
                    # usage. Keep the hold pending a trusted generation receipt.
                    self.policy.budget.record_attempt(admitted.attempt_id, "CompletedPendingSettlement",
                        generation_id=usage_observation.generation_id,
                        wire_sha256=hashlib.sha256(raw).hexdigest(),
                        reported_cost_usd=usage_observation.cost_usd)
                    pending = True
            return Err(ProviderFailure(code, "provider.completion", retry,
                admitted.attempt_id if admitted else "", exc,
                reply_bytes=retained, reply_truncated=truncated,
                usage_observation=usage_observation, attempt_state=attempt_state))
        finally:
            if admitted is not None and self.policy is not None and not pending:
                self.policy.budget.record_attempt(admitted.attempt_id, "OutcomeUnknown")
