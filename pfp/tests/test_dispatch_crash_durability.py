"""Process-termination durability, in a separate process, verified by a third.

The earlier durability tests proved ordering and same-process visibility. They
did not prove durability: closed-and-flushed data stays readable through the page
cache, so every one of them would still pass with the `fsync` calls removed.

These kill a real child at each barrier cut with `os._exit(1)` -- no unwinding,
no `atexit`, no flush -- and then read the wreckage from a fresh process.

**What that does and does not establish**, stated plainly so the result is not
read as more than it is:

*Established.* Barrier ordering survives abrupt process death; the recovery
derivation runs against a file written by a process that no longer exists; an
attempt cut after barrier 1 recovers as `STATUS_UNKNOWN` and never as "never
dispatched"; a cut inside barrier 2 leaves orphan bytes rather than a trace
asserting bytes that are absent.

*Not established.* This does not test `fsync`. Process termination is not power
loss -- data written and flushed survives in the OS page cache regardless of
whether `fsync` was called, so these tests would still pass with the `fsync`
calls removed. Proving `fsync` requires power interruption or a fault-injecting
filesystem, neither of which is reachable from a portable test suite. The
durability *scope* recorded in each trace is what a later, stronger harness would
need to interpret these results, and it is asserted below for that reason.

The durability *scope* under which these results hold is recorded by the trace
itself and asserted below, because a green crash test on one host says nothing
about another. Windows is the development host and is covered here; Linux is
complementary evidence and runs wherever this suite runs.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import pytest

from operating_system.adapters.security import (
    FixtureOnlyAeadProtector,
)
from operating_system.infrastructure import EncryptedArtifactCas
from pfp.infrastructure.trace import (
    CRASH_MODEL_ABRUPT_PROCESS_EXIT,
    DISPATCH_COMPLETE,
    DISPATCH_EVIDENCE_MISSING,
    DISPATCH_STATUS_UNKNOWN,
    EVENT_DISPATCH_INTENT_DURABLE,
    EVENT_RESPONSE_DURABLE,
    EVIDENCE_CEILING_PROCESS_CRASH,
    RUN_MODE_DETERMINISTIC_FIXTURE,
    STATUS_BOUNDED_RUN_COMPLETE,
    STATUS_INCOMPLETE,
    derive_dispatch_outcomes,
    derive_status,
    scan_trace,
)

CHILD = Path(__file__).with_name("crash_child.py")
FIXTURE_KEY = b"symbol-game-provider-dispatch-test-key-v1"


def _artifact_store(trace_path):
    return EncryptedArtifactCas(
        trace_path.parent / "encrypted-artifacts",
        FixtureOnlyAeadProtector(FIXTURE_KEY),
    )


def _crash(tmp_path, cut):
    """Run the child to the requested cut and return its trace path.

    Each cut gets its own directory. The child declares one `execution_id`, so a
    shared artifact store would make the second run collide on attempt id -- which the
    exclusive-creation guard correctly refuses. Isolating the store keeps this
    helper measuring crashes rather than re-measuring that guard.
    """
    directory = tmp_path / cut
    directory.mkdir(exist_ok=True)
    trace_path = directory / f"{cut}.jsonl"
    result = subprocess.run(
        [sys.executable, str(CHILD), cut, str(trace_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return trace_path, result


def _outcomes(trace_path):
    """Recovery from a *fresh* process's point of view: file only, no memory."""
    scan = scan_trace(trace_path)
    return scan, derive_dispatch_outcomes(
        scan.records, artifact_store=_artifact_store(trace_path)
    )


# --------------------------------------------------------------------------
# Control -- the child can complete
# --------------------------------------------------------------------------


def test_a_clean_child_run_seals_and_recovers_complete(tmp_path):
    """Without this, every crash assertion below could pass on a broken child."""
    trace_path, result = _crash(tmp_path, "clean")
    assert result.returncode == 0, result.stderr

    scan, outcomes = _outcomes(trace_path)
    assert derive_status(scan) == STATUS_BOUNDED_RUN_COMPLETE
    assert [o.status for o in outcomes] == [DISPATCH_COMPLETE]
    assert outcomes[0].retry_permitted is False


# --------------------------------------------------------------------------
# Cut 1 -- terminated after durable intent, before any response
# --------------------------------------------------------------------------


def test_termination_after_intent_recovers_as_unknown(tmp_path):
    """The reason barrier 1 exists.

    A process killed here may or may not have reached the network. Recovery must
    read *unknown*, never "never dispatched" -- the latter licenses a retry that
    could double a real charge.
    """
    trace_path, result = _crash(tmp_path, "after_intent")
    assert result.returncode != 0, "the child must have died"
    assert trace_path.exists(), "the intent record must have survived the kill"

    scan, outcomes = _outcomes(trace_path)
    events = [r.event for r in scan.records]
    assert EVENT_DISPATCH_INTENT_DURABLE in events, "barrier 1 must be durable"
    assert EVENT_RESPONSE_DURABLE not in events

    assert derive_status(scan) == STATUS_INCOMPLETE
    assert [o.status for o in outcomes] == [DISPATCH_STATUS_UNKNOWN]
    assert outcomes[0].retry_permitted is False
    assert outcomes[0].raw_response_sha256 is None


# --------------------------------------------------------------------------
# Cut 2 -- terminated after encrypted CAS commit, before the record naming it
# --------------------------------------------------------------------------


