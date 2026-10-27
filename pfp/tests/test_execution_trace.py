"""The trace must not be able to overstate what an execution did.

Three properties carry the weight, and each has a test that fails loudly if the
recorder is "simplified" later:

1. A truncated file is distinguishable from a short one. The hash chain is what
   makes a crashed run detectable rather than merely quiet.
2. Absence of a seal derives `INCOMPLETE`. The status is read off the file; the
   producer never writes it.
3. A live transport under buffered durability is refused *at RunStarted*, before
   anything can be dispatched.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from pfp.infrastructure.trace import (
    CHAIN_GENESIS,
    CRASH_MODEL_ABRUPT_PROCESS_EXIT,
    DURABILITY_BUFFERED_REPLAY,
    DURABILITY_FSYNC_LIVE,
    EVENT_RUN_SEALED,
    EVENT_RUN_STARTED,
    EVIDENCE_CEILING_PROCESS_CRASH,
    RUN_MODE_DETERMINISTIC_FIXTURE,
    RUN_MODE_LIVE,
    EVENT_DISPATCH_INTENT_DURABLE,
    EVENT_RESPONSE_DURABLE,
    STATUS_BOUNDED_RUN_COMPLETE,
    STATUS_INCOMPLETE,
    TRACE_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION_V1,
    EventSchema,
    ExecutionTrace,
    RunMode,
    TraceRefusal,
    coerce_run_mode,
    derive_status,
    read_records,
    read_status,
    register_event_schema,
    require_run_mode,
    scan_trace,
    terminal_digest,
    verify_trace,
)

#: Two diagnostic events this file writes, declared through the public registry.
#: The V1 format is closed -- an event it does not declare can neither be written
#: nor read -- so a test that writes its own step records has to say so. That the
#: registration is three lines is the point: closing the format costs a
#: declaration, not a redesign.
register_event_schema(EventSchema("Work"))
register_event_schema(EventSchema("Late"))


def _trace(tmp_path, name="exec-1", **kwargs):
    kwargs.setdefault("execution_id", name)
    kwargs.setdefault("durability", DURABILITY_FSYNC_LIVE)
    return ExecutionTrace(tmp_path / f"{name}.jsonl", **kwargs)


# --------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------


def test_a_new_trace_opens_with_run_started(tmp_path):
    trace = _trace(tmp_path)
    trace.seal("DONE")

    records = read_records(trace.path)
    assert records[0].event == EVENT_RUN_STARTED
    assert records[-1].event == EVENT_RUN_SEALED
    assert records[0].payload["execution_id"] == "exec-1"
    assert records[0].payload["durability"] == DURABILITY_FSYNC_LIVE


def test_one_file_per_execution_is_enforced(tmp_path):
    """Reusing a path would splice two executions into one hash chain."""
    trace = _trace(tmp_path)
    trace.seal("DONE")
    with pytest.raises(TraceRefusal, match="one file per execution"):
        _trace(tmp_path)


def test_a_sealed_trace_refuses_further_records(tmp_path):
    trace = _trace(tmp_path)
    trace.seal("DONE")
    with pytest.raises(TraceRefusal, match="sealed"):
        trace.record("Late")


# --------------------------------------------------------------------------
# Derived status -- never written by the producer
# --------------------------------------------------------------------------


def test_a_sealed_trace_derives_bounded_run_complete(tmp_path):
    trace = _trace(tmp_path)
    trace.record("Work", step=1)
    trace.seal("DONE")
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE


def test_an_unsealed_trace_derives_incomplete(tmp_path):
    """The plan's mapping: no sealed terminal record -> derived INCOMPLETE."""
    trace = _trace(tmp_path)
    trace.record("Work", step=1)
    trace.abandon()
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_an_exception_leaves_the_trace_unsealed(tmp_path):
    """A run that raised did not complete, and the file must say so."""
    path = tmp_path / "boom.jsonl"
    with pytest.raises(ValueError):
        with ExecutionTrace(
            path, execution_id="boom", durability=DURABILITY_FSYNC_LIVE
        ) as trace:
            trace.record("Work", step=1)
            raise ValueError("mid-run failure")
    assert read_status(path) == STATUS_INCOMPLETE


def test_the_status_is_not_readable_from_a_producer_field(tmp_path):
    """A record claiming completion does not make the run complete.

    This is the trace-level form of the claim/conclusion separation: a producer
    may say whatever it likes in a payload, and the derived status still comes
    from the file's structure.
    """
    trace = _trace(tmp_path)
    trace.record("Work", terminal=STATUS_BOUNDED_RUN_COMPLETE, status="complete")
    trace.abandon()
    assert read_status(trace.path) == STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# The chain -- truncation and tampering
# --------------------------------------------------------------------------


