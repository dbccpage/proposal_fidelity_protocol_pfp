"""One JSONL file per execution, hash-chained and explicitly sealed.

The harness reads these files as its only record of what happened. That makes
two properties load-bearing, and neither is automatic:

**A truncated trace must be distinguishable from a short one.** Every record
carries the digest of the record before it, so the chain verifies. A process
that dies mid-write leaves a file whose last line either fails to parse or fails
its link -- both detectable. Without the chain, a crashed run and a run that
simply did little look identical, and the harness would silently score a partial
execution as a complete one.

*What the chain does not do.* It detects isolated edits and incomplete suffix
rewrites. It does **not** detect a rewrite by anyone able to re-sign the edited
record and every successor, because nothing here anchors the terminal digest
outside the file. Treat the chain as tamper-*evident* against partial edits, not
as tamper-proof. Anchoring the final digest somewhere the writer cannot reach is
a separate piece of work and is not claimed by this module.

What *is* here is the attachment point that work would need. ``seal`` returns the
terminal digest instead of discarding it, ``terminal_digest`` reads one back off
a scanned file, and ``verify_trace`` refuses a file whose terminal digest is not
the one it was handed. The comparison is exactly as strong as the place the
expected digest is kept, and this module does not provide such a place: a digest
written into the same tree is re-signable by whoever re-signed the trace. Read
``verify_trace`` as "this is the run that digest came from", never as "this run
was not rewritten".

**Absence of a seal is not silence, it is a verdict.** A trace with no
``RunSealed`` record derives ``INCOMPLETE``. The plan's mapping is explicit: "no
sealed terminal record -> derived ``INCOMPLETE``". The status is *derived from
the file*, never written by the thing being measured, which is the same
separation the code-change evaluator enforces between a producer's claim and an
evaluator's conclusion.

Durability is recorded per execution rather than assumed. ``fsync_live`` is
mandatory for any live or irreversible call; ``buffered_replay`` is admissible
only for fully-recorded cassette execution. A live transport declared alongside
buffered durability is refused at ``RunStarted`` -- before anything can be
dispatched -- because that combination can lose paid bytes and there is no
recovery after the fact.

P1a records the deterministic core: ``create -> submit -> gates``. There is no
provider on this path, so no dispatch records appear here; the transport events
arrive with P1b.

AuthorityEffect: None. A trace is evidence about an execution, not a verdict on
one.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform as _platform
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from .trace_schema import (
    EVENT_RUN_SEALED,
    EVENT_RUN_STARTED,
    TRACE_SCHEMA_VERSION,
    SUPPORTED_TRACE_SCHEMA_VERSIONS,
    event_schema,
)


#: Whether an execution may reach a real provider at all.
RUN_MODE_DETERMINISTIC_FIXTURE = "deterministic_fixture"
RUN_MODE_LIVE = "live"

#: The strongest interruption a portable test suite can actually produce, and
#: therefore the ceiling on what any green durability result here is evidence
#: about. Recorded structurally rather than left in a docstring: a later, stronger
#: harness has to be able to tell these results from power-loss results by reading
#: the file, and prose in a module nobody opens is not a limitation anyone can
#: query.
CRASH_MODEL_ABRUPT_PROCESS_EXIT = "abrupt_process_exit_os__exit"
EVIDENCE_CEILING_PROCESS_CRASH = "process_crash_not_power_loss"


class RunMode(Enum):
    """Whether this execution may reach a real provider.

    Defined beside the trace rather than beside the fixture wiring because the
    trace is what has to record it. A run mode that lives only in a
    construction-time argument is a claim nothing can audit afterwards, and the
    claim that matters -- "no real provider was contacted" -- is exactly the one
    a reader of the file needs to check without trusting the writer.
    """

    DETERMINISTIC_FIXTURE = RUN_MODE_DETERMINISTIC_FIXTURE
    LIVE = RUN_MODE_LIVE


class RunModeRefusal(RuntimeError):
    """A model, provider and run mode combination that must not be admitted.

    Distinct from `TraceRefusal` (a durability refusal) and from the gateway's
    `ModelNotAllowed` (a gate refusal), so a report can name which of the three
    happened rather than reporting "it failed".
    """


def durability_scope(path: str | os.PathLike[str] | None = None) -> dict[str, str]:
    """What a durability result on this host is actually evidence about.

    Derived, never supplied. A free-form label can claim ``"linux-ci"`` from a
    Windows laptop, and a green fsync result carrying a lie about its host is
    worse than no result: it is a durability claim about a platform nobody
    tested. Everything here comes from the running interpreter.

    ``filesystem`` is best-effort and reports ``"unknown"`` rather than guessing
    -- fsync semantics differ enough between filesystems that a wrong answer
    would misdirect exactly the investigation this field exists to support.

    ``crash_model`` and ``evidence_ceiling`` record the limit of the interruption
    this estate can produce, so a green result is never read as a power-loss
    result by someone who only has the file.
    """
    scope = {
        "os": _platform.system() or "unknown",
        "os_release": _platform.release() or "unknown",
        "os_version": _platform.version() or "unknown",
        "machine": _platform.machine() or "unknown",
        "python": _platform.python_version(),
        "barrier_api": "os.fsync",
        "filesystem": "unknown",
        # What "durable" was actually tested against here. `os._exit` kills the
        # process without unwinding or flushing, which is the strongest cut a
        # portable suite can make -- and it is still not power loss, because
        # flushed data survives in the page cache whether or not `fsync` ran.
        # A result carrying this ceiling can be compared with a stronger
        # harness's; one that omits it reads as a stronger claim than it is.
        "crash_model": CRASH_MODEL_ABRUPT_PROCESS_EXIT,
        "evidence_ceiling": EVIDENCE_CEILING_PROCESS_CRASH,
    }
    if path is not None:
        scope["filesystem"] = _filesystem_of(path)
    return scope


def _filesystem_of(path: str | os.PathLike[str]) -> str:
    """Best-effort filesystem name for the volume holding ``path``."""
    target = Path(path)
    probe = target if target.exists() else target.parent
    if os.name == "nt":
        try:
            import ctypes

            buf = ctypes.create_unicode_buffer(256)
            drive = os.path.splitdrive(os.path.abspath(probe))[0]
            if drive and ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
                ctypes.c_wchar_p(drive + "\\"),
                None,
                0,
                None,
                None,
                None,
                buf,
                ctypes.sizeof(buf),
            ):
                return buf.value or "unknown"
        except Exception:  # pragma: no cover - platform probing is advisory
            return "unknown"
        return "unknown"
    try:  # pragma: no cover - exercised on POSIX hosts
        import subprocess

        out = subprocess.run(
            ["stat", "-f", "-c", "%T", str(probe)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() or "unknown"
    except Exception:  # pragma: no cover
        return "unknown"


#: fsync after every record. Mandatory for any live or irreversible call.
DURABILITY_FSYNC_LIVE = "fsync_live"
#: Buffered writes. Admissible only when the whole execution is replayable from
#: a recorded cassette, so a lost tail costs nothing that cannot be regenerated.
DURABILITY_BUFFERED_REPLAY = "buffered_replay"

DURABILITY_MODES = (DURABILITY_FSYNC_LIVE, DURABILITY_BUFFERED_REPLAY)

# ``EVENT_RUN_STARTED``, ``EVENT_RUN_SEALED`` and ``TRACE_SCHEMA_VERSION`` are
# imported from ``trace_schema`` and re-exported here, which is where callers have
# always found them. The format owns the names; this module owns the file.

#: Derived statuses. Neither is ever written into the file by the producer.
STATUS_BOUNDED_RUN_COMPLETE = "BOUNDED_RUN_COMPLETE"
STATUS_INCOMPLETE = "INCOMPLETE"

#: Genesis link for the first record's ``prev_sha256``.
CHAIN_GENESIS = "0" * 64

#: Exactly the keys every record envelope carries. Compared by equality rather
#: than containment: an extra top-level key is a record this writer did not
#: produce, and admitting it would mean the reader cannot say what it is holding.
ENVELOPE_KEYS = frozenset({"index", "event", "prev_sha256", "payload", "sha256"})

_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


class TraceRefusal(RuntimeError):
    """A trace could not be opened or extended under its declared contract."""


def coerce_run_mode(
    run_mode: "RunMode | str | None", *, live_transport: bool
) -> RunMode:
    """Resolve a declared run mode to a `RunMode`, or refuse it.

    Public because every caller that accepts a run mode has to apply exactly this
    rule. A type annotation is not a check: `mode is RunMode.LIVE` and
    `mode is RunMode.DETERMINISTIC_FIXTURE` are *both* false for the string
    `"deterministic_fixture"`, so an annotated-but-unchecked parameter silently
    disabled every confinement branch that depended on it. Anything that takes a
    mode from outside runs it through here first.

    A foreign `RunMode` -- a same-named enum from another module identity, which
    this estate produces -- is refused rather than accepted by value. Two enums
    that mean the same thing are still two things, and admitting one would put the
    identity comparisons back where they started.

    Defaulting is derived rather than fixed: a constant default would be a
    standing claim about every trace that never sets the field, and half of those
    claims would be wrong in the dangerous direction.
    """
    if run_mode is None:
        return RunMode.LIVE if live_transport else RunMode.DETERMINISTIC_FIXTURE
    if isinstance(run_mode, RunMode):
        return run_mode
    if isinstance(run_mode, str) and not isinstance(run_mode, Enum):
        try:
            return RunMode(run_mode)
        except ValueError:
            pass
    raise TraceRefusal(
        f"run mode {run_mode!r} is not a RunMode; expected one of "
        f"{tuple(m.value for m in RunMode)} or the enum member itself"
    )


def require_run_mode(run_mode: "RunMode | str") -> RunMode:
    """`coerce_run_mode` for callers where a mode is mandatory.

    Separate from `coerce_run_mode` because the two defaults are opposites and
    silently sharing one would be the dangerous kind of convenience: the trace
    may legitimately derive a mode it was not given, but a gateway that was not
    told which mode it is running under must refuse, not assume the safe-looking
    one. Assuming `DETERMINISTIC_FIXTURE` for `None` would mark a live gateway as
    a fixture, which is the false testimony the whole run-mode field exists to
    prevent.
    """
    if run_mode is None:
        raise TraceRefusal(
            "a run mode is required here and was not supplied; "
            f"expected one of {tuple(m.value for m in RunMode)}"
        )
    return coerce_run_mode(run_mode, live_transport=False)


def _canonical_line(record: Mapping[str, Any]) -> bytes:
    """Sorted-key, compact, ASCII-safe JSON.

    ``ensure_ascii=True`` on purpose: these files are read on Windows consoles
    whose cp1252 default turns a stray non-ASCII byte into a crash rather than a
    mojibake, and a trace that cannot be printed is a trace that will not be
    read.
    """
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


@dataclass(frozen=True)
class TraceRecord:
    """One parsed line, with its position and link already checked."""

    index: int
    event: str
    payload: Mapping[str, Any]
    sha256: str
    prev_sha256: str


class ExecutionTrace:
    """Append-only writer for a single execution's JSONL file.

    One instance owns one file. Reusing a path is refused rather than appended
    to: two executions in one file would share a hash chain and become
    inseparable, and "one file per execution" is the contract the harness reads
    against.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        execution_id: str,
        durability: str,
        live_transport: bool = False,
        run_mode: RunMode | str | None = None,
    ) -> None:
        if durability not in DURABILITY_MODES:
            raise TraceRefusal(
                f"unknown durability mode {durability!r}; expected one of {DURABILITY_MODES}"
            )
        mode = coerce_run_mode(run_mode, live_transport=live_transport)
        # Run mode and transport must agree, and the contradiction is refused
        # rather than reconciled. A deterministic-fixture execution recorded with
        # `live_transport=True` is the exact false testimony this field exists to
        # stop: the file reads as a paid provider call while a scripted transport
        # supplied every byte, and nothing downstream can tell the difference.
        # Durability stays an orthogonal choice -- a fixture execution may
        # legitimately select `fsync_live` to exercise the barriers without
        # claiming a provider was ever contacted.
        if (mode is RunMode.LIVE) != live_transport:
            raise TraceRefusal(
                f"run_mode {mode.value!r} contradicts live_transport={live_transport}; "
                "a scripted execution may not be recorded as live, and a live one "
                "may not be recorded as scripted"
            )
        # Refused here, at RunStarted, and not later: once a live call has been
        # dispatched under buffered durability the paid bytes are already at
        # risk, and no downstream check can un-spend them.
        if live_transport and durability != DURABILITY_FSYNC_LIVE:
            raise TraceRefusal(
                "live transport requires fsync_live durability; "
                "buffered_replay is admissible only for fully-recorded cassette execution"
            )
        self._path = Path(path)
        if self._path.exists():
            raise TraceRefusal(
                f"{self._path} already exists; one file per execution, never appended to"
            )
        self._execution_id = execution_id
        self._durability = durability
        self._live_transport = live_transport
        self._run_mode = mode
        self._schema_version = TRACE_SCHEMA_VERSION
        self._scope = durability_scope(self._path)
        self._prev = CHAIN_GENESIS
        self._sealed = False
        self._count = 0

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self._path.open("xb")
        # The ``RunStarted`` digest is the chain's first link and nothing else.
        # It was briefly used as an execution-scoped identity; it is not one. It
        # covers the derived durability scope -- OS, OS version, interpreter
        # version, filesystem -- so the same declared execution replayed after a
        # host or interpreter change hashes differently, and anything bound to it
        # stops being replay-stable across platforms. Attempt identity binds the
        # declared inputs instead; see ``DurableDispatchTransport._attempt_id``.
        self.record(
            EVENT_RUN_STARTED,
            schema_version=TRACE_SCHEMA_VERSION,
            execution_id=execution_id,
            durability=durability,
            live_transport=live_transport,
            # Recorded beside `live_transport` and cross-checked against it, so
            # the file states its confinement in its own words rather than
            # leaving a reader to infer it from a boolean.
            run_mode=mode.value,
            # Derived from the running interpreter, never supplied. A durability
            # result is evidence about the host that produced it and nothing
            # else, and a caller-supplied label can name a host it never touched.
            durability_scope=self._scope,
        )

    @property
    def path(self) -> Path:
        return self._path

    @property
    def sealed(self) -> bool:
        return self._sealed

    @property
    def durability(self) -> str:
        """Exposed so a dispatcher can refuse to make a live call against a
        buffered trace. The check belongs to whoever is about to spend money,
        and it can only make it if it can read the mode."""
        return self._durability

    @property
    def live_transport(self) -> bool:
        return self._live_transport

    @property
    def execution_id(self) -> str:
        return self._execution_id

    @property
    def terminal_digest(self) -> str:
        """The digest of the most recent record: the chain's head right now.

        Exposed over the private link field because a caller that has to reach
        into ``_prev`` will instead recompute the digest itself, and a second
        implementation of "the head of this chain" is a second thing that can
        disagree with the file.

        Never ``CHAIN_GENESIS`` on a live instance -- ``RunStarted`` is written
        by the constructor, so the head always names a record that exists. After
        ``seal`` this is the terminal digest of a complete file, and it is the
        value ``verify_trace`` expects to be handed back.
        """
        return self._prev

    @property
    def run_mode(self) -> RunMode:
        """Whether this execution may reach a real provider.

        Exposed so a dispatcher can refuse to record a live call against a trace
        that declared itself scripted. The check belongs to whoever is about to
        write the record, and it can only make it if it can read the mode.
        """
        return self._run_mode

    def record(self, event: str, **fields: Any) -> str:
        """Append one linked record. Returns its digest.

        The event and its payload are checked against the declared format before
        anything is written. Checking only on the way in would let a writer
        produce records its own reader refuses -- a file that is corrupt the
        moment it is created, discovered at recovery time when the run it
        describes is already over.
        """
        if self._sealed:
            raise TraceRefusal("trace is sealed; no further records may be appended")
        schema = event_schema(event, self._schema_version)
        if schema is None:
            raise TraceRefusal(
                f"event {event!r} is not declared in {TRACE_SCHEMA_VERSION}; "
                "register it in trace_schema before writing it"
            )
        problems = schema.violations(fields)
        if problems:
            raise TraceRefusal(
                f"{event} payload is not admissible: " + "; ".join(problems)
            )
        body = {
            "index": self._count,
            "event": event,
            "prev_sha256": self._prev,
            "payload": fields,
        }
        digest = hashlib.sha256(_canonical_line(body)).hexdigest()
        line = _canonical_line({**body, "sha256": digest})
        self._handle.write(line + b"\n")
        self._handle.flush()
        if self._durability == DURABILITY_FSYNC_LIVE:
            os.fsync(self._handle.fileno())
        self._prev = digest
        self._count += 1
        return digest

    def seal(self, terminal: str, **fields: Any) -> str:
        """Write the terminal record. After this the file is complete.

        Returns the terminal digest -- the one value a caller can carry out of a
        finished run and check the file against later. It was computed and thrown
        away before, which made every downstream anchoring attempt start by
        re-deriving a number the writer already held.

        Returning it anchors nothing. It is the attachment point: where the
        digest is kept, and whether that place is beyond the reach of whoever
        wrote the trace, is the part this module cannot supply.
        """
        digest = self.record(EVENT_RUN_SEALED, terminal=terminal, **fields)
        self._sealed = True
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        return digest

    def abandon(self) -> None:
        """Close without sealing. The trace will derive ``INCOMPLETE``.

        Provided so a caller can drop a run deliberately and have it read the
        same as a crash, rather than inventing a third state that means "we meant
        to stop". Whether the stop was intended is recorded in the payload of
        whatever record preceded it, not in the derived status.
        """
        if not self._handle.closed:
            self._handle.flush()
            self._handle.close()

    def __enter__(self) -> ExecutionTrace:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # An exception leaves the trace unsealed on purpose: a run that raised
        # did not complete, and the file should say so.
        if not self._sealed:
            self.abandon()


