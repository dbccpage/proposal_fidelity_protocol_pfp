"""A submission path nothing ever executed.

`SubmitCandidateUseCase.execute` built both of its artifacts from an earlier
shape of the domain. `LlmTurnContentArtifactV1` was handed `content_artifact_id`,
`reply_text` and `byte_count`; `CandidateArtifactV1` was handed `candidate_id`,
`task_id`, `content_artifact_id` and four more. Neither class has any of those
fields, and both are `slots=True`, so the first constructor raised

    TypeError: LlmTurnContentArtifactV1.__init__() got an unexpected keyword
    argument 'content_artifact_id'

on every first submission. Everything below that line -- the run-root
reconstruction, the return, the whole of `EvaluateCandidateUseCase` -- was
unreachable code.

`EvaluateCandidateUseCase` then read `content.reply_text` and
`candidate.dual_witness_ref`, neither of which exists either, and
`MemoryTurnRepository` keyed content on `content_artifact_id` while never
defining the `save_candidate_artifact` its own port declares and its own
controller calls.

Four separate breaks on one path, and the reason all four survived is the same:
**no test reached the return.** A budget gate was repaired at the top of this
function while the body beneath it could not run at all, which is what an
assertion on `len(candidate_ids)` alone cannot tell you.

The identity rule these tests pin: `candidate_id` and `content_id` are derived
digests over the artifacts' identity fields, not the caller's label. The run
root stores the derived values, and its `candidate_ids` / `content_ids` go
through `_validate_ordered_unique_strings`, which *refuses* unsorted input
rather than sorting it. Digests do not arrive in sorted order.

AuthorityEffect: None.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from omega_engine_pfp.domain import (
    CandidateArtifactV1,
    CanonicalizationError,
    InvariantViolationError,
    LlmTurnAttemptV1,
    LlmTurnContentArtifactV1,
    LlmTurnRunRootV1,
    REFUSAL_ATTEMPT_ID_MISBIND,
    REFUSAL_CANDIDATE_CONTENT_MISBIND,
    REFUSAL_CONTENT_DIGEST_MISMATCH,
    REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    REFUSAL_INHERITED_MEANING,
    REFUSAL_MISSING_REQUIRED_REPLY_FIELDS,
    thaw,
    verify_llm_turn_run_root_shape,
)
from omega_engine_pfp.domain.aggregates.llm_turn_run_root import (
    _assert_candidate_binds_content,
)
from omega_engine_pfp.infrastructure.persistence.repositories import (
    MemoryTurnRepository,
)
from omega_engine_pfp.use_cases.llm_turn import (
    CONTENT_ENCODING,
    CreateTurnUseCase,
    EvaluateCandidateUseCase,
    LlmTurnSubmissionBody,
    SubmitCandidateUseCase,
)

PRODUCER = "agent_alpha"


def _reply(**overrides: object) -> str:
    """A machine block satisfying the default `required_reply_fields`."""
    body: dict[str, object] = {
        "status": "PASS",
        "step_claims": ["c1"],
        "obstruction_receipts": [],
        "residual_colour": "Open",
        "AUTHORITY_EFFECT": "None",
    }
    body.update(overrides)
    return "```json\n" + json.dumps(body) + "\n```"


def _run_root(budget: int = 4) -> LlmTurnRunRootV1:
    return CreateTurnUseCase().execute(
        task_id="task_turn_001",
        objective="Resolve obstruction obs_1",
        candidate_budget=budget,
    )


def _submit(
    root: LlmTurnRunRootV1,
    label: str,
    reply: str | None = None,
    **kwargs: object,
) -> tuple[LlmTurnRunRootV1, CandidateArtifactV1, LlmTurnContentArtifactV1]:
    return SubmitCandidateUseCase().execute(
        run_root=root,
        candidate_id=label,
        producer_id=PRODUCER,
        reply_text=reply if reply is not None else _reply(),
        **kwargs,  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------
# The unreachable return
# --------------------------------------------------------------------------


def test_a_first_submission_reaches_its_return() -> None:
    """The defect at its smallest: this call used to raise `TypeError`.

    Mutation: restore any one of the removed keyword arguments and this fails
    before a single assertion runs.
    """
    root, candidate, content = _submit(_run_root(), "cand_001")

    assert isinstance(candidate, CandidateArtifactV1)
    assert isinstance(content, LlmTurnContentArtifactV1)
    assert len(root.candidate_ids) == 1
    assert len(root.content_ids) == 1


def test_the_content_artifact_binds_a_digest_rather_than_the_bytes() -> None:
    """`LlmTurnContentArtifactV1` is a binding, and its encoding is fixed."""
    _, _, content = _submit(_run_root(), "cand_001", "hello")

    assert content.content_encoding == CONTENT_ENCODING
    assert content.content_byte_count == len("hello")
    assert content.content_sha256 != content.content_id
    assert content.payload.reply_text == "hello"
    assert content.payload.candidate_label == "cand_001"


# --------------------------------------------------------------------------
# Derived identity, not the caller's label
# --------------------------------------------------------------------------


def test_the_run_root_records_derived_digests_not_the_caller_label() -> None:
    """The label is an input; the id is a digest the artifact computes.

    Mutation: store `candidate_id` (the label) in `candidate_ids` and the first
    two assertions invert.
    """
    root, candidate, content = _submit(_run_root(), "cand_001")

    assert "cand_001" not in root.candidate_ids
    assert candidate.candidate_id in root.candidate_ids
    assert content.content_id in root.content_ids
    for value in (candidate.candidate_id, content.content_id):
        assert len(value) == 64
        assert set(value) <= set("0123456789abcdef")


def test_the_label_still_separates_two_submissions_of_identical_bytes() -> None:
    """Identical replies under different labels are different candidates.

    The label rides inside the payload the candidate digest covers, so this is
    what stops two submissions of the same text from colliding into one id and
    silently costing one unit of budget instead of two.
    """
    root = _run_root()
    same_text = _reply()
    root, first, _ = _submit(root, "cand_001", same_text)
    root, second, _ = _submit(root, "cand_002", same_text)

    assert first.candidate_id != second.candidate_id
    assert len(root.candidate_ids) == 2


# --------------------------------------------------------------------------
# The sorted-tuple invariant
# --------------------------------------------------------------------------


def _labels_whose_digests_descend() -> tuple[str, str]:
    """Two labels whose derived candidate ids arrive in descending order.

    Digests are deterministic, so this search is too. It exists because a pair
    picked by hand would silently stop exercising the sort if the identity
    fields ever changed.
    """
    root = _run_root(budget=8)
    seen: list[tuple[str, str]] = []
    for index in range(64):
        label = f"cand_{index:03d}"
        _, candidate, _ = _submit(root, label)
        seen.append((candidate.candidate_id, label))
    for digest_a, label_a in seen:
        for digest_b, label_b in seen:
            if digest_a > digest_b:
                return label_a, label_b
    raise AssertionError("no descending digest pair found in 64 labels")


def test_candidate_ids_stay_sorted_when_digests_arrive_out_of_order() -> None:
    """`_validate_ordered_unique_strings` refuses unsorted input, it does not sort.

    Mutation: append instead of sorting -- `candidate_ids=(*root.candidate_ids,
    candidate.candidate_id)` -- and this raises "candidate_ids must be unique
    and sorted".
    """
    first_label, second_label = _labels_whose_digests_descend()

    root = _run_root()
    root, first, _ = _submit(root, first_label)
    root, second, _ = _submit(root, second_label)

    assert first.candidate_id > second.candidate_id, "fixture must be descending"
    assert root.candidate_ids == tuple(sorted(root.candidate_ids))
    assert set(root.candidate_ids) == {first.candidate_id, second.candidate_id}


def test_content_ids_stay_sorted_too() -> None:
    """The second tuple carries the same invariant and the same digests."""
    root = _run_root()
    for index in range(4):
        root, _, _ = _submit(root, f"cand_{index:03d}", _reply(step_claims=[f"c{index}"]))

    assert root.content_ids == tuple(sorted(root.content_ids))
    assert len(root.content_ids) == 4


def test_identical_bytes_bind_to_one_content_artifact() -> None:
    """Content addressing: same producer, same packet, same bytes -- one id.

    `content_ids` therefore unions rather than refusing a repeat, which is the
    opposite of the `candidate_ids` rule directly above. The two tuples differ
    because a content artifact is identified by what it holds, while a
    candidate is a distinct submission event that has to cost budget.
    """
    root = _run_root()
    same_text = _reply()
    root, _, first = _submit(root, "cand_001", same_text)
    root, _, second = _submit(root, "cand_002", same_text)

    assert first.content_id == second.content_id
    assert len(root.content_ids) == 1
    assert len(root.candidate_ids) == 2


# --------------------------------------------------------------------------
# Budget honesty
# --------------------------------------------------------------------------


def test_a_repeat_submission_is_refused_rather_than_silently_dropped() -> None:
    """A duplicate must not leave the budget unable to exhaust.

    Deduplicating `candidate_ids` would make a resubmitted candidate a no-op:
    the tuple would not grow, so `len(candidate_ids) >= budget_limit` would
    never become true and the gate could be looped against forever.
    """
    root = _run_root()
    root, _, _ = _submit(root, "cand_001")
    before = root.candidate_ids

    with pytest.raises(InvariantViolationError):
        _submit(root, "cand_001")

    assert root.candidate_ids == before


# --------------------------------------------------------------------------
# The evaluator's two dead field reads
# --------------------------------------------------------------------------


def test_the_evaluator_reads_the_reply_text_the_submission_carried() -> None:
    """`content.reply_text` did not exist; the body travels in the payload."""
    root, candidate, content = _submit(_run_root(), "cand_001")
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )

    assert verdict["disposition"] == "ACCEPTED"
    assert verdict["refusals"] == []
    assert verdict["candidate_id"] == candidate.candidate_id


def test_a_vague_reply_trips_the_inherited_meaning_kill_condition() -> None:
    """The F-01 gate fires -- which it could not do before.

    `payload.kill_conditions` is a tuple of `Code` value objects, so the guard
    `"F-01_inherited_meaning" in run_root.payload.kill_conditions` compared a
    `str` against a value object and was unconditionally False. The declared
    kill condition was structurally dead: no input could trip it.

    Mutation: compare against the `Code` objects again and this returns
    ACCEPTED.
    """
    root, candidate, content = _submit(
        _run_root(), "cand_001", _reply(status="I think it passes")
    )
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )

    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_INHERITED_MEANING in verdict["refusals"]


def test_the_kill_condition_fires_only_where_it_is_declared() -> None:
    """Negative control: the gate reads the declaration, it is not unconditional.

    Without this, a fix that simply always applied the F-01 text check would
    pass the test above while ignoring `kill_conditions` entirely. The payload
    refuses an empty `kill_conditions`, so this declares a different one.
    """
    root = CreateTurnUseCase().execute(
        task_id="task_turn_002",
        objective="Resolve obstruction obs_2",
        kill_conditions=("F-02_unstated_assumption",),
    )
    root, candidate, content = _submit(
        root, "cand_001", _reply(status="I think it passes")
    )
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )

    assert REFUSAL_INHERITED_MEANING not in verdict["refusals"]
    assert verdict["disposition"] == "ACCEPTED"


def test_an_exact_residual_without_a_dual_witness_is_refused() -> None:
    """`candidate.dual_witness_ref` did not exist either.

    This branch was reachable only for `residual_colour: Exact`, so it raised
    `AttributeError` on precisely the candidates that claim the strongest
    result. Mutation: drop `dual_witness_ref` from the submission body and the
    paired test below fails instead.
    """
    root, candidate, content = _submit(
        _run_root(), "cand_001", _reply(residual_colour="Exact")
    )
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )

    assert REFUSAL_EXACT_WITHOUT_DUAL_WITNESS in verdict["refusals"]


def test_an_exact_residual_with_a_dual_witness_is_accepted() -> None:
    """The other half of the branch, so the refusal above is not unconditional."""
    root, candidate, content = _submit(
        _run_root(),
        "cand_001",
        _reply(residual_colour="Exact"),
        dual_witness_ref="witness_packet_001",
    )
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )

    assert REFUSAL_EXACT_WITHOUT_DUAL_WITNESS not in verdict["refusals"]
    assert verdict["disposition"] == "ACCEPTED"


# --------------------------------------------------------------------------
# The evidence the artifact actually binds
# --------------------------------------------------------------------------


def test_the_submitted_run_root_passes_the_domains_own_verifier() -> None:
    """`verify_llm_turn_run_root_shape` is the oracle, not a hand-written shape.

    The reconstruction advanced the two id tuples and left `attempts=()` with
    `terminal_status="OpenEvaluation"`. `_derive_llm_turn_terminal` returns
    `InvalidPacket` whenever an attempt is absent, so the verifier rejected
    every submitted root with `TERMINAL_NOT_DERIVED_FROM_EVIDENCE` -- the use
    case returned an aggregate the domain would not accept back.

    Mutation: drop the attempt, or hardcode the terminal, and this raises.
    """
    root, _, _ = _submit(_run_root(), "cand_001")

    assert len(root.attempts) == 1
    assert root.attempts[0].attempt_index == 0
    assert root.terminal_status == "TransportValidated"
    verified = verify_llm_turn_run_root_shape(root)
    assert verified.terminal_status == root.terminal_status


def test_attempts_stay_contiguous_across_submissions() -> None:
    """The aggregate requires zero-indexed contiguous attempts."""
    root = _run_root()
    for index in range(3):
        root, _, _ = _submit(root, f"cand_{index:03d}", _reply(step_claims=[f"c{index}"]))

    assert [a.attempt_index for a in root.attempts] == [0, 1, 2]
    verify_llm_turn_run_root_shape(root)


def test_the_candidate_binds_the_content_artifact() -> None:
    """The domain's own binding rule must hold for what this use case mints."""
    _, candidate, content = _submit(_run_root(), "cand_001")

    # Raises if the binding is wrong; the shape below is what it requires.
    _assert_candidate_binds_content(candidate, content)
    assert candidate.witness == content.content_sha256
    meta = thaw(candidate.metadata)
    assert meta["content_id"] == content.content_id
    assert meta["reply_sha256"] == content.content_sha256


