"""P1b: both fsync barriers, through the real gateway.

The three failure modes this file exists to keep apart, because every report that
confuses them is worthless:

| what happened | spent? | safe to retry? |
| --- | --- | --- |
| a gate refused before dispatch | no | yes |
| dispatched, response durable | yes | n/a |
| dispatched, raw response refused as oversize | maybe | **no** |
| dispatched, outcome unknown | maybe | **no** |

The third is the dangerous one, and barrier 1 is the only reason it is
distinguishable from "never dispatched" at all.

Acceptance test 42 (plan v2.5 §2.2) lives here: the scripted model must be
present in *both* `ModelAllowlist` and `PriceTable`, and removing it from either
must refuse before dispatch with a code distinct from a durability failure.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from types import SimpleNamespace

import pytest

from operating_system.adapters.security import (
    FixtureOnlyAeadProtector,
)
from operating_system.infrastructure import EncryptedArtifactCas
from operating_system.domain import EncryptedArtifactRefV1
from governance.domain.ingress.limits import (
    MAX_PROVIDER_PROMPT_BYTES,
    MAX_PROVIDER_REPLY_BYTES,
    REFUSAL_PROVIDER_PROMPT_TOO_LARGE,
    REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    REFUSAL_TEXT_INVALID_UTF8,
    REFUSAL_TEXT_TOO_LARGE,
    IngressRefusal,
    bounded_reply_chunks,
    read_bounded,
)
from adversary.domain.providers.types import (
    CandidateRequest,
    ModelNotAllowed,
    PromptInvalidUtf8,
    PromptTooLarge,
    Provider,
    ProviderError,
    ReplyTooLarge,
)
from pfp.infrastructure.trace import (
    DISPATCH_COMPLETE,
    DISPATCH_EVIDENCE_MALFORMED,
    DISPATCH_EVIDENCE_MISSING,
    DISPATCH_EVIDENCE_UNVERIFIED,
    DISPATCH_REFUSED_PREFLIGHT,
    DISPATCH_REPLY_REFUSED_TOO_LARGE,
    DISPATCH_STATUS_UNKNOWN,
    DURABILITY_BUFFERED_REPLAY,
    DURABILITY_FSYNC_LIVE,
    EVENT_DISPATCH_INTENT_DURABLE,
    EVENT_DISPATCH_STATUS_UNKNOWN,
    EVENT_RESPONSE_DURABLE,
    RUN_MODE_DETERMINISTIC_FIXTURE,
    SCRIPTED_MODEL,
    SCRIPTED_PROVIDER,
    ConfinedGateway,
    DurableDispatchTransport,
    ExecutionTrace,
    RunMode,
    RunModeRefusal,
    ScriptedTransport,
    TraceRecord,
    TraceRefusal,
    assert_mode_admissible,
    derive_dispatch_outcomes,
    fixture_gateway,
    live_gateway,
    read_records,
    scripted_allowlist,
    scripted_openai_payload,
    scripted_price_table,
    verify_encrypted_response,
)
from pfp.infrastructure.trace import provider_dispatch as _dispatch
from pfp.infrastructure.trace.traced_gateway import (
    GATE_EXCEPTIONS,
    TracedGateway,
)

REQUEST = CandidateRequest(system="you are a symbol game worker", user="solve this")
FIXTURE_KEY = b"symbol-game-provider-dispatch-test-key-v1"


def _artifact_store(root, name="encrypted-artifacts"):
    return EncryptedArtifactCas(
        root / name,
        FixtureOnlyAeadProtector(FIXTURE_KEY),
    )


def _artifact_bytes(store, outcome):
    assert outcome.encrypted_artifact_ref is not None
    return store.get_canonical(outcome.encrypted_artifact_ref)


def _artifact_path(store, outcome):
    assert outcome.encrypted_artifact_ref is not None
    reference = EncryptedArtifactRefV1.from_canonical(outcome.encrypted_artifact_ref)
    return store.object_path(reference)


def _reply_at_size(size: int) -> bytes:
    raw = json.dumps(scripted_openai_payload("ok"), separators=(",", ":")).encode(
        "utf-8"
    )
    assert len(raw) < size
    return raw + b" " * (size - len(raw))


def _trace(tmp_path, name="dispatch", durability=DURABILITY_FSYNC_LIVE, live=False):
    """A deterministic-fixture trace, with `fsync_live` durability retained.

    `live=False` is the default, and the earlier `live=True` was the bug: every
    scripted call in this file was recorded as a live provider call, so the trace
    testified to a paid dispatch that a script had answered. Durability is an
    orthogonal axis and stays at `fsync_live` -- a fixture execution may exercise
    the barriers without claiming anything about a provider.
    """
    return ExecutionTrace(
        tmp_path / f"{name}.jsonl",
        execution_id=name,
        durability=durability,
        live_transport=live,
        run_mode=RunMode.LIVE if live else RunMode.DETERMINISTIC_FIXTURE,
    )


def _durable(trace, inner, **kwargs):
    """A barriered transport for fixture execution.

    `live=False` is not a convenience. Every trace in this file is a deterministic
    fixture, and the dispatcher writes its own `live` flag into the intent record;
    a scripted call recorded as live is the false testimony these tests exist to
    prevent. The two tests that are genuinely about live dispatch pass `live=True`
    explicitly and are refused for it, which is the point.
    """
    kwargs.setdefault("live", False)
    kwargs.setdefault("artifact_store", _artifact_store(trace.path.parent))
    return DurableDispatchTransport(trace, inner, **kwargs)


def _run(tmp_path, payloads=None, name="dispatch", **kw):
    """One deterministic fixture execution, built by the only factory that can.

    There is no provider, model or mode argument to pass and no transport to
    inject: `fixture_gateway` owns all four. Every test in this file goes through
    it, so closed construction is the arrangement under measurement rather than a
    property asserted once and bypassed everywhere else.
    """
    return fixture_gateway(
        tmp_path / f"{name}.jsonl",
        payloads
        if payloads is not None
        else [scripted_openai_payload("scripted reply")],
        artifact_store=_artifact_store(tmp_path),
        execution_id=name,
        **kw,
    )


def _wire(tmp_path, payloads=None, name="dispatch", **gw):
    """`(trace, run, gateway)`, the shape most of this file is written against."""
    run = _run(tmp_path, payloads=payloads, name=name, **gw)
    return run.trace, run, run.gateway


class _ForeignProvider(str, Enum):
    """Independent caller enum carrying the same wire values, not an alias."""

    FIXTURE = "fixture"
    OPENROUTER = "openrouter"


def _foreign_provider(name):
    """A foreign enum instance with no canonical Provider class identity."""
    return getattr(_ForeignProvider, name)


def _with_payload(record, **overrides):
    """One trace record with a doctored payload, chain untouched.

    Models an editor who can re-sign, which the chain explicitly does not defend
    against -- `execution_trace` calls itself tamper-*evident* against partial
    edits, not tamper-proof. That is exactly the threat model in which recovery's
    own validation of a payload field has to hold on its own.
    """
    return TraceRecord(
        index=record.index,
        event=record.event,
        payload={**record.payload, **overrides},
        sha256=record.sha256,
        prev_sha256=record.prev_sha256,
    )


# --------------------------------------------------------------------------
# The happy path, through the real adapter
# --------------------------------------------------------------------------


def test_a_scripted_call_traverses_the_real_gateway(tmp_path):
    """Allowlist, pricing, budget and the real openai-compat parser all run."""
    trace, script, gateway = _wire(tmp_path)
    response, receipt = gateway.complete(
        REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL
    )
    trace.seal("DISPATCH_DONE")

    assert response.content == "scripted reply"
    assert response.model == SCRIPTED_MODEL
    assert response.authority_effect == "None"
    assert receipt.model == SCRIPTED_MODEL
    assert receipt.cost_microusd == 0, "the scripted row is priced at zero"
    assert script.calls == ((SCRIPTED_PROVIDER.value, SCRIPTED_MODEL),)


def test_both_barriers_are_recorded_in_order(tmp_path):
    """Intent strictly before the response record. The order is the guarantee."""
    trace, _, gateway = _wire(tmp_path)
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DISPATCH_DONE")

    events = [r.event for r in read_records(trace.path)]
    assert events.index(EVENT_DISPATCH_INTENT_DURABLE) < events.index(
        EVENT_RESPONSE_DURABLE
    )


def test_the_raw_bytes_are_encrypted_and_match_the_recorded_digest(tmp_path):
    """Encrypted raw-byte durability, not a plaintext path or transient digest."""
    trace, run, gateway = _wire(tmp_path)
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DISPATCH_DONE")

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=_artifact_store(trace.path.parent)
    )
    assert len(outcomes) == 1
    assert outcomes[0].status == DISPATCH_COMPLETE
    assert verify_encrypted_response(run.artifact_store, outcomes[0])

    stored = json.loads(_artifact_bytes(run.artifact_store, outcomes[0]))
    assert stored["choices"][0]["message"]["content"] == "scripted reply"
    assert (
        b"scripted reply"
        not in _artifact_path(run.artifact_store, outcomes[0]).read_bytes()
    )


def test_a_tampered_encrypted_envelope_fails_verification(tmp_path):
    """Negative control: the digest must actually be checked against the bytes."""
    trace, run, gateway = _wire(tmp_path)
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DISPATCH_DONE")

    outcome = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=_artifact_store(trace.path.parent)
    )[0]
    path = _artifact_path(run.artifact_store, outcome)
    path.write_bytes(b'{"choices":[{"message":{"content":"forged"}}]}')
    assert not verify_encrypted_response(run.artifact_store, outcome)


def test_the_attempt_id_is_deterministic_for_the_same_request(tmp_path):
    """A replay must derive the same attempt identity, or recovery cannot join."""
    a, _, ga = _wire(tmp_path, name="a")
    ga.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    a.seal("DONE")
    b, _, gb = _wire(tmp_path, name="a2")
    gb.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    b.seal("DONE")

    # Attempt ids bind the declared `execution_id`, so two executions that
    # declared different ids never collide even with the same file name in
    # different directories sharing one encrypted artifact store.
    id_a = derive_dispatch_outcomes(
        read_records(a.path), artifact_store=_artifact_store(a.path.parent)
    )[0].attempt_id
    id_b = derive_dispatch_outcomes(
        read_records(b.path), artifact_store=_artifact_store(b.path.parent)
    )[0].attempt_id
    assert id_a != id_b
    assert len(id_a) == 64 and len(id_b) == 64


def _dispatch_into(shared_store, directory, execution_id, filename="dispatch.jsonl"):
    directory.mkdir(exist_ok=True)
    run = fixture_gateway(
        directory / filename,
        [scripted_openai_payload("reply")],
        artifact_store=_artifact_store(shared_store, name="cas"),
        execution_id=execution_id,
    )
    run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.seal("DONE")
    return derive_dispatch_outcomes(read_records(run.trace.path))[0].attempt_id


def test_same_file_name_different_executions_do_not_collide(tmp_path):
    """The collision the old filename-bound attempt id allowed.

    Two executions writing `dispatch.jsonl` into separate directories while
    sharing one artifact store used to derive the same attempt id, and the artifact was
    opened `"wb"` -- so the second silently overwrote the first's evidence. Bound
    to the `RunStarted` digest, identical file names no longer matter.
    """
    shared_store = tmp_path / "shared_store"
    first = _dispatch_into(shared_store, tmp_path / "one", "execution-one")
    second = _dispatch_into(shared_store, tmp_path / "two", "execution-two")

    assert first != second, "distinct executions must derive distinct attempts"
    assert len(list(shared_store.rglob("*.oeos-envelope"))) == 2


def test_a_reused_execution_id_never_overwrites_encrypted_evidence(tmp_path):
    """Attempt identity repeats, while randomized CAS envelopes remain distinct."""
    shared_store = tmp_path / "shared_store"
    first = _dispatch_into(shared_store, tmp_path / "one", "same-id")
    second = _dispatch_into(shared_store, tmp_path / "two", "same-id")

    assert first == second, "attempt identity remains deterministic"
    assert len(list(shared_store.rglob("*.oeos-envelope"))) == 2


def test_artifact_store_is_required_at_the_durability_seam(tmp_path):
    """A plaintext fallback cannot be selected when encrypted custody is absent."""
    trace = _trace(tmp_path, name="collide")
    with pytest.raises(TypeError, match="artifact_store"):
        DurableDispatchTransport(  # type: ignore[call-arg]
            trace, ScriptedTransport([scripted_openai_payload("reply")]), live=False
        )
    trace.abandon()


# --------------------------------------------------------------------------
# Byte fidelity -- the seam sits below decoding
# --------------------------------------------------------------------------


#: Two byte-distinct bodies that decode to the same mapping. The first has
#: whitespace and a different key order; the second is minified.
SPACED = (
    b'{\n  "id": "chatcmpl_scripted",\n  "object": "chat.completion",\n'
    b'  "model": "scripted/p1b-fixture",\n'
    b'  "choices": [ { "index": 0, "message": { "role": "assistant",'
    b' "content": "same" }, "finish_reason": "stop" } ],\n'
    b'  "usage": { "prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33 }\n}'
)
MINIFIED = (
    b'{"choices":[{"finish_reason":"stop","index":0,"message":'
    b'{"content":"same","role":"assistant"}}],"id":"chatcmpl_scripted",'
    b'"model":"scripted/p1b-fixture","object":"chat.completion",'
    b'"usage":{"completion_tokens":22,"prompt_tokens":11,"total_tokens":33}}'
)
#: A duplicate property. `json.loads` keeps the last value and the first is
#: destroyed on decode -- so only exact bytes can prove the provider sent both.
DUPLICATE_PROPERTY = (
    b'{"id":"chatcmpl_scripted","object":"chat.completion",'
    b'"model":"scripted/p1b-fixture","choices":[{"index":0,"message":'
    b'{"role":"assistant","content":"first"},"message":'
    b'{"role":"assistant","content":"second"},"finish_reason":"stop"}],'
    b'"usage":{"prompt_tokens":11,"completion_tokens":22,"total_tokens":33}}'
)


def test_byte_distinct_responses_that_decode_alike_stay_byte_distinct(tmp_path):
    """The P0 correction, asserted where it can regress.

    `SPACED` and `MINIFIED` decode to equal mappings. A barrier placed above
    decoding -- persisting `_canonical(decoded)` -- stores identical bytes for
    both and destroys the difference. The stored artifacts must differ.
    """
    stored = []
    for index, body in enumerate((SPACED, MINIFIED)):
        run = _run(tmp_path, payloads=[body], name=f"fidelity{index}")
        response, _ = run.gateway.complete(
            REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL
        )
        run.trace.seal("DONE")
        assert response.content == "same", "both decode to the same reply"
        outcome = derive_dispatch_outcomes(
            read_records(run.trace.path), artifact_store=run.artifact_store
        )[0]
        stored.append(_artifact_bytes(run.artifact_store, outcome))

    assert json.loads(stored[0]) == json.loads(stored[1]), "same decoded value"
    assert stored[0] != stored[1], "byte fidelity must survive the barrier"
    assert stored[0] == SPACED and stored[1] == MINIFIED, "exact provider bytes"


def test_a_duplicate_json_property_survives_on_disk(tmp_path):
    """Decoding destroys the first value; the artifact must keep both.

    This is unrecoverable from any reconstruction, so it is the sharpest
    available proof that the stored bytes are the provider's own.
    """
    run = _run(tmp_path, payloads=[DUPLICATE_PROPERTY], name="duplicate")
    with pytest.raises(ProviderError, match="duplicate object keys"):
        run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.abandon()

    outcome = derive_dispatch_outcomes(
        read_records(run.trace.path), artifact_store=run.artifact_store
    )[0]
    on_disk = _artifact_bytes(run.artifact_store, outcome)

    assert on_disk == DUPLICATE_PROPERTY
    assert on_disk.count(b'"message"') == 2, "both properties present in the artifact"
    assert b'"content":"first"' in on_disk
    # Strict decoding refuses the ambiguity, but custody precedes parsing.


@pytest.mark.parametrize("delta", [-1, 0])
def test_raw_reply_at_or_below_the_ceiling_is_persisted_exactly(tmp_path, delta):
    size = MAX_PROVIDER_REPLY_BYTES + delta
    raw = _reply_at_size(size)
    run = _run(tmp_path, payloads=[raw], name=f"reply_boundary_{delta}")

    response, _ = run.gateway.complete(
        REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL
    )
    run.trace.seal("DONE")

    assert response.content == "ok"
    outcome = derive_dispatch_outcomes(
        read_records(run.trace.path), artifact_store=run.artifact_store
    )[0]
    assert outcome.status == DISPATCH_COMPLETE
    assert _artifact_bytes(run.artifact_store, outcome) == raw
    assert outcome.encrypted_artifact_ref["byte_length"] == size


def test_raw_reply_one_byte_over_is_typed_nonretryable_and_never_persisted(tmp_path):
    raw = _reply_at_size(MAX_PROVIDER_REPLY_BYTES + 1)
    run = _run(tmp_path, payloads=[raw], name="reply_too_large")

    with pytest.raises(ReplyTooLarge) as caught:
        run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.abandon()

    receipt = caught.value.receipt
    assert receipt.refusal_code == REFUSAL_PROVIDER_REPLY_TOO_LARGE
    assert receipt.observed_bytes == MAX_PROVIDER_REPLY_BYTES + 1
    assert receipt.observed_prefix_sha256 == hashlib.sha256(raw).hexdigest()
    assert not list(run.artifact_store.root.rglob("*.oeos-envelope"))

    records = read_records(run.trace.path)
    events = [record.event for record in records]
    assert EVENT_DISPATCH_INTENT_DURABLE in events, "the dispatch did happen"
    assert EVENT_RESPONSE_DURABLE not in events, "no oversize artifact is durable"
    outcome = derive_dispatch_outcomes(records, artifact_store=run.artifact_store)[0]
    assert outcome.status == DISPATCH_REPLY_REFUSED_TOO_LARGE
    assert outcome.retry_permitted is False, "a dispatched call may have been billed"


@pytest.mark.parametrize("reader", ["read_bounded", "bounded_reply_chunks"])
def test_official_reply_readers_produce_the_known_nonretryable_terminal(
    tmp_path, reader
):
    chunks = [b"x" * 5, b"y" * 4]

    def bounded_socket(provider, model, request):
        if reader == "read_bounded":
            return read_bounded(
                chunks,
                limit=8,
                refusal_code=REFUSAL_PROVIDER_REPLY_TOO_LARGE,
            )
        return b"".join(
            bounded_reply_chunks(
                chunks,
                limit=8,
                refusal_code=REFUSAL_PROVIDER_REPLY_TOO_LARGE,
            )
        )

    trace = _trace(tmp_path, name=f"official_reader_{reader}")
    durable = _durable(trace, bounded_socket)

    with pytest.raises(ReplyTooLarge) as caught:
        durable(SCRIPTED_PROVIDER, SCRIPTED_MODEL, REQUEST)
    trace.abandon()

    receipt = caught.value.receipt
    assert receipt.refusal_code == REFUSAL_PROVIDER_REPLY_TOO_LARGE
    assert receipt.limit_bytes == 8
    assert receipt.observed_bytes == 9
    assert receipt.observed_prefix_sha256 == hashlib.sha256(b"xxxxxyyyy").hexdigest()
    records = read_records(trace.path)
    assert EVENT_RESPONSE_DURABLE not in [record.event for record in records]
    outcome = derive_dispatch_outcomes(records, artifact_store=durable.artifact_store)[
        0
    ]
    assert outcome.status == DISPATCH_REPLY_REFUSED_TOO_LARGE
    assert outcome.retry_permitted is False


def test_non_provider_ingress_refusal_remains_status_unknown(tmp_path):
    def text_refusal(provider, model, request):
        return read_bounded(
            [b"x" * 9],
            limit=8,
            refusal_code=REFUSAL_TEXT_TOO_LARGE,
        )

    trace = _trace(tmp_path, name="non_provider_ingress_refusal")
    durable = _durable(trace, text_refusal)

    with pytest.raises(IngressRefusal) as caught:
        durable(SCRIPTED_PROVIDER, SCRIPTED_MODEL, REQUEST)
    trace.abandon()

    assert type(caught.value) is IngressRefusal
    assert caught.value.receipt.refusal_code == REFUSAL_TEXT_TOO_LARGE
    records = read_records(trace.path)
    unknown = next(
        record for record in records if record.event == EVENT_DISPATCH_STATUS_UNKNOWN
    )
    assert "outcome_code" not in unknown.payload
    outcome = derive_dispatch_outcomes(records, artifact_store=durable.artifact_store)[
        0
    ]
    assert outcome.status == DISPATCH_STATUS_UNKNOWN
    assert outcome.retry_permitted is False


def test_oversize_reply_is_never_hashed_in_full_before_refusal(tmp_path, monkeypatch):
    raw = _reply_at_size(MAX_PROVIDER_REPLY_BYTES * 2)
    observed: list[int] = []
    real_sha256 = hashlib.sha256

    def bounded_sha256(data=b""):
        size = memoryview(data).nbytes
        observed.append(size)
        if size > MAX_PROVIDER_REPLY_BYTES:
            raise AssertionError("the complete oversize reply was hashed")
        return real_sha256(data)

    monkeypatch.setattr(_dispatch, "hashlib", SimpleNamespace(sha256=bounded_sha256))
    run = _run(tmp_path, payloads=[raw], name="reply_hash_bound")

    with pytest.raises(ReplyTooLarge):
        run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.abandon()

    assert observed, "the attempt/request identities are the positive control"
    assert max(observed) < MAX_PROVIDER_REPLY_BYTES
    assert not list(run.artifact_store.root.rglob("*.oeos-envelope"))


def test_a_transport_returning_a_decoded_mapping_is_refused(tmp_path):
    """The seam must not silently accept a pre-decoded value.

    A transport handing back a `dict` has already destroyed the evidence, and
    persisting a re-encoding of it under the name "raw" would be a false claim
    rather than a missing one.
    """
    trace = _trace(tmp_path, name="predecoded")
    durable = _durable(trace, lambda provider, model, request: {"already": "decoded"})
    with pytest.raises(TypeError, match="must return exact response bytes"):
        durable(SCRIPTED_PROVIDER, SCRIPTED_MODEL, REQUEST)
    trace.abandon()


# --------------------------------------------------------------------------
# Run-mode confinement
# --------------------------------------------------------------------------


def test_scripted_model_in_fixture_mode_is_admitted(tmp_path):
    """Positive control for the three refusals below."""
    trace, script, gateway = _wire(tmp_path, name="mode_ok")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")
    assert script.calls, "the admitted combination must actually dispatch"


def test_scripted_model_in_live_mode_is_refused():
    """A scripted reply recorded as live is a false durability claim.

    A predicate test now rather than a construction test: there is no longer any
    way to *build* this combination, because `fixture_gateway` takes no mode and
    `live_gateway` takes no scripted transport. The predicate is still the thing
    both factories consult, so it is still worth its own assertion.
    """
    with pytest.raises(RunModeRefusal, match="may not run in LIVE mode"):
        assert_mode_admissible(
            provider=Provider.OPENROUTER,
            model=SCRIPTED_MODEL,
            mode=RunMode.LIVE,
            scripted_transport=False,
        )


def test_a_scripted_transport_behind_a_real_provider_is_refused():
    """A fake socket must never wear a real vendor's identity.

    ``scripted_transport`` is a fact the constructor supplies, not a property
    inferred from the object -- see
    `test_a_hidden_scripted_transport_defeats_inspection` for why the previous
    inference could not work.
    """
    with pytest.raises(RunModeRefusal, match="may not sit behind real provider"):
        assert_mode_admissible(
            provider=Provider.OPENROUTER,
            model="deepseek/deepseek-v4-flash",
            mode=RunMode.DETERMINISTIC_FIXTURE,
            scripted_transport=True,
        )


def test_the_scripted_provider_is_not_a_real_vendor():
    """Identity separated from parser.

    `FIXTURE` names no vendor, and the gateway still routes it through
    `parse_openai_compat_response`, so the real parser runs without borrowing a
    real provider's name for a reply no provider sent.
    """
    from adversary.domain.providers.types import (
        Provider,
    )
    from pfp.infrastructure.trace import LIVE_PROVIDERS

    assert SCRIPTED_PROVIDER is Provider.FIXTURE
    assert SCRIPTED_PROVIDER not in LIVE_PROVIDERS
    assert Provider.OPENROUTER in LIVE_PROVIDERS


# --------------------------------------------------------------------------
# Recovery checks the artifact, not merely the record naming it
# --------------------------------------------------------------------------


def test_a_missing_artifact_is_evidence_missing_not_complete(tmp_path):
    trace, run, gateway = _wire(tmp_path, name="gone")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")
    outcome = derive_dispatch_outcomes(read_records(trace.path))[0]
    _artifact_path(run.artifact_store, outcome).unlink()

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=run.artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MISSING]
    assert outcomes[0].retry_permitted is False, "it was dispatched regardless"


def test_an_altered_artifact_is_evidence_missing(tmp_path):
    """Byte count and digest are both checked, so a same-length edit still fails."""
    trace, run, gateway = _wire(tmp_path, name="altered")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")
    outcome = derive_dispatch_outcomes(read_records(trace.path))[0]
    artifact = _artifact_path(run.artifact_store, outcome)
    original = artifact.read_bytes()
    artifact.write_bytes(b"x" * len(original))

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=run.artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MISSING]


def test_trace_only_recovery_does_not_claim_completion(tmp_path):
    """Without the era-specific store, evidence cannot be checked or asserted."""
    trace, _, gateway = _wire(tmp_path, name="traceonly")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")

    outcomes = derive_dispatch_outcomes(read_records(trace.path))
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_UNVERIFIED]
    assert DISPATCH_COMPLETE not in [o.status for o in outcomes]


# --------------------------------------------------------------------------
# Preflight refusal is recorded by machinery, not by discipline
# --------------------------------------------------------------------------


def test_the_traced_gateway_records_a_preflight_refusal_without_being_asked(tmp_path):
    """`record_preflight_refusal` had no production caller.

    That is the same defect this branch started from: a correct function nothing
    invokes. `TracedGateway` is the one seam, and it records the refusal itself.
    """
    trace, _, gateway = _wire(
        tmp_path, name="auto_preflight", register_in_allowlist=False
    )

    with pytest.raises(GATE_EXCEPTIONS):
        gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.abandon()

    outcomes = derive_dispatch_outcomes(read_records(trace.path))
    assert [o.status for o in outcomes] == [DISPATCH_REFUSED_PREFLIGHT]
    assert outcomes[0].retry_permitted is True, "nothing was spent"
    assert EVENT_DISPATCH_INTENT_DURABLE not in [
        r.event for r in read_records(trace.path)
    ]


def test_prompt_too_large_records_its_bounded_receipt_before_any_dispatch(tmp_path):
    run = _run(tmp_path, name="prompt_too_large")
    request = CandidateRequest(system="", user="u" * (MAX_PROVIDER_PROMPT_BYTES + 1))

    with pytest.raises(PromptTooLarge) as caught:
        run.gateway.complete(request, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.abandon()

    assert run.calls == (), "an oversize prompt must never reach the transport"
    records = read_records(run.trace.path)
    assert EVENT_DISPATCH_INTENT_DURABLE not in [record.event for record in records]
    refusal = next(
        record
        for record in records
        if record.event == "ProviderDispatchRefusedPreflight"
    )
    assert refusal.payload["refusal_type"] == "PromptTooLarge"
    assert refusal.payload["dispatched"] is False
    assert refusal.payload["refusal_receipt"] == caught.value.receipt.to_dict()
    assert (
        refusal.payload["refusal_receipt"]["refusal_code"]
        == REFUSAL_PROVIDER_PROMPT_TOO_LARGE
    )


def test_invalid_utf8_prompt_records_a_typed_preflight_receipt(tmp_path):
    run = _run(tmp_path, name="prompt_invalid_utf8")

    with pytest.raises(PromptInvalidUtf8) as caught:
        run.gateway.complete(
            CandidateRequest(system="safe", user="\ud800"),
            provider=SCRIPTED_PROVIDER,
            model=SCRIPTED_MODEL,
        )
    run.trace.abandon()

    assert run.calls == ()
    records = read_records(run.trace.path)
    assert EVENT_DISPATCH_INTENT_DURABLE not in [record.event for record in records]
    refusal = next(
        record
        for record in records
        if record.event == "ProviderDispatchRefusedPreflight"
    )
    assert refusal.payload["refusal_type"] == "PromptInvalidUtf8"
    assert refusal.payload["refusal_receipt"] == caught.value.receipt.to_dict()
    assert (
        refusal.payload["refusal_receipt"]["refusal_code"] == REFUSAL_TEXT_INVALID_UTF8
    )


def test_the_traced_gateway_does_not_swallow_a_post_intent_failure(tmp_path):
    """Preflight and unknown must not collapse into one recorded outcome."""
    # The failure is *declared* in the script rather than injected as a callable:
    # accepting arbitrary callables is the hole this round closed.
    trace, _, gateway = _wire(
        tmp_path, payloads=[ConnectionError("socket died")], name="auto_unknown"
    )
    with pytest.raises(ConnectionError):
        gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.abandon()

    outcomes = derive_dispatch_outcomes(read_records(trace.path))
    assert [o.status for o in outcomes] == [DISPATCH_STATUS_UNKNOWN]
    assert outcomes[0].retry_permitted is False


def test_the_gate_exception_tuple_uses_one_canonical_identity_and_includes_size():
    from adversary.domain.providers import types as canonical

    assert set(GATE_EXCEPTIONS) == {
        canonical.ModelNotAllowed,
        canonical.BudgetExceeded,
        canonical.ProviderConfigError,
        canonical.PromptInvalidUtf8,
        canonical.PromptTooLarge,
    }
    names = {candidate.__name__ for candidate in GATE_EXCEPTIONS}
    assert names == {
        "ModelNotAllowed",
        "BudgetExceeded",
        "ProviderConfigError",
        "PromptInvalidUtf8",
        "PromptTooLarge",
    }


# --------------------------------------------------------------------------
# Acceptance test 42 -- both gates, ahead of dispatch
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("gate", "kwargs"),
    [
        ("allowlist", {"register_in_allowlist": False}),
        ("price_table", {"register_in_price_table": False}),
    ],
)
def test_42_removing_the_model_from_either_gate_refuses_before_dispatch(
    tmp_path, gate, kwargs
):
    """The scripted model must be declared in BOTH gates.

    An unlisted or unpriced model raises before any transport is invoked. Without
    this test, a scripted transport under an unregistered name would never run,
    and P1b would report a durability failure it never measured.

    The refusal is recorded by the seam, not by this test. An earlier revision
    called `record_preflight_refusal` by hand right here, which demonstrated that
    the recorder worked while leaving production free never to call it -- so the
    test passed and the trace stayed empty in the only run that mattered.
    """
    trace, script, gateway = _wire(tmp_path, name=f"gate_{gate}", **kwargs)

    with pytest.raises(ModelNotAllowed):
        gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.abandon()

    assert script.calls == (), "the transport must never have been reached"
    events = [r.event for r in read_records(trace.path)]
    assert EVENT_DISPATCH_INTENT_DURABLE not in events, "no intent: nothing was spent"

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=_artifact_store(trace.path.parent)
    )
    assert [o.status for o in outcomes] == [DISPATCH_REFUSED_PREFLIGHT]
    assert outcomes[0].retry_permitted is True


def test_42_a_gate_refusal_is_a_distinct_type_from_a_durability_failure(tmp_path):
    """The codes must not collide, or a report cannot say which happened."""
    _, _, blocked = _wire(tmp_path, name="typed", register_in_allowlist=False)
    with pytest.raises(ModelNotAllowed):
        blocked.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)

    with pytest.raises(TraceRefusal):
        _durable(
            ExecutionTrace(
                tmp_path / "buffered.jsonl",
                execution_id="buffered",
                durability=DURABILITY_BUFFERED_REPLAY,
            ),
            ScriptedTransport([scripted_openai_payload("x")]),
            live=True,
        )

    assert not issubclass(ModelNotAllowed, TraceRefusal)
    assert not issubclass(TraceRefusal, ModelNotAllowed)


def test_the_registered_path_is_the_positive_control(tmp_path):
    """Both gates registered -> the transport is reached. Without this, the two
    refusal tests above would pass against a gateway that refuses everything."""
    _, script, gateway = _wire(tmp_path, name="control")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    assert script.calls, "the scripted transport must actually run"


# --------------------------------------------------------------------------
# Unknown status -- and never a retry
# --------------------------------------------------------------------------


def _exploding_transport(exc):
    def _transport(provider, model, request):
        raise exc

    return _transport


def test_a_transport_failure_after_intent_is_status_unknown(tmp_path):
    """Barrier 1 passed, barrier 2 not reached: the outcome is unknown, not failed.

    The call may have completed and been billed. Recording it as a plain failure
    would licence a retry that spends again.
    """
    trace, _, gateway = _wire(
        tmp_path, payloads=[ConnectionError("socket died")], name="unknown"
    )

    with pytest.raises(ConnectionError):
        gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.abandon()

    events = [r.event for r in read_records(trace.path)]
    assert EVENT_DISPATCH_INTENT_DURABLE in events
    assert EVENT_DISPATCH_STATUS_UNKNOWN in events
    assert EVENT_RESPONSE_DURABLE not in events

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=_artifact_store(trace.path.parent)
    )
    assert [o.status for o in outcomes] == [DISPATCH_STATUS_UNKNOWN]
    assert outcomes[0].retry_permitted is False
    assert outcomes[0].raw_response_sha256 is None


def test_there_is_no_auto_retry_on_unknown_status(tmp_path):
    """Counted, not asserted by inspection.

    A retry loop added later would make this fail rather than silently double the
    bill on every unknown outcome.
    """
    run = _run(tmp_path, payloads=[TimeoutError("no response")], name="noretry")

    with pytest.raises(TimeoutError):
        run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.abandon()

    # Counted at the socket, which is the only place a retry would show up.
    assert len(run.calls) == 1, "an unknown outcome must never be retried automatically"


def test_a_crash_between_barriers_recovers_as_unknown(tmp_path):
    """The recovery case barrier 1 exists for.

    Truncating the trace after the intent record is exactly what a process death
    between fsync and socket-return leaves behind. Recovery must read it as
    unknown -- not as "never dispatched", which would be safe to retry.
    """
    trace, _, gateway = _wire(tmp_path, name="crash")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")

    lines = trace.path.read_bytes().split(b"\n")
    keep = [ln for ln in lines if ln]
    cut = next(
        i
        for i, ln in enumerate(keep)
        if json.loads(ln)["event"] == EVENT_DISPATCH_INTENT_DURABLE
    )
    trace.path.write_bytes(b"\n".join(keep[: cut + 1]) + b"\n")

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=_artifact_store(trace.path.parent)
    )
    assert [o.status for o in outcomes] == [DISPATCH_STATUS_UNKNOWN]
    assert outcomes[0].retry_permitted is False


def test_bytes_are_durable_before_the_record_that_names_them(tmp_path):
    """Ordering inside barrier 2.

    If the trace record were written first, a crash between the two would leave
    the trace asserting durable bytes that do not exist. Asserted by observing
    that the file is already present and correct at the moment the record is
    written.
    """
    run = _run(tmp_path, payloads=[scripted_openai_payload("ordered")], name="ordering")
    trace = run.trace
    observed: dict[str, bool] = {}
    real_record = trace.record

    def _spy(event, **fields):
        if event == EVENT_RESPONSE_DURABLE:
            reference = fields["encrypted_artifact_ref"]
            observed["file_exists"] = run.artifact_store.get_canonical(reference) != b""
            observed["digest_matches"] = (
                "sha256:"
                + hashlib.sha256(
                    run.artifact_store.get_canonical(reference)
                ).hexdigest()
                == reference["plaintext_sha256"]
            )
        return real_record(event, **fields)

    trace.record = _spy  # type: ignore[method-assign]
    run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.record = real_record  # type: ignore[method-assign]
    trace.seal("DONE")

    assert observed["file_exists"], "encrypted envelope must exist before the record"
    assert observed["digest_matches"]


def test_encrypted_cas_failure_propagates_without_response_claim(tmp_path):
    """A failed encrypted commit leaves durable intent and no response claim."""

    class FailingStore:
        def put(self, payload, *, artifact_schema):
            raise OSError("encrypted CAS unavailable")

        def get_canonical(self, value):
            raise OSError("encrypted CAS unavailable")

    trace = _trace(tmp_path, name="cas_failure")
    durable = DurableDispatchTransport(
        trace,
        ScriptedTransport([scripted_openai_payload("x")]),
        artifact_store=FailingStore(),
        live=False,
    )
    with pytest.raises(OSError, match="encrypted CAS unavailable"):
        durable(SCRIPTED_PROVIDER, SCRIPTED_MODEL, REQUEST)
    trace.abandon()
    events = [record.event for record in read_records(trace.path)]
    assert EVENT_DISPATCH_INTENT_DURABLE in events
    assert EVENT_RESPONSE_DURABLE not in events
    outcome = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=durable.artifact_store
    )[0]
    assert outcome.status == DISPATCH_STATUS_UNKNOWN
    assert outcome.retry_permitted is False


# --------------------------------------------------------------------------
# Durability mode
# --------------------------------------------------------------------------


def test_live_dispatch_against_a_buffered_trace_is_refused(tmp_path):
    """Refused at construction, before anything can be spent."""
    buffered = ExecutionTrace(
        tmp_path / "buf.jsonl",
        execution_id="buf",
        durability=DURABILITY_BUFFERED_REPLAY,
    )
    with pytest.raises(TraceRefusal, match="live dispatch requires an fsync_live"):
        _durable(buffered, ScriptedTransport([scripted_openai_payload("x")]), live=True)


def test_a_replay_dispatch_may_use_a_buffered_trace(tmp_path):
    """Positive control: the refusal is about live calls, not about buffering."""
    run = _run(
        tmp_path,
        payloads=[scripted_openai_payload("replayed")],
        name="replay",
        durability=DURABILITY_BUFFERED_REPLAY,
    )
    response, _ = run.gateway.complete(
        REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL
    )
    run.trace.seal("DONE")
    assert response.content == "replayed"


# --------------------------------------------------------------------------
# Confinement at dispatch, not merely at construction
# --------------------------------------------------------------------------


ESCAPE_PROVIDER = Provider.OPENROUTER
ESCAPE_MODEL = "deepseek/deepseek-v4-flash"


def test_the_escaped_pair_is_one_the_gates_would_have_admitted():
    """Negative control for every confinement test below.

    If the builtin allowlist or price table refused this pair anyway, the
    confinement refusals would be untested -- they would merely be arriving first
    and the old code would have been safe by accident.
    """
    scripted_allowlist().check(ESCAPE_PROVIDER, ESCAPE_MODEL)
    assert scripted_price_table().cost_microusd(ESCAPE_MODEL, 100, 100) > 0
    # ...and the same for the other escape: a second fixture-provider model.
    scripted_allowlist().check(SCRIPTED_PROVIDER, "fixture-model")
    assert scripted_price_table().cost_microusd("fixture-model", 100, 100) > 0


def test_a_dispatch_override_cannot_escape_fixture_confinement(tmp_path):
    """The P0 escape, asserted where it happened.

    Construction admitted the gateway as FIXTURE and then returned a plain
    `OearsLlmGateway` that had forgotten the mode. `complete()` takes `provider=`
    and `model=` overrides, and the test above shows both gates admit this pair,
    so a real vendor identity dispatched through the scripted socket -- with the
    trace recording OPENROUTER as though a provider had answered.
    """
    trace, script, gateway = _wire(tmp_path, name="override")

    with pytest.raises(RunModeRefusal, match="confined to the sealed pair"):
        gateway.complete(REQUEST, provider=ESCAPE_PROVIDER, model=ESCAPE_MODEL)
    trace.abandon()

    assert script.calls == (), "the scripted socket must never have been reached"
    events = [r.event for r in read_records(trace.path)]
    assert EVENT_DISPATCH_INTENT_DURABLE not in events, "nothing was dispatched"


def test_a_model_override_alone_is_refused_in_fixture_mode(tmp_path):
    """A different model over the same socket returns bytes it never produced.

    `fixture-model` is on the builtin allowlist and priced, and it keeps the
    provider identity the gateway was sealed with -- so only the sealed *pair*,
    not the provider alone, can be the admissible unit.
    """
    trace, script, gateway = _wire(tmp_path, name="model_override")

    with pytest.raises(RunModeRefusal, match="confined to the sealed pair"):
        gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model="fixture-model")
    trace.abandon()

    assert script.calls == ()


def test_a_foreign_provider_object_cannot_evade_dispatch_confinement(tmp_path):
    """Confinement compares declared values, so a foreign enum cannot slip past.

    The allowlist compares by value and admits a foreign `OPENROUTER` member
    happily. A confinement check written with `is` would answer "not a real
    vendor" about the exact object the gate is about to admit.
    """
    trace, script, gateway = _wire(tmp_path, name="foreign_override")

    with pytest.raises(RunModeRefusal, match="confined to the sealed pair"):
        gateway.complete(
            REQUEST, provider=_foreign_provider("OPENROUTER"), model=ESCAPE_MODEL
        )
    trace.abandon()

    assert script.calls == ()


def test_a_foreign_fixture_provider_cannot_evade_the_live_refusal():
    """Equal wire values must be refused despite distinct enum class identities."""
    foreign = _foreign_provider("FIXTURE")
    assert type(foreign) is not Provider
    assert foreign is not SCRIPTED_PROVIDER
    assert foreign.value == SCRIPTED_PROVIDER.value

    with pytest.raises(RunModeRefusal, match="not a live provider"):
        assert_mode_admissible(
            provider=foreign,
            model="gpt-4o-mini",
            mode=RunMode.LIVE,
            scripted_transport=False,
        )


@pytest.mark.parametrize("spelling", ["foreign_enum", "plain_string"])
def test_a_real_provider_cannot_evade_the_scripted_transport_refusal(spelling):
    """A fake socket under a real vendor's name, however that name is spelled.

    Stated plainly, because the alternative would overclaim: **neither case
    discriminates against the form this replaced.** `provider in LIVE_PROVIDERS`
    already caught both. `Provider` mixes in `str`, and `str` precedes `Enum` in
    the MRO, so members hash and compare exactly like their values -- a set of
    members matches a foreign member and a bare string alike. Unlike the `is`
    comparison in the live-provider refusal, that one was never evadable.

    What this pins is the contract rather than the accident: the refusal fires
    for every spelling a caller can actually arrive with. It fails if `Provider`
    ever loses its `str` mixin, and it fails against the obvious "tidier"
    rewrite, `provider.value in ...`, which raises `AttributeError` on a bare
    string instead of refusing it.
    """
    provider = (
        _foreign_provider("OPENROUTER")
        if spelling == "foreign_enum"
        else ESCAPE_PROVIDER.value
    )
    with pytest.raises(RunModeRefusal, match="may not sit behind real provider"):
        assert_mode_admissible(
            provider=provider,
            model=ESCAPE_MODEL,
            mode=RunMode.DETERMINISTIC_FIXTURE,
            scripted_transport=True,
        )


def test_the_sealed_pair_is_admitted_through_a_foreign_enum_identity(tmp_path):
    """Positive control: value normalisation admits as well as it refuses.

    Without this, a confinement that refused *everything* -- including the pair it
    was sealed with -- would pass every test above.
    """
    trace, script, gateway = _wire(tmp_path, name="foreign_ok")
    response, _ = gateway.complete(
        REQUEST, provider=_foreign_provider("FIXTURE"), model=SCRIPTED_MODEL
    )
    trace.seal("DONE")

    assert response.content == "scripted reply"
    assert script.calls == ((SCRIPTED_PROVIDER.value, SCRIPTED_MODEL),)


def test_a_live_gateway_may_still_dispatch_to_more_than_one_provider():
    """The confinement is fixture-scoped, not a blanket ban on overrides.

    `LIVE` mode applies the general rules only; pinning a live gateway to one
    sealed pair would be a different product, and asserting that here would let
    the fixture rule be quietly widened later.
    """
    assert_mode_admissible(
        provider=ESCAPE_PROVIDER,
        model=ESCAPE_MODEL,
        mode=RunMode.LIVE,
        scripted_transport=False,
    )


# --------------------------------------------------------------------------
# The trace must not testify to a provider call that never happened
# --------------------------------------------------------------------------


def test_a_scripted_execution_is_not_recorded_as_live(tmp_path):
    """The false testimony, asserted in the record rather than in the wiring.

    The main fixture opened `ExecutionTrace(live_transport=True)` and
    `DurableDispatchTransport(live=True)`, so every scripted call in this file
    was written down as a live provider call. `fsync_live` durability is kept:
    the two are orthogonal, and a fixture execution may exercise the barriers
    without claiming a provider was contacted.
    """
    trace, _, gateway = _wire(tmp_path, name="not_live")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")

    records = read_records(trace.path)
    started = records[0].payload
    assert started["run_mode"] == RUN_MODE_DETERMINISTIC_FIXTURE
    assert started["live_transport"] is False
    assert started["durability"] == DURABILITY_FSYNC_LIVE, "durability is orthogonal"

    intent = next(r for r in records if r.event == EVENT_DISPATCH_INTENT_DURABLE)
    assert intent.payload["live"] is False


def test_a_live_dispatcher_is_refused_against_a_scripted_trace(tmp_path):
    """`fsync_live` durability is not permission to record a live call.

    The durability refusal alone let this through: the trace is `fsync_live`, so
    the only remaining check passed, and the dispatcher then wrote `live=True`
    into a file whose `RunStarted` swore no provider would be contacted.
    """
    trace = _trace(tmp_path, name="scripted_trace")
    with pytest.raises(TraceRefusal, match="declared live_transport"):
        DurableDispatchTransport(
            trace,
            ScriptedTransport([scripted_openai_payload("x")]),
            artifact_store=_artifact_store(tmp_path, "live-refusal-artifacts"),
            live=True,
        )
    trace.abandon()


def test_the_traced_gateway_refuses_a_fixture_gateway_on_a_live_trace(tmp_path):
    """Neither object can catch this alone, so the seam holding both does.

    The trace cannot see the gateway's mode and the gateway cannot see the
    trace's declaration; a fixture gateway writing into a live trace would
    produce a file saying a scripted reply was a paid call.
    """
    live_trace = _trace(tmp_path, name="live_trace", live=True)

    # A minimal object that declares a mode, because the factories can no longer
    # build the contradiction: `fixture_gateway` always makes its own non-live
    # trace. The check under test reads `.mode` and nothing else, so this is the
    # whole of its input.
    class _DeclaresFixtureMode:
        mode = RunMode.DETERMINISTIC_FIXTURE
        default_provider = SCRIPTED_PROVIDER
        default_model = SCRIPTED_MODEL

    with pytest.raises(RunModeRefusal, match="contradicts the trace"):
        TracedGateway(live_trace, _DeclaresFixtureMode())
    live_trace.abandon()


# --------------------------------------------------------------------------
# Attempt identity binds declared inputs, never the host
# --------------------------------------------------------------------------


def test_attempt_identity_does_not_depend_on_the_host(tmp_path, monkeypatch):
    """Replay-stability across an interpreter or machine change.

    The attempt id used to include the trace's `RunStarted` digest, which covers
    the derived durability scope -- OS, OS version, interpreter version,
    filesystem. Upgrading Python changed the digest, so replaying the same
    declared execution derived ids that no longer joined to the artifacts the
    first run wrote, and a recovery join that silently misses is indistinguishable
    from a dispatch that never happened.
    """
    from pfp.infrastructure.trace import execution_trace as et

    real_scope = et.durability_scope
    ids, digests = [], []
    for index, python in enumerate(("3.14.0", "9.9.9-other-host")):
        monkeypatch.setattr(
            et,
            "durability_scope",
            lambda path=None, _p=python: {**real_scope(path), "python": _p},
        )
        directory = tmp_path / f"host{index}"
        directory.mkdir()
        run = fixture_gateway(
            directory / "run.jsonl",
            [scripted_openai_payload("r")],
            artifact_store=_artifact_store(directory),
            execution_id="declared-run",
        )
        run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
        run.trace.seal("DONE")

        records = read_records(run.trace.path)
        digests.append(records[0].sha256)
        ids.append(
            derive_dispatch_outcomes(records, artifact_store=run.artifact_store)[
                0
            ].attempt_id
        )

    assert digests[0] != digests[1], "the premise: the host material really differs"
    assert ids[0] == ids[1], "attempt identity must bind only what was declared"


# --------------------------------------------------------------------------
# Recovery validates the record it is handed
# --------------------------------------------------------------------------


def test_a_v2_response_cannot_mix_in_a_legacy_artifact_path(tmp_path):
    """Recovery fails closed even when preconstructed records bypass admission."""
    trace, run, gateway = _wire(tmp_path, name="traversal")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")

    records = read_records(trace.path)
    assert [
        o.status
        for o in derive_dispatch_outcomes(records, artifact_store=run.artifact_store)
    ] == [DISPATCH_COMPLETE]

    doctored = [
        _with_payload(r, raw_response_path="../../outside.json")
        if r.event == EVENT_RESPONSE_DURABLE
        else r
        for r in records
    ]
    outcomes = derive_dispatch_outcomes(doctored, artifact_store=run.artifact_store)
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]


@pytest.mark.parametrize(
    "count",
    ["47", 47.0, None, True, -1],
    ids=["str", "float", "null", "bool", "negative"],
)
def test_a_v2_response_cannot_mix_in_a_legacy_byte_count(tmp_path, count):
    """V2 rejects every legacy count representation, including integer values."""
    trace, run, gateway = _wire(tmp_path, name=f"count_{type(count).__name__}")
    gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DONE")

    records = read_records(trace.path)
    doctored = [
        _with_payload(r, raw_response_byte_count=count)
        if r.event == EVENT_RESPONSE_DURABLE
        else r
        for r in records
    ]
    outcomes = derive_dispatch_outcomes(doctored, artifact_store=run.artifact_store)
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]


# --------------------------------------------------------------------------
# Confinement by construction, not by inspection
# --------------------------------------------------------------------------


def _hidden_scripted_transport():
    """A `ScriptedTransport` wrapped in an ordinary closure.

    Three lines, no `.inner`, no subclass, nothing to recognise.
    """
    script = ScriptedTransport([scripted_openai_payload("fake")])

    def hidden(provider, model, request):
        return script(provider, model, request)

    return hidden, script


def test_a_hidden_scripted_transport_defeats_inspection():
    """Why the guarantee had to stop being a predicate.

    The previous confinement asked an object whether it was scripted, by walking
    `.inner` attributes looking for a `ScriptedTransport`. Reproduced here
    verbatim, it answers "not scripted" about a transport that is entirely
    scripted -- and on that answer a scripted socket could be sealed under
    `Provider.OPENROUTER`, admitted by both production gates, and written into a
    trace that said `deterministic_fixture`.

    The predicate was not weak. It was answering a question that cannot be
    answered by looking at an object, because any callable can hide anything. The
    test is kept as a standing argument against reintroducing it.
    """
    hidden, script = _hidden_scripted_transport()

    def historical_wraps_scripted(transport):
        seen = set()
        current = transport
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            if isinstance(current, ScriptedTransport):
                return True
            current = getattr(current, "inner", None)
        return False

    assert historical_wraps_scripted(script) is True, "it finds the bare object"
    assert historical_wraps_scripted(hidden) is False, (
        "and misses the same object behind a closure -- which is why confinement "
        "is now a fact the constructor knows, not a property it infers"
    )


def test_the_fixture_factory_declares_no_transport_provider_model_or_mode():
    """The bypass is closed by absence, which is the only way it stays closed.

    There is no argument to `fixture_gateway` through which a fixture execution
    can name a real vendor, supply a socket, or claim a different run mode -- so
    there is nothing for a hidden closure to be passed *to*. A guard can be
    defeated; a parameter that does not exist cannot.
    """
    import inspect

    parameters = set(inspect.signature(fixture_gateway).parameters)
    for forbidden in ("transport", "provider", "model", "mode", "run_mode"):
        assert forbidden not in parameters, (
            f"fixture_gateway grew a {forbidden!r} parameter; the confinement "
            "guarantee is that this cannot be chosen by a caller"
        )
    assert "responses" in parameters, "it takes declared bytes instead"


def test_a_callable_response_is_refused(tmp_path):
    """The hidden transport has nowhere to go, asserted rather than assumed.

    Handing the closure to the factory as a "response" is the one remaining shape
    of the old bypass, and it is refused at the point the script is declared.
    """
    hidden, _ = _hidden_scripted_transport()
    with pytest.raises(TypeError, match="declared bytes, not a callable"):
        fixture_gateway(
            tmp_path / "callable.jsonl",
            [hidden],
            artifact_store=_artifact_store(tmp_path, "callable-artifacts"),
            execution_id="callable",
        )


def test_no_supported_path_reaches_an_unconfined_gateway(tmp_path):
    """`traced.gateway.gateway.complete(...)` was a documented attribute chain.

    Whatever the comment beside it said, an attribute chain is an API, and this
    one handed back the raw `OearsLlmGateway` with every confinement check
    behind it. The confined object now holds no attribute referring to the
    gateway at all -- dispatch is a closure.

    What this does *not* claim: that the gateway is unreachable. Python has
    `__closure__` and `gc`; nothing here changes that. The claim is that no
    supported expression returns it, which is a bound on drift and accident.
    """
    run = _run(tmp_path, name="noescape")
    confined = run.gateway.gateway
    assert isinstance(confined, ConfinedGateway)

    assert not hasattr(confined, "gateway"), "the escape hatch is gone"
    assert "gateway" not in ConfinedGateway.__slots__
    # `__slots__` also means an attribute cannot be quietly added back later.
    assert not hasattr(confined, "__dict__")
    with pytest.raises(AttributeError):
        confined.gateway = "reattached"


def test_only_the_sanctioned_functions_construct_raw_gateways():
    """Trace confinement and accounted OpenRouter retain their distinct owners."""
    from pathlib import Path

    from pfp.infrastructure.architecture_fitness import (
        raw_gateway_constructors,
        sanctioned_gateway_factory_builds_one,
    )

    root = Path(__file__).resolve().parents[2]
    assert raw_gateway_constructors(root) == ()
    # The positive control: the rule above also passes if the gateway stops being
    # constructed anywhere at all, which would make it meaningless.
    assert sanctioned_gateway_factory_builds_one(root) is True


class _AdmittedLiveTestTransport:
    """Explicit liability double; never evidence of a vendor-enforced cap."""
    def __init__(self, socket):
        self.socket = socket

    def maximum_liability(self, provider, model, request, max_output_tokens, quote):
        return quote.cost_microusd

    def dispatch(self, admitted):
        return self.socket(admitted.provider, admitted.model, admitted.request)


def test_public_traced_gateway_native_http_receipt_and_settlement_survive_restart(tmp_path):
    """Native arithmetic, real loopback HTTP, durable ledger and custody barriers.

    The local peer's cap and the artifact protector are explicit fixtures;
    neither attests live vendor billing nor production encryption.
    """
    import threading
    import urllib.request
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from adversary.domain.providers.budget import BudgetController
    from adversary.infrastructure.providers.budget_ledger import SqliteBudgetLedger
    from adversary.infrastructure.providers.generation_reconciler import GenerationReconciler
    from adversary.infrastructure.providers.openai_compat import OpenAiCompatTransport
    from adversary.infrastructure.providers.wire import decode_reply
    from governance.domain.ingress.limits import MAX_PROVIDER_REPLY_BYTES

    requests = []
    model = "openai/gpt-4o-mini"
    reply = json.dumps({"id": "generation-native-loopback", "model": model,
        "choices": [{"message": {"content": "recorded"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}}).encode()
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(reply)
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"data":{"id":"generation-native-loopback","total_cost":"0.0001"}}')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    class LocalCap(OpenAiCompatTransport):
        def maximum_liability(self, *args):
            return 1000
    ledger = SqliteBudgetLedger(tmp_path / "budget.db", budget_id="restart-session")
    trace = _trace(tmp_path, name="native-http-settlement", live=True)
    store = _artifact_store(tmp_path, "native-http-artifacts")
    try:
        gateway = live_gateway(trace, LocalCap(Provider.OPENROUTER, api_key="synthetic-only", base_url=url, max_tokens=2048),
            artifact_store=store, provider=Provider.OPENROUTER, model=model,
            max_output_tokens=1, budget_microusd=10_000, budget_ledger=ledger)
        candidate, receipt = gateway.complete(REQUEST)
        trace.seal("DONE")
        assert candidate.content == "recorded" and receipt.cost_microusd == 1000
        assert requests[0]["max_tokens"] == 1
        outcomes = derive_dispatch_outcomes(read_records(trace.path), artifact_store=store)
        assert [o.status for o in outcomes] == [DISPATCH_COMPLETE]
        assert verify_encrypted_response(store, outcomes[0])
        restored = BudgetController(10_000, ledger=SqliteBudgetLedger(tmp_path / "budget.db", budget_id="restart-session"))
        attempt = restored.pending_attempts()[0]
        assert attempt["generation_id"] == candidate.generation_id
        assert attempt["wire_sha256"] == hashlib.sha256(reply).hexdigest()
        def fetch(generation):
            with urllib.request.urlopen(url + "/generation", timeout=2) as response:
                return dict(decode_reply(response.read(MAX_PROVIDER_REPLY_BYTES + 1)))
        reconciler = GenerationReconciler(restored, fetch)
        args = dict(precharge_micro_usd=1000, attempt_id=attempt["attempt_id"])
        first = reconciler.reconcile_generation(candidate.generation_id, **args)
        assert reconciler.reconcile_generation(candidate.generation_id, **args) == first
        assert restored.spent_microusd == 100 and restored.pending_attempts() == ()
        assert len(requests) == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_live_execution_is_a_separate_factory(tmp_path):
    """Live runs get their own door, and it refuses the fixture's furniture."""
    import json as _json

    fixture_trace = _trace(tmp_path, name="not_live_trace")
    with pytest.raises(RunModeRefusal, match="requires a trace opened in LIVE mode"):
        live_gateway(
            fixture_trace,
            lambda provider, model, request: {},
            artifact_store=_artifact_store(tmp_path, "not-live-artifacts"),
            provider=Provider.OPENROUTER,
            model=ESCAPE_MODEL,
        )
    fixture_trace.abandon()

    live_trace = _trace(tmp_path, name="live_scripted", live=True)
    with pytest.raises(RunModeRefusal, match="may not be used for live execution"):
        live_gateway(
            live_trace,
            ScriptedTransport([scripted_openai_payload("x")]),
            artifact_store=_artifact_store(tmp_path, "scripted-live-artifacts"),
            provider=Provider.OPENROUTER,
            model=ESCAPE_MODEL,
        )
    live_trace.abandon()

    # The positive control. Without it the two refusals above would pass against
    # a factory that refuses everything.
    ok_trace = _trace(tmp_path, name="live_ok", live=True)

    def _socket(provider, model, request):
        return _json.dumps(
            scripted_openai_payload("live-shaped", model=ESCAPE_MODEL)
        ).encode("utf-8")

    # The raw socket, not a pre-wrapped transport: the factory owns the
    # barriers. Passing a `DurableDispatchTransport` here is what hid the defect
    # that this file now pins in `test_the_live_factory_owns_the_barriers`.
    gateway = live_gateway(
        ok_trace,
        _AdmittedLiveTestTransport(_socket),
        artifact_store=_artifact_store(tmp_path, "live-ok-artifacts"),
        provider=Provider.OPENROUTER,
        model=ESCAPE_MODEL,
    )
    response, _ = gateway.complete(REQUEST)
    ok_trace.seal("DONE")

    assert response.content == "live-shaped"
    started = read_records(ok_trace.path)[0].payload
    assert started["live_transport"] is True
    assert started["run_mode"] == "live"