@dataclass(frozen=True)
class TraceScan:
    """The verified prefix of a trace, plus whether anything followed it.

    ``clean_eof`` is separate from "the last record is a seal" and both are
    required for completion. A file can carry a perfectly valid ``RunSealed``
    record and then trailing bytes -- a partially-overwritten older trace, a
    concatenation, a truncated append from a second writer. Returning only the
    verified prefix would report that file as complete while silently discarding
    evidence that something else happened to it.
    """

    records: list[TraceRecord]
    clean_eof: bool
    schema_version: str | None = None


def scan_trace(path: str | os.PathLike[str]) -> TraceScan:
    """Parse a trace, verifying the hash chain, and report whether it ended clean.

    Stops at the first line that fails to parse or fails its link. A partial
    result is the normal outcome for a crashed run and is not an error --
    ``derive_status`` reads the truncation, which is what it exists to detect.
    """
    records: list[TraceRecord] = []
    expected_prev = CHAIN_GENESIS
    schema_version: str | None = None
    clean = True
    lines = list(_iter_lines(path))
    for index, raw in enumerate(lines):
        record = _admit(
            raw,
            index=index,
            expected_prev=expected_prev,
            schema_version=schema_version,
        )
        if record is None:
            clean = False
            break
        records.append(record)
        expected_prev = record.sha256
        if index == 0:
            declared = record.payload.get("schema_version")
            if type(declared) is str:
                schema_version = declared

    # A trace that does not end with a newline had its final write torn, even if
    # every complete line before it verified.
    if clean and records:
        try:
            tail = Path(path).read_bytes()[-1:]
        except OSError:  # pragma: no cover - unreadable file
            tail = b""
        if tail != b"\n":
            clean = False
    return TraceScan(records=records, clean_eof=clean, schema_version=schema_version)


