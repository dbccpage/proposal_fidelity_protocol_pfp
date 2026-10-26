"""LLM Turn Use Cases."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from typing import Any, Mapping

from ..domain import (
    LLM_TURN_FAMILY,
    REFUSAL_ATTEMPT_ID_MISBIND,
    REFUSAL_AUTHORITY_NON_NONE,
    REFUSAL_CANDIDATE_CONTENT_MISBIND,
    REFUSAL_CONTENT_DIGEST_MISMATCH,
    REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    REFUSAL_INHERITED_MEANING,
    REFUSAL_MISSING_REQUIRED_REPLY_FIELDS,
    AuthorityEffect,
    BudgetExhaustedError,
    BytePayload,
    CandidateArtifactV1,
    CanonicalizationError,
    InvariantViolationError,
    LlmTurnAttemptV1,
    LlmTurnContentArtifactV1,
    LlmTurnPayloadV1,
    LlmTurnRunRootV1,
    ResidualColour,
    llm_turn_task_packet_sha256,
    thaw,
)

# Both helpers are module-private in the aggregate, and both are imported rather
# than re-implemented on purpose: a second copy of the terminal derivation or of
# the candidate/content binding rule in the use-case layer is precisely the
# defect class this file has already been repaired for twice.
from ..domain.aggregates.llm_turn_run_root import (
    _assert_candidate_binds_content,
    _derive_llm_turn_terminal,
)

#: The only encoding `LlmTurnContentArtifactV1` admits. Declared here rather
#: than inlined, matching `code_change.PATCH_ENCODING_UNIFIED_DIFF`.
CONTENT_ENCODING = "utf8-lf-v1"


@dataclasses.dataclass(frozen=True, slots=True)
class LlmTurnSubmissionBody:
    """The turn body and submission refs travelling beside a content artifact.

    `LlmTurnContentArtifactV1` binds a digest, not bytes, and its
    `identity_fields` deliberately omit `explicit_payload`. That makes the
    payload the one place a submission can carry the reply text and its refs
    forward to evaluation without perturbing `content_id`.
    """

    reply_text: str
    candidate_label: str
    parent_packet_id: str | None = None
    dual_witness_ref: str | None = None


class CreateTurnUseCase:
    """Creates a new LLM turn execution run."""

    def execute(
        self,
        *,
        task_id: str,
        objective: str,
        role: str = "assistant",
        # `"symbol_game_turn"` is not in `ALLOWED_TURN_KINDS`
        # ({claimed_result, code_change, prose, status, tool_result}), so
        # calling this use case with its own default always raised
        # "turn_kind is unsupported". Only `TurnController.create_turn`, which
        # passes `"prose"`, ever reached a run root -- so the sole caller in the
        # suite masked the broken default. Aligned with the controller.
        turn_kind: str = "prose",
        candidate_budget: int = 4,
        operation_budget: int = 16,
        prompt_artifact_id: str | None = None,
        prompt_body: str | None = None,
        required_reply_fields: tuple[str, ...] = ("status", "step_claims", "obstruction_receipts"),
        kill_conditions: tuple[str, ...] = ("F-01_inherited_meaning",),
    ) -> LlmTurnRunRootV1:
        body_sha256 = None
        body_len = None
        if prompt_body is not None:
            bp = BytePayload.from_str(prompt_body)
            body_sha256 = bp.digest.hex_digest
            body_len = len(bp)

        payload = LlmTurnPayloadV1.create(
            task_id=task_id,
            objective=objective,
            role=role,
            turn_kind=turn_kind,
            candidate_budget=candidate_budget,
            operation_budget=operation_budget,
            prompt_artifact_id=prompt_artifact_id,
            prompt_body_sha256=body_sha256,
            prompt_body_bytes_len=body_len,
            required_reply_fields=required_reply_fields,
            kill_conditions=kill_conditions,
            authority_effect=AuthorityEffect.NONE.value,
        )

        # `task_packet_id` identifies the task; `task_packet_sha256` identifies
        # the packet's *content*. Both were `sha256(task_id)`, so the content
        # was bound to nothing: two turns for one task id with different
        # objectives or budgets shared a `run_root_id`, and one repository save
        # overwrote the other.
        task_sha = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
        return LlmTurnRunRootV1(
            task_packet_id=task_sha,
            task_packet_sha256=llm_turn_task_packet_sha256(payload),
            turn_kind=turn_kind,
            candidate_ids=(),
            content_ids=(),
            attempts=(),
            refusals=(),
            terminal_status="OpenEvaluation",
            open_obstruction_ids=(),
            explicit_task_id=task_id,
            explicit_payload=payload,
        )


class ParseMachineBlockUseCase:
    """Extracts and parses JSON machine block from raw reply text."""

    def execute(self, reply_text: str) -> dict[str, Any]:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply_text, re.DOTALL)
        if match:
            raw_json = match.group(1)
        else:
            raw_json = reply_text.strip()
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise InvariantViolationError(f"Failed to parse machine block JSON: {exc}") from exc


class SubmitCandidateUseCase:
    """Submits and validates a candidate turn against the active run root."""

    def execute(
        self,
        *,
        run_root: LlmTurnRunRootV1,
        candidate_id: str,
        producer_id: str,
        reply_text: str,
        parent_packet_id: str | None = None,
        dual_witness_ref: str | None = None,
    ) -> tuple[LlmTurnRunRootV1, CandidateArtifactV1, LlmTurnContentArtifactV1]:
        budget_limit = int(run_root.payload.candidate_budget)
        # `LlmTurnRunRootV1` holds `candidate_ids`, not candidate artifacts.
        # This read was `run_root.candidates`, which does not exist, so the
        # budget check raised `AttributeError` before it could compare anything
        # -- a budget gate that crashed instead of enforcing.
        if len(run_root.candidate_ids) >= budget_limit:
            raise BudgetExhaustedError(
                f"Candidate budget ({budget_limit}) exhausted for task {run_root.task_id}"
            )

        payload_vo = BytePayload.from_str(reply_text)
        content_sha256 = payload_vo.digest.hex_digest
        byte_count = len(payload_vo)

        # Both artifacts were built against an earlier shape of the domain and
        # named fields the exported classes do not have, so every first
        # submission raised `TypeError` here and the reconstruction below was
        # unreachable.
        #
        # `LlmTurnContentArtifactV1` is a content-addressed *binding*: it carries
        # the digest and byte count of the turn body, never the bytes, and its
        # identity is the derived `content_id` property rather than a caller
        # label. `identity_fields` deliberately excludes `explicit_payload`, so
        # the reply text and the submission refs ride in that side channel where
        # they cannot perturb the digest.
        content_art = LlmTurnContentArtifactV1(
            packet_id=run_root.task_packet_id,
            producer_id=producer_id,
            content_encoding=CONTENT_ENCODING,
            content_sha256=content_sha256,
            content_byte_count=byte_count,
            authority_effect=AuthorityEffect.NONE.value,
            explicit_task_id=str(run_root.task_id),
            explicit_payload=LlmTurnSubmissionBody(
                reply_text=reply_text,
                candidate_label=candidate_id,
                parent_packet_id=parent_packet_id,
                dual_witness_ref=dual_witness_ref,
            ),
        )

        # `CandidateArtifactV1.candidate_id` is likewise a canonical digest over
        # the identity fields, not the caller's `candidate_id` label.
        #
        # The shape below is not free-form. `_assert_candidate_binds_content`
        # is the domain's own binding rule and it requires exactly this:
        # `payload` must rebuild the content artifact through `from_dict`,
        # `witness` must equal `content_sha256`, and `metadata` must carry
        # `content_id` and `family`. The previous hand-rolled payload satisfied
        # none of it, so no binding could be checked -- which is what let a
        # caller swap the reply text under a fixed `content_id`.
        #
        # `reply_sha256` binds the body that travels in `explicit_payload`.
        # That field is excluded from `content_id` by design, so without a
        # digest recorded *here* -- inside the candidate's own identity -- the
        # evaluator would have no way to tell a substituted reply from the one
        # the artifact was minted for.
        cand_art = CandidateArtifactV1(
            packet_id=run_root.task_packet_id,
            producer_id=producer_id,
            payload=content_art.to_dict(),
            witness=content_sha256,
            metadata={
                "content_id": content_art.content_id,
                "family": LLM_TURN_FAMILY,
                "reply_sha256": content_sha256,
                "reply_bytes_len": byte_count,
                "candidate_label": candidate_id,
                "parent_packet_id": parent_packet_id,
                "dual_witness_ref": dual_witness_ref,
            },
            authority_effect=AuthorityEffect.NONE.value,
        )

        # This called `LlmTurnRunRootV1.create(...)`, a factory that does not
        # exist, with `candidates=`, `evaluations=` and `disposition=` -- none of
        # which are fields of the aggregate. The whole call was written against
        # an earlier shape of the run root and could never have run.
        #
        # `CreateTurnUseCase` above already builds the current shape directly, so
        # the only honest reconstruction is to advance the two id tuples the
        # aggregate actually carries and let `__post_init__` re-validate
        # ordering, uniqueness and the budget ceiling. Both tuples go through
        # `_validate_ordered_unique_strings`, which *refuses* unsorted input
        # rather than sorting it -- and these ids are digests, so append order is
        # effectively random. They must be sorted here.
        if cand_art.candidate_id in run_root.candidate_ids:
            raise InvariantViolationError(
                "Candidate already submitted for this run root: "
                f"{cand_art.candidate_id}"
            )
        # Byte-identical content from the same producer on the same packet *is*
        # the same content artifact, so `content_ids` unions. `candidate_ids`
        # refuses instead, because a repeat submission that silently failed to
        # advance the tuple would leave the budget gate unable to ever exhaust.
        #
        # The two id tuples alone are not a valid run root. `_derive_llm_turn_terminal`
        # returns `InvalidPacket` whenever an attempt is absent, so a root that
        # advanced the ids while leaving `attempts=()` and
        # `terminal_status="OpenEvaluation"` failed the domain's own
        # `verify_llm_turn_run_root_shape` with
        # `TERMINAL_NOT_DERIVED_FROM_EVIDENCE` -- every submission produced an
        # aggregate that could not be persisted or re-read. The attempt is the
        # evidence the terminal is derived *from*, so it is recorded here and
        # the terminal is derived rather than asserted.
        attempt = LlmTurnAttemptV1(
            attempt_index=len(run_root.attempts),
            candidate_id=cand_art.candidate_id,
            content_id=content_art.content_id,
            operation_count=1,
            disposition="AcceptedForEvaluation",
            refusal_codes=(),
            authority_effect=AuthorityEffect.NONE.value,
        )
        candidate_ids = tuple(sorted((*run_root.candidate_ids, cand_art.candidate_id)))
        content_ids = tuple(sorted({*run_root.content_ids, content_art.content_id}))
        attempts = (*run_root.attempts, attempt)
        terminal_status = _derive_llm_turn_terminal(
            refusals=set(run_root.refusals),
            open_obstructions=set(run_root.open_obstruction_ids),
            has_candidate=bool(candidate_ids),
            has_content=bool(content_ids),
            has_attempt=bool(attempts),
            turn_kind=run_root.turn_kind,
        )
        updated_root = dataclasses.replace(
            run_root,
            candidate_ids=candidate_ids,
            content_ids=content_ids,
            attempts=attempts,
            terminal_status=terminal_status,
        )

        return updated_root, cand_art, content_art


class EvaluateCandidateUseCase:
    """Evaluates a candidate turn against declared kill conditions and reply structure."""

    def execute(
        self,
        *,
        run_root: LlmTurnRunRootV1,
        candidate: CandidateArtifactV1,
        content: LlmTurnContentArtifactV1,
    ) -> dict[str, Any]:
        refusals: list[str] = []

        # `_assert_candidate_binds_content` below proves only that these two
        # artifacts belong to *each other*. It says nothing about whether they
        # belong to *this* run root, and nothing did: a valid pair minted under
        # task B evaluated cleanly under task A's objective, required reply
        # fields and kill conditions and came back ACCEPTED, and a freshly
        # forged candidate carrying its own dual witness could be evaluated
        # without ever having been submitted into the root at all.
        #
        # Membership is checked first and returns immediately, because every
        # later step reads evidence -- the reply text, the kill conditions, the
        # dual witness -- and evidence that is not part of this aggregate should
        # not be read at all, let alone scored.
        # The linking attempt must be an *accepted* one. Matching on the two
        # ids alone treated a refusal as membership evidence: a shape-valid
        # `TypedRefusal` root whose only attempt was `Refused` or
        # `BudgetExhausted` could be handed back to this evaluator and collect
        # ACCEPTED, because the ids still matched. An attempt records what
        # happened to a submission, not merely that one occurred.
        attempt_links_pair = any(
            attempt.candidate_id == candidate.candidate_id
            and attempt.content_id == content.content_id
            and attempt.disposition == "AcceptedForEvaluation"
            for attempt in run_root.attempts
        )
        if (
            candidate.packet_id != run_root.task_packet_id
            or content.packet_id != run_root.task_packet_id
            or candidate.candidate_id not in run_root.candidate_ids
            or content.content_id not in run_root.content_ids
            or not attempt_links_pair
        ):
            return {
                "candidate_id": candidate.candidate_id,
                "disposition": "REJECTED",
                "refusals": [REFUSAL_ATTEMPT_ID_MISBIND],
                "authority_effect": AuthorityEffect.NONE.value,
            }

        # The reply body travels in `content.explicit_payload`, which
        # `identity_fields` deliberately excludes from `content_id`. Reading it
        # and acting on it -- as this did -- trusts evidence the artifact never
        # bound: a caller could swap `explicit_payload` while `content_id`
        # stayed byte-for-byte identical, drop an inherited-meaning phrase or
        # invent a dual witness, and collect an ACCEPTED verdict for a reply no
        # digest covers.
        #
        # So nothing in the body is trusted until two bindings hold: the
        # candidate must be bound to *this* content artifact, and the body's
        # recomputed digest must match the digest the candidate minted. Only
        # then is the text read, and the dual witness is taken from the bound
        # metadata rather than from the unbound body.
        try:
            _assert_candidate_binds_content(candidate, content)
        except CanonicalizationError:
            # The domain reports every binding failure this way. Catching wider
            # than that would turn a genuine bug into a quiet refusal.
            refusals.append(REFUSAL_CANDIDATE_CONTENT_MISBIND)

        meta_raw = thaw(candidate.metadata)
        meta = meta_raw if isinstance(meta_raw, Mapping) else {}
        dual_witness_ref = meta.get("dual_witness_ref")

        body = content.payload
        reply_text = ""
        if isinstance(body, LlmTurnSubmissionBody):
            observed = BytePayload.from_str(body.reply_text)
            if (
                observed.digest.hex_digest != content.content_sha256
                or len(observed) != content.content_byte_count
                or observed.digest.hex_digest != meta.get("reply_sha256")
            ):
                # The body is not the one this artifact was minted for.
                refusals.append(REFUSAL_CONTENT_DIGEST_MISMATCH)
            else:
                reply_text = body.reply_text
        else:
            # A content artifact rehydrated from `to_dict` carries no body, by
            # design. Refuse rather than score an empty reply as if it had been
            # read.
            refusals.append(REFUSAL_MISSING_REQUIRED_REPLY_FIELDS)

        # 1. Authority effect check
        if candidate.authority_effect != AuthorityEffect.NONE.value or content.authority_effect != AuthorityEffect.NONE.value:
            refusals.append(REFUSAL_AUTHORITY_NON_NONE)

        # 2. Parse machine block
        try:
            parsed = ParseMachineBlockUseCase().execute(reply_text)
        except Exception:
            parsed = {}
            if REFUSAL_MISSING_REQUIRED_REPLY_FIELDS not in refusals:
                refusals.append(REFUSAL_MISSING_REQUIRED_REPLY_FIELDS)

        # 3. Check required fields
        for rf in run_root.payload.required_reply_fields:
            if rf not in parsed:
                if REFUSAL_MISSING_REQUIRED_REPLY_FIELDS not in refusals:
                    refusals.append(REFUSAL_MISSING_REQUIRED_REPLY_FIELDS)
                break

        # 4. Check exact dual witness
        if parsed.get("residual_colour") == ResidualColour.EXACT.value:
            if not dual_witness_ref:
                refusals.append(REFUSAL_EXACT_WITHOUT_DUAL_WITNESS)

        # 5. Check inherited meaning kill condition
        #
        # `payload.kill_conditions` is a tuple of `Code` value objects, not of
        # strings, and `Code.__eq__` does not admit a bare `str`. So
        # `"F-01_inherited_meaning" in run_root.payload.kill_conditions` was
        # unconditionally False and this kill condition could never fire on any
        # input -- a declared gate that was structurally dead. Compare the
        # carried values.
        kill_conditions = {
            str(getattr(code, "value", code))
            for code in run_root.payload.kill_conditions
        }
        if "F-01_inherited_meaning" in kill_conditions:
            # Check for vague prose claims
            if "I think" in reply_text or "probably" in reply_text:
                refusals.append(REFUSAL_INHERITED_MEANING)

        disposition = "REJECTED" if refusals else "ACCEPTED"

        return {
            "candidate_id": candidate.candidate_id,
            "disposition": disposition,
            "refusals": refusals,
            "authority_effect": AuthorityEffect.NONE.value,
        }
