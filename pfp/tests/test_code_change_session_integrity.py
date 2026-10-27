"""`CodeChangeSession` must not be usable as forged admission testimony.

The gate fence added in the previous round proves a candidate is consistent
*with the session it is handed*. That is only worth something if the session
itself cannot be manufactured to say whatever the caller wants.

The earlier session stored `payload` and `task_id` as independent copies
alongside the envelope. Every downstream check then compared against those
copies, so a caller could pair envelope A with payload B and present a
*narrower* set of fences than the packet actually declares -- different
`owned_paths`, an empty `protected_paths`, fewer `required_gates`, a larger
`candidate_budget` -- while every consistency check still passed. The gates
would then evaluate a real candidate against fences the packet never granted.

The repair is to derive rather than store: `payload` and `task_id` come out of
the envelope through `parse_code_change_proposal_envelope`, which also verifies
the envelope's own internal bindings. Substitution is now a `TypeError` rather
than a refusal, because the parameters do not exist -- which is the stronger
outcome, and why these tests assert on construction rather than on behaviour.

The ledgers are validated too. They are the thing `_require_bound_for_evaluation`
appeals to when it asks whether a candidate was admitted, so a caller must not
be able to seed them with labels, blanks, or duplicates.

One residual is deliberately left open and asserted as open at the bottom of
this file, so that a future reader finds it stated rather than discovers it.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from pfp.controllers.code_change_controller import (
    CodeChangeController,
)
from pfp.domain import (
    CanonicalizationError,
    CodeChangeProposalPayloadV1,
    build_code_change_proposal_envelope,
)
from pfp.use_cases.code_change import CodeChangeSession

OWNED = "src"
PROTECTED = "README.md"
BASE_REVISION = "a" * 40


def _diff(path: str) -> str:
    return f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,1 @@\n+x = 1\n"


@pytest.fixture()
def controller() -> CodeChangeController:
    return CodeChangeController()


@pytest.fixture()
def strict(controller: CodeChangeController) -> CodeChangeSession:
    """A deliberately narrow packet: one owned root, one protected path, budget 1."""
    return controller.create_proposal(
        task_id="task-strict",
        objective="narrow fences",
        base_revision=BASE_REVISION,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
        candidate_budget=1,
    )


# --------------------------------------------------------------------------
# Nothing derivable may be supplied
# --------------------------------------------------------------------------


def test_a_payload_cannot_be_supplied_alongside_the_envelope(strict):
    """The headline forgery: envelope A with payload B.

    A `TypeError` rather than a refusal is the point. A refusal would mean the
    field still exists and is merely checked; the parameter is gone, so the
    substitution cannot be expressed.
    """
    wider = CodeChangeProposalPayloadV1(
        objective="narrow fences",
        source_revision=BASE_REVISION,
        owned_paths=(PROTECTED, OWNED),
        protected_paths=(),
        allowed_transforms=("edit", "emit_evidence", "test"),
        candidate_budget=32,
        operation_budget=64,
        required_gates=("gate_syntax",),
    )
    with pytest.raises(TypeError):
        CodeChangeSession(envelope=strict.envelope, payload=wider)


def test_a_task_id_cannot_be_supplied_alongside_the_envelope(strict):
    with pytest.raises(TypeError):
        CodeChangeSession(envelope=strict.envelope, task_id="not-the-real-task")


def test_the_payload_is_the_packets_own(strict):
    """Positive control. Without it, a session that derived *nothing* usable
    would satisfy both refusals above."""
    assert strict.payload.owned_paths == (OWNED,)
    assert strict.payload.protected_paths == (PROTECTED,)
    assert int(strict.payload.candidate_budget) == 1
    assert strict.task_id == "task-strict"
    assert strict.packet_id == strict.envelope.packet_id


def test_wider_fences_require_a_different_packet_identity(strict):
    """The fences are bound into the packet id, so widening them is visible.

    A caller may of course *declare* a wider packet -- that is legitimate. What
    it cannot do is present wider fences under the strict packet's identity, and
    this is the assertion that says so.
    """
    wider = CodeChangeProposalPayloadV1(
        objective="narrow fences",
        source_revision=BASE_REVISION,
        owned_paths=(PROTECTED, OWNED),
        protected_paths=(),
        allowed_transforms=("edit", "emit_evidence", "test"),
        candidate_budget=32,
        operation_budget=64,
        required_gates=("gate_syntax",),
    )
    wide_session = CodeChangeSession(
        envelope=build_code_change_proposal_envelope(wider, task_id="task-strict")
    )
    assert wide_session.packet_id != strict.packet_id
    assert wide_session.payload.protected_paths == ()


# --------------------------------------------------------------------------
# The ledgers are digest sets, not free-form lists
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ledger", "expected"),
    [
        (("cand-1",), "64-character digests"),
        (("",), "64-character digests"),
        (("A" * 64,), "lowercase hex"),
        (("z" * 64,), "lowercase hex"),
        (("a" * 64, "a" * 64), "unique and sorted"),
        (("b" * 64, "a" * 64), "unique and sorted"),
    ],
)
def test_malformed_candidate_ledgers_are_refused(strict, ledger, expected):
    """A caller must not be able to seed the ledger the fence appeals to.

    `_require_bound_for_evaluation` asks whether a candidate id is *in* this
    ledger. If the ledger could hold a producer label, a blank, or duplicates,
    that question would be answerable by construction.
    """
    with pytest.raises(CanonicalizationError, match="FORGED_SESSION"):
        CodeChangeSession(envelope=strict.envelope, candidate_ids=ledger)


def test_malformed_patch_ledgers_are_refused(strict):
    """The patch ledger gets the same treatment; both are consulted."""
    with pytest.raises(CanonicalizationError, match="FORGED_SESSION"):
        CodeChangeSession(envelope=strict.envelope, patch_ids=("patch-1",))


def test_a_non_envelope_is_refused(strict):
    """A mapping that merely looks like an envelope is not one."""
    with pytest.raises(CanonicalizationError, match="FORGED_SESSION"):
        CodeChangeSession(envelope={"packet_id": "a" * 64})


def test_a_well_formed_ledger_is_accepted(strict):
    """Positive control for the validator: correct input must not be refused."""
    session = CodeChangeSession(
        envelope=strict.envelope,
        candidate_ids=("a" * 64, "b" * 64),
        patch_ids=("c" * 64,),
    )
    assert session.candidate_ids == ("a" * 64, "b" * 64)


# --------------------------------------------------------------------------
# An injected id is still not an admitted candidate
# --------------------------------------------------------------------------


def test_a_fabricated_ledger_entry_does_not_admit_a_real_candidate(controller, strict):
    """Structural validity of the ledger is not membership of *this* candidate.

    The ledger here is perfectly well-formed -- 64 lowercase hex, sorted, unique
    -- and simply names digests that no artifact hashes to. A real, correctly
    bound candidate presented against it is still refused, because the fence
    compares the candidate's own derived identity rather than trusting that the
    ledger describes something real.
    """
    _, bound = controller.submit_patch(
        session=strict, producer_id="model-worker", patch_text=_diff("src/x.py")
    )
    fabricated = CodeChangeSession(
        envelope=strict.envelope,
        candidate_ids=("c" * 64,),
        patch_ids=("d" * 64,),
    )
    with pytest.raises(CanonicalizationError, match="UNBOUND_EVALUATION_INPUT"):
        controller.evaluate_patch_gates(session=fabricated, bound=bound)


# --------------------------------------------------------------------------
# The residual, asserted so it is not mistaken for closed
# --------------------------------------------------------------------------


def test_ledger_membership_is_state_consistency_not_proof_of_admission(
    controller, strict
):
    """The open item, pinned as a test so it is stated rather than discovered.

    `CodeChangeSession` is publicly constructible, so a caller can declare a
    session whose ledger never grew through `submit_patch`. After the repairs
    above this buys very little: the gate fence still requires a candidate that
    genuinely binds a genuinely-bound patch against this exact packet, which is
    what `attach_candidate` produces anyway -- so nothing gets evaluated that
    would not have been admitted.

    If a future change makes sessions unforgeable, this test should fail and be
    deleted -- that is the intended signal.
    """
    spent, _ = controller.submit_patch(
        session=strict, producer_id="model-worker", patch_text=_diff("src/x.py")
    )
    assert len(spent.candidate_ids) == 1
    assert int(spent.payload.candidate_budget) == 1

    reset = CodeChangeSession(envelope=strict.envelope)
    assert reset.candidate_ids == (), "documented residual: spend can be reset"


def test_budget_counters_are_host_testimony_independent_of_the_session(
    controller, strict
):
    """The residual is wider than session construction, and this pins where.

    Resetting a session's ledger is not the only way to restate spend:
    `finalize_run` passes `prior_candidate_count` and `operation_count` straight
    through to the evaluator, so both counters are caller-supplied however the
    session was built. Candidate and operation budget enforcement is host-
    supplied and resettable.

    It is a resource-fence gap rather than an authority-fence gap, and the reason
    is asserted below rather than assumed: the evaluator adds
    `BUDGET_HOST_STATE_ABSENT` unconditionally and discards its own
    `host_budget_counters_bound` argument, so no host can discharge it and no run
    root reaches a positive terminal on the strength of counters it was merely
    told. A change that makes that obstruction conditional turns this into an
    authority gap; this test is what should fail first if that happens.
    """
    session, bound = controller.submit_patch(
        session=strict, producer_id="model-worker", patch_text=_diff("src/x.py")
    )
    receipts = controller.evaluate_patch_gates(session=session, bound=bound)

    # A caller that simply declares it has spent nothing draws no refusal.
    reset = controller.finalize_run(
        session=session,
        bound=bound,
        gate_receipts=receipts,
        prior_candidate_count=0,
        operation_count=1,
    )
    assert reset.refusals == (), "the counters are believed as given"

    # The same call declaring overspend is refused -- proving the evaluator reads
    # these arguments and does not derive them from anything it can check.
    overspent = controller.finalize_run(
        session=session,
        bound=bound,
        gate_receipts=receipts,
        prior_candidate_count=99,
    )
    assert "CANDIDATE_BUDGET_EXCEEDED" in overspent.refusals

    # ... and the honest run still cannot claim a verified budget, which is what
    # keeps this out of the authority axis.
    assert "BUDGET_HOST_STATE_ABSENT" in reset.open_obstruction_ids
    assert reset.terminal_status == "DeclaredUnverified"
