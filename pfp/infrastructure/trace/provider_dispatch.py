"""P1b: durable provider dispatch through the real gateway.

Two barriers, and the reason for each is a distinct way to lose money.

**Barrier 1 — intent, before the socket.** The process can die after the write
and before the request leaves. Without a durable intent record, recovery cannot
tell "never dispatched" from "dispatched, outcome unknown", and those demand
opposite actions: the first is safe to retry, the second is not. So the intent
is fsynced *immediately* before the call, at the tightest seam available.

**Barrier 2 — encrypted custody, before any state mutation.** A paid response can
return, downstream state can mutate, and the evidence can still vanish. Then the
system has acted on a response it can no longer produce, which is unfalsifiable
after the fact.

Ordering inside barrier 2 is itself load-bearing: **the exact response bytes are
atomically committed to the OEOS encrypted CAS first, then the trace records only
their typed reference.** The reverse order has a failure where the trace claims a
durable envelope that does not exist. This way the worst case is an orphaned
encrypted envelope with the run reading `STATUS_UNKNOWN` — conservative, and
recoverable by hand.

**No auto-retry on `ProviderDispatchStatusUnknown`.** An unknown outcome may have
been a completed, billed call. Retrying spends again on a coin-flip, and the
budget controller has already charged for the first attempt. Recovery is a human
decision with the trace in hand.

The transport wraps the *real* `OearsLlmGateway`, so both fail-closed gates run
ahead of it: `ModelAllowlist.check` then the effective-dated `PriceTable.quote`,
both inside `admit()`, which `complete()` calls before touching the transport.
A scripted model absent from either raises `ModelNotAllowed` **before dispatch** — a
different exception type from any durability failure, which is what makes the
two distinguishable in a report.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from governance.domain.ingress.limits import (
    REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    IngressRefusal,
)
from adversary.domain.providers.types import (
    ReplyTooLarge,
    check_reply_bytes,
)

from .execution_trace import (
    DURABILITY_FSYNC_LIVE,
    ExecutionTrace,
    TraceRecord,
    TraceRefusal,
)
from .trace_schema import (
    EVENT_DISPATCH_INTENT_DURABLE,
    EVENT_DISPATCH_REFUSED_PREFLIGHT,
    EVENT_DISPATCH_STATUS_UNKNOWN,
    EVENT_RESPONSE_DURABLE,
)

# The four dispatch event names are declared by ``trace_schema`` and re-exported
# here. They used to be defined in this module, which made a reader's idea of
# which events exist depend on whether it had imported the dispatcher.

#: Derived per-attempt outcomes.
#: Dispatched, response durable, artifact present and matching.
DISPATCH_COMPLETE = "DISPATCH_COMPLETE"
#: Intent durable, no durable response. May have been billed. Never retryable.
DISPATCH_STATUS_UNKNOWN = "DISPATCH_STATUS_UNKNOWN"
#: The provider returned a body, but its raw bytes crossed the admitted ceiling.
#: The attempt was dispatched and may have been billed, so it is never retryable;
#: unlike STATUS_UNKNOWN, the terminal mechanism is known exactly.
DISPATCH_REPLY_REFUSED_TOO_LARGE = "DISPATCH_REPLY_REFUSED_TOO_LARGE"
#: A fail-closed gate refused ahead of dispatch. Nothing spent; safe to re-run.
DISPATCH_REFUSED_PREFLIGHT = "DISPATCH_REFUSED_PREFLIGHT"
#: Response recorded, but encrypted CAS replay fails or does not match the ref.
#: Still not retryable: the call was dispatched regardless of the envelope's fate.
DISPATCH_EVIDENCE_MISSING = "DISPATCH_EVIDENCE_MISSING"
#: Response recorded; no matching era-specific store was supplied for replay.
DISPATCH_EVIDENCE_UNVERIFIED = "DISPATCH_EVIDENCE_UNVERIFIED"
#: The trace's own records about this attempt contradict each other or repeat --
#: two intents under one id, a response naming a different provider than its
#: intent, a response with no intent at all. Not retryable: evidence that cannot
#: be read is not evidence that nothing was spent.
DISPATCH_EVIDENCE_MALFORMED = "DISPATCH_EVIDENCE_MALFORMED"

#: The declared test model. Registered in BOTH gates rather than bypassing them,
#: so P1b exercises the allowlist and pricing path instead of proving something
#: about a code path production never takes.
SCRIPTED_MODEL = "scripted/p1b-fixture"
#: Priced at zero: a scripted transport spends nothing, and a nonzero row would
#: make budget exhaustion in a test mean something it does not.
SCRIPTED_PRICE_MICROUSD_PER_MTOK = 0
RAW_PROVIDER_RESPONSE_SCHEMA = "core.provider.raw-response.v1"


class EncryptedArtifactStorePort(Protocol):
    """The OEOS-owned encrypted CAS surface used at the provider seam."""

    def put(self, payload: bytes, *, artifact_schema: str) -> Any: ...

    def get_canonical(self, value: Mapping[str, object]) -> bytes: ...


def provider_label(provider: Any) -> str:
    """The provider's declared value, whatever class object it arrived as.

    Never `is`, never `isinstance`. `providers/types.py` is loaded twice under
    two module names, so a legacy `Provider.FIXTURE` and the canonical one are
    unrelated class objects; identity comparisons across that seam silently
    answer "no", which in a confinement check reads as a passing gate.
    """
    return str(getattr(provider, "value", provider))


def _canonical(payload: Mapping[str, Any]) -> bytes:
    """Canonical encoding for *derived identities only*, never for stored evidence."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


