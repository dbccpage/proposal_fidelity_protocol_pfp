"""Code-change packet binding and evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

from . import code_change_packets as _packets

globals().update({key: value for key, value in vars(_packets).items() if not key.startswith("__")})


from .research_claim import canonical_json_artifact_bytes
from ..diff_parser import is_path_contained_in_root, parse_unified_diff
from ..entities.candidate_artifact import CandidateArtifactV1
from ..entities.packet_envelope import PacketEnvelopeV2


# Presenter Functions
def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads_strict_json(text: str, label: str = "JSON") -> Any:
    """Parse JSON while refusing duplicate keys and non-finite constants."""

    def _reject_constant(value: str) -> None:
        _fail(f"non-finite JSON number is refused: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_constant,
        )
    except CanonicalizationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise CanonicalizationError(f"invalid JSON in {label}") from exc


def verify_code_change_run_root_shape(
    value: CodeChangeRunRootV1 | Any,
) -> CodeChangeRunRootV1:
    """Parse + terminal re-derivation + attempt ID cross-links only."""


    if isinstance(value, CodeChangeRunRootV1):
        root = CodeChangeRunRootV1.from_dict(value.to_dict())
    else:
        root = CodeChangeRunRootV1.from_dict(
            _require_exact_dict(value, "code-change run root")
        )
    if root.terminal_status == "VerifiedProposal":
        _fail(REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN)
    candidate_set = set(root.candidate_ids)
    patch_set = set(root.patch_ids)
    for attempt in root.attempts:
        if attempt.candidate_id not in candidate_set:
            _fail(f"{REFUSAL_ATTEMPT_ID_MISBIND}: candidate_id")
        if attempt.patch_id not in patch_set:
            _fail(f"{REFUSAL_ATTEMPT_ID_MISBIND}: patch_id")
    expected = _derive_code_change_terminal(
        refusals=set(root.refusals),
        open_obstructions=set(root.open_obstruction_ids),
        has_candidate=bool(root.candidate_ids),
        has_patch=bool(root.patch_ids),
        has_attempt=bool(root.attempts),
    )
    if expected != root.terminal_status:
        _fail(
            f"{REFUSAL_TERMINAL_NOT_DERIVED}: wire={root.terminal_status} "
            f"derived={expected}"
        )
    return root


def render_code_change_run_root_markdown(root: CodeChangeRunRootV1) -> str:
    """Render a non-authoritative Markdown view of a verified run root."""
    if not isinstance(root, CodeChangeRunRootV1):
        raise TypeError("root must be a CodeChangeRunRootV1")
    verified = verify_code_change_run_root_shape(root)
    lines = [
        "# Code Change Proposal Run Root",
        "",
        f"- run_root_id: `{verified.run_root_id}`",
        f"- task_packet_id: `{verified.task_packet_id}`",
        f"- task_packet_sha256: `{verified.task_packet_sha256}`",
        f"- terminal_status: `{verified.terminal_status}`",
        f"- authority_effect: `{verified.authority_effect}`",
        "",
        "## Candidates",
    ]
    if verified.candidate_ids:
        for candidate_id in verified.candidate_ids:
            lines.append(f"- `{candidate_id}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Patches"])
    if verified.patch_ids:
        for patch_id in verified.patch_ids:
            lines.append(f"- `{patch_id}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Gate receipts"])
    if verified.gate_receipt_ids:
        for receipt_id in verified.gate_receipt_ids:
            lines.append(f"- `{receipt_id}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Attempts"])
    if verified.attempts:
        for attempt in verified.attempts:
            lines.append(
                f"- attempt[{attempt.attempt_index}] disposition=`{attempt.disposition}` "
                f"candidate=`{attempt.candidate_id}` patch=`{attempt.patch_id}`"
            )
            if attempt.refusal_codes:
                lines.append(
                    "  refusals: "
                    + ", ".join(f"`{code}`" for code in attempt.refusal_codes)
                )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Repairs"])
    if verified.repairs:
        for repair in verified.repairs:
            lines.append(
                f"- repair[{repair.repair_index}] "
                f"`{repair.prior_candidate_id}` -> `{repair.repaired_candidate_id}` "
                f"reason=`{repair.reason}`"
            )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Refusals"])
    if verified.refusals:
        for code in verified.refusals:
            lines.append(f"- `{code}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Open obstructions"])
    if verified.open_obstruction_ids:
        for code in verified.open_obstruction_ids:
            lines.append(f"- `{code}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append(
        "_This Markdown is a non-authoritative rendering. "
        "Machine state lives in the run root._"
    )
    lines.append("")
    return "\n".join(lines)


def verify_markdown_does_not_mutate_claims(
    root: CodeChangeRunRootV1, markdown: str
) -> None:
    """Fail closed if rendered Markdown erases a refusal or invents a claim."""
    verified = verify_code_change_run_root_shape(root)
    if type(markdown) is not str:
        raise TypeError("markdown must be a string")
    for code in verified.refusals:
        if f"`{code}`" not in markdown:
            _fail(REFUSAL_REFUSAL_ERASURE)
    forbidden_phrases = (
        "promotion_eligible",
        "promotion eligible",
        "trusted proposal",
        "verified safe to merge",
        "authority_effect: `Promote`",
        "authority_effect: Promote",
    )
    lowered = markdown.casefold()
    for phrase in forbidden_phrases:
        if phrase.casefold() in lowered:
            _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    if f"`{verified.terminal_status}`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    if "`None`" not in markdown and "authority_effect: `None`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)




# Use Cases Functions
def derive_touched_paths_from_patch_bytes(
    patch_encoding: str, patch_bytes: bytes
) -> tuple[str, ...]:
    """Host-derive touched paths from patch body bytes. Never trust callers."""
    if type(patch_bytes) is not bytes:
        raise TypeError("patch_bytes must be exact bytes")
    _require_string(patch_encoding, "patch_encoding", nonempty=True)
    if patch_encoding not in PATCH_ENCODINGS:
        _fail("patch_encoding is unsupported")
    if patch_encoding == "unified-diff-utf8-lf-v1":
        try:
            text = patch_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail(f"unified-diff patch is not utf-8: {exc}")
        parse_res = parse_unified_diff(text)
        if not parse_res.is_valid:
            _fail(f"unified-diff patch is invalid: {parse_res.error_message}")
        return _validate_path_tuple(parse_res.touched_paths, "derived_touched_paths")
    if patch_encoding == "file-set-v1":
        try:
            payload = json.loads(patch_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _fail(f"file-set-v1 patch is not valid JSON: {exc}")
        if type(payload) is not dict:
            _fail("file-set-v1 patch must be a JSON object")
        files = payload.get("files")
        if type(files) is not list:
            _fail("file-set-v1 patch.files must be an array")
        paths_list: list[str] = []
        for index, item in enumerate(files):
            if type(item) is not dict:
                _fail(f"file-set-v1 files[{index}] must be an object")
            path = item.get("path")
            paths_list.append(_validate_repo_relative_path(path, f"files[{index}].path"))
        if not paths_list:
            _fail("file-set-v1 patch yields no host-derived touched paths")
        return _validate_path_tuple(tuple(sorted(set(paths_list))), "derived_touched_paths")
    _fail("patch_encoding is unsupported")
    raise AssertionError("unreachable")


def bind_patch_bytes(
    *,
    packet_id: str,
    producer_id: str,
    base_source_revision: str,
    patch_encoding: str,
    patch_bytes: bytes,
    touched_paths: Sequence[str] | None = None,
    claimed_summary: str | None = None,
) -> CodeChangePatchArtifactV1:
    """Content-address immutable patch bytes; host-derive touched paths."""
    if type(patch_bytes) is not bytes:
        raise TypeError("patch_bytes must be exact bytes")
    if len(patch_bytes) > MAX_PATCH_BYTES:
        _fail("patch_bytes exceeds the patch resource limit")
    derived = derive_touched_paths_from_patch_bytes(patch_encoding, patch_bytes)
    if touched_paths is not None:
        declared = _validate_path_tuple(tuple(touched_paths), "touched_paths")
        if frozenset(declared) != frozenset(derived):
            _fail(REFUSAL_TOUCHED_PATH_DECLARED_MISMATCH)
    digest = hashlib.sha256(patch_bytes).hexdigest()
    return CodeChangePatchArtifactV1(
        packet_id=packet_id,
        producer_id=producer_id,
        base_source_revision=base_source_revision,
        patch_encoding=patch_encoding,
        patch_sha256=digest,
        patch_byte_count=len(patch_bytes),
        touched_paths=derived,
        claimed_summary=claimed_summary,
    )


def verify_patch_bytes(
    artifact: CodeChangePatchArtifactV1, patch_bytes: bytes
) -> None:
    """Fail closed if bytes mismatch digest or host-derived path set."""
    if type(patch_bytes) is not bytes:
        raise TypeError("patch_bytes must be exact bytes")
    digest = hashlib.sha256(patch_bytes).hexdigest()
    if (
        digest != artifact.patch_sha256
        or len(patch_bytes) != artifact.patch_byte_count
    ):
        _fail(REFUSAL_PATCH_DIGEST_MISMATCH)
    derived = derive_touched_paths_from_patch_bytes(
        artifact.patch_encoding, patch_bytes
    )
    if frozenset(derived) != frozenset(artifact.touched_paths):
        _fail(REFUSAL_TOUCHED_PATH_DECLARED_MISMATCH)


def build_code_change_proposal_envelope(
    payload: CodeChangeProposalPayloadV1,
    *,
    task_id: str,
    carrier_id: str = "core-repository-pathset-v1",
    step_budget: int | None = None,
) -> PacketEnvelopeV2:
    """Bind a typed code-change payload into the host-owned packet envelope."""
    if not isinstance(payload, CodeChangeProposalPayloadV1):
        raise TypeError("payload must be a CodeChangeProposalPayloadV1")
    _require_string(task_id, "task_id", nonempty=True)
    _require_string(carrier_id, "carrier_id", nonempty=True)
    budget = (
        payload.operation_budget
        if step_budget is None
        else _require_positive_int(step_budget, "step_budget")
    )
    return PacketEnvelopeV2(
        task_id=task_id,
        packet_family=CODE_CHANGE_PACKET_FAMILY,
        carrier_id=carrier_id,
        initial_state_hash=payload.path_manifest_root,
        payload=payload.to_dict(),
        constraints=CODE_CHANGE_ENVELOPE_CONSTRAINTS,
        protected_boundaries=payload.protected_paths,
        terminal_target=CODE_CHANGE_TERMINAL_TARGET,
        evidence_ceiling=CODE_CHANGE_EVIDENCE_CEILING,
        oracle_policy=CODE_CHANGE_ORACLE_POLICY,
        allowed_transforms=payload.allowed_transforms,
        step_budget=budget,
        framing_mode="strict",
        packet_kind="problem",
        parent_event_id=payload.parent_packet_id,
        source_digest=payload.path_manifest_root,
        authority_effect="None",
    )


def parse_code_change_proposal_envelope(
    value: PacketEnvelopeV2 | Mapping[str, Any],
) -> CodeChangeProposalPayloadV1:
    """Strictly parse and cross-check a code-change envelope and payload."""
    if isinstance(value, PacketEnvelopeV2):
        envelope = PacketEnvelopeV2.from_dict(value.to_dict())
    else:
        envelope = PacketEnvelopeV2.from_dict(
            _require_exact_dict(value, "code-change packet envelope")
        )
    if envelope.packet_family != CODE_CHANGE_PACKET_FAMILY:
        _fail("code-change packet family is unsupported")
    if envelope.constraints != CODE_CHANGE_ENVELOPE_CONSTRAINTS:
        _fail("code-change packet constraints are not canonical")
    if envelope.terminal_target != CODE_CHANGE_TERMINAL_TARGET:
        _fail("code-change packet terminal target is unsupported")
    if envelope.evidence_ceiling != CODE_CHANGE_EVIDENCE_CEILING:
        _fail("code-change packet evidence ceiling is unsupported")
    if envelope.oracle_policy != CODE_CHANGE_ORACLE_POLICY:
        _fail("code-change packet oracle policy is unsupported")
    if (
        envelope.packet_kind != "problem"
        or envelope.framing_mode != "strict"
        or envelope.authority_effect != "None"
    ):
        _fail("code-change packet framing or authority is unsupported")
    primitive_payload = thaw(envelope.payload)
    payload = CodeChangeProposalPayloadV1.from_dict(
        _require_exact_dict(primitive_payload, "code-change proposal payload")
    )
    if envelope.allowed_transforms != payload.allowed_transforms:
        _fail("envelope allowed_transforms do not match payload")
    if envelope.protected_boundaries != payload.protected_paths:
        _fail("envelope protected_boundaries do not match payload protected_paths")
    if envelope.initial_state_hash != payload.path_manifest_root:
        _fail("envelope initial_state_hash does not bind the path manifest")
    if envelope.source_digest != payload.path_manifest_root:
        _fail("envelope source_digest does not bind the path manifest")
    if envelope.parent_event_id != payload.parent_packet_id:
        _fail("envelope parent_event_id does not match payload parent_packet_id")
    return payload


def attach_candidate(
    envelope: PacketEnvelopeV2 | Mapping[str, Any],
    patch: CodeChangePatchArtifactV1,
    *,
    producer_id: str | None = None,
    claimed_terminal: str | None = None,
    claimed_valid: bool | None = None,
) -> CandidateArtifactV1:
    """Attach an immutable patch as an untrusted candidate for one packet."""
    payload = parse_code_change_proposal_envelope(envelope)
    if isinstance(envelope, PacketEnvelopeV2):
        packet = PacketEnvelopeV2.from_dict(envelope.to_dict())
    else:
        packet = PacketEnvelopeV2.from_dict(
            _require_exact_dict(envelope, "code-change packet envelope")
        )
    if not isinstance(patch, CodeChangePatchArtifactV1):
        raise TypeError("patch must be a CodeChangePatchArtifactV1")
    if patch.packet_id != packet.packet_id:
        _fail("patch packet_id does not match the task packet")
    if patch.base_source_revision != payload.source_revision:
        _fail("patch base_source_revision does not match the task source_revision")
    owned = set(payload.owned_paths)
    protected = set(payload.protected_paths)
    refusals: list[str] = []
    for path in patch.touched_paths:
        if not any(is_path_contained_in_root(path, o) for o in owned):
            refusals.append(REFUSAL_TOUCHED_PATH_OUTSIDE_OWNED)
        if any(is_path_contained_in_root(path, pr) for pr in protected):
            refusals.append(REFUSAL_TOUCHED_PATH_PROTECTED)
    producer = producer_id or patch.producer_id
    _require_stable_id(producer, "producer_id")
    return CandidateArtifactV1(
        packet_id=packet.packet_id,
        producer_id=producer,
        payload=patch.to_dict(),
        witness=patch.patch_sha256,
        claimed_terminal=claimed_terminal,
        claimed_valid=claimed_valid,
        metadata={
            "family": CODE_CHANGE_FAMILY,
            "patch_id": patch.patch_id,
            "path_fence_refusals": sorted(set(refusals)),
        },
        authority_effect="None",
    )


def _derive_code_change_terminal(
    *,
    refusals: set[str],
    open_obstructions: set[str],
    has_candidate: bool,
    has_patch: bool,
    has_attempt: bool,
) -> str:
    """Recompute terminal from evidence only. Never author VerifiedProposal."""
    if REFUSAL_CANDIDATE_BUDGET_EXCEEDED in refusals or (
        REFUSAL_OPERATION_BUDGET_EXCEEDED in refusals
    ):
        return "BudgetExhausted"
    if refusals:
        return "TypedRefusal"
    if not has_candidate or not has_patch or not has_attempt:
        return "InvalidPacket"
    if open_obstructions:
        if OBSTRUCTION_VERIFIER_RECEIPT_REQUIRED in open_obstructions:
            return "DeclaredUnverified"
        return "OpenEvaluation"
    return "TransportValidated"


def assert_candidate_binds_patch(
    candidate: CandidateArtifactV1, patch: CodeChangePatchArtifactV1
) -> None:
    """Refuse evaluating a candidate against a substituted patch artifact.

    Public because the application layer needs exactly this check before it
    builds a gate receipt, and a second copy of a security check is how the two
    drift apart. There is one implementation and this is it.
    """
    try:
        bound = CodeChangePatchArtifactV1.from_dict(
            _require_exact_dict(thaw(candidate.payload), "candidate.payload")
        )
    except (CanonicalizationError, TypeError, ValueError) as exc:
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: {exc}")
    if bound.patch_id != patch.patch_id:
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: patch_id mismatch")
    if candidate.witness != patch.patch_sha256:
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: witness mismatch")
    meta = thaw(candidate.metadata)
    if not isinstance(meta, Mapping):
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: metadata missing")
    if meta.get("patch_id") != patch.patch_id:
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: metadata patch_id mismatch")
    if meta.get("family") != CODE_CHANGE_FAMILY:
        _fail(f"{REFUSAL_CANDIDATE_PATCH_MISBIND}: family mismatch")


def evaluate_code_change_candidate(
    envelope: PacketEnvelopeV2 | Mapping[str, Any],
    candidate: CandidateArtifactV1,
    patch: CodeChangePatchArtifactV1,
    gate_receipts: Sequence[GateReceiptV1],
    *,
    prior_candidate_count: int = 0,
    operation_count: int = 1,
    patch_bytes: bytes | None = None,
    host_budget_counters_bound: bool = False,
    host_source_revision: str | None = None,
) -> CodeChangeRunRootV1:
    """Evaluate candidate against path fences and declared gate receipts."""
    _ = host_budget_counters_bound
    _ = host_source_revision
    payload = parse_code_change_proposal_envelope(envelope)
    if isinstance(envelope, PacketEnvelopeV2):
        packet = PacketEnvelopeV2.from_dict(envelope.to_dict())
    else:
        packet = PacketEnvelopeV2.from_dict(
            _require_exact_dict(envelope, "code-change packet envelope")
        )
    if not isinstance(candidate, CandidateArtifactV1):
        raise TypeError("candidate must be a CandidateArtifactV1")
    if not isinstance(patch, CodeChangePatchArtifactV1):
        raise TypeError("patch must be a CodeChangePatchArtifactV1")
    if candidate.packet_id != packet.packet_id or patch.packet_id != packet.packet_id:
        _fail("candidate/patch packet_id does not match the task packet")
    CandidateArtifactV1.from_dict(candidate.to_dict())
    assert_candidate_binds_patch(candidate, patch)
    _ = candidate.claimed_valid

    refusals: set[str] = set()
    open_obstructions: set[str] = set()

    if patch_bytes is None:
        refusals.add(REFUSAL_PATCH_BYTES_ABSENT)
    else:
        verify_patch_bytes(patch, patch_bytes)

    if prior_candidate_count >= payload.candidate_budget:
        refusals.add(REFUSAL_CANDIDATE_BUDGET_EXCEEDED)
    if operation_count > payload.operation_budget:
        refusals.add(REFUSAL_OPERATION_BUDGET_EXCEEDED)
    open_obstructions.add(OBSTRUCTION_BUDGET_HOST_STATE_ABSENT)
    open_obstructions.add(OBSTRUCTION_SOURCE_REVISION_UNBOUND)

    owned = set(payload.owned_paths)
    protected = set(payload.protected_paths)
    for path in patch.touched_paths:
        if not any(is_path_contained_in_root(path, o) for o in owned):
            refusals.add(REFUSAL_TOUCHED_PATH_OUTSIDE_OWNED)
        if any(is_path_contained_in_root(path, pr) for pr in protected):
            refusals.add(REFUSAL_TOUCHED_PATH_PROTECTED)

    if type(gate_receipts) not in {list, tuple}:
        _fail("gate_receipts must be a sequence")
    if len(gate_receipts) > MAX_GATE_RECEIPTS:
        _fail("gate_receipts exceed the resource limit")
    receipts = tuple(gate_receipts)
    any_declared_pass = False
    for receipt in receipts:
        if not isinstance(receipt, GateReceiptV1):
            raise TypeError("gate_receipts must contain GateReceiptV1")
        if receipt.packet_id != packet.packet_id:
            _fail("gate receipt packet_id mismatch")
        if receipt.candidate_id != candidate.candidate_id:
            _fail("gate receipt candidate_id mismatch")
        if receipt.model_claimed_passed is True and receipt.disposition != "PASS":
            refusals.add(REFUSAL_MODEL_VERDICT_UNTRUSTED)
        if receipt.disposition == "FAIL":
            refusals.add(REFUSAL_GATE_FAILED)
            refusals.update(receipt.refusal_codes)
        elif receipt.disposition == "REFUSED":
            refusals.add(REFUSAL_GATE_REFUSED)
            refusals.update(receipt.refusal_codes)
        elif receipt.disposition == "SKIPPED":
            open_obstructions.add(f"GATE_SKIPPED:{receipt.gate_id}")
        elif receipt.disposition == "PASS":
            any_declared_pass = True

    present_gates = {receipt.gate_id for receipt in receipts}
    for gate_id in payload.required_gates:
        if gate_id not in present_gates:
            refusals.add(REFUSAL_REQUIRED_GATE_MISSING)
            open_obstructions.add(f"GATE_ABSENT:{gate_id}")

    if any_declared_pass or (
        present_gates and not refusals and payload.required_gates
    ):
        open_obstructions.add(OBSTRUCTION_VERIFIER_RECEIPT_REQUIRED)

    attempt_disposition = "AcceptedForGates"
    attempt_refusals: tuple[str, ...] = ()
    if REFUSAL_CANDIDATE_BUDGET_EXCEEDED in refusals or (
        REFUSAL_OPERATION_BUDGET_EXCEEDED in refusals
    ):
        attempt_disposition = "BudgetExhausted"
        attempt_refusals = tuple(sorted(refusals))
    elif refusals:
        attempt_disposition = "Refused"
        attempt_refusals = tuple(sorted(refusals))

    terminal = _derive_code_change_terminal(
        refusals=refusals,
        open_obstructions=open_obstructions,
        has_candidate=True,
        has_patch=True,
        has_attempt=True,
    )

    packet_bytes = canonical_json_artifact_bytes(packet.to_dict())
    attempt = CodeChangeAttemptV1(
        attempt_index=0,
        candidate_id=candidate.candidate_id,
        patch_id=patch.patch_id,
        operation_count=operation_count,
        disposition=attempt_disposition,
        refusal_codes=attempt_refusals,
    )
    return CodeChangeRunRootV1(
        task_packet_id=packet.packet_id,
        task_packet_sha256=hashlib.sha256(packet_bytes).hexdigest(),
        candidate_ids=(candidate.candidate_id,),
        patch_ids=(patch.patch_id,),
        gate_receipt_ids=tuple(sorted(receipt.receipt_id for receipt in receipts)),
        attempts=(attempt,),
        repairs=(),
        refusals=tuple(sorted(refusals)),
        terminal_status=terminal,
        open_obstruction_ids=tuple(sorted(open_obstructions)),
    )


def verify_code_change_run_root(
    value: CodeChangeRunRootV1 | Mapping[str, Any],
    *,
    packet: PacketEnvelopeV2 | Mapping[str, Any] | None = None,
    candidate: CandidateArtifactV1 | None = None,
    patch: CodeChangePatchArtifactV1 | None = None,
    patch_bytes: bytes | None = None,
    gate_receipts: Sequence[GateReceiptV1] | None = None,
    prior_candidate_count: int = 0,
    operation_count: int = 1,
) -> CodeChangeRunRootV1:
    """Shape-check plus optional full evaluate replay for positive terminals."""
    root = verify_code_change_run_root_shape(value)
    if root.terminal_status not in POSITIVE_TERMINALS:
        return root
    if (
        packet is None
        or candidate is None
        or patch is None
        or patch_bytes is None
        or gate_receipts is None
    ):
        _fail(REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY)
    recomputed = evaluate_code_change_candidate(
        packet,
        candidate,
        patch,
        gate_receipts,
        prior_candidate_count=prior_candidate_count,
        operation_count=operation_count,
        patch_bytes=patch_bytes,
    )
    if recomputed.run_root_id != root.run_root_id:
        _fail(
            f"{REFUSAL_TERMINAL_NOT_DERIVED}: run_root_id replay mismatch "
            f"wire={root.run_root_id} derived={recomputed.run_root_id}"
        )
    if recomputed.task_packet_sha256 != root.task_packet_sha256:
        _fail("task_packet_sha256 does not recompute from supplied packet")
    return root