def test_termination_after_encrypted_cas_leaves_orphan_envelope_not_false_claim(
    tmp_path,
):
    """The window barrier-2 ordering exists to make safe.

    The encrypted envelope is committed before the record that names it, so a
    kill in between leaves the envelope on disk with no trace record pointing at
    it. Recovery reads `STATUS_UNKNOWN` -- conservative and hand-recoverable.

    Reversing the order would produce the opposite and much worse wreckage: a
    trace asserting durable evidence that does not exist.
    """
    trace_path, result = _crash(tmp_path, "after_encrypted_cas")
    assert result.returncode != 0, "the child must have died"

    scan, outcomes = _outcomes(trace_path)
    events = [r.event for r in scan.records]
    assert EVENT_DISPATCH_INTENT_DURABLE in events
    assert EVENT_RESPONSE_DURABLE not in events, "the naming record must be absent"

    # The orphan is really on disk -- that is the point of committing it first.
    encrypted_files = list(
        (trace_path.parent / "encrypted-artifacts").rglob("*.oeos-envelope")
    )
    assert encrypted_files, "the encrypted envelope must have survived the kill"
    assert b"crash-test reply" not in encrypted_files[0].read_bytes()

    assert [o.status for o in outcomes] == [DISPATCH_STATUS_UNKNOWN]
    assert outcomes[0].retry_permitted is False


# --------------------------------------------------------------------------
# A fresh process reads only what survived
# --------------------------------------------------------------------------


def test_recovery_runs_in_a_process_that_never_saw_the_write(tmp_path):
    """Recovery must depend on the file, not on surviving in-process state.

    The child wrote and died; this process has no shared memory with it. Reading
    the durable prefix here is what makes the recovery claim about durability
    rather than about object lifetime.
    """
    trace_path, _ = _crash(tmp_path, "after_intent")
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys,json;"
                f"sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r});"
                "from pfp.infrastructure.trace import "
                "scan_trace, derive_dispatch_outcomes, derive_status;"
                f"s = scan_trace({str(trace_path)!r});"
                "o = derive_dispatch_outcomes(s.records);"
                "print(json.dumps({'status': derive_status(s),"
                " 'events': [r.event for r in s.records],"
                " 'outcomes': [x.status for x in o]}))"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert probe.returncode == 0, probe.stderr
    seen = json.loads(probe.stdout)
    assert seen["status"] == STATUS_INCOMPLETE
    assert EVENT_DISPATCH_INTENT_DURABLE in seen["events"]
    assert seen["outcomes"] == [DISPATCH_STATUS_UNKNOWN]


# --------------------------------------------------------------------------
# The scope these results are evidence about
# --------------------------------------------------------------------------


def test_the_trace_records_the_scope_these_results_hold_for(tmp_path):
    """A durability result is evidence about one host, and must say which.

    Derived from the running interpreter, never supplied -- a caller-provided
    label can name a platform it never touched.

    The ceiling is recorded alongside it. Everything this file establishes was
    established under `os._exit`, which is process termination and not power
    loss; the limitation is stated in this module's docstring, and a docstring is
    not something a later harness comparing results can read.
    """
    trace_path, _ = _crash(tmp_path, "clean")
    started = scan_trace(trace_path).records[0]
    scope = started.payload["durability_scope"]

    assert scope["os"] == platform.system()
    assert scope["os_version"] == platform.version()
    assert scope["barrier_api"] == "os.fsync"
    assert scope["python"] == platform.python_version()
    assert "filesystem" in scope
    assert scope["crash_model"] == CRASH_MODEL_ABRUPT_PROCESS_EXIT
    assert scope["evidence_ceiling"] == EVIDENCE_CEILING_PROCESS_CRASH


def test_the_child_does_not_record_its_scripted_call_as_live(tmp_path):
    """The crash matrix must not buy its barriers with a false provider claim.

    `fsync_live` durability is what these cuts interrupt, and it is available to
    a fixture execution without declaring `live_transport`. Asserted from a fresh
    process, against the file the dead child left behind.
    """
    trace_path, _ = _crash(tmp_path, "clean")
    started = scan_trace(trace_path).records[0].payload

    assert started["run_mode"] == RUN_MODE_DETERMINISTIC_FIXTURE
    assert started["live_transport"] is False
    assert started["durability"] == "fsync_live", "durability is orthogonal"


@pytest.mark.skipif(
    platform.system() != "Windows", reason="Windows is the development host"
)
def test_windows_is_covered_by_the_crash_matrix(tmp_path):
    """Named explicitly so the Windows result is visible in a report.

    The plan's durability requirement is platform-scoped; a green run on another
    OS is not evidence about the host where the work actually happens.
    """
    for cut, expected in (
        ("after_intent", DISPATCH_STATUS_UNKNOWN),
        ("after_encrypted_cas", DISPATCH_STATUS_UNKNOWN),
        ("clean", DISPATCH_COMPLETE),
    ):
        trace_path, _ = _crash(tmp_path, cut)
        _, outcomes = _outcomes(trace_path)
        assert [o.status for o in outcomes] == [expected], cut


def test_a_deleted_artifact_is_evidence_missing_not_complete(tmp_path):
    """Completion must require the artifact, not merely a record naming it."""
    trace_path, _ = _crash(tmp_path, "clean")
    for artifact in (trace_path.parent / "encrypted-artifacts").rglob(
        "*.oeos-envelope"
    ):
        artifact.unlink()

    _, outcomes = _outcomes(trace_path)
    assert [o.status for o in outcomes] == [DISPATCH_EVIDENCE_MISSING]
    assert outcomes[0].retry_permitted is False