def test_a_swapped_reply_body_is_refused_under_an_unchanged_content_id() -> None:
    """The defect this section exists for.

    `explicit_payload` is excluded from `content_id` by design. So a caller can
    replace the whole submission body -- dropping an inherited-meaning phrase,
    adding required fields, inventing a dual witness -- and the content artifact
    still hashes to exactly the same id. Evaluation used to read that body and
    return ACCEPTED for a reply no digest covered.

    Mutation: delete the digest comparison in `EvaluateCandidateUseCase` and
    the tampered verdict flips back to ACCEPTED.
    """
    root, candidate, content = _submit(
        _run_root(), "cand_001", _reply(status="I think it passes")
    )
    honest = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )
    assert honest["disposition"] == "REJECTED"
    assert REFUSAL_INHERITED_MEANING in honest["refusals"]

    tampered = dataclasses.replace(
        content,
        explicit_payload=LlmTurnSubmissionBody(
            reply_text=_reply(),  # the offending phrase removed
            candidate_label="cand_001",
            dual_witness_ref="forged",
        ),
    )
    assert tampered.content_id == content.content_id, "fixture must keep the id fixed"

    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=tampered
    )
    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_CONTENT_DIGEST_MISMATCH in verdict["refusals"]


def test_a_forged_dual_witness_in_the_body_cannot_satisfy_the_exact_gate() -> None:
    """The dual witness is read from bound metadata, not from the free body.

    An Exact residual without a witness must refuse. Injecting one into
    `explicit_payload` must not satisfy the gate, because that field is outside
    the candidate's identity.
    """
    root, candidate, content = _submit(
        _run_root(), "cand_001", _reply(residual_colour="Exact")
    )
    forged = dataclasses.replace(
        content,
        explicit_payload=LlmTurnSubmissionBody(
            reply_text=_reply(residual_colour="Exact"),
            candidate_label="cand_001",
            dual_witness_ref="witness_packet_001",
        ),
    )
    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=forged
    )

    assert REFUSAL_EXACT_WITHOUT_DUAL_WITNESS in verdict["refusals"]
    assert verdict["disposition"] == "REJECTED"


