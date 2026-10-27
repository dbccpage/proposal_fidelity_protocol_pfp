"""Immutable admitted provider request and explicit failure/outcome states."""

import base64
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

from adversary.domain.providers.types import (
    BudgetReceipt,
    CandidateRequest,
    CandidateResponse,
    Provider,
    ProviderError,
)


@dataclass(frozen=True)
class ProviderUsageObservation:
    """Validated billing/usage, independent of an unusable model completion."""

    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    generation_id: str
    cost_usd: float | None
    transport: str

    def __post_init__(self):
        # Reuse the existing exact scalar validation; this value never carries
        # a proposed answer and cannot be consumed as a CandidateResponse.
        CandidateResponse("", self.model, self.provider, self.input_tokens,
            self.output_tokens, transport=self.transport,
            generation_id=self.generation_id, cost_usd=self.cost_usd)

    def metadata(self) -> dict:
        return {key: getattr(self, key) for key in (
            "model", "provider", "input_tokens", "output_tokens", "generation_id",
            "cost_usd", "transport")}


class RetryClass(str, Enum):
    TERMINAL = "terminal"
    TRANSIENT_BEFORE_DISPATCH = "transient_before_dispatch"
    OUTCOME_UNKNOWN = "outcome_unknown"


class TransportFailure(ProviderError):
    def __init__(self, code: str, *, retry: RetryClass = RetryClass.OUTCOME_UNKNOWN,
        reply_bytes: bytes = b"", http_status: int | None = None,
        reply_truncated: bool = False):
        self.code, self.retry = code, retry
        self.reply_bytes, self.http_status = reply_bytes, http_status
        self.reply_truncated = reply_truncated
        super().__init__(code)


@dataclass(frozen=True)
class AdmittedRequest:
    attempt_id: str
    reservation_id: str
    request_digest: str
    provider: Provider
    model: str
    request: CandidateRequest
    max_output_tokens: int
    receipt: BudgetReceipt | None
    estimated_microusd: int | None


@dataclass(frozen=True)
class ProviderFailure:
    code: str
    locus: str
    retry: RetryClass
    attempt_id: str = ""
    # The compatibility facade re-raises the original typed error; safe result
    # metadata never includes its potentially vendor-authored message.
    cause: ProviderError | None = None
    reply_bytes: bytes | None = None
    reply_truncated: bool = False
    usage_observation: ProviderUsageObservation | None = None
    attempt_state: str | None = None

    def response_metadata(self) -> dict:
        """Bounded raw custody for internal observations, never a public message.

        A truncated body's digest binds the retained prefix only. The transport
        boundary bounds the bytes; an absent HTTP response adds no invented raw.
        """
        status = getattr(self.cause, "http_status", None)
        raw = self.reply_bytes if self.reply_bytes is not None else getattr(self.cause, "reply_bytes", None)
        if type(raw) is not bytes:
            return {}
        metadata = dict(
            raw_reply_base64=base64.b64encode(raw).decode("ascii"),
            raw_reply_sha256=sha256(raw).hexdigest(),
            raw_reply_bytes=len(raw),
            raw_reply_truncated=(
                self.reply_truncated
                if self.reply_bytes is not None
                else getattr(self.cause, "reply_truncated", False)
            ),
        )
        if status is not None:
            metadata["http_status"] = status
        if self.usage_observation is not None:
            metadata.update(self.usage_observation.metadata())
        if self.attempt_state is not None:
            metadata["attempt_state"] = self.attempt_state
        return metadata


@dataclass(frozen=True)
class CompletionOutcome:
    candidate: CandidateResponse
    admitted: AdmittedRequest
    state: str = "CompletedPendingSettlement"
    reply_bytes: bytes = b""
