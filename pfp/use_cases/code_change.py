"""Code Change Proposal Use Cases.

These four stages are a thin orchestration layer over the canonical domain
lifecycle in ``domain/aggregates/code_change_run_root.py``. They deliberately
own no state machine of their own:

    build_code_change_proposal_envelope   -> PacketEnvelopeV2     (stage 1)
    bind_patch_bytes + attach_candidate   -> patch + candidate    (stage 2)
    <gate evaluation>                     -> GateReceiptV1...     (stage 3)
    evaluate_code_change_candidate        -> CodeChangeRunRootV1  (stage 4)

The previous shape built a ``CodeChangeRunRootV1`` in stage 1 and appended to
it in stage 2. That was a second, parallel state machine, and it could never
meet the first one: it set ``task_packet_id`` to ``sha256(task_id)``, whereas
the canonical ``packet_id`` is a digest over the *payload*. Every downstream id
was therefore bound to a packet identity the domain would never mint, which is
why ``evaluate_code_change_candidate`` was unreachable from application code
and why the run root here never acquired a terminal status from an evaluator.

The run root is the **result** of evaluation, not a session ledger. Whatever
orchestration state is genuinely needed between stages lives in
``CodeChangeSession`` below, which is explicitly not an aggregate and carries
no authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from ..domain import (
    REFUSAL_PROTECTED_FILE_PATCHED,
    REFUSAL_TOUCHED_OUTSIDE_OWNED,
    BudgetExhaustedError,
    CandidateArtifactV1,
    CanonicalizationError,
    CodeChangePatchArtifactV1,
    CodeChangeProposalPayloadV1,
    CodeChangeRunRootV1,
    GateReceiptV1,
    PacketEnvelopeV2,
    # The domain's own candidate/patch binding check, now a public seam: it
    # reconstructs the patch from `candidate.payload` via `from_dict` and checks
    # patch_id, witness, metadata patch_id and `family`. The application layer
    # needs exactly this before building a gate receipt, and a second copy of a
    # security check is how the two drift. One implementation, imported.
    assert_candidate_binds_patch,
    attach_candidate,
    bind_patch_bytes,
    build_code_change_proposal_envelope,
    canonical_bytes,
    evaluate_code_change_candidate,
    is_path_contained_in_root,
    parse_code_change_proposal_envelope,
    verify_patch_bytes,
)

#: The only encoding this use case submits. Declared here rather than inline so
#: a second encoding is a visible edit; ``PATCH_ENCODINGS`` holds the admitted set.
PATCH_ENCODING_UNIFIED_DIFF = "unified-diff-utf8-lf-v1"


@dataclass(frozen=True)
class BoundCandidate:
    """A candidate, its patch, and the exact bytes the patch was bound from.

    The bytes travel with the artifacts because every later stage must be able
    to re-verify them against ``patch_sha256``. A stage that accepts a patch
    artifact without the bytes can only take the artifact's own word for its
    contents, and a content-addressed artifact whose content is never presented
    is an assertion rather than evidence.
    """

    candidate: CandidateArtifactV1
    patch: CodeChangePatchArtifactV1
    patch_bytes: bytes


#: Prefix on the ``CanonicalizationError`` raised when a session's own fields
#: are not internally derivable from its envelope.
REFUSAL_FORGED_SESSION = "FORGED_SESSION"


def _require_digest_set(values: tuple[str, ...], label: str) -> None:
    """Ledgers hold sorted, unique, lowercase 64-hex digests. Nothing else.

    Without this a caller could seed a session with ``("", "")`` or with a
    producer's label, and the membership checks in
    ``_require_bound_for_evaluation`` would compare against whatever was
    injected. The ledger is the thing those checks appeal to, so its shape has
    to be validated at construction rather than assumed.
    """
    if not isinstance(values, tuple):
        raise CanonicalizationError(f"{REFUSAL_FORGED_SESSION}: {label} must be a tuple")
    for value in values:
        if not isinstance(value, str) or len(value) != 64:
            raise CanonicalizationError(
                f"{REFUSAL_FORGED_SESSION}: {label} entries must be 64-character digests"
            )
        if any(character not in "0123456789abcdef" for character in value):
            raise CanonicalizationError(
                f"{REFUSAL_FORGED_SESSION}: {label} entries must be lowercase hex"
            )
    if list(values) != sorted(set(values)):
        raise CanonicalizationError(
            f"{REFUSAL_FORGED_SESSION}: {label} must be unique and sorted"
        )


@dataclass(frozen=True)
class CodeChangeSession:
    """Pre-evaluation orchestration state. **Not** a run root, not an aggregate.

    It has no ``terminal_status``, no ``refusals`` and no ``authority_effect``,
    because it is not the record of an evaluation and must not be mistakable for
    one. ``evaluate_code_change_candidate`` produces that record.

    **Everything derivable is derived.** ``payload`` and ``task_id`` are read
    out of the envelope, never stored alongside it. The earlier shape kept
    independent copies, which made the session forgeable in the one way that
    mattered: a caller could pair envelope A with payload B and hand the gates a
    *narrower* set of fences than the packet actually declares -- different
    ``owned_paths``, different ``protected_paths``, different ``required_gates``,
    a larger ``candidate_budget`` -- while every downstream consistency check
    still passed, because those checks compared against the substituted payload.
    ``parse_code_change_proposal_envelope`` is now the single source, and it also
    verifies the envelope's own internal bindings.

    **Known limitation, stated rather than papered over.** This class is publicly
    constructible, so ledger membership proves *state consistency*, not that
    ``submit_patch`` was actually called. What that residual buys an attacker is
    now narrow: ``_require_bound_for_evaluation`` still requires a candidate that
    genuinely binds a genuinely-bound patch against this exact packet, which is
    precisely what ``attach_candidate`` produces -- so a forged session cannot
    smuggle in an artifact that would not have been admitted anyway.

    **Budget enforcement is host testimony, and the gap is wider than this
    class.** A manufactured session can reset ``candidate_ids``, but that is not
    the only route: ``evaluate_code_change_candidate`` takes
    ``prior_candidate_count`` and ``operation_count`` as arguments, so *both*
    budget counters are caller-supplied regardless of how the session was built.
    Stated plainly: candidate and operation budget enforcement remains
    host-supplied and resettable. It is a resource-fence gap, not currently an
    authority-fence gap.

    The reason it is not an authority gap is structural rather than incidental.
    ``evaluate_code_change_candidate`` adds ``BUDGET_HOST_STATE_ABSENT`` to the
    open obstructions *unconditionally*, and discards its own
    ``host_budget_counters_bound`` parameter, so no host can currently discharge
    it. A run root therefore cannot reach a positive terminal on the strength of
    counters it was simply told. A future change that makes that obstruction
    conditional would turn this resource gap into an authority gap, and must not
    land before the counters are bound to something the host cannot restate.

    **Session opacity is a prerequisite for admitting typed producer claims.**
    Claims are absent from this path today. When a typed ``ProducerClaim`` is
    introduced, it must not be introduced against a publicly constructible
    session: a caller could otherwise attach a claimed candidate directly and
    manufacture the admission ledger that vouches for it, which would make the
    claim's provenance exactly as forgeable as the bare bool it replaced.
    """

    envelope: PacketEnvelopeV2
    candidate_ids: tuple[str, ...] = ()
    patch_ids: tuple[str, ...] = ()
    #: Derived in ``__post_init__``; never a constructor argument. Excluded from
    #: comparison and repr so two sessions with the same envelope compare equal.
    _payload: CodeChangeProposalPayloadV1 | None = field(
        init=False, repr=False, compare=False, default=None
    )

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, PacketEnvelopeV2):
            raise CanonicalizationError(
                f"{REFUSAL_FORGED_SESSION}: envelope must be a PacketEnvelopeV2"
            )
        # Parsing is the validation: this refuses an envelope whose family,
        # payload or manifest-root bindings do not agree with each other.
        object.__setattr__(
            self, "_payload", parse_code_change_proposal_envelope(self.envelope)
        )
        _require_digest_set(self.candidate_ids, "candidate_ids")
        _require_digest_set(self.patch_ids, "patch_ids")

    @property
    def payload(self) -> CodeChangeProposalPayloadV1:
        """The packet's own payload, parsed from the envelope. Never supplied."""
        assert self._payload is not None  # set unconditionally in __post_init__
        return self._payload

    @property
    def task_id(self) -> str:
        return str(self.envelope.task_id)

    @property
    def packet_id(self) -> str:
        return self.envelope.packet_id