def test_a_substituted_content_artifact_is_refused() -> None:
    """A candidate evaluated against content it never bound must refuse.

    Membership is the stronger gate and now catches this first: the substituted
    content belongs to a different run root, so no attempt links the pair. The
    candidate/content binding check below is what catches the residual case
    where both ids *are* members.
    """
    root, candidate, _ = _submit(_run_root(), "cand_001")
    _, _, other_content = _submit(_run_root(), "cand_002", _reply(step_claims=["other"]))

    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=other_content
    )

    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_ATTEMPT_ID_MISBIND in verdict["refusals"]


def test_a_refused_attempt_is_not_membership_evidence() -> None:
    """An attempt records what happened, not merely that something happened.

    Matching on the two ids alone treated a refusal as membership: a
    shape-valid `TypedRefusal` root whose only attempt was `Refused` could be
    handed back to this evaluator and collect ACCEPTED, because the ids still
    matched. `BudgetExhausted` behaves the same way.

    Mutation: drop the `disposition` comparison and this returns ACCEPTED.
    """
    root = _run_root()
    root, candidate, content = _submit(root, "cand_001")

    refused = dataclasses.replace(
        root,
        attempts=(
            LlmTurnAttemptV1(
                attempt_index=0,
                candidate_id=candidate.candidate_id,
                content_id=content.content_id,
                operation_count=1,
                disposition="Refused",
                refusal_codes=(REFUSAL_INHERITED_MEANING,),
            ),
        ),
        refusals=(REFUSAL_INHERITED_MEANING,),
        terminal_status="TypedRefusal",
    )
    # The fixture must be a root the domain itself accepts, or this proves
    # nothing about the evaluator.
    verify_llm_turn_run_root_shape(refused)

    verdict = EvaluateCandidateUseCase().execute(
        run_root=refused, candidate=candidate, content=content
    )
    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_ATTEMPT_ID_MISBIND in verdict["refusals"]

    # Negative control: the same pair under its accepted attempt still passes.
    accepted = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=content
    )
    assert accepted["disposition"] == "ACCEPTED"