def test_a_live_gateway_is_not_pinned_to_one_pair(tmp_path):
    """The sealed-pair rule is fixture-scoped, and must not leak into live runs.

    Asserting it here keeps the fixture rule from being quietly widened into a
    general one, which would break real dispatch for no safety gain.
    """
    import json as _json

    trace = _trace(tmp_path, name="live_multi", live=True)

    def _socket(provider, model, request):
        return _json.dumps(scripted_openai_payload("ok", model=model)).encode("utf-8")

    gateway = live_gateway(
        trace,
        _AdmittedLiveTestTransport(_socket),
        artifact_store=_artifact_store(tmp_path, "live-multi-artifacts"),
        provider=Provider.OPENROUTER,
        model=ESCAPE_MODEL,
    )
    response, _ = gateway.complete(
        REQUEST, provider=Provider.OPENAI, model="gpt-4o-mini"
    )
    trace.seal("DONE")
    assert response.content == "ok"


def test_the_live_factory_owns_the_barriers(tmp_path):
    """A live dispatch must be impossible to make without recording it.

    `live_gateway` passed the caller's transport straight into the gateway, so an
    ordinary live socket dispatched and returned with **no intent record and no
    response record** -- a paid call leaving nothing behind, on the only supported
    live path. Every test in this file missed it because each one wrapped the
    transport by hand before calling the factory, which is precisely the step a
    caller cannot be relied on to take. Barriers that depend on the caller
    remembering them are not barriers.

    Asserted from the file rather than from the returned object: the whole point
    of barrier 1 is what survives when the process does not.
    """
    import json as _json

    trace = _trace(tmp_path, name="live_barriers", live=True)

    def _socket(provider, model, request):
        return _json.dumps(
            scripted_openai_payload("paid reply", model=ESCAPE_MODEL)
        ).encode("utf-8")

    artifact_store = _artifact_store(tmp_path, "live-barrier-artifacts")
    gateway = live_gateway(
        trace,
        _AdmittedLiveTestTransport(_socket),
        artifact_store=artifact_store,
        provider=Provider.OPENROUTER,
        model=ESCAPE_MODEL,
    )
    response, _ = gateway.complete(REQUEST)
    trace.seal("DONE")

    assert response.content == "paid reply"
    events = [r.event for r in read_records(trace.path)]
    assert EVENT_DISPATCH_INTENT_DURABLE in events, "barrier 1 must have run"
    assert EVENT_RESPONSE_DURABLE in events, "barrier 2 must have run"
    assert events.index(EVENT_DISPATCH_INTENT_DURABLE) < events.index(
        EVENT_RESPONSE_DURABLE
    )

    outcomes = derive_dispatch_outcomes(
        read_records(trace.path), artifact_store=artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_COMPLETE]
    assert verify_encrypted_response(artifact_store, outcomes[0])


