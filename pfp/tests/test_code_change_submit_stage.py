"""`create -> submit` through the default controller wiring.

Two defects are pinned here, one behind the other.

The first was that `SubmitPatchCandidateUseCase.execute` was dead: it built
`CodeChangePatchArtifactV1` and `CandidateArtifactV1` with keyword arguments
neither type has, read `run_root.candidates` and `run_root.disposition` which do
not exist, and called `CodeChangeRunRootV1.create`, which is not a classmethod
of anything. It raised on every call.

The second, found only after the first was repaired, was that the repair still
ran a *parallel* lifecycle: stage 1 built a `CodeChangeRunRootV1` whose
`task_packet_id` was `sha256(task_id)`, while the canonical `packet_id` is a
digest over the payload. Every downstream id was therefore bound to a packet
identity the domain would never mint, and `evaluate_code_change_candidate` --
the function that actually produces a run root -- was unreachable from
application code. A hand-built candidate carrying a five-field payload was
rejected by `verify_code_change_run_root` as `CANDIDATE_PATCH_MISBIND`.

So these tests assert the shape of the lifecycle, not only that it runs:
stage 1 yields a `CodeChangeSession` holding the canonical envelope, and the
run root appears only as the *result* of evaluation (see
`test_code_change_gates_stage.py`).

Every binding asserted here is one the domain enforces: identity is derived
rather than supplied, touched paths are derived from the patch bytes rather
than declared by the producer, and the producer's claims are recorded as absent
rather than invented.

AuthorityEffect: execution_reachability_restored; authority_set_unchanged.
"""

from __future__ import annotations

import pytest

from pfp.controllers.code_change_controller import (
    CodeChangeController,
)
from pfp.domain import (
    PATCH_ENCODINGS,
    CodeChangeRunRootV1,
    PacketEnvelopeV2,
    thaw,
)
from pfp.use_cases.code_change import (
    PATCH_ENCODING_UNIFIED_DIFF,
    CodeChangeSession,
)

OWNED = "src/x.py"
PROTECTED = "README.md"
BASE_REVISION = "a" * 40


def _patch_for(path: str = OWNED, body: str = "def add(a, b):\n    return a + b\n") -> str:
    lines = "".join(f"+{line}\n" for line in body.splitlines())
    return f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(body.splitlines())} @@\n{lines}"


@pytest.fixture()
def controller() -> CodeChangeController:
    return CodeChangeController()


@pytest.fixture()
def session(controller: CodeChangeController) -> CodeChangeSession:
    return controller.create_proposal(
        task_id="task-001",
        objective="add a function",
        base_revision=BASE_REVISION,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )


# --------------------------------------------------------------------------
# Stage 1 produces a session, not a run root
# --------------------------------------------------------------------------


def test_proposal_yields_a_session_holding_the_canonical_envelope(session):
    """The architectural assertion: stage 1 has not evaluated anything.

    A `CodeChangeRunRootV1` here would be a record of an evaluation that has
    not happened, carrying a `terminal_status` no evaluator assigned. That was
    the previous shape and it is what made the canonical evaluator unreachable.
    """
    assert isinstance(session, CodeChangeSession)
    assert not isinstance(session, CodeChangeRunRootV1)
    assert isinstance(session.envelope, PacketEnvelopeV2)
    assert session.packet_id == session.envelope.packet_id


def test_the_packet_id_is_the_canonical_digest_not_a_hash_of_the_task_id():
    """The precise defect: `task_packet_id = sha256(task_id)`.

    Two proposals with the same `task_id` but different payloads must not share
    a packet identity, and one with the same payload under a different task id
    must still differ from a bare digest of that id. Asserting inequality with
    `sha256(task_id)` directly is what pins the old behaviour out.
    """
    import hashlib

    controller = CodeChangeController()
    common = dict(
        task_id="task-001",
        base_revision=BASE_REVISION,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    first = controller.create_proposal(objective="add a function", **common)
    second = controller.create_proposal(objective="a different objective", **common)

    stale = hashlib.sha256(b"task-001").hexdigest()
    assert first.packet_id != stale
    assert first.packet_id != second.packet_id, "packet identity must follow the payload"


def test_the_seeded_session_starts_empty_so_the_append_is_observable(session):
    """Anti-vacuity: an append to a non-empty ledger would prove less."""
    assert session.candidate_ids == ()
    assert session.patch_ids == ()


# --------------------------------------------------------------------------
# The path is alive
# --------------------------------------------------------------------------


def test_submit_traverses_the_default_controller_wiring(controller, session):
    """The headline regression. This raised `TypeError` before the repair."""
    updated, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(),
    )
    assert updated is not session, "the session must be a new immutable value"
    assert bound.candidate is not None and bound.patch is not None
    assert bound.patch_bytes == _patch_for().encode("utf-8")