def test_a_mismatched_pair_linked_by_an_attempt_is_still_refused() -> None:
    """The binding check is not made dead by the membership gate.

    Membership admits any pair an attempt links. If the attempt ledger itself
    crossed two artifacts -- both ids present, both members, but minted for
    different bodies -- membership passes and only
    `_assert_candidate_binds_content` stands between that pair and a verdict.

    Mutation: remove the binding check and this returns ACCEPTED.
    """
    root = _run_root()
    root, first, first_content = _submit(root, "cand_001")
    root, _, second_content = _submit(root, "cand_002", _reply(step_claims=["second"]))
    assert first_content.content_id != second_content.content_id

    crossed = dataclasses.replace(
        root,
        attempts=(
            LlmTurnAttemptV1(
                attempt_index=0,
                candidate_id=first.candidate_id,
                content_id=second_content.content_id,
                operation_count=1,
                disposition="AcceptedForEvaluation",
                refusal_codes=(),
            ),
        ),
    )

    verdict = EvaluateCandidateUseCase().execute(
        run_root=crossed, candidate=first, content=second_content
    )

    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_CANDIDATE_CONTENT_MISBIND in verdict["refusals"]


# --------------------------------------------------------------------------
# Membership: evidence must belong to *this* run root
# --------------------------------------------------------------------------


