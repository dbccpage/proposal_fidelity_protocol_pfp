"""`create -> submit -> gates -> finalize` through the default controller wiring.

`EvaluatePatchGatesUseCase.execute` was dead in a way the seven broken
`GateReceiptV1` constructions understate: its signature received no candidate,
and a gate receipt *requires* a `candidate_id` digest and carries the producer's
`model_claimed_passed`. No repair of those seven call sites could have produced
a valid receipt.

The repair that followed was worse in a quieter way. It built receipts from
whatever artifacts it was handed, verifying nothing. A probe confirmed the
consequence: a fabricated patch and candidate, present in no ledger, from
producer "attacker", with `payload={"anything": "at all"}`, drew three PASS
receipts. A receipt is the evaluator's word that it examined a specific
artifact; minting one for an artifact that was never admitted makes the
signature worthless everywhere else it appears. The `refuses_*` tests below are
that hole, closed.

The other central assertion here is the separation of a producer's claim from
an evaluator's conclusion. `model_claimed_passed` and `disposition` are two
different facts about the same candidate, and a receipt that collapsed them --
by deriving one from the other, or by dropping the claim when it disagreed --
would destroy the only record that they ever differed.

AuthorityEffect: execution_reachability_restored; authority_set_unchanged.
"""

from __future__ import annotations

import hashlib

import pytest

from pfp.controllers.code_change_controller import (
    CodeChangeController,
)
from pfp.domain import (
    CandidateArtifactV1,
    CanonicalizationError,
    CodeChangeRunRootV1,
    REFUSAL_PROTECTED_FILE_PATCHED,
    REFUSAL_TOUCHED_OUTSIDE_OWNED,
    attach_candidate,
    bind_patch_bytes,
    canonical_bytes,
)
from pfp.domain.aggregates.code_change_run_root import (
    GATE_DISPOSITIONS,
    REQUIRED_GATE_IDS,
)
from pfp.use_cases.code_change import (
    GATE_CONTRACT,
    GATE_EVALUATOR_ID,
    GATE_OWNERSHIP,
    GATE_SYNTAX,
    PATCH_ENCODING_UNIFIED_DIFF,
    BoundCandidate,
    CodeChangeSession,
)

OWNED = "src/x.py"
PROTECTED = "README.md"


def _diff(path: str) -> str:
    return f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,1 @@\n+x = 1\n"


@pytest.fixture()
def controller() -> CodeChangeController:
    return CodeChangeController()


@pytest.fixture()
def session(controller: CodeChangeController):
    return controller.create_proposal(
        task_id="task-001",
        objective="add a function",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )


@pytest.fixture()
def seeded(controller: CodeChangeController, session):
    """`create -> submit`, returning everything the gates stage consumes."""
    return controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_diff(OWNED),
    )


# --------------------------------------------------------------------------
# The path is alive
# --------------------------------------------------------------------------


def test_gates_traverse_the_default_controller_wiring(controller, seeded):
    """The headline regression. Every construction raised before the repair."""
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    assert len(receipts) == 3
    assert {r.gate_id for r in receipts} == {GATE_SYNTAX, GATE_OWNERSHIP, GATE_CONTRACT}


def test_every_gate_id_is_admitted(controller, seeded):
    """`gate_protected` is not in `REQUIRED_GATE_IDS`; the old body used it."""
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    for receipt in receipts:
        assert receipt.gate_id in REQUIRED_GATE_IDS
        assert receipt.disposition in GATE_DISPOSITIONS
    assert "gate_protected" not in {r.gate_id for r in receipts}


# --------------------------------------------------------------------------
# Nothing unbound gets a receipt
# --------------------------------------------------------------------------