class ScriptedTransport:
    """A deterministic byte transport. Replays declared **bytes**, in order.

    Returns ``bytes``, not a mapping, and that is the whole point. The gateway's
    ``TransportFn`` contract hands back an already-decoded ``dict``, so a
    durability barrier placed at that boundary can only persist a *canonical
    re-encoding of a decoded value* -- which is not what the provider sent. It
    silently discards duplicate JSON properties, original number and string
    encodings, whitespace, key order, and any malformed or truncated output.
    Those are exactly the artifacts a durability record exists to preserve, and a
    reconstruction cannot prove what the adapter received.

    So the seam sits below decoding: this yields bytes, ``DurableDispatchTransport``
    persists those bytes, and only then decodes them for the gateway.

    Not a mock of the gateway: allowlist, pricing, budget and the real
    openai-compatible parser all still execute. Only the socket is replaced.
    """

    def __init__(
        self, payloads: Sequence[bytes | str | Mapping[str, Any] | BaseException]
    ) -> None:
        if not payloads:
            raise ValueError("ScriptedTransport requires at least one payload")
        self._payloads = [
            p if isinstance(p, (BaseException, AbruptProcessExit)) else _as_bytes(p)
            for p in payloads
        ]
        self.calls: list[tuple[str, str]] = []

    def __call__(self, provider: Any, model: str, request: Any) -> bytes:
        index = len(self.calls)
        self.calls.append((provider_label(provider), model))
        if index >= len(self._payloads):
            raise ProviderScriptExhausted(
                f"scripted transport has {len(self._payloads)} payload(s); call {index + 1} has none"
            )
        payload = self._payloads[index]
        if isinstance(payload, AbruptProcessExit):
            os._exit(payload.code)
        if isinstance(payload, BaseException):
            # A declared failure. The script says what the socket does, and
            # "raises this" is one of the things a socket does -- so failure
            # cases stay inside closed construction instead of requiring an
            # arbitrary callable, which is the hole that let a scripted transport
            # be hidden behind a real provider identity.
            raise payload
        return payload