def test_a_valid_pair_from_another_task_is_refused() -> None:
    """Binding candidate to content does not bind either to a run root.

    `_assert_candidate_binds_content` proves only that two artifacts belong to
    each other. A perfectly valid pair minted under task B therefore evaluated
    cleanly under task A's objective, required reply fields and kill
    conditions, and came back ACCEPTED.

    Mutation: drop the membership check and this returns ACCEPTED.
    """
    root_a = CreateTurnUseCase().execute(task_id="task_A", objective="objective A")
    root_b = CreateTurnUseCase().execute(task_id="task_B", objective="objective B")
    root_b, candidate_b, content_b = _submit(root_b, "cand_b")

    foreign = EvaluateCandidateUseCase().execute(
        run_root=root_a, candidate=candidate_b, content=content_b
    )
    assert foreign["disposition"] == "REJECTED"
    assert REFUSAL_ATTEMPT_ID_MISBIND in foreign["refusals"]

    # Negative control: the same pair under its own root still evaluates.
    native = EvaluateCandidateUseCase().execute(
        run_root=root_b, candidate=candidate_b, content=content_b
    )
    assert native["disposition"] == "ACCEPTED"


def test_a_candidate_never_submitted_into_the_root_is_refused() -> None:
    """A forged pair carrying its own dual witness must not be evaluable.

    The artifacts here are internally consistent -- they bind to each other and
    to the right packet -- but they were never submitted, so no attempt links
    them and neither id is in the root's tuples.
    """
    root = _run_root()
    root_after, _, _ = _submit(root, "cand_001")
    # Built against the ORIGINAL root, so never recorded in `root_after`.
    _, forged_candidate, forged_content = SubmitCandidateUseCase().execute(
        run_root=root,
        candidate_id="cand_forged",
        producer_id=PRODUCER,
        reply_text=_reply(residual_colour="Exact"),
        dual_witness_ref="witness_packet_001",
    )

    verdict = EvaluateCandidateUseCase().execute(
        run_root=root_after, candidate=forged_candidate, content=forged_content
    )

    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_ATTEMPT_ID_MISBIND in verdict["refusals"]