def terminal_digest(scan: TraceScan | Sequence[TraceRecord]) -> str | None:
    """The digest of the last **verified** record, or ``None`` if there is none.

    Named because callers were reaching into ``scan.records[-1].sha256`` by
    index, which is three decisions -- that a last record exists, that its digest
    is the chain head, and that an unverified tail does not change the answer --
    spelled as one subscript.

    "Verified prefix", not "the file". On a scan whose ``clean_eof`` is false
    this is the head of the part that parsed, and the bytes after it are exactly
    the evidence that the file's own terminal digest is something else. Callers
    for whom that distinction matters should use ``verify_trace``, which refuses
    an unclean file rather than reporting a prefix digest as though it stood for
    the whole.
    """
    records = scan.records if isinstance(scan, TraceScan) else list(scan)
    return records[-1].sha256 if records else None


def verify_trace(
    path: str | os.PathLike[str], *, expected_terminal_digest: str
) -> TraceScan:
    """Scan ``path`` and refuse it unless it is the run that digest came from.

    The verifier half of ``seal``'s return value. ``read_status`` answers "is
    this file a complete, internally consistent trace"; a wholesale re-signed
    rewrite answers yes, because every link in a rebuilt chain verifies. This
    answers the narrower question the chain cannot: "is this the *same* file the
    digest was taken from". A rewrite changes the terminal digest, and nothing
    the forger can do to the file changes the value being compared against.

    Refuses in three distinguishable ways, in this order:

    * The expected digest is not a digest. Checked first and deliberately: there
      is no value of this argument -- not ``None``, not ``""`` -- that means
      "skip the comparison". A verifier with an off switch is not one.
    * The file does not derive ``BOUNDED_RUN_COMPLETE``. A digest cannot vouch
      for a file the reader could not verify to a clean end, and admitting the
      verified prefix of a file with trailing bytes would make this check weaker
      than ``read_status``, which already refuses exactly that.
    * The terminal digest differs. This is the anchoring comparison.

    **This function anchors nothing.** It moves the trust from the file to
    wherever the caller keeps ``expected_terminal_digest``; a value stored beside
    the trace is re-signable by the same actor, and a forged trace verifies
    perfectly against its own digest. Returning the scan rather than a bare
    ``True`` keeps callers from scanning twice and from being tempted to treat
    the boolean as a verdict about the run.
    """
    if not isinstance(expected_terminal_digest, str) or not _HEX64.match(
        expected_terminal_digest
    ):
        raise TraceRefusal(
            f"expected_terminal_digest {expected_terminal_digest!r} is not a "
            "64-character lowercase hex digest; no value of this argument means "
            "'do not check'"
        )
    scan = scan_trace(path)
    status = derive_status(scan)
    if status != STATUS_BOUNDED_RUN_COMPLETE:
        raise TraceRefusal(
            f"trace derives {status}; a terminal digest cannot vouch for a file "
            f"the reader could not verify to a clean end ({path})"
        )
    found = terminal_digest(scan)
    if found != expected_terminal_digest:
        raise TraceRefusal(
            f"terminal digest {found} is not the expected "
            f"{expected_terminal_digest}; this is not the run that digest came "
            f"from ({path})"
        )
    return scan