def test_the_live_factory_refuses_an_already_barriered_transport(tmp_path):
    """Wrapping twice writes two intent records for one dispatch.

    Recovery now reads a repeated attempt id as malformed, which is correct and
    is why this has to be refused at construction rather than discovered later.
    """
    trace = _trace(tmp_path, name="double_wrap", live=True)
    durable = DurableDispatchTransport(
        trace,
        lambda provider, model, request: b"{}",
        artifact_store=_artifact_store(tmp_path, "double-wrap-artifacts"),
        live=True,
    )
    with pytest.raises(RunModeRefusal, match="pass the raw socket"):
        live_gateway(
            trace,
            durable,
            artifact_store=_artifact_store(tmp_path, "outer-artifacts"),
            provider=Provider.OPENROUTER,
            model=ESCAPE_MODEL,
        )
    trace.abandon()


def test_an_orphaned_unknown_status_record_is_malformed_not_a_crash():
    """Recovery must classify the evidence it is handed, not die on it.

    An attempt can reach recovery with only a `ProviderDispatchStatusUnknown`
    record -- barrier 1 torn away by a partial overwrite, or a hand-assembled
    record list. Tracking unknowns in a bare set left nothing to read a provider
    and model from, and the outcome construction dereferenced `None`: the
    function raised `AttributeError` on exactly the wreckage it exists to
    describe, which is the worst possible moment to lose the reader.
    """
    orphan = TraceRecord(
        index=1,
        event=EVENT_DISPATCH_STATUS_UNKNOWN,
        payload={
            "attempt_id": "a" * 64,
            "provider": "openrouter",
            "model": ESCAPE_MODEL,
            "failure_type": "ConnectionError",
            "failure": "socket died",
            "retry_permitted": False,
        },
        sha256="b" * 64,
        prev_sha256="c" * 64,
    )

    outcomes = derive_dispatch_outcomes([orphan])
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]
    assert outcomes[0].retry_permitted is False, "it may already have been billed"
    # The provider and model survive, which is the whole reason the record is
    # kept rather than counted: a report has to be able to name what was called.
    assert outcomes[0].provider == "openrouter"
    assert outcomes[0].model == ESCAPE_MODEL
    assert outcomes[0].attempt_id == "a" * 64