# --------------------------------------------------------------------------
# Identity binding -- the ledger records a derived digest
# --------------------------------------------------------------------------


def test_the_ledger_records_the_candidates_canonical_identity(controller, session):
    updated, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(),
    )
    assert updated.candidate_ids == (bound.candidate.candidate_id,)
    assert len(bound.candidate.candidate_id) == 64
    int(bound.candidate.candidate_id, 16)  # raises if it is not hex


def test_two_different_patches_yield_different_candidate_identities(controller, session):
    """Negative control for the identity binding.

    Without this, an implementation returning a constant id would satisfy every
    other assertion in this file.
    """
    _, first = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(body="def add(a, b):\n    return a + b\n"),
    )
    _, second = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(body="def sub(a, b):\n    return a - b\n"),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id


# --------------------------------------------------------------------------
# Patch binding -- the payload is the whole patch, not a summary of it
# --------------------------------------------------------------------------


def test_the_candidate_payload_is_the_exact_patch_artifact(controller, session):
    """`attach_candidate` sets `payload = patch.to_dict()`.

    The earlier repair hand-built a five-field summary here, which
    `_assert_candidate_binds_patch` rejected because it reconstructs the patch
    from the payload via `from_dict`. Asserting full equality rather than a few
    keys is what prevents that summary from creeping back.
    """
    updated, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(),
    )
    assert thaw(bound.candidate.payload) == bound.patch.to_dict()
    assert bound.candidate.witness == bound.patch.patch_sha256
    assert thaw(bound.candidate.metadata)["patch_id"] == bound.patch.patch_id
    assert updated.patch_ids == (bound.patch.patch_id,)


def test_the_declared_encoding_is_an_admitted_one(controller, session):
    _, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(),
    )
    assert bound.patch.patch_encoding == PATCH_ENCODING_UNIFIED_DIFF
    assert PATCH_ENCODING_UNIFIED_DIFF in PATCH_ENCODINGS


def test_touched_paths_are_derived_from_the_bytes_not_declared(controller, session):
    """The fence the dead code lacked.

    It passed `parse_unified_diff(...).touched_paths` through unchecked, so a
    producer could name paths its patch did not touch. `bind_patch_bytes`
    derives them instead. The submit signature has no `touched_paths` parameter
    at all, which is why this cannot regress by omission.
    """
    _, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(path=OWNED),
    )
    assert bound.patch.touched_paths == (OWNED,)

    _, other = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(path="src/y.py"),
    )
    assert other.patch.touched_paths == ("src/y.py",), "derivation must follow the bytes"


# --------------------------------------------------------------------------
# Producer claims are recorded, never manufactured
# --------------------------------------------------------------------------


def test_the_use_case_invents_no_producer_claim(controller, session):
    """`claimed_terminal` / `claimed_valid` are the producer's to make.

    This use case is not the producer. An invented claim is worse than an
    absent one: it is indistinguishable from a real one downstream, and
    `CandidateArtifactV1` exists precisely to keep an untrusted proposal's
    claims separable from an evaluator's conclusions.
    """
    _, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_patch_for(),
    )
    assert bound.candidate.claimed_terminal is None
    assert bound.candidate.claimed_valid is None
    assert bound.candidate.authority_effect == "None"


# --------------------------------------------------------------------------
# The budget guard still refuses, and a duplicate does not spend it
# --------------------------------------------------------------------------


def test_the_candidate_budget_is_still_enforced(controller, session):
    """Pre-existing behaviour that must survive the rewrite.

    The guard sits above the construction; a repair that moved it below would
    spend budget on a refused submission.
    """
    from pfp.domain import BudgetExhaustedError

    current = session
    budget = int(current.payload.candidate_budget)
    for index in range(budget):
        current, _ = controller.submit_patch(
            session=current,
            producer_id="model-worker",
            patch_text=_patch_for(body=f"def f{index}():\n    return {index}\n"),
        )
    assert len(current.candidate_ids) == budget

    with pytest.raises(BudgetExhaustedError):
        controller.submit_patch(
            session=current,
            producer_id="model-worker",
            patch_text=_patch_for(body="def g():\n    return 0\n"),
        )


def test_resubmitting_the_identical_patch_does_not_spend_budget(controller):
    """Content-addressed identity means a resubmission *is* the same candidate.

    Membership is therefore checked before capacity. With the checks in the
    other order, a budget-1 session would refuse an identical resubmission at
    the boundary even though the ledger -- a sorted unique set -- would not have
    grown. The `budget=1` fixture is what makes the ordering observable.
    """
    session = controller.create_proposal(
        task_id="task-dup",
        objective="one candidate only",
        base_revision=BASE_REVISION,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
        candidate_budget=1,
    )
    session, first = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_patch_for()
    )
    session, again = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_patch_for()
    )
    assert first.candidate.candidate_id == again.candidate.candidate_id
    assert len(session.candidate_ids) == 1