# --------------------------------------------------------------------------
# Persistence: a saved run must be able to resume
# --------------------------------------------------------------------------


def test_a_saved_run_root_can_be_loaded_and_submitted_into() -> None:
    """create -> save -> load -> submit, which used to raise.

    `identity_fields` omits `explicit_payload` and `explicit_task_id`, so a
    loaded root came back with `payload is None` and a `task_id` degraded to
    the packet digest. Both use cases dereference
    `run_root.payload.candidate_budget` immediately, so resuming a persisted
    run died with `AttributeError: 'NoneType' object has no attribute
    'candidate_budget'`. The ledger shape round-tripped; the state the
    controller needs did not.

    Mutation: drop the payload reattachment in `get_run_root` and this raises.
    """
    repo = MemoryTurnRepository()
    root = _run_root()
    root, _, _ = _submit(root, "cand_001")
    repo.save_run_root(root)

    loaded = repo.get_run_root(str(root.run_root_id))
    assert loaded is not None
    assert loaded.payload is not None
    assert int(loaded.payload.candidate_budget) == 4
    assert loaded.task_id == "task_turn_001"
    # The ledger wire form is unchanged: the payload travels beside it, not
    # smuggled into it.
    assert loaded.to_dict() == root.to_dict()

    resumed, _, _ = _submit(loaded, "cand_002", _reply(step_claims=["second"]))
    assert len(resumed.candidate_ids) == 2
    verify_llm_turn_run_root_shape(resumed)