class CreateCodeChangeProposalUseCase:
    """Builds the canonical proposal envelope for a code-change task."""

    def execute(
        self,
        *,
        task_id: str,
        objective: str,
        base_revision: str,
        owned_paths: tuple[str, ...],
        protected_paths: tuple[str, ...],
        path_manifest_root: str | None = None,
        candidate_budget: int = 4,
        operation_budget: int = 16,
        required_gates: tuple[str, ...] = ("gate_syntax", "gate_ownership", "gate_contract"),
    ) -> CodeChangeSession:
        payload = CodeChangeProposalPayloadV1(
            objective=objective,
            source_revision=base_revision,
            owned_paths=owned_paths,
            protected_paths=protected_paths,
            allowed_transforms=("edit", "emit_evidence", "test"),
            candidate_budget=candidate_budget,
            operation_budget=operation_budget,
            required_gates=tuple(sorted(set(required_gates))),
            # Passed through rather than dropped. The domain *derives* this
            # digest from the owned and protected paths, and refuses a supplied
            # value that disagrees ("path_manifest_root does not bind owned and
            # protected paths"). So a caller may assert the fences it expects
            # and be refused if the packet does not match. The previous
            # signature accepted this argument and silently discarded it, which
            # read as an assertion while checking nothing. `None` means derive.
            path_manifest_root=path_manifest_root or "",
        )
        # The envelope mints the packet identity. Nothing here computes an id,
        # and the session derives its payload back out of the envelope rather
        # than keeping this local copy.
        envelope = build_code_change_proposal_envelope(payload, task_id=task_id)
        return CodeChangeSession(envelope=envelope)