def test_a_truncated_trace_is_detected_as_incomplete(tmp_path):
    """A crash mid-write must not read as a short but complete run."""
    trace = _trace(tmp_path)
    for step in range(4):
        trace.record("Work", step=step)
    trace.seal("DONE")
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE

    # Chop the seal off, as a crash would.
    lines = trace.path.read_bytes().split(b"\n")
    trace.path.write_bytes(b"\n".join(lines[:-2]) + b"\n")
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_a_torn_final_write_is_detected(tmp_path):
    """A half-written last line must not abort parsing of what came before."""
    trace = _trace(tmp_path)
    trace.record("Work", step=0)
    trace.seal("DONE")

    raw = trace.path.read_bytes()
    trace.path.write_bytes(raw[: len(raw) - 12])  # shear the final record

    records = read_records(trace.path)
    assert records, "records before the tear must still parse"
    assert records[0].event == EVENT_RUN_STARTED
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_an_edited_record_breaks_the_chain(tmp_path):
    """Editing a payload must invalidate everything from that point on.

    Without this, a trace could be quietly rewritten to say a gate passed. The
    edited line's own digest fails first, so parsing stops there and the run
    derives INCOMPLETE rather than reporting the forged content.
    """
    trace = _trace(tmp_path)
    trace.record("Work", step=0, disposition="FAIL")
    trace.seal("DONE")

    lines = trace.path.read_bytes().split(b"\n")
    forged = json.loads(lines[1])
    forged["payload"]["disposition"] = "PASS"
    lines[1] = json.dumps(forged, sort_keys=True, separators=(",", ":")).encode("utf-8")
    trace.path.write_bytes(b"\n".join(lines))

    assert read_status(trace.path) == STATUS_INCOMPLETE
    assert len(read_records(trace.path)) == 1, "parsing stops at the forged record"