def _fabricated(session):
    """A patch and candidate that were never submitted to `session`.

    Deliberately *well-formed*: `bind_patch_bytes` really did bind these bytes,
    and the packet id is the session's own. The only thing wrong with them is
    that they entered from outside the admitted path -- which is exactly the
    case the previous implementation could not detect.
    """
    body = b"--- a/src/evil.py\n+++ b/src/evil.py\n@@ -0,0 +1,1 @@\n+evil = 1\n"
    patch = bind_patch_bytes(
        packet_id=session.packet_id,
        producer_id="attacker",
        base_source_revision=session.payload.source_revision,
        patch_encoding=PATCH_ENCODING_UNIFIED_DIFF,
        patch_bytes=body,
    )
    candidate = CandidateArtifactV1(
        packet_id=session.packet_id,
        producer_id="attacker",
        payload={"anything": "at all"},
        witness=patch.patch_sha256,
        claimed_terminal=None,
        claimed_valid=True,
        metadata={"patch_id": patch.patch_id},
    )
    return BoundCandidate(candidate=candidate, patch=patch, patch_bytes=body)


def test_refuses_a_candidate_that_was_never_submitted(controller, seeded):
    """The confirmed hole: this drew three PASS receipts before the fence.

    The producer is "attacker", the payload is `{"anything": "at all"}`, and
    neither artifact appears in any ledger.
    """
    updated, _ = seeded
    with pytest.raises(CanonicalizationError, match="UNBOUND_EVALUATION_INPUT"):
        controller.evaluate_patch_gates(session=updated, bound=_fabricated(updated))


def test_refuses_substituted_patch_bytes(controller, seeded):
    """A real candidate, with its content swapped after binding.

    Without `verify_patch_bytes` the artifact's content is its own unchecked
    claim, and every gate below would read `touched_paths` derived from bytes
    nobody presented.
    """
    updated, bound = seeded
    swapped = BoundCandidate(
        candidate=bound.candidate,
        patch=bound.patch,
        patch_bytes=b"totally different bytes\n",
    )
    with pytest.raises(CanonicalizationError, match="UNBOUND_EVALUATION_INPUT"):
        controller.evaluate_patch_gates(session=updated, bound=swapped)