class SubmitPatchCandidateUseCase:
    """Binds patch bytes and attaches them to the packet as an untrusted candidate."""

    def execute(
        self,
        *,
        session: CodeChangeSession,
        producer_id: str,
        patch_text: str,
    ) -> tuple[CodeChangeSession, BoundCandidate]:
        patch_bytes = patch_text.encode("utf-8")

        # The patch is bound by the domain factory, never hand-rolled. It
        # *derives* touched paths from the bytes and refuses a declared/derived
        # mismatch, so a producer cannot declare paths its patch did not touch.
        patch = bind_patch_bytes(
            packet_id=session.packet_id,
            producer_id=producer_id,
            base_source_revision=session.payload.source_revision,
            patch_encoding=PATCH_ENCODING_UNIFIED_DIFF,
            patch_bytes=patch_bytes,
        )

        # `attach_candidate` is the domain's own binding factory: it sets
        # `payload` to the full `patch.to_dict()`, witnesses `patch_sha256`,
        # records the path-fence refusals, and re-checks packet and revision
        # agreement. Hand-building `CandidateArtifactV1` here -- the previous
        # shape -- produced a five-field payload that `verify_code_change_run_
        # root` rejected as `CANDIDATE_PATCH_MISBIND`. There is one binding
        # function, and this calls it.
        #
        # No producer claim is recorded, and none can be supplied here.
        #
        # An earlier revision took loose `claimed_valid` / `claimed_terminal`
        # arguments so a claim could enter through the admitted path. That was
        # the wrong trade. A bare bool reaching this signature has no provenance:
        # nothing ties it to a producer's actual response, so any caller can
        # invent one and corrupt the audit record. Evaluation stays independent
        # either way -- `disposition` never reads the claim -- but the record of
        # *who claimed what* would become unreliable, and that record is the only
        # reason `model_claimed_passed` exists.
        #
        # A claim will be admitted again when it can arrive as a typed untrusted
        # object bound to durable provider bytes (producer_id,
        # provider_attempt_id, raw_response_sha256, extraction_receipt), which is
        # tracked separately. Until then `None` is the honest value: the producer
        # claimed nothing *through this path*, which is distinct from claiming
        # failure.
        candidate = attach_candidate(session.envelope, patch, producer_id=producer_id)

        # Content-addressed identity means resubmitting the identical patch from
        # the identical producer *is* the same candidate. Membership is checked
        # before capacity so a duplicate never consumes budget -- the reverse
        # order refuses a resubmission at the boundary, while the ledger, being
        # a sorted unique set, would not have grown anyway.
        if candidate.candidate_id not in session.candidate_ids:
            budget_limit = int(session.payload.candidate_budget)
            if len(session.candidate_ids) >= budget_limit:
                raise BudgetExhaustedError(
                    f"Candidate budget ({budget_limit}) exhausted for code change {session.task_id}"
                )

        updated = replace(
            session,
            candidate_ids=tuple(sorted({*session.candidate_ids, candidate.candidate_id})),
            patch_ids=tuple(sorted({*session.patch_ids, patch.patch_id})),
        )
        return updated, BoundCandidate(candidate=candidate, patch=patch, patch_bytes=patch_bytes)


#: The evaluator that produces these receipts. Pinned here rather than taken as
#: a parameter: a caller-supplied evaluator id would let a producer nominate its
#: own judge, and ``evaluator_id`` is the field a reader uses to decide how much
#: a disposition is worth.
GATE_EVALUATOR_ID = "symbol-game-patch-gate-evaluator-v1"