def _admit(
    raw: bytes,
    *,
    index: int,
    expected_prev: str,
    schema_version: str | None,
) -> TraceRecord | None:
    """One line, admitted under its RunStarted-declared format, or ``None``.

    Every check here answers a way a file can chain perfectly and still be
    meaningless. In order:

    * **Blank line.** Neither a record nor a terminator. Dropping empty lines let
      ``RunSealed\n\n`` derive complete.
    * **Envelope shape.** Exactly five keys, with `index` an `int` that matches
      its position, both digests 64 lowercase hex, and `payload` an object. The
      payload check is load-bearing rather than defensive: recovery calls
      ``.get()`` on it, and a JSON `null` or array there crashes the reader that
      was sent to explain a crash.
    * **The chain.** Digest over the body, and the link to the record before.
    * **Canonical bytes.** The line must equal the bytes this writer would
      produce for that record. Hashing the *decoded* body meant duplicate JSON
      properties, key order and whitespace were normalised away before the digest
      was taken -- so two different files could carry the same chain, and a
      re-encoded trace verified as though untouched. This is the one check that
      makes the digest a statement about the bytes on disk.
    * **The format.** The event must be declared, its payload must satisfy the
      declared fields and types, `RunStarted` must be first and only first, and
      its `schema_version` must be the version this reader implements. A trace
      written by a future format is refused rather than half-understood.
    """
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None  # torn final write
    if not isinstance(parsed, dict) or set(parsed) != ENVELOPE_KEYS:
        return None

    claimed = parsed["sha256"]
    prev = parsed["prev_sha256"]
    if not isinstance(claimed, str) or not _HEX64.match(claimed):
        return None
    if not isinstance(prev, str) or not _HEX64.match(prev) or prev != expected_prev:
        return None
    position = parsed["index"]
    if type(position) is not int or position != index:
        return None
    event = parsed["event"]
    if not isinstance(event, str):
        return None
    payload = parsed["payload"]
    if not isinstance(payload, dict):
        return None

    body = {k: v for k, v in parsed.items() if k != "sha256"}
    if hashlib.sha256(_canonical_line(body)).hexdigest() != claimed:
        return None
    if raw != _canonical_line({**body, "sha256": claimed}):
        return None

    declared_version = payload.get("schema_version") if index == 0 else schema_version
    if (
        type(declared_version) is not str
        or declared_version not in SUPPORTED_TRACE_SCHEMA_VERSIONS
    ):
        return None
    schema = event_schema(event, declared_version)
    if schema is None or schema.violations(payload):
        return None
    if (event == EVENT_RUN_STARTED) != (index == 0):
        # `RunStarted` opens the file and appears nowhere else. A second one is a
        # concatenation of two executions, which the one-file-per-execution
        # contract exists to keep out.
        return None
    if index == 0 and payload.get("schema_version") != declared_version:
        return None

    return TraceRecord(
        index=index,
        event=event,
        payload=payload,
        sha256=claimed,
        prev_sha256=prev,
    )