def test_refuses_a_cross_run_replay(controller, seeded):
    """A wholly valid candidate -- from a different packet.

    This is the subtlest of the three: every internal binding holds, so only a
    check against *this* session's packet catches it.
    """
    updated, _ = seeded
    other_session = controller.create_proposal(
        task_id="task-other",
        objective="a different task",
        base_revision="c" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    _, other_bound = controller.submit_patch(
        session=other_session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    with pytest.raises(CanonicalizationError, match="UNBOUND_EVALUATION_INPUT"):
        controller.evaluate_patch_gates(session=updated, bound=other_bound)


def test_a_programming_defect_is_not_masked_as_a_refusal(controller, seeded, monkeypatch):
    """The fence catches declared validation failures only.

    A bare `except Exception` around `verify_patch_bytes` would turn an
    `AttributeError` from a renamed field -- or a `NameError`, or any other
    defect -- into an ordinary `UNBOUND_EVALUATION_INPUT` refusal. That is the
    masking pattern that let these modules sit dead behind a live import: a body
    that raises on every call is indistinguishable from a body that legitimately
    refuses, once the difference has been swallowed.

    The defect must escape as itself, and specifically must NOT arrive as a
    `CanonicalizationError`, which is what a caller would reasonably log and move
    on from.
    """
    from pfp.use_cases import code_change as module

    def _defective(*args, **kwargs):
        raise AttributeError("patch_sha256 was renamed and this call site was missed")

    monkeypatch.setattr(module, "verify_patch_bytes", _defective)

    updated, bound = seeded
    with pytest.raises(AttributeError, match="was renamed"):
        controller.evaluate_patch_gates(session=updated, bound=bound)


def test_finalize_refuses_the_same_unbound_inputs(controller, seeded):
    """The fence is on both stages, not only on the receipt builder.

    A finalize that trusted its inputs would let a refused candidate reach the
    canonical evaluator with receipts minted for something else.
    """
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    with pytest.raises(CanonicalizationError, match="UNBOUND_EVALUATION_INPUT"):
        controller.finalize_run(
            session=updated, bound=_fabricated(updated), gate_receipts=receipts
        )


# --------------------------------------------------------------------------
# Claim and conclusion are two facts, and both survive
# --------------------------------------------------------------------------


def _with_claim(session, *, path: str, producer_id: str, claimed_valid: bool):
    """A producer that *did* make a claim, admitted into a session ledger.

    `submit_patch` deliberately accepts no claim arguments. A bare bool reaching
    that signature has no provenance -- nothing ties it to a producer's actual
    response -- so any caller could invent one and corrupt the audit record.
    Claims will be admitted again only as a typed untrusted object bound to
    durable provider bytes (producer_id, provider_attempt_id,
    raw_response_sha256, extraction_receipt), which is tracked separately.

    To test that a claim survives disagreement, one has to exist. This helper
    therefore reaches past the use case to the domain factory, then declares a
    session whose ledger contains the result. That is deliberately the
    publicly-constructible-session residual documented on `CodeChangeSession`,
    used here as a stand-in for the future typed-claim path. **When that path
    lands, this helper should be deleted and these two tests rewritten to go
    through it** -- it is scaffolding, not an endorsement of the residual.

    That ordering is a prerequisite, not a preference: session opacity has to
    come first. What this helper does in six lines -- attach a claimed candidate
    and manufacture the ledger that vouches for its admission -- is exactly what
    a caller could do to a typed `ProducerClaim` introduced against a publicly
    constructible session. The claim's provenance would then be precisely as
    forgeable as the bare bool it was meant to replace.
    """
    body = _diff(path).encode("utf-8")
    patch = bind_patch_bytes(
        packet_id=session.packet_id,
        producer_id=producer_id,
        base_source_revision=session.payload.source_revision,
        patch_encoding=PATCH_ENCODING_UNIFIED_DIFF,
        patch_bytes=body,
    )
    candidate = attach_candidate(
        session.envelope,
        patch,
        producer_id=producer_id,
        claimed_terminal="VerifiedProposal",
        claimed_valid=claimed_valid,
    )
    admitted = CodeChangeSession(
        envelope=session.envelope,
        candidate_ids=(candidate.candidate_id,),
        patch_ids=(patch.patch_id,),
    )
    return admitted, BoundCandidate(candidate=candidate, patch=patch, patch_bytes=body)


def test_a_model_claiming_pass_does_not_make_the_gate_pass(controller, session):
    """The required regression: producer claims pass, evaluator fails, both kept.

    The patch touches a protected path. The producer asserts the candidate is
    valid. The evaluator disagrees. A receipt that derived `disposition` from
    the claim would report PASS; one that dropped the claim on disagreement
    would lose the evidence that a producer over-claimed.
    """
    admitted, bound = _with_claim(
        session, path=PROTECTED, producer_id="over-claiming-worker", claimed_valid=True
    )
    receipts = controller.evaluate_patch_gates(session=admitted, bound=bound)
    contract = next(r for r in receipts if r.gate_id == GATE_CONTRACT)

    assert contract.model_claimed_passed is True, "the producer's claim must survive"
    assert contract.disposition == "FAIL", "the evaluator must reach its own verdict"
    assert REFUSAL_PROTECTED_FILE_PATCHED in contract.refusal_codes


def test_a_model_claiming_failure_does_not_make_the_gate_fail(controller, session):
    """The mirror. Without it, an implementation that simply copied the claim
    into the disposition would pass the test above and fail nothing."""
    admitted, bound = _with_claim(
        session, path=OWNED, producer_id="pessimistic-worker", claimed_valid=False
    )
    receipts = controller.evaluate_patch_gates(session=admitted, bound=bound)
    for receipt in receipts:
        assert receipt.model_claimed_passed is False
        assert receipt.disposition == "PASS"


def test_submit_admits_no_producer_claim(controller, session):
    """P0 ruling: loose claim arguments do not enter through the use case.

    Asserted as a signature fact, not only a value fact. Checking that
    `claimed_valid` is `None` would still pass if the parameter existed and the
    caller omitted it; rejecting the keyword is what pins the decision.
    """
    with pytest.raises(TypeError):
        controller.submit_patch(
            session=session,
            producer_id="worker",
            patch_text=_diff(OWNED),
            claimed_valid=True,
        )


def test_an_absent_claim_is_distinguishable_from_a_negative_one(controller, seeded):
    """`None` means the producer claimed nothing, which is not `False`."""
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    assert all(r.model_claimed_passed is None for r in receipts)


# --------------------------------------------------------------------------
# Field authority
# --------------------------------------------------------------------------


def test_every_field_is_bound_to_its_declared_source(controller, seeded):
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    for receipt in receipts:
        assert receipt.packet_id == updated.packet_id
        assert receipt.candidate_id == bound.candidate.candidate_id
        assert receipt.evaluator_id == GATE_EVALUATOR_ID
        assert receipt.authority_effect == "None"


def test_the_evidence_digest_is_recomputable(controller, seeded):
    """Evidence must be checkable by a reader, not asserted by the writer.

    The ownership gate's evidence is reconstructed here from the session and the
    patch, canonicalized the same way, and its digest compared. A receipt whose
    digest covered something else -- or nothing -- fails.
    """
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    ownership = next(r for r in receipts if r.gate_id == GATE_OWNERSHIP)

    expected = canonical_bytes(
        {
            "owned_paths": list(updated.payload.owned_paths),
            "touched_paths": list(bound.patch.touched_paths),
            "unowned_paths": [],
        }
    )
    assert ownership.evidence_sha256 == hashlib.sha256(expected).hexdigest()
    assert ownership.evidence_byte_count == len(expected)


def test_the_evidence_digest_moves_with_the_evidence(controller, seeded):
    """Negative control for the assertion above.

    A builder that hashed a constant would satisfy the recomputation test on a
    single fixture. Two gates over different evidence must not collide.
    """
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    digests = {r.evidence_sha256 for r in receipts}
    assert len(digests) == len(receipts), "each gate's evidence must be its own"


# --------------------------------------------------------------------------
# Refusal codes, and the domain invariant that pairs them with disposition
# --------------------------------------------------------------------------


def test_an_unowned_path_fails_ownership_with_its_governed_code(controller):
    session = controller.create_proposal(
        task_id="task-002",
        objective="touch something unowned",
        base_revision="a" * 40,
        owned_paths=("src/only_here.py",),
        protected_paths=(PROTECTED,),
    )
    updated, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_diff("src/elsewhere.py"),
    )
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    ownership = next(r for r in receipts if r.gate_id == GATE_OWNERSHIP)
    assert ownership.disposition == "FAIL"
    assert ownership.refusal_codes == (REFUSAL_TOUCHED_OUTSIDE_OWNED,)


def test_passing_gates_carry_no_refusal_codes(controller, seeded):
    """The domain refuses a PASS with codes and a FAIL without them.

    Asserted here because the centralized builder is the only place that pairing
    can now be broken, and breaking it raises rather than returning a bad
    receipt -- so this test also proves the builder is reached.
    """
    updated, bound = seeded
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    for receipt in receipts:
        if receipt.disposition == "PASS":
            assert receipt.refusal_codes == ()
        else:
            assert receipt.refusal_codes, "FAIL must name its governed code"


# --------------------------------------------------------------------------
# The run root is the result of evaluation, not a session ledger
# --------------------------------------------------------------------------


def test_the_full_lifecycle_terminates_in_the_canonical_evaluator(controller):
    """`create -> submit -> gates -> finalize`, ending in a real run root.

    This is the test the previous architecture could not have: its run root was
    built at stage 1 and never passed through `evaluate_code_change_candidate`,
    so `terminal_status` was a value the application had typed in rather than
    one an evaluator assigned. Here the status is whatever the domain concludes,
    and the ledger contents come back from the evaluator.

    `DeclaredUnverified` is the correct terminal for a passing candidate: the
    gates passed, and the domain still declines to call it verified. A change
    that made this assert a "verified" status would be the failure this whole
    file exists to prevent.
    """
    session = controller.create_proposal(
        task_id="task-003",
        objective="end to end",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
        required_gates=("gate_syntax", "gate_ownership", "gate_contract"),
    )
    updated, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)
    run_root = controller.finalize_run(
        session=updated, bound=bound, gate_receipts=receipts
    )

    assert isinstance(run_root, CodeChangeRunRootV1)
    assert run_root.terminal_status == "DeclaredUnverified"
    assert run_root.refusals == ()
    assert run_root.task_packet_id == updated.packet_id
    assert run_root.candidate_ids == (bound.candidate.candidate_id,)
    assert run_root.patch_ids == (bound.patch.patch_id,)
    for receipt in receipts:
        assert receipt.candidate_id in run_root.candidate_ids
        assert receipt.packet_id == run_root.task_packet_id