#: Admitted gate ids used here. ``REQUIRED_GATE_IDS`` holds the full set; note
#: there is no ``gate_protected`` in it, so protected-path violations are
#: reported under ``gate_contract`` rather than under an id the domain refuses.
GATE_SYNTAX = "gate_syntax"
GATE_OWNERSHIP = "gate_ownership"
GATE_CONTRACT = "gate_contract"

#: Prefix on the ``CanonicalizationError`` raised when the artifacts presented
#: for evaluation are not the ones this session admitted.
REFUSAL_UNBOUND_EVALUATION_INPUT = "UNBOUND_EVALUATION_INPUT"


def _require_bound_for_evaluation(session: CodeChangeSession, bound: BoundCandidate) -> None:
    """Refuse to evaluate anything not provably bound to this session's packet.

    This runs to completion **before** the first receipt is constructed. The
    previous shape had no such check, and a probe confirmed the consequence: a
    fabricated patch and candidate, present in no ledger, from producer
    ``"attacker"``, with ``payload={"anything": "at all"}``, drew three PASS
    receipts. A receipt is the evaluator's word that it examined a specific
    artifact; minting one for an artifact that was never admitted makes the
    signature worthless everywhere else it appears.

    Each check closes a distinct substitution:

    ``verify_patch_bytes``  the bytes hash to ``patch_sha256``. Without it the
                            artifact's content is its own unchecked claim and a
                            patch could be swapped after binding.
    packet agreement        both artifacts belong to *this* packet, blocking a
                            cross-run replay of an otherwise valid candidate.
    ledger membership       both ids were admitted through this session, so an
                            artifact minted outside the flow cannot be presented.
    witness + payload       the candidate still describes this exact patch, with
                            the payload re-derived rather than trusted.
    """
    # 1. The bytes are what the artifact says they are.
    #
    # Only the declared validation failures are caught. A bare `except Exception`
    # here would convert a programming defect -- an AttributeError from a renamed
    # field, a NameError, a TypeError from a signature change -- into an ordinary
    # unbound-input refusal. That is precisely the masking pattern that let these
    # modules sit dead behind a live import for as long as they did: a body that
    # raises on every call looks identical to a body that legitimately refuses,
    # once the difference has been swallowed. A defect must escape as itself.
    try:
        verify_patch_bytes(bound.patch, bound.patch_bytes)
    except (CanonicalizationError, TypeError) as exc:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: patch bytes do not match patch_sha256"
        ) from exc

    # 2. Both artifacts belong to this packet.
    if bound.patch.packet_id != session.packet_id:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: patch packet_id is not this session's packet"
        )
    if bound.candidate.packet_id != session.packet_id:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: candidate packet_id is not this session's packet"
        )

    # 3. The patch is against the declared source revision.
    if bound.patch.base_source_revision != session.payload.source_revision:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: patch base_source_revision does not match the task"
        )

    # 4. Both were admitted through this session, not minted elsewhere.
    if bound.candidate.candidate_id not in session.candidate_ids:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: candidate was not submitted to this session"
        )
    if bound.patch.patch_id not in session.patch_ids:
        raise CanonicalizationError(
            f"{REFUSAL_UNBOUND_EVALUATION_INPUT}: patch was not submitted to this session"
        )

    # 5. The candidate still describes this exact patch. Delegated to the
    #    domain, which reconstructs the patch from `candidate.payload` and
    #    checks patch_id, witness, metadata patch_id and family, raising
    #    `CANDIDATE_PATCH_MISBIND` with its own detail.
    assert_candidate_binds_patch(bound.candidate, bound.patch)


