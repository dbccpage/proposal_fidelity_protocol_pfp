"""P1a: `create -> submit -> gates -> finalize`, recorded.

This is P0's regression instrumented, and that ordering is deliberate. The first
execution the harness records involves no provider, so two runs of the same
fixture must agree exactly. Any disagreement is a defect in the recorder rather
than sampling noise from a model, which is the only condition under which the
recorder can be trusted to measure one.

The trace records derived identities -- packet id, candidate id, patch digest,
gate dispositions -- and never patch bytes. A trace is read far more often than
an execution is run, and a file carrying payloads gets treated as an artifact
store.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain import CanonicalizationError
from omega_engine_pfp.infrastructure.trace import (
    DURABILITY_FSYNC_LIVE,
    EVENT_CANDIDATE_SUBMITTED,
    EVENT_GATES_EVALUATED,
    EVENT_PROPOSAL_CREATED,
    EVENT_RUN_FINALIZED,
    EVENT_RUN_SEALED,
    EVENT_RUN_STARTED,
    EVENT_STAGE_REFUSED,
    STATUS_BOUNDED_RUN_COMPLETE,
    STATUS_INCOMPLETE,
    TERMINAL_PATH_COMPLETE,
    ExecutionTrace,
    TracedCodeChangeController,
    read_records,
    read_status,
)
from omega_engine_pfp.use_cases.code_change import BoundCandidate

OWNED = "src/x.py"
PROTECTED = "README.md"
FIXTURE_PATCH = f"--- a/{OWNED}\n+++ b/{OWNED}\n@@ -0,0 +1,1 @@\n+x = 1\n"


def _run(tmp_path, name="run", patch_text=FIXTURE_PATCH):
    """One complete recorded execution over the deterministic path."""
    trace = ExecutionTrace(
        tmp_path / f"{name}.jsonl",
        execution_id=name,
        durability=DURABILITY_FSYNC_LIVE,
    )
    traced = TracedCodeChangeController(trace)
    session = traced.create_proposal(
        task_id="task-p1a",
        objective="instrumented regression",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    session, bound = traced.submit_patch(
        session=session, producer_id="fixture-worker", patch_text=patch_text
    )
    receipts = traced.evaluate_patch_gates(session=session, bound=bound)
    run_root = traced.finalize_run(
        session=session, bound=bound, gate_receipts=receipts
    )
    trace.seal(TERMINAL_PATH_COMPLETE)
    return trace, session, bound, run_root


def _events(path):
    return [r.event for r in read_records(path)]


def _payload(path, event):
    return next(r.payload for r in read_records(path) if r.event == event)


# --------------------------------------------------------------------------
# The recorded shape
# --------------------------------------------------------------------------


def test_a_full_run_records_every_stage_in_order(tmp_path):
    trace, _, _, _ = _run(tmp_path)
    assert _events(trace.path) == [
        EVENT_RUN_STARTED,
        EVENT_PROPOSAL_CREATED,
        EVENT_CANDIDATE_SUBMITTED,
        EVENT_GATES_EVALUATED,
        EVENT_RUN_FINALIZED,
        EVENT_RUN_SEALED,
    ]
    assert read_status(trace.path) == STATUS_BOUNDED_RUN_COMPLETE


def test_the_recorded_identities_match_the_returned_objects(tmp_path):
    """The trace must describe *this* execution, not a plausible one."""
    trace, session, bound, run_root = _run(tmp_path)

    created = _payload(trace.path, EVENT_PROPOSAL_CREATED)
    assert created["packet_id"] == session.packet_id
    assert created["task_id"] == session.task_id
    assert created["owned_paths"] == [OWNED]

    submitted = _payload(trace.path, EVENT_CANDIDATE_SUBMITTED)
    assert submitted["candidate_id"] == bound.candidate.candidate_id
    assert submitted["patch_id"] == bound.patch.patch_id
    assert submitted["patch_sha256"] == bound.patch.patch_sha256

    finalized = _payload(trace.path, EVENT_RUN_FINALIZED)
    assert finalized["terminal_status"] == run_root.terminal_status
    assert finalized["candidate_ids"] == list(run_root.candidate_ids)


def test_the_trace_carries_no_patch_bytes(tmp_path):
    """Digests, not payloads. A trace is not an artifact store."""
    trace, _, _, _ = _run(tmp_path)
    raw = trace.path.read_bytes()
    assert b"x = 1" not in raw
    assert b"@@" not in raw


def test_the_recorded_terminal_is_the_domains_not_the_harnesss(tmp_path):
    """`DeclaredUnverified` with the budget obstruction standing.

    The recorder must not upgrade what the evaluator concluded. If this ever
    reads as a positive terminal, either the domain changed or the recorder
    started editorialising -- both worth failing over.
    """
    trace, _, _, _ = _run(tmp_path)
    finalized = _payload(trace.path, EVENT_RUN_FINALIZED)
    assert finalized["terminal_status"] == "DeclaredUnverified"
    assert "BUDGET_HOST_STATE_ABSENT" in finalized["open_obstruction_ids"]
    assert finalized["refusals"] == []


def test_no_producer_claim_is_recorded_on_this_path(tmp_path):
    """P0 admits no claims, so the trace must record their absence as absence.

    `None` is not `False`. When typed claims land, this is the field that gains
    provenance, and this assertion is what will need updating -- deliberately, by
    someone who has read why it was `None`.
    """
    trace, _, _, _ = _run(tmp_path)
    submitted = _payload(trace.path, EVENT_CANDIDATE_SUBMITTED)
    assert submitted["model_claimed_valid"] is None

    gates = _payload(trace.path, EVENT_GATES_EVALUATED)["gates"]
    assert all(g["model_claimed_passed"] is None for g in gates)
    assert all(g["disposition"] == "PASS" for g in gates)


# --------------------------------------------------------------------------
# Determinism -- the reason P1a precedes any provider
# --------------------------------------------------------------------------


def test_two_runs_of_one_fixture_record_identical_identities(tmp_path):
    """No model on this path, so disagreement can only be a recorder defect.

    Execution id and file name differ; every derived identity must not.
    """
    first, _, _, _ = _run(tmp_path, name="a")
    second, _, _, _ = _run(tmp_path, name="b")

    def identities(path):
        return [
            {k: v for k, v in r.payload.items() if k not in ("execution_id",)}
            for r in read_records(path)
            if r.event not in (EVENT_RUN_STARTED,)
        ]

    assert identities(first.path) == identities(second.path)


def test_a_different_patch_yields_a_different_recorded_identity(tmp_path):
    """Negative control: a recorder emitting constants would pass the test above."""
    first, _, _, _ = _run(tmp_path, name="p1")
    second, _, _, _ = _run(
        tmp_path,
        name="p2",
        patch_text=f"--- a/{OWNED}\n+++ b/{OWNED}\n@@ -0,0 +1,1 @@\n+y = 2\n",
    )
    assert (
        _payload(first.path, EVENT_CANDIDATE_SUBMITTED)["patch_sha256"]
        != _payload(second.path, EVENT_CANDIDATE_SUBMITTED)["patch_sha256"]
    )


# --------------------------------------------------------------------------
# Refusals are recorded before they are raised
# --------------------------------------------------------------------------


def test_a_refused_stage_is_recorded_then_raised(tmp_path):
    """A refusal that escaped unrecorded would make the trace say the stage
    never happened. Refusing and not running are different facts."""
    trace = ExecutionTrace(
        tmp_path / "refused.jsonl",
        execution_id="refused",
        durability=DURABILITY_FSYNC_LIVE,
    )
    traced = TracedCodeChangeController(trace)
    session = traced.create_proposal(
        task_id="task-refuse",
        objective="will refuse",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    session, bound = traced.submit_patch(
        session=session, producer_id="fixture-worker", patch_text=FIXTURE_PATCH
    )
    swapped = BoundCandidate(
        candidate=bound.candidate, patch=bound.patch, patch_bytes=b"different\n"
    )

    with pytest.raises(CanonicalizationError):
        traced.evaluate_patch_gates(session=session, bound=swapped)
    trace.abandon()

    events = _events(trace.path)
    assert EVENT_STAGE_REFUSED in events
    assert EVENT_GATES_EVALUATED not in events

    refused = _payload(trace.path, EVENT_STAGE_REFUSED)
    assert refused["stage"] == "evaluate_patch_gates"
    assert "UNBOUND_EVALUATION_INPUT" in refused["refusal"]

    # A refused run is not a complete run.
    assert read_status(trace.path) == STATUS_INCOMPLETE