# --------------------------------------------------------------------------
# Evidence that contradicts itself is malformed, never reconciled
# --------------------------------------------------------------------------


def _one_dispatch(tmp_path, name):
    """A single completed attempt, as records."""
    run = _run(tmp_path, name=name)
    run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    run.trace.seal("DONE")
    return run, read_records(run.trace.path)


def test_a_duplicated_intent_is_malformed(tmp_path):
    """Two barrier-1 records under one attempt id cannot both be true."""
    run, records = _one_dispatch(tmp_path, "dupe_intent")
    intent = next(r for r in records if r.event == EVENT_DISPATCH_INTENT_DURABLE)
    outcomes = derive_dispatch_outcomes(
        records + [intent], artifact_store=run.artifact_store
    )

    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]
    assert outcomes[0].retry_permitted is False


def test_a_duplicated_response_is_malformed_rather_than_last_write_wins(tmp_path):
    """The silent reconciliation this replaces.

    Recovery kept the last record under each attempt id, so a trace carrying two
    contradictory answers reported one of them as fact -- and the result looked
    exactly like a clean one.
    """
    run, records = _one_dispatch(tmp_path, "dupe_response")
    response = next(r for r in records if r.event == EVENT_RESPONSE_DURABLE)
    forged = _with_payload(response, raw_response_sha256="c" * 64)

    outcomes = derive_dispatch_outcomes(
        records + [forged], artifact_store=run.artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]
    assert DISPATCH_COMPLETE not in [o.status for o in outcomes]