def test_two_turns_for_one_task_id_are_distinct_run_roots() -> None:
    """The packet digest must bind the packet's content, not repeat its name.

    `task_packet_id` and `task_packet_sha256` were both `sha256(task_id)`, so
    the payload was bound to nothing. Two turns for one task id with different
    objectives and budgets shared a `run_root_id`, and saving the second
    silently overwrote the first -- the store held one record where two runs
    existed, and loading the first returned the second's objective.

    Mutation: set `task_packet_sha256` back to the task-id digest and the ids
    collide again.
    """
    first = CreateTurnUseCase().execute(
        task_id="task_shared", objective="objective ONE", candidate_budget=2
    )
    second = CreateTurnUseCase().execute(
        task_id="task_shared", objective="objective TWO", candidate_budget=9
    )

    assert first.task_packet_id == second.task_packet_id, "same task, same packet id"
    assert first.task_packet_sha256 != second.task_packet_sha256
    assert first.run_root_id != second.run_root_id

    repo = MemoryTurnRepository()
    repo.save_run_root(first)
    repo.save_run_root(second)
    assert len(repo.context.runs) == 2

    loaded_first = repo.get_run_root(str(first.run_root_id))
    assert loaded_first is not None
    assert str(loaded_first.payload.objective) == "objective ONE"
    assert int(loaded_first.payload.candidate_budget) == 2


def test_a_swapped_payload_sidecar_is_refused_on_load() -> None:
    """The sidecar is evidence, so it is checked rather than trusted.

    Storing the payload beside the ledger and reattaching it unchecked let a
    swapped or stale record change the candidate budget, the required reply
    fields and the kill conditions with no id changing and nothing objecting.

    Mutation: drop the digest comparison in `get_run_root` and the load
    silently returns the other task's policy.
    """
    root = CreateTurnUseCase().execute(
        task_id="task_A", objective="objective A", candidate_budget=2
    )
    other = CreateTurnUseCase().execute(
        task_id="task_B", objective="objective B", candidate_budget=9
    )
    repo = MemoryTurnRepository()
    repo.save_run_root(root)
    repo.context.runs[str(root.run_root_id)]["payload"] = other.payload.to_dict()

    with pytest.raises(CanonicalizationError):
        repo.get_run_root(str(root.run_root_id))


def test_a_run_root_saved_before_any_submission_also_resumes() -> None:
    """The empty root is the one a controller saves first."""
    repo = MemoryTurnRepository()
    root = _run_root()
    repo.save_run_root(root)

    loaded = repo.get_run_root(str(root.run_root_id))
    assert loaded is not None
    assert loaded.task_id == "task_turn_001"
    submitted, _, _ = _submit(loaded, "cand_001")
    assert len(submitted.candidate_ids) == 1


def test_a_content_artifact_with_no_submission_body_is_refused() -> None:
    """A binding carries no bytes, so a rehydrated one cannot be scored.

    `to_dict` emits identity fields only, so a content artifact read back from
    a repository has no reply text. Evaluating it must refuse, not quietly
    score an empty string as though the reply had been read.
    """
    root, candidate, content = _submit(_run_root(), "cand_001")
    rehydrated = LlmTurnContentArtifactV1.from_dict(content.to_dict())
    assert rehydrated.payload is None

    verdict = EvaluateCandidateUseCase().execute(
        run_root=root, candidate=candidate, content=rehydrated
    )

    assert verdict["disposition"] == "REJECTED"
    assert REFUSAL_MISSING_REQUIRED_REPLY_FIELDS in verdict["refusals"]