def read_records(path: str | os.PathLike[str]) -> list[TraceRecord]:
    """The verified prefix only. Prefer ``scan_trace`` where completion matters."""
    return scan_trace(path).records


def _iter_lines(path: str | os.PathLike[str]) -> Iterator[bytes]:
    """Every physical line, with only its own terminating newline removed.

    Empty lines are yielded rather than dropped, and the caller refuses them.
    Exactly one newline terminates each record; a second one is trailing content,
    and a scanner that quietly absorbs it cannot report the file it was handed.
    """
    with Path(path).open("rb") as handle:
        for line in handle:
            yield line[:-1] if line.endswith(b"\n") else line


def derive_status(scan: TraceScan | Sequence[TraceRecord]) -> str:
    """Derive the run status from the file. Never read from a producer field.

    A run is ``BOUNDED_RUN_COMPLETE`` only when the chain verifies from genesis,
    opens with ``RunStarted``, closes with ``RunSealed``, **and parsing reached a
    clean end of file**. Everything else -- empty, unsealed, truncated, tampered,
    sealed in the wrong position, or sealed with garbage after it -- is
    ``INCOMPLETE``. There is deliberately no third status: "probably fine" is the
    reading this function exists to make unavailable.

    Accepting a bare sequence is a convenience for callers that only hold
    records; it cannot express clean EOF, so it is treated as unverified and can
    never return complete. Pass a ``TraceScan`` when the answer matters.
    """
    if isinstance(scan, TraceScan):
        records, clean = scan.records, scan.clean_eof
    else:
        records, clean = list(scan), False
    if not clean:
        return STATUS_INCOMPLETE
    if not records:
        return STATUS_INCOMPLETE
    if records[0].event != EVENT_RUN_STARTED:
        return STATUS_INCOMPLETE
    if records[-1].event != EVENT_RUN_SEALED:
        return STATUS_INCOMPLETE
    if any(r.event == EVENT_RUN_SEALED for r in records[:-1]):
        return STATUS_INCOMPLETE
    return STATUS_BOUNDED_RUN_COMPLETE


def read_status(path: str | os.PathLike[str]) -> str:
    """Convenience: scan and derive in one call."""
    return derive_status(scan_trace(path))