def test_a_response_without_an_intent_is_malformed(tmp_path):
    """Barrier 1 is what makes an attempt visible; a response without it means the
    file lost the record saying a dispatch was about to happen."""
    run, records = _one_dispatch(tmp_path, "orphan")
    without_intent = [r for r in records if r.event != EVENT_DISPATCH_INTENT_DURABLE]

    outcomes = derive_dispatch_outcomes(
        without_intent, artifact_store=run.artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]


@pytest.mark.parametrize("field", ["provider", "model"])
def test_a_response_disagreeing_with_its_intent_is_malformed(tmp_path, field):
    """The binding is more than a shared id.

    Unchecked, a response recorded under one provider could be joined to an intent
    recorded under another -- which is how a fixture reply comes to stand as the
    answer to a real call.
    """
    run, records = _one_dispatch(tmp_path, f"mismatch_{field}")
    doctored = [
        _with_payload(r, **{field: "something-else"})
        if r.event == EVENT_RESPONSE_DURABLE
        else r
        for r in records
    ]
    outcomes = derive_dispatch_outcomes(doctored, artifact_store=run.artifact_store)
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]


def test_an_attempt_that_is_both_unknown_and_answered_is_malformed(tmp_path):
    """The dispatcher writes one or the other, never both."""
    run, records = _one_dispatch(tmp_path, "both")
    intent = next(r for r in records if r.event == EVENT_DISPATCH_INTENT_DURABLE)
    unknown = TraceRecord(
        index=intent.index,
        event=EVENT_DISPATCH_STATUS_UNKNOWN,
        payload={
            "attempt_id": intent.payload["attempt_id"],
            "provider": intent.payload["provider"],
            "model": intent.payload["model"],
            "failure_type": "ConnectionError",
            "failure": "socket died",
            "retry_permitted": False,
        },
        sha256=intent.sha256,
        prev_sha256=intent.prev_sha256,
    )
    outcomes = derive_dispatch_outcomes(
        records + [unknown], artifact_store=run.artifact_store
    )
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MALFORMED]