def test_a_missing_required_gate_is_refused_by_the_evaluator(controller):
    """The evaluator enforces `required_gates`; the application does not.

    Submitting no receipts at all must not produce a clean run root. This is the
    fence that proves the terminal status is the domain's conclusion rather than
    an application default -- the previous shape hard-coded "OpenEvaluation" and
    would have reported exactly the same thing here.
    """
    session = controller.create_proposal(
        task_id="task-004",
        objective="no gates run",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    updated, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    run_root = controller.finalize_run(session=updated, bound=bound, gate_receipts=())

    assert "REQUIRED_GATE_MISSING" in run_root.refusals
    assert run_root.terminal_status != "DeclaredUnverified"


def test_a_protected_file_inside_an_owned_root_fails_only_the_contract_gate(controller):
    """The contract gate's own defender, and the symmetric partner to the
    ownership test above.

    Until this existed, exactly **one** test stood between a contract gate that
    never refuses and a green suite -- and that one is about producer claims, so
    it would have left with any refactor of the claim surface. A mutation making
    the gate always PASS was killed by a single assertion. A gate this
    load-bearing should not have a single defender.

    The isolation took a correction to get right, and the correction is worth
    recording. A path cannot be declared owned *and* protected: the payload
    refuses that outright, because `protected_paths` must be string-disjoint
    from `owned_paths`. But containment is prefix-based, so a protected **file
    inside an owned root** is perfectly admissible -- ownership passes on the
    prefix, and only the protected rule bites. That is the sole arrangement in
    which this gate's FAIL can be attributed to it alone.

    Asserting both dispositions is the point: a version that refused everything
    would satisfy a FAIL-only assertion.
    """
    session = controller.create_proposal(
        task_id="task-003",
        objective="touch a protected file inside an owned root",
        base_revision="a" * 40,
        owned_paths=("src",),
        protected_paths=("src/secret.py",),
    )
    updated, bound = controller.submit_patch(
        session=session,
        producer_id="model-worker",
        patch_text=_diff("src/secret.py"),
    )
    receipts = controller.evaluate_patch_gates(session=updated, bound=bound)

    ownership = next(r for r in receipts if r.gate_id == GATE_OWNERSHIP)
    contract = next(r for r in receipts if r.gate_id == GATE_CONTRACT)

    assert ownership.disposition == "PASS", "the file sits under an owned root"
    assert ownership.refusal_codes == ()
    assert contract.disposition == "FAIL"
    assert contract.refusal_codes == (REFUSAL_PROTECTED_FILE_PATCHED,)