def test_a_rehashed_edit_still_breaks_the_link(tmp_path):
    """The stronger forgery: recompute the digest after editing.

    A per-record digest alone would accept this. The chain is what refuses it,
    because the *following* record still carries the old prev_sha256.
    """
    trace = _trace(tmp_path)
    trace.record("Work", step=0, disposition="FAIL")
    trace.seal("DONE")

    import hashlib

    lines = trace.path.read_bytes().split(b"\n")
    forged = json.loads(lines[1])
    forged["payload"]["disposition"] = "PASS"
    body = {k: v for k, v in forged.items() if k != "sha256"}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    forged["sha256"] = hashlib.sha256(encoded).hexdigest()
    lines[1] = json.dumps(forged, sort_keys=True, separators=(",", ":")).encode("utf-8")
    trace.path.write_bytes(b"\n".join(lines))

    records = read_records(trace.path)
    assert len(records) == 2, "the forged record verifies alone; its successor must not"
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_an_empty_file_derives_incomplete(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_bytes(b"")
    assert read_status(path) == STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# Durability
# --------------------------------------------------------------------------


def test_live_transport_under_buffered_durability_is_refused_at_run_started(tmp_path):
    """Refused before dispatch, because paid bytes cannot be un-spent."""
    with pytest.raises(TraceRefusal, match="live transport requires fsync_live"):
        ExecutionTrace(
            tmp_path / "live.jsonl",
            execution_id="live",
            durability=DURABILITY_BUFFERED_REPLAY,
            live_transport=True,
        )
    assert not (tmp_path / "live.jsonl").exists(), "refusal must leave no file"


def test_buffered_durability_is_admissible_without_a_live_transport(tmp_path):
    """Positive control: the refusal is about the combination, not about buffering."""
    trace = _trace(tmp_path, name="cassette", durability=DURABILITY_BUFFERED_REPLAY)
    trace.seal("DONE")
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE


def test_an_unknown_durability_mode_is_refused(tmp_path):
    with pytest.raises(TraceRefusal, match="unknown durability mode"):
        _trace(tmp_path, name="bad", durability="whatever")


def test_fsync_is_actually_called_in_live_mode(tmp_path, monkeypatch):
    """`fsync_live` must mean fsync, not merely flush.

    Asserted because a flush-only implementation passes every other test in this
    file while providing none of the durability the mode's name promises.
    """
    import os as os_module

    calls: list[int] = []
    real_fsync = os_module.fsync
    monkeypatch.setattr(
        os_module, "fsync", lambda fd: (calls.append(fd), real_fsync(fd))[1]
    )

    trace = _trace(tmp_path, name="fsynced")
    before = len(calls)
    trace.record("Work", step=0)
    assert len(calls) > before, "fsync_live must fsync each record"
    trace.seal("DONE")


def test_buffered_mode_does_not_fsync_each_record(tmp_path, monkeypatch):
    """Negative control for the assertion above."""
    import os as os_module

    calls: list[int] = []
    real_fsync = os_module.fsync
    monkeypatch.setattr(
        os_module, "fsync", lambda fd: (calls.append(fd), real_fsync(fd))[1]
    )

    trace = _trace(tmp_path, name="buffered", durability=DURABILITY_BUFFERED_REPLAY)
    before = len(calls)
    trace.record("Work", step=0)
    assert len(calls) == before, "buffered_replay must not fsync per record"
    trace.seal("DONE")


def test_the_durability_scope_is_derived_and_cannot_be_supplied(tmp_path):
    """A durability result is evidence about the host that produced it.

    An earlier revision took a free-form `platform` argument, which could claim
    `"linux-ci"` from a Windows laptop and omitted OS version, filesystem and
    barrier API entirely. A green fsync result carrying a false host label is
    worse than no result: it is a durability claim about a platform nobody
    tested. The scope is now derived from the running interpreter, and the
    parameter is gone rather than validated.
    """
    import platform as platform_module

    with pytest.raises(TypeError):
        _trace(tmp_path, name="supplied", platform="linux-ci")

    trace = _trace(tmp_path, name="scoped")
    trace.seal("DONE")
    scope = read_records(trace.path)[0].payload["durability_scope"]

    assert scope["os"] == platform_module.system()
    assert scope["os_version"] == platform_module.version()
    assert scope["python"] == platform_module.python_version()
    assert scope["barrier_api"] == "os.fsync"
    assert "filesystem" in scope, "recorded even when it can only say 'unknown'"


# --------------------------------------------------------------------------
# Clean EOF -- a valid seal is not enough
# --------------------------------------------------------------------------


def test_a_valid_seal_followed_by_garbage_is_not_complete(tmp_path):
    """The verified prefix is not the whole file.

    Returning only the prefix reported this file as complete while silently
    discarding evidence that something else happened to it -- a concatenation, a
    partially-overwritten older trace, a truncated append from a second writer.
    Completion now requires parsing to reach a clean end of file.
    """
    trace = _trace(tmp_path, name="garbage")
    trace.record("Work", step=0)
    trace.seal("DONE")
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE

    with trace.path.open("ab") as handle:
        handle.write(b'{"not":"a valid record"}\n')

    scan = scan_trace(trace.path)
    assert scan.records[-1].event == EVENT_RUN_SEALED, "the prefix still verifies"
    assert scan.clean_eof is False
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_a_missing_final_newline_is_not_clean_eof(tmp_path):
    """A file whose last write was torn mid-line, even if every full line verifies."""
    trace = _trace(tmp_path, name="nonewline")
    trace.seal("DONE")
    raw = trace.path.read_bytes()
    trace.path.write_bytes(raw.rstrip(b"\n"))

    assert scan_trace(trace.path).clean_eof is False
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_derive_status_on_a_bare_record_list_never_claims_completion(tmp_path):
    """A sequence cannot express clean EOF, so it must not be able to claim it."""
    trace = _trace(tmp_path, name="bare")
    trace.seal("DONE")
    records = read_records(trace.path)
    assert derive_status(records) == STATUS_INCOMPLETE
    assert derive_status(scan_trace(trace.path)) == STATUS_BOUNDED_RUN_COMPLETE


# --------------------------------------------------------------------------
# Run mode -- the trace states what it was, and cannot state the opposite
# --------------------------------------------------------------------------


def test_run_mode_defaults_to_what_the_transport_declares(tmp_path):
    """Derived, not defaulted to a constant.

    A fixed default would be a standing claim about every trace that never sets
    the field, and half of those claims would be wrong in the direction that
    matters -- a scripted run described as live.
    """
    fixture = _trace(tmp_path, name="derived_fixture")
    fixture.seal("DONE")
    assert (
        read_records(fixture.path)[0].payload["run_mode"]
        == RUN_MODE_DETERMINISTIC_FIXTURE
    )

    live = _trace(tmp_path, name="derived_live", live_transport=True)
    live.seal("DONE")
    assert read_records(live.path)[0].payload["run_mode"] == RUN_MODE_LIVE


def test_a_scripted_run_may_not_be_recorded_as_live(tmp_path):
    """The false-testimony case, refused at RunStarted.

    A trace declaring `deterministic_fixture` alongside `live_transport=True`
    would read as a paid provider call while a script supplied every byte, and
    nothing downstream could tell the difference.
    """
    with pytest.raises(TraceRefusal, match="contradicts live_transport"):
        _trace(
            tmp_path,
            name="lying_fixture",
            live_transport=True,
            run_mode=RunMode.DETERMINISTIC_FIXTURE,
        )


def test_a_live_run_may_not_be_recorded_as_scripted(tmp_path):
    """The same refusal in the other direction, so the field cannot be decorative."""
    with pytest.raises(TraceRefusal, match="contradicts live_transport"):
        _trace(tmp_path, name="lying_live", live_transport=False, run_mode=RunMode.LIVE)


def test_durability_stays_orthogonal_to_run_mode(tmp_path):
    """A fixture execution may exercise fsync without claiming a provider call.

    Collapsing the two would force every barrier test to declare a live transport
    -- which is exactly how the false testimony got written in the first place.
    """
    trace = _trace(tmp_path, name="fixture_fsync", durability=DURABILITY_FSYNC_LIVE)
    trace.seal("DONE")

    started = read_records(trace.path)[0].payload
    assert started["run_mode"] == RUN_MODE_DETERMINISTIC_FIXTURE
    assert started["durability"] == DURABILITY_FSYNC_LIVE
    assert started["live_transport"] is False


def test_an_unknown_run_mode_is_refused(tmp_path):
    """Fail-closed on a spelling nobody defined, rather than recording it."""
    with pytest.raises(TraceRefusal, match="is not a RunMode"):
        _trace(tmp_path, name="bogus_mode", run_mode="mostly_fixture")


# --------------------------------------------------------------------------
# The scope a durability result is evidence about
# --------------------------------------------------------------------------


def test_the_scope_records_the_crash_model_it_was_tested_under(tmp_path):
    """The evidence ceiling belongs in the file, not only in a docstring.

    The crash tests kill a child with `os._exit`, which is not power loss:
    flushed data survives in the page cache whether or not `fsync` ran. Prose
    saying so lives in a module nobody opens; a later, stronger harness has to be
    able to tell these results apart from power-loss results by reading the
    record.
    """
    trace = _trace(tmp_path, name="ceiling")
    trace.seal("DONE")

    scope = read_records(trace.path)[0].payload["durability_scope"]
    assert scope["crash_model"] == CRASH_MODEL_ABRUPT_PROCESS_EXIT
    assert scope["evidence_ceiling"] == EVIDENCE_CEILING_PROCESS_CRASH


# --------------------------------------------------------------------------
# Blank physical lines are not records
# --------------------------------------------------------------------------


def test_a_trailing_blank_line_is_not_clean_eof(tmp_path):
    """A valid seal followed by an empty line is still trailing content.

    `_iter_lines` dropped empty physical lines, so a file ending `RunSealed\n\n`
    derived complete. That second newline is a byte the writer never produced --
    the same evidence of a second writer or a partial overwrite that trailing
    garbage is, and the only reason it read differently is that the scanner threw
    it away before deciding.
    """
    trace = _trace(tmp_path, name="blankline")
    trace.seal("DONE")
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE

    with trace.path.open("ab") as handle:
        handle.write(b"\n")

    assert scan_trace(trace.path).clean_eof is False
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_a_blank_line_between_records_truncates_the_verified_prefix(tmp_path):
    """Absorbing it silently would let the records after it keep their positions.

    The prefix before the blank line still verifies, and everything from the
    blank line on is unverified -- which is what a partially-overwritten file
    looks like.
    """
    trace = _trace(tmp_path, name="blankmiddle")
    trace.record("Work", step=0)
    trace.seal("DONE")

    lines = trace.path.read_bytes().split(b"\n")[:-1]
    assert len(lines) == 3, "RunStarted, Work, RunSealed"
    trace.path.write_bytes(b"\n".join([lines[0], b"", lines[1], lines[2]]) + b"\n")

    scan = scan_trace(trace.path)
    assert [r.event for r in scan.records] == [EVENT_RUN_STARTED]
    assert scan.clean_eof is False
    assert read_status(trace.path) == STATUS_INCOMPLETE


def test_a_single_terminating_newline_per_record_is_still_clean(tmp_path):
    """Positive control: refusing blank lines must not refuse ordinary files."""
    trace = _trace(tmp_path, name="ordinary")
    trace.record("Work", step=0)
    trace.seal("DONE")

    assert scan_trace(trace.path).clean_eof is True
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE


# --------------------------------------------------------------------------
# Strict V1 admission -- linking is not the same as meaning
# --------------------------------------------------------------------------
#
# A hash chain proves a file was not partially edited. It says nothing about
# whether the records mean anything, and recovery reads these payloads. So the
# tests below all start from a *hand-built* file that chains perfectly, and then
# change exactly one thing about what it says.


def _forge(index, event, payload, prev):
    """One record encoded exactly the way the writer encodes it.

    Built by hand so the negative cases below can chain perfectly and still be
    wrong -- which is the only way to test admission separately from the chain.
    """
    body = {"index": index, "event": event, "prev_sha256": prev, "payload": payload}
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    line = json.dumps(
        {**body, "sha256": digest},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return line, digest


def _started_payload(**overrides):
    payload = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "execution_id": "forged",
        "durability": DURABILITY_FSYNC_LIVE,
        "live_transport": False,
        "run_mode": RUN_MODE_DETERMINISTIC_FIXTURE,
        "durability_scope": {"os": "test"},
    }
    payload.update(overrides)
    return payload


def _forged_trace(tmp_path, name, *, started=None, extra=(), sealed=True):
    """A complete, correctly chained file assembled outside the writer."""
    started_line, digest = _forge(
        0, EVENT_RUN_STARTED, started or _started_payload(), CHAIN_GENESIS
    )
    lines = [started_line]
    index = 1
    for event, payload in extra:
        line, digest = _forge(index, event, payload, digest)
        lines.append(line)
        index += 1
    if sealed:
        line, digest = _forge(index, EVENT_RUN_SEALED, {"terminal": "DONE"}, digest)
        lines.append(line)
    path = tmp_path / f"{name}.jsonl"
    path.write_bytes(b"\n".join(lines) + b"\n")
    return path


def test_a_forged_but_wellformed_trace_is_admitted(tmp_path):
    """The positive control every test below depends on.

    Without it, each negative case could be passing because `_forge` writes
    something the reader would reject anyway -- which would make the whole
    section assert nothing at all.
    """
    path = _forged_trace(tmp_path, "wellformed", extra=[("Work", {"step": 1})])
    assert read_status(path) == STATUS_BOUNDED_RUN_COMPLETE


def test_a_trace_from_another_schema_version_is_not_complete(tmp_path):
    """A file written by a format this reader does not implement.

    Refused rather than half-understood: the fields it does recognise may mean
    something else entirely in the version that wrote them.
    """
    path = _forged_trace(
        tmp_path,
        "future",
        started=_started_payload(schema_version="core.symbol-game.execution-trace.v3"),
    )
    assert scan_trace(path).records == []
    assert read_status(path) == STATUS_INCOMPLETE


def test_a_missing_schema_version_is_not_complete(tmp_path):
    payload = _started_payload()
    del payload["schema_version"]
    path = _forged_trace(tmp_path, "noversion", started=payload)
    assert read_status(path) == STATUS_INCOMPLETE


def test_a_non_object_payload_is_refused(tmp_path):
    """Recovery calls `.get()` on this. A `null` or a list crashes the reader
    that was sent to explain a crash, which is the worst possible moment for it.
    """
    for name, payload in (("nullpayload", None), ("listpayload", [1, 2])):
        line, digest = _forge(0, EVENT_RUN_STARTED, payload, CHAIN_GENESIS)
        path = tmp_path / f"{name}.jsonl"
        path.write_bytes(line + b"\n")
        assert scan_trace(path).records == [], name
        assert read_status(path) == STATUS_INCOMPLETE, name


def test_an_undeclared_event_is_refused_on_read(tmp_path):
    """An event nobody declared cannot be interpreted, so it is not admitted."""
    path = _forged_trace(
        tmp_path, "unknownevent", extra=[("SomethingNobodyDeclared", {})]
    )
    assert [r.event for r in scan_trace(path).records] == [EVENT_RUN_STARTED]
    assert read_status(path) == STATUS_INCOMPLETE


def test_an_undeclared_event_is_refused_on_write(tmp_path):
    """Writer and reader agree, so a trace cannot be corrupt the moment it is made.

    Checking only on the way in would let a run produce a file its own recovery
    refuses -- discovered when the run it describes is already over.
    """
    trace = _trace(tmp_path, name="writeunknown")
    with pytest.raises(TraceRefusal, match="is not declared"):
        trace.record("SomethingNobodyDeclared", step=1)
    trace.abandon()


def test_a_payload_missing_a_required_field_is_refused_on_write(tmp_path):
    trace = _trace(tmp_path, name="missingfield")
    with pytest.raises(TraceRefusal, match="missing required field"):
        trace.record(EVENT_DISPATCH_INTENT_DURABLE, attempt_id="a")
    trace.abandon()


def test_a_field_of_the_wrong_type_is_refused(tmp_path):
    """A V2 encrypted reference rejects a string byte count."""
    path = _forged_trace(
        tmp_path,
        "badtype",
        extra=[
            (
                EVENT_RESPONSE_DURABLE,
                {
                    "attempt_id": "a" * 64,
                    "provider": "fixture",
                    "model": "scripted/p1b-fixture",
                    "encrypted_artifact_ref": _encrypted_ref(byte_length="47"),
                },
            )
        ],
    )
    assert [r.event for r in scan_trace(path).records] == [EVENT_RUN_STARTED]


def test_a_boolean_where_an_integer_belongs_is_refused(tmp_path):
    """`isinstance(True, int)` is true, so `true` would have passed as the int 1."""
    path = _forged_trace(
        tmp_path,
        "boolcount",
        extra=[
            (
                EVENT_RESPONSE_DURABLE,
                {
                    "attempt_id": "a" * 64,
                    "provider": "fixture",
                    "model": "scripted/p1b-fixture",
                    "encrypted_artifact_ref": _encrypted_ref(byte_length=True),
                },
            )
        ],
    )
    assert [r.event for r in scan_trace(path).records] == [EVENT_RUN_STARTED]


def _encrypted_ref(**overrides):
    value = {
        "artifact_schema": "core.provider.raw-response.v1",
        "authority_effect": "None",
        "byte_length": 47,
        "encrypted_envelope_digest": "sha256:" + "c" * 64,
        "plaintext_sha256": "sha256:" + "b" * 64,
        "protector_id": "fixture-only-hmac-stream.v1",
        "schema": "core.oeos.encrypted-artifact-ref.v1",
    }
    value.update(overrides)
    return value


def test_v2_refuses_legacy_plaintext_path_fields(tmp_path):
    path = _forged_trace(
        tmp_path,
        "v2-legacy-path",
        extra=[
            (
                EVENT_RESPONSE_DURABLE,
                {
                    "attempt_id": "a" * 64,
                    "provider": "fixture",
                    "model": "scripted/p1b-fixture",
                    "encrypted_artifact_ref": _encrypted_ref(),
                    "raw_response_path": "raw/response.json",
                },
            )
        ],
    )
    assert [r.event for r in scan_trace(path).records] == [EVENT_RUN_STARTED]


def test_v1_is_read_only_but_remains_replayable(tmp_path):
    started = _started_payload(schema_version=TRACE_SCHEMA_VERSION_V1)
    path = _forged_trace(
        tmp_path,
        "legacy-v1",
        started=started,
        extra=[
            (
                EVENT_RESPONSE_DURABLE,
                {
                    "attempt_id": "a" * 64,
                    "provider": "fixture",
                    "model": "scripted/p1b-fixture",
                    "raw_response_sha256": "b" * 64,
                    "raw_response_byte_count": 47,
                    "raw_response_path": f"{'a' * 64}.json",
                },
            )
        ],
    )
    scan = scan_trace(path)
    assert scan.schema_version == TRACE_SCHEMA_VERSION_V1
    assert derive_status(scan) == STATUS_BOUNDED_RUN_COMPLETE


def test_noncanonical_json_is_refused_even_though_it_chains(tmp_path):
    """The digest must be a statement about the bytes on disk.

    Hashing the *decoded* body normalised key order and whitespace away before
    the digest was taken, so two visibly different files carried the same chain
    and a re-encoded trace verified as though untouched.
    """
    path = _forged_trace(tmp_path, "noncanonical")
    lines = path.read_bytes().split(b"\n")[:-1]
    parsed = json.loads(lines[0])
    # Re-encode with the keys in a different order and a space after each colon.
    # The chain still verifies: the digest is over the decoded body.
    reordered = json.dumps(
        {k: parsed[k] for k in reversed(list(parsed))}, separators=(", ", ": ")
    ).encode("utf-8")
    assert json.loads(reordered) == parsed, "same decoded record"
    assert reordered != lines[0], "different bytes"
    path.write_bytes(b"\n".join([reordered] + lines[1:]) + b"\n")

    assert scan_trace(path).records == []
    assert read_status(path) == STATUS_INCOMPLETE


def test_a_duplicate_json_property_in_a_record_is_refused(tmp_path):
    """`json.loads` keeps the last value, so a decoded-body digest never saw the
    first. Only a byte-level check can tell that the file said both."""
    path = _forged_trace(tmp_path, "dupeprop")
    lines = path.read_bytes().split(b"\n")[:-1]
    doubled = lines[0].replace(b'{"event"', b'{"event":"Injected","event"', 1)
    assert doubled != lines[0]
    path.write_bytes(b"\n".join([doubled] + lines[1:]) + b"\n")

    assert scan_trace(path).records == []


def test_an_extra_envelope_key_is_refused(tmp_path):
    """A record this writer never produces. Admitting it means the reader cannot
    say what it is holding."""
    line, _ = _forge(0, EVENT_RUN_STARTED, _started_payload(), CHAIN_GENESIS)
    parsed = json.loads(line)
    parsed["annotation"] = "added later"
    path = tmp_path / "extrakey.jsonl"
    path.write_bytes(
        json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    assert scan_trace(path).records == []


def test_a_second_run_started_is_refused(tmp_path):
    """Two executions spliced into one file -- what one-file-per-execution exists
    to keep out, arriving through the back door of a concatenation."""
    path = _forged_trace(
        tmp_path, "tworuns", extra=[(EVENT_RUN_STARTED, _started_payload())]
    )
    assert [r.event for r in scan_trace(path).records] == [EVENT_RUN_STARTED]


def test_a_trace_not_opening_with_run_started_is_refused(tmp_path):
    line, _ = _forge(0, "Work", {"step": 1}, CHAIN_GENESIS)
    path = tmp_path / "noopen.jsonl"
    path.write_bytes(line + b"\n")
    assert scan_trace(path).records == []
    assert read_status(path) == STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# Run mode is a value, not an annotation
# --------------------------------------------------------------------------


def test_a_run_mode_string_is_coerced_to_the_enum():
    """The P1 hole. `mode="deterministic_fixture"` made *both* `mode is
    RunMode.LIVE` and `mode is RunMode.DETERMINISTIC_FIXTURE` false, so every
    branch that depended on the mode was silently skipped. A type annotation is
    not a check; this is the check.
    """
    assert coerce_run_mode("deterministic_fixture", live_transport=False) is (
        RunMode.DETERMINISTIC_FIXTURE
    )
    assert require_run_mode("live") is RunMode.LIVE
    assert require_run_mode(RunMode.LIVE) is RunMode.LIVE


def test_a_foreign_run_mode_enum_is_refused():
    """Two enums that mean the same thing are still two things.

    Accepting one by value would put the identity comparisons straight back where
    they started -- and this estate demonstrably produces same-named enums from
    two module identities.
    """
    import enum

    class RunMode(enum.Enum):  # deliberately shadows the real one
        DETERMINISTIC_FIXTURE = "deterministic_fixture"
        LIVE = "live"

    with pytest.raises(TraceRefusal, match="is not a RunMode"):
        require_run_mode(RunMode.DETERMINISTIC_FIXTURE)
    with pytest.raises(TraceRefusal, match="is not a RunMode"):
        coerce_run_mode(RunMode.LIVE, live_transport=True)


def test_a_missing_run_mode_is_refused_where_one_is_mandatory():
    """`coerce_run_mode` may derive a default; `require_run_mode` may not.

    The two defaults are opposites, and sharing one would be the dangerous kind
    of convenience: a gateway that was not told which mode it is under must
    refuse, not assume the safe-looking one.
    """
    with pytest.raises(TraceRefusal, match="run mode is required"):
        require_run_mode(None)
    assert coerce_run_mode(None, live_transport=True) is RunMode.LIVE


# --------------------------------------------------------------------------
# The terminal digest -- an attachment point, and what it is not
# --------------------------------------------------------------------------
#
# Nothing in this section anchors anything, and none of it makes the chain
# tamper-proof. `test_a_forged_but_wellformed_trace_is_admitted` above stays
# green and always will: a rebuilt file that chains perfectly is a complete trace
# by every test a reader can apply to it *alone*.
#
# What is pinned here is that the digest the writer computes is carried out of
# the run instead of discarded, read back off the file by the same name, and
# compared in one place -- so that if a value is ever kept somewhere the writer
# cannot reach, there is one thing for it to bind to and one function that
# refuses when it does not match. Where such a value would live is not answered
# here, and the last test in this section says so in the form of a passing
# assertion rather than a comment.


def test_seal_returns_the_terminal_digest(tmp_path):
    """The digest was computed and thrown away.

    Every caller that wanted it had to re-derive it, which means a second
    implementation of "the last record's digest" -- and a second thing that can
    disagree with the file.
    """
    trace = _trace(tmp_path, name="sealdigest")
    digest = trace.seal("DONE")

    assert isinstance(digest, str)
    assert re.fullmatch(r"[0-9a-f]{64}", digest), digest
    assert read_records(trace.path)[-1].sha256 == digest


def test_the_writers_digest_is_the_readers_digest(tmp_path):
    """One value, computed twice, from opposite sides of the file.

    Not a tautology: the reader does not trust the `sha256` field it is handed.
    `_admit` recomputes the digest from the canonical bytes and refuses the
    record unless the line on disk is exactly what the writer would have
    produced. So this equality says the writer's return value survives a
    byte-level re-derivation, which is the only reason it is worth carrying
    anywhere.
    """
    trace = _trace(tmp_path, name="roundtrip")
    trace.record("Work", step=0)
    digest = trace.seal("DONE")

    assert terminal_digest(scan_trace(trace.path)) == digest


def test_the_head_of_the_chain_advances_with_every_record(tmp_path):
    """`terminal_digest` on the writer must always name a record that exists.

    `CHAIN_GENESIS` is a link value, not a record digest. A head still reading
    genesis after `RunStarted` would be a chain reporting itself empty while
    holding a record -- and an anchor bound to that value would be an anchor on
    nothing.
    """
    trace = _trace(tmp_path, name="head")
    opened = trace.terminal_digest
    assert opened != CHAIN_GENESIS

    stepped = trace.record("Work", step=0)
    assert trace.terminal_digest == stepped
    assert stepped != opened

    sealed = trace.seal("DONE")
    assert trace.terminal_digest == sealed
    assert sealed != stepped


def test_the_terminal_digest_of_an_empty_scan_is_none(tmp_path):
    """No records, no head.

    Returning a placeholder -- genesis, or the empty string -- would give a
    caller something to compare, and every value it could be compared against is
    the wrong answer.
    """
    path = tmp_path / "nothing.jsonl"
    path.write_bytes(b"")

    assert terminal_digest(scan_trace(path)) is None
    assert terminal_digest([]) is None


def test_verify_trace_admits_the_run_the_digest_came_from(tmp_path):
    """The positive control the refusals below depend on.

    Without it, every `pytest.raises` in this section could be passing because
    `verify_trace` refuses everything.
    """
    trace = _trace(tmp_path, name="genuine")
    trace.record("Work", step=0)
    digest = trace.seal("DONE")

    scan = verify_trace(trace.path, expected_terminal_digest=digest)
    assert derive_status(scan) == STATUS_BOUNDED_RUN_COMPLETE


def test_a_forged_trace_admitted_by_read_status_is_refused_against_a_genuine_digest(
    tmp_path,
):
    """The one question the file cannot answer about itself.

    The forged trace is complete by `read_status`, and that is not a bug -- it is
    what the hash chain can and cannot prove, held as a positive control at
    `test_a_forged_but_wellformed_trace_is_admitted`. The only thing separating
    it from the genuine run is a value that appears in neither file. Handed that
    value, the forgery is refused.
    """
    genuine = _trace(tmp_path, name="genuine_run")
    genuine.record("Work", step=1)
    genuine_digest = genuine.seal("DONE")

    forged = _forged_trace(tmp_path, "forgery", extra=[("Work", {"step": 1})])
    assert read_status(forged) == STATUS_BOUNDED_RUN_COMPLETE, (
        "the chain cannot tell a rebuilt file from an original; that is the residual"
    )

    with pytest.raises(TraceRefusal, match="is not the expected"):
        verify_trace(forged, expected_terminal_digest=genuine_digest)


def _resign(path, new_path, mutate):
    """Rebuild a whole trace from its own records, with one payload changed.

    The forgery the chain provably cannot see: every record is re-encoded and
    re-hashed in order, so every link verifies and the canonical-bytes check
    passes. `test_an_edited_record_breaks_the_chain` and
    `test_a_rehashed_edit_still_breaks_the_link` catch partial rewrites because a
    successor still carries the old `prev_sha256`; here no successor does.
    """
    records = [json.loads(line) for line in path.read_bytes().split(b"\n") if line]
    lines = []
    prev = CHAIN_GENESIS
    for record in records:
        payload = mutate(record["event"], dict(record["payload"]))
        line, prev = _forge(record["index"], record["event"], payload, prev)
        lines.append(line)
    new_path.write_bytes(b"\n".join(lines) + b"\n")
    return new_path, prev


def test_a_wholesale_resigned_rewrite_is_complete_to_the_reader(tmp_path):
    """Rewrite history, re-sign every successor, and the file still derives
    complete. This is the residual in executable form, and the refusal below is
    the only thing that separates the two files.
    """
    trace = _trace(tmp_path, name="original")
    trace.record("Work", step=0, disposition="FAIL")
    original_digest = trace.seal("DONE")

    def flip(event, payload):
        if event == "Work":
            payload["disposition"] = "PASS"
        return payload

    rewritten, rewritten_digest = _resign(
        trace.path, tmp_path / "rewritten.jsonl", flip
    )

    assert read_status(rewritten) == STATUS_BOUNDED_RUN_COMPLETE
    assert [r.payload.get("disposition") for r in scan_trace(rewritten).records] == [
        None,
        "PASS",
        None,
    ], "the forged verdict is what the reader now reports"
    assert rewritten_digest != original_digest

    with pytest.raises(TraceRefusal, match="is not the expected"):
        verify_trace(rewritten, expected_terminal_digest=original_digest)


def test_verify_trace_refuses_an_unclean_file_whose_prefix_digest_matches(tmp_path):
    """The completeness check is not subsumed by the comparison.

    Trailing bytes leave the verified prefix -- and therefore its digest --
    untouched. A verifier that compared only the digest would admit exactly the
    file `test_a_valid_seal_followed_by_garbage_is_not_complete` refuses, making
    it weaker than the `read_status` it sits beside.
    """
    trace = _trace(tmp_path, name="withgarbage")
    digest = trace.seal("DONE")
    with trace.path.open("ab") as handle:
        handle.write(b'{"not":"a valid record"}\n')

    assert terminal_digest(scan_trace(trace.path)) == digest, "the prefix is untouched"

    with pytest.raises(TraceRefusal, match="cannot vouch for a file"):
        verify_trace(trace.path, expected_terminal_digest=digest)


def test_no_value_of_the_expected_digest_means_do_not_check(tmp_path):
    """A verifier with an off switch is not one.

    `None` and `""` are how a caller loses the digest without noticing: an unset
    config field, an empty environment variable. Both must refuse loudly, and the
    refusal must name the *argument* rather than report a digest mismatch --
    which reads as a tampering verdict on a file that is fine, and sends the
    investigation to the wrong place.
    """
    trace = _trace(tmp_path, name="offswitch")
    trace.seal("DONE")

    for bogus in (None, "", "not-a-digest", "A" * 64, "0" * 63):
        with pytest.raises(TraceRefusal, match="no value of this argument"):
            verify_trace(trace.path, expected_terminal_digest=bogus)


def test_a_forgery_verifies_against_its_own_digest(tmp_path):
    """What this check does **not** do, asserted rather than promised.

    `verify_trace` does not anchor a trace. It moves the question from the file
    to wherever the expected digest is kept, and a forged trace checked against a
    digest read out of the forged trace passes -- as it must, since the two are
    consistent. The residual is untouched: the value has to come from somewhere
    the writer cannot reach, and nothing in this repository provides such a
    place. A digest stored beside the trace is re-signable by whoever re-signed
    the trace.
    """
    forged = _forged_trace(tmp_path, "selfconsistent", extra=[("Work", {"step": 1})])
    self_digest = terminal_digest(scan_trace(forged))

    scan = verify_trace(forged, expected_terminal_digest=self_digest)
    assert scan.clean_eof is True