def test_the_undoctored_run_is_the_positive_control(tmp_path):
    """Every malformed case above starts from this, so it has to be clean."""
    run, records = _one_dispatch(tmp_path, "clean_control")
    outcomes = derive_dispatch_outcomes(records, artifact_store=run.artifact_store)
    assert [o.status for o in outcomes] == [DISPATCH_COMPLETE]


# --------------------------------------------------------------------------
# An estate defect found while wiring this, pinned rather than papered over
# --------------------------------------------------------------------------


def test_canonical_provider_boundaries_share_catchable_exception_identity():
    """A real allowlist rejection crosses the gateway as its domain exception."""
    import adversary.domain.providers.allowlist as allowlist_module
    import adversary.domain.providers.types as types_module
    import adversary.infrastructure.providers.gateway as gateway_module

    assert allowlist_module.ModelNotAllowed is ModelNotAllowed
    assert allowlist_module.Provider is Provider
    assert gateway_module.Provider is Provider
    assert gateway_module.ProviderError is types_module.ProviderError
    assert gateway_module.ReplyTooLarge is ReplyTooLarge
    assert ModelNotAllowed in GATE_EXCEPTIONS

    calls = []

    def forbidden_transport(provider, model, request):
        calls.append((provider, model))
        raise AssertionError("an unallowlisted request reached transport")

    gateway = gateway_module.OearsLlmGateway.builtin(transport=forbidden_transport)
    with pytest.raises(ModelNotAllowed, match="fixture:not-allowlisted"):
        gateway.complete(REQUEST, provider=Provider.FIXTURE, model="not-allowlisted")
    assert calls == []
    assert gateway.policy.budget.spent_microusd == 0