def _as_bytes(payload: bytes | str | Mapping[str, Any]) -> bytes:
    """Accept bytes verbatim; encode a str; serialize a mapping as a convenience.

    A mapping is admitted only so simple fixtures stay readable. It is a lossy
    entry point by construction -- a mapping cannot express duplicate properties
    or original encodings -- so any test that cares about byte fidelity must
    supply ``bytes``.
    """
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if callable(payload):
        # Refused explicitly rather than left to fail obscurely inside
        # `dict(payload)`. A scripted response is *data*: the socket's behaviour
        # is declared, never supplied. Accepting a callable here is exactly what
        # let a `ScriptedTransport` hide inside a closure, defeat every attempt to
        # recognise it, and be sealed under a real vendor's identity.
        raise TypeError(
            "a scripted response must be declared bytes, not a callable; "
            "the socket's behaviour is data, and a callable is the shape that "
            "cannot be checked"
        )
    return json.dumps(dict(payload), separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class AbruptProcessExit:
    """A declared script instruction: terminate the process at this point.

    The crash matrix needs a socket that kills its own process *after* barrier 1
    has fsynced and before anything else happens. That used to be arranged by
    assigning a closure onto the transport, which meant the crash child could
    only be built by hand -- and a harness built by hand is not measuring the
    wiring that ships.

    Declared rather than injected, so it travels inside a response script and the
    fixture factory stays closed over its own transport. `os._exit` is deliberate:
    no unwinding, no `atexit`, no buffer flush. It is the strongest interruption a
    portable suite can produce and it is still not power loss, which is what
    ``durability_scope``'s ``evidence_ceiling`` records.
    """

    code: int = 1


class ProviderScriptExhausted(RuntimeError):
    """The script ran out of declared responses.

    Distinct from a durability failure and from a gate refusal, so a report can
    say which of the three happened.
    """


def scripted_openai_payload(content: str, *, model: str = SCRIPTED_MODEL) -> dict:
    """An openai-compatible body, so the real parser runs against it."""
    return {
        "id": "chatcmpl_scripted",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
    }


@dataclass(frozen=True)
class DispatchOutcome:
    """One attempt, as recovered from a trace."""

    attempt_id: str
    status: str
    provider: str
    model: str
    raw_response_sha256: str | None
    retry_permitted: bool
    encrypted_artifact_ref: Mapping[str, object] | None = None


class DurableDispatchTransport:
    """Wraps a ``TransportFn`` with intent and encrypted-CAS barriers.

    Placed at the transport seam rather than around ``complete()`` because that
    is the only point where the raw bytes exist and nothing has yet consumed
    them. Wrapping ``complete()`` would put barrier 2 after parsing, which is
    already a state mutation.
    """

    def __init__(
        self,
        trace: ExecutionTrace,
        inner: Callable[..., bytes | bytearray | memoryview],
        *,
        artifact_store: EncryptedArtifactStorePort,
        live: bool = True,
    ) -> None:
        # A live call against a buffered trace can lose the record of paid bytes.
        # Refused here as well as at RunStarted: a trace opened for replay can be
        # handed to a live dispatcher later, and this is the last point where
        # nothing has been spent yet.
        if live and trace.durability != DURABILITY_FSYNC_LIVE:
            raise TraceRefusal(
                "live dispatch requires an fsync_live trace; "
                f"this trace is {trace.durability}"
            )
        # ...and the trace must already have said it is live. Otherwise every
        # record below is written into a file whose `RunStarted` swore no real
        # provider would be contacted, which is a false statement about the one
        # thing the trace is read for. Checked in this direction only: a
        # non-live dispatcher against a live trace is merely a run that spent
        # nothing.
        if live and not trace.live_transport:
            raise TraceRefusal(
                "live dispatch requires a trace that declared live_transport; "
                f"this trace declared run_mode={trace.run_mode.value!r}, so the "
                "records would testify to the opposite of what happened"
            )
        self.trace = trace
        self.inner = inner
        self.live = live
        if not callable(getattr(artifact_store, "put", None)) or not callable(
            getattr(artifact_store, "get_canonical", None)
        ):
            raise TypeError("artifact_store must implement the encrypted CAS port")
        self.artifact_store = artifact_store
        self._attempts = 0

    def _attempt_id(self, provider: Any, model: str, request: Any) -> str:
        """Content-addressed over the *declared* inputs, so a replay on any host
        derives the same id.

        Everything host-shaped is deliberately excluded. An earlier revision
        mixed in the trace's ``RunStarted`` digest, which covers the derived
        durability scope: OS, OS version, interpreter version, filesystem. Attempt
        ids therefore changed when the interpreter was upgraded or the work moved
        machines, so replaying the same declared execution produced ids that no
        longer joined to the artifacts the first run had written -- and a recovery
        join that silently misses is indistinguishable from a dispatch that never
        happened. Identity must be a function of what the caller declared and
        nothing else.

        The consequence is accepted rather than engineered around: two different
        executions that declare the same ``execution_id`` genuinely do collide,
        because they declared the same thing. That collision is made *loud*
        instead of impossible by exclusive ``"xb"`` creation of the artifact,
        which is the guard that actually protects the evidence.
        """
        material = _canonical(
            {
                "execution_id": self.trace.execution_id,
                "index": self._attempts,
                "provider": provider_label(provider),
                "model": model,
                "system_sha256": hashlib.sha256(
                    getattr(request, "system", "").encode("utf-8")
                ).hexdigest(),
                "user_sha256": hashlib.sha256(
                    getattr(request, "user", "").encode("utf-8")
                ).hexdigest(),
            }
        )
        return hashlib.sha256(material).hexdigest()

    def _record_reply_refusal(
        self,
        *,
        attempt_id: str,
        provider: str,
        model: str,
        exc: ReplyTooLarge,
    ) -> None:
        self.trace.record(
            EVENT_DISPATCH_STATUS_UNKNOWN,
            attempt_id=attempt_id,
            provider=provider,
            model=model,
            failure_type=type(exc).__name__,
            failure=str(exc)[:512],
            retry_permitted=False,
            outcome_code=DISPATCH_REPLY_REFUSED_TOO_LARGE,
            refusal_receipt=exc.receipt.to_dict(),
            dispatched=True,
        )

    def maximum_liability(self, provider, model, request, max_output_tokens, quote):
        if not self.live:
            return quote.cost_microusd
        maximum = getattr(self.inner, "maximum_liability", None)
        return None if maximum is None or not callable(getattr(self.inner, "dispatch", None)) else maximum(provider, model, request, max_output_tokens, quote)

    def dispatch(self, admitted) -> bytes:
        return self(admitted.provider, admitted.model, admitted.request, admitted=admitted)

    def __call__(self, provider: Any, model: str, request: Any, *, admitted=None) -> bytes:
        attempt_id = self._attempt_id(provider, model, request)
        self._attempts += 1
        label = provider_label(provider)

        # ---- BARRIER 1: intent durable, immediately before the socket --------
        self.trace.record(
            EVENT_DISPATCH_INTENT_DURABLE,
            attempt_id=attempt_id,
            provider=label,
            model=model,
            live=self.live,
            request_system_sha256=hashlib.sha256(
                getattr(request, "system", "").encode("utf-8")
            ).hexdigest(),
            request_user_sha256=hashlib.sha256(
                getattr(request, "user", "").encode("utf-8")
            ).hexdigest(),
        )

        try:
            if admitted is not None and callable(getattr(self.inner, "dispatch", None)):
                raw_bytes = self.inner.dispatch(admitted)
            else:
                raw_bytes = self.inner(provider, model, request)
        except ReplyTooLarge as exc:
            # A streaming socket may enforce the same raw-byte boundary before
            # it can hand a body back.  The dispatch happened, the refusal
            # mechanism is known, and a retry could bill again.
            self._record_reply_refusal(
                attempt_id=attempt_id,
                provider=label,
                model=model,
                exc=exc,
            )
            raise
        except BaseException as exc:
            if (
                isinstance(exc, IngressRefusal)
                and exc.receipt.refusal_code == REFUSAL_PROVIDER_REPLY_TOO_LARGE
            ):
                # The governance streaming readers raise their base refusal
                # before a provider adapter can return raw bytes. Translate
                # only the provider-reply code into the stable provider type;
                # unrelated ingress refusals remain generic unknown outcomes.
                reply_too_large = ReplyTooLarge(exc.receipt)
                self._record_reply_refusal(
                    attempt_id=attempt_id,
                    provider=label,
                    model=model,
                    exc=reply_too_large,
                )
                raise reply_too_large from exc
            # The call may have completed and been billed. Record and re-raise;
            # do NOT retry here under any circumstance.
            self.trace.record(
                EVENT_DISPATCH_STATUS_UNKNOWN,
                attempt_id=attempt_id,
                provider=label,
                model=model,
                failure_type=type(exc).__name__,
                failure=str(exc)[:512],
                retry_permitted=False,
            )
            raise

        if not isinstance(raw_bytes, (bytes, bytearray, memoryview)):
            # A transport that hands back a decoded value has already destroyed
            # the evidence this barrier exists to keep. Refuse rather than
            # persist a reconstruction and label it "raw".
            raise TypeError(
                "transport must return exact response bytes, not a decoded "
                f"{type(raw_bytes).__name__}; the durability seam sits below "
                "JSON decoding"
            )

        # The limit applies to the complete wire body, not the parsed content.
        # This is deliberately before bytes(), JSON decoding, hashing, mkdir,
        # and persistence.  Therefore a whitespace or metadata bomb produces a
        # bounded receipt and no encrypted artifact rather than consuming those
        # resources and only then being rejected.
        try:
            check_reply_bytes(raw_bytes)
        except ReplyTooLarge as exc:
            self._record_reply_refusal(
                attempt_id=attempt_id,
                provider=label,
                model=model,
                exc=exc,
            )
            raise
        raw_bytes = bytes(raw_bytes)

        # ---- BARRIER 2: encrypted bytes durable, before parsing --------------
        # OEOS owns encryption and atomic CAS publication. Only the typed
        # reference crosses back into this semantic trace; no plaintext path is
        # serialized and V2 has no compatibility dual-write.
        reference = self.artifact_store.put(
            raw_bytes, artifact_schema=RAW_PROVIDER_RESPONSE_SCHEMA
        )
        to_canonical = getattr(reference, "to_canonical", None)
        if not callable(to_canonical):
            raise TypeError("encrypted artifact store returned no canonical reference")
        canonical_reference = to_canonical()
        if type(canonical_reference) is not dict:
            raise TypeError(
                "encrypted artifact reference must serialize to an exact dict"
            )

        self.trace.record(
            EVENT_RESPONSE_DURABLE,
            attempt_id=attempt_id,
            provider=label,
            model=model,
            encrypted_artifact_ref=canonical_reference,
        )

        # Decoding belongs to the gateway and happens only after this transport
        # has made the admitted raw bytes durable.  Returning bytes keeps the
        # raw-body ceiling ahead of every parser and every parser normalisation.
        return raw_bytes


def record_preflight_refusal(
    trace: ExecutionTrace, *, provider: Any, model: str, exc: BaseException
) -> None:
    """Record a gate refusal that happened ahead of dispatch.

    Kept distinct from `ProviderDispatchStatusUnknown` because the difference is
    the whole point: a preflight refusal spent nothing and is safe to correct and
    re-run, while an unknown status may already have been billed.
    """
    fields: dict[str, Any] = {
        "provider": provider_label(provider),
        "model": model,
        "refusal_type": type(exc).__name__,
        "refusal": str(exc)[:512],
        "dispatched": False,
    }
    receipt = getattr(exc, "receipt", None)
    to_dict = getattr(receipt, "to_dict", None)
    if callable(to_dict):
        # Receipts contain only the stable mechanism, bounded counts/digest, and
        # AuthorityEffect None.  Never serialize an exception's arbitrary state.
        fields["refusal_receipt"] = to_dict()
    trace.record(EVENT_DISPATCH_REFUSED_PREFLIGHT, **fields)


def derive_dispatch_outcomes(
    records: Sequence[TraceRecord],
    *,
    raw_dir: str | os.PathLike[str] | None = None,
    artifact_store: EncryptedArtifactStorePort | None = None,
) -> list[DispatchOutcome]:
    """Crash recovery: what happened to each attempt, read from the trace.

    An attempt with a durable intent and no durable response is
    ``DISPATCH_STATUS_UNKNOWN`` with ``retry_permitted=False``. That is the whole
    reason barrier 1 exists -- without the intent record such an attempt is
    invisible, and an invisible attempt gets silently retried.

    A V2 response completes only when ``artifact_store`` replays and validates
    its exact encrypted reference. ``raw_dir`` is consulted only for a trace
    whose selected V1 response shape carries the legacy name, count, and digest.
    Deriving ``DISPATCH_COMPLETE`` from either trace record alone would report
    completion for evidence that has vanished or been altered. Missing or corrupt
    evidence is ``DISPATCH_EVIDENCE_MISSING`` and remains non-retryable because
    the call may already have been billed.

    Omitting the matching store yields trace-only recovery, which cannot assert
    the artifact and therefore never returns ``DISPATCH_COMPLETE``.

    Records that contradict each other yield ``DISPATCH_EVIDENCE_MALFORMED``
    rather than a resolved answer. The previous implementation kept the last
    record under each attempt id, so a duplicated or mismatched pair was silently
    reconciled into whichever record happened to come last -- a recovery result
    that looks exactly like a clean one.
    """
    intents: dict[str, TraceRecord] = {}
    responses: dict[str, TraceRecord] = {}
    unknowns: set[str] = set()
    # Kept, not merely counted. An attempt can reach recovery with *only* an
    # unknown-status record -- barrier 1 torn away by a partial overwrite, or a
    # hand-assembled record list -- and it still has to be reported. Tracking
    # unknowns in a bare set left nothing to read a provider and model off, and
    # the outcome construction dereferenced `None`: recovery crashed on exactly
    # the evidence it exists to classify.
    unknown_records: dict[str, TraceRecord] = {}
    repeated: set[str] = set()
    nameless = False
    order: list[str] = []
    outcomes: list[DispatchOutcome] = []

    for record in records:
        payload = record.payload
        if record.event == EVENT_DISPATCH_REFUSED_PREFLIGHT:
            outcomes.append(
                DispatchOutcome(
                    attempt_id="",
                    status=DISPATCH_REFUSED_PREFLIGHT,
                    provider=str(payload.get("provider", "")),
                    model=str(payload.get("model", "")),
                    raw_response_sha256=None,
                    # Nothing was spent, so correcting and re-running is fine.
                    retry_permitted=True,
                )
            )
            continue
        if record.event not in (
            EVENT_DISPATCH_INTENT_DURABLE,
            EVENT_RESPONSE_DURABLE,
            EVENT_DISPATCH_STATUS_UNKNOWN,
        ):
            continue

        attempt = payload.get("attempt_id")
        if not isinstance(attempt, str) or not attempt:
            # An attempt record that does not name an attempt cannot be joined to
            # anything. Reported rather than skipped: skipping it would make a
            # dispatch that really happened invisible.
            nameless = True
            attempt = ""
        if attempt not in order:
            order.append(attempt)

        if record.event == EVENT_DISPATCH_INTENT_DURABLE:
            if attempt in intents:
                repeated.add(attempt)
            intents[attempt] = record
        elif record.event == EVENT_RESPONSE_DURABLE:
            if attempt in responses:
                repeated.add(attempt)
            responses[attempt] = record
        else:
            unknowns.add(attempt)
            unknown_records.setdefault(attempt, record)

    for attempt_id in order:
        intent = intents.get(attempt_id)
        response = responses.get(attempt_id)
        # Whichever record actually exists, in order of how much it says. Every
        # attempt id in `order` came from one of these three, so this is never
        # `None` -- but it is written as a chain rather than a pair because the
        # pair silently became `None` for an unknown-only attempt.
        source = (
            intent
            if intent is not None
            else response
            if response is not None
            else unknown_records[attempt_id]
        )
        artifact_ref = (
            response.payload.get("encrypted_artifact_ref")
            if response is not None
            else None
        )
        if type(artifact_ref) is not dict:
            artifact_ref = None
        if artifact_ref is not None:
            plaintext_digest = artifact_ref.get("plaintext_sha256")
            digest = (
                plaintext_digest[7:]
                if type(plaintext_digest) is str
                and plaintext_digest.startswith("sha256:")
                else None
            )
        else:
            digest = (
                str(response.payload.get("raw_response_sha256"))
                if response is not None
                else None
            )

        # Malformed dominates every other reading. An attempt whose records
        # disagree with each other cannot be recovered from at all, and the
        # previous last-write-wins behaviour resolved the disagreement silently:
        # a second `ProviderResponseDurable` under one attempt id simply replaced
        # the first, so a trace carrying two contradictory answers reported one
        # of them as fact.
        if attempt_id == "" and nameless:
            status = DISPATCH_EVIDENCE_MALFORMED
        elif attempt_id in repeated:
            status = DISPATCH_EVIDENCE_MALFORMED
        elif intent is None:
            # A response or an unknown with no intent. Barrier 1 is what makes an
            # attempt visible; a later record without it means the file lost the
            # record that says a dispatch was about to happen.
            status = DISPATCH_EVIDENCE_MALFORMED
        elif response is not None and attempt_id in unknowns:
            # Both "the outcome is unknown" and "here is the outcome". The
            # dispatcher writes one or the other, never both.
            status = DISPATCH_EVIDENCE_MALFORMED
        elif (
            response is not None
            and artifact_ref is not None
            and any(
                name in response.payload
                for name in (
                    "raw_response_sha256",
                    "raw_response_byte_count",
                    "raw_response_path",
                )
            )
        ):
            # A response cannot belong to both eras. Scan-time schema admission
            # already refuses this; recovery also fails closed when handed
            # preconstructed records that bypass the scanner.
            status = DISPATCH_EVIDENCE_MALFORMED
        elif response is not None and (
            response.payload.get("provider") != intent.payload.get("provider")
            or response.payload.get("model") != intent.payload.get("model")
        ):
            # The response is bound to its intent by more than a shared id. An
            # unchecked binding let a response recorded under one provider be
            # joined to an intent recorded under another, which is how a fixture
            # reply could come to stand as the answer to a real call.
            status = DISPATCH_EVIDENCE_MALFORMED
        elif response is None:
            unknown = unknown_records.get(attempt_id)
            if unknown is not None and unknown.payload.get("outcome_code") == (
                DISPATCH_REPLY_REFUSED_TOO_LARGE
            ):
                receipt = unknown.payload.get("refusal_receipt")
                if (
                    unknown.payload.get("failure_type") == "ReplyTooLarge"
                    and unknown.payload.get("retry_permitted") is False
                    and unknown.payload.get("dispatched") is True
                    and isinstance(receipt, Mapping)
                    and receipt.get("refusal_code") == "SWARM_PROVIDER_REPLY_TOO_LARGE"
                ):
                    status = DISPATCH_REPLY_REFUSED_TOO_LARGE
                else:
                    status = DISPATCH_EVIDENCE_MALFORMED
            else:
                status = DISPATCH_STATUS_UNKNOWN
        elif artifact_ref is not None and artifact_store is None:
            status = DISPATCH_EVIDENCE_UNVERIFIED
        elif artifact_ref is not None and _encrypted_artifact_matches(
            artifact_store, artifact_ref
        ):
            status = DISPATCH_COMPLETE
        elif artifact_ref is not None:
            status = DISPATCH_EVIDENCE_MISSING
        elif raw_dir is None:
            # Trace-only recovery cannot see the artifact, so it must not claim
            # the artifact is there.
            status = DISPATCH_EVIDENCE_UNVERIFIED
        elif _artifact_matches(raw_dir, attempt_id, response.payload):
            status = DISPATCH_COMPLETE
        else:
            status = DISPATCH_EVIDENCE_MISSING

        outcomes.append(
            DispatchOutcome(
                attempt_id=attempt_id,
                status=status,
                provider=str(source.payload.get("provider", "")),
                model=str(source.payload.get("model", "")),
                raw_response_sha256=digest,
                retry_permitted=False,
                encrypted_artifact_ref=artifact_ref,
            )
        )
    return outcomes


def _artifact_matches(
    raw_dir: str | os.PathLike[str], attempt_id: str, payload: Mapping[str, Any]
) -> bool:
    """Exact name, existence, exact byte count, and digest. All four.

    **The name is required, not merely joined.** ``raw_response_path`` is read
    out of a file whose entire purpose is to be consulted after something went
    wrong, so it is untrusted input. Joining it onto ``raw_dir`` let a rewritten
    trace supply ``../../somewhere/else.json`` and have recovery hash a file
    outside the artifact store, then report ``DISPATCH_COMPLETE`` about it. The
    writer only ever produces one name, so accepting any other name buys nothing
    and costs the containment of the store.

    **The byte count is required to be usable.** It was previously checked only
    when it happened to be an ``int``, so a record whose count was a string, a
    float, ``null`` or absent skipped the length check entirely -- the one place a
    malformed record most needs to fail. ``bool`` is excluded explicitly, since
    ``isinstance(True, int)`` is true and ``true`` would otherwise be compared
    against a length.
    """
    expected_name = f"{attempt_id}.json"
    if payload.get("raw_response_path") != expected_name:
        return False
    path = Path(raw_dir) / expected_name
    if not path.exists():
        return False
    expected_count = payload.get("raw_response_byte_count")
    if type(expected_count) is not int or expected_count < 0:
        return False
    data = path.read_bytes()
    if len(data) != expected_count:
        return False
    return hashlib.sha256(data).hexdigest() == payload.get("raw_response_sha256")


def verify_raw_response(
    raw_dir: str | os.PathLike[str], outcome: DispatchOutcome
) -> bool:
    """Re-hash the stored bytes against what the trace recorded.

    A digest in a trace is a claim about a file; this is the check that the file
    still says the same thing.
    """
    if outcome.raw_response_sha256 is None:
        return False
    path = Path(raw_dir) / f"{outcome.attempt_id}.json"
    if not path.exists():
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == outcome.raw_response_sha256


def _encrypted_artifact_matches(
    artifact_store: EncryptedArtifactStorePort | None,
    reference: Mapping[str, object],
) -> bool:
    if artifact_store is None:
        return False
    try:
        plaintext = artifact_store.get_canonical(reference)
    except Exception:
        return False
    digest = reference.get("plaintext_sha256")
    length = reference.get("byte_length")
    return (
        type(plaintext) is bytes
        and type(length) is int
        and len(plaintext) == length
        and type(digest) is str
        and "sha256:" + hashlib.sha256(plaintext).hexdigest() == digest
    )


def verify_encrypted_response(
    artifact_store: EncryptedArtifactStorePort, outcome: DispatchOutcome
) -> bool:
    """Replay a V2 response reference through the injected OEOS CAS."""

    reference = outcome.encrypted_artifact_ref
    return reference is not None and _encrypted_artifact_matches(
        artifact_store, reference
    )