def _build_gate_receipt(
    *,
    gate_id: str,
    session: CodeChangeSession,
    candidate: CandidateArtifactV1,
    disposition: str,
    evidence: Mapping[str, Any],
    refusal_codes: tuple[str, ...] = (),
) -> GateReceiptV1:
    """The single audited construction path for a gate receipt.

    Every field is bound to exactly one source, and the binding is the point:

    ``model_claimed_passed``  the producer's own claim, carried through from
                              ``candidate.claimed_valid`` and **never** derived
                              from anything this evaluator concluded. It may be
                              ``None``, meaning the producer claimed nothing --
                              distinct from claiming failure.
    ``disposition``           this evaluator's independent conclusion, computed
                              from the artifact, never reading the claim above.
    ``evidence_sha256``       digest of the exact canonical bytes of the evidence
                              mapping, so a reader can recompute it.
    ``refusal_codes``         governed codes from the refusal vocabulary.
    ``packet_id``             this session's canonical packet.
    ``candidate_id``          the derived identity of the artifact evaluated.
    ``evaluator_id``          the pinned constant above.
    """
    evidence_bytes = canonical_bytes(evidence)
    return GateReceiptV1(
        gate_id=gate_id,
        packet_id=session.packet_id,
        candidate_id=candidate.candidate_id,
        evaluator_id=GATE_EVALUATOR_ID,
        disposition=disposition,
        model_claimed_passed=candidate.claimed_valid,
        evidence_sha256=hashlib.sha256(evidence_bytes).hexdigest(),
        evidence_byte_count=len(evidence_bytes),
        # `_validate_ordered_unique_strings` requires sorted-unique, and the
        # domain refuses a PASS carrying codes or a FAIL carrying none.
        refusal_codes=tuple(sorted(set(refusal_codes))),
    )


class EvaluatePatchGatesUseCase:
    """Evaluates a bound patch candidate against the admitted gates.

    Refuses before constructing any receipt unless the presented artifacts are
    provably the ones this session admitted -- see
    ``_require_bound_for_evaluation``.

    Gates read ``patch.touched_paths``, which ``bind_patch_bytes`` already
    derived from the patch bytes and validated as nonempty.
    """

    def execute(
        self,
        *,
        session: CodeChangeSession,
        bound: BoundCandidate,
    ) -> tuple[GateReceiptV1, ...]:
        _require_bound_for_evaluation(session, bound)

        candidate = bound.candidate
        patch = bound.patch
        receipts: list[GateReceiptV1] = []
        touched = tuple(patch.touched_paths)

        # Gate 1: syntax. The artifact exists and its bytes were just verified,
        # so the encoding parsed successfully -- binding *is* the syntax check.
        receipts.append(
            _build_gate_receipt(
                gate_id=GATE_SYNTAX,
                session=session,
                candidate=candidate,
                disposition="PASS",
                evidence={
                    "patch_sha256": patch.patch_sha256,
                    "patch_encoding": patch.patch_encoding,
                    "touched_paths": list(touched),
                },
            )
        )

        # Gate 2: ownership.
        owned = tuple(session.payload.owned_paths)
        unowned = sorted(
            path
            for path in touched
            if not any(is_path_contained_in_root(path, root) for root in owned)
        )
        receipts.append(
            _build_gate_receipt(
                gate_id=GATE_OWNERSHIP,
                session=session,
                candidate=candidate,
                disposition="FAIL" if unowned else "PASS",
                evidence={
                    "owned_paths": list(owned),
                    "touched_paths": list(touched),
                    "unowned_paths": unowned,
                },
                refusal_codes=(REFUSAL_TOUCHED_OUTSIDE_OWNED,) if unowned else (),
            )
        )

        # Gate 3: protected paths, reported under `gate_contract`.
        protected = tuple(session.payload.protected_paths)
        violated = sorted(
            path
            for path in touched
            if any(is_path_contained_in_root(path, root) for root in protected)
        )
        receipts.append(
            _build_gate_receipt(
                gate_id=GATE_CONTRACT,
                session=session,
                candidate=candidate,
                disposition="FAIL" if violated else "PASS",
                evidence={
                    "protected_paths": list(protected),
                    "touched_paths": list(touched),
                    "violated_paths": violated,
                },
                refusal_codes=(REFUSAL_PROTECTED_FILE_PATCHED,) if violated else (),
            )
        )

        return tuple(receipts)


class FinalizeCodeChangeRunUseCase:
    """Produces the run root by calling the canonical evaluator.

    This is the only place a ``CodeChangeRunRootV1`` comes into existence in the
    application layer. It is a *result*: the evaluator decides
    ``terminal_status`` and ``refusals`` from the packet, the candidate, the
    patch bytes and the receipts. Nothing here constructs one directly, which is
    what previously allowed a run root to exist carrying a terminal status no
    evaluator had assigned.
    """

    def execute(
        self,
        *,
        session: CodeChangeSession,
        bound: BoundCandidate,
        gate_receipts: tuple[GateReceiptV1, ...],
        prior_candidate_count: int = 0,
        operation_count: int = 1,
    ) -> CodeChangeRunRootV1:
        _require_bound_for_evaluation(session, bound)
        return evaluate_code_change_candidate(
            session.envelope,
            bound.candidate,
            bound.patch,
            gate_receipts,
            prior_candidate_count=prior_candidate_count,
            operation_count=operation_count,
            patch_bytes=bound.patch_bytes,
        )
