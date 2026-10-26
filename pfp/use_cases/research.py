"""Research Claim and Intake Use Cases."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.aggregates.research_claim import (
    INITIAL_STATE_DOMAIN,
    MAX_SOURCE_BYTES,
    RESEARCH_ALLOWED_TRANSFORMS,
    RESEARCH_ENVELOPE_CONSTRAINTS,
    RESEARCH_EVIDENCE_CEILING,
    RESEARCH_FAMILY_OWNER_LAWS,
    RESEARCH_ORACLE_POLICY,
    RESEARCH_PACKET_FAMILY,
    RESEARCH_TERMINAL_TARGET,
    ResearchClaimPayloadV1,
    SourceArtifactV1,
    SourceIntakeBundleV1,
    SourceIntakeReceiptV1,
    _validate_initial_state,
    normalized_source_digest,
)
from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.exceptions import RefusalError
from omega_engine_pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    domain_digest,
    thaw,
)
from omega_engine_pfp.domain.validation import (
    _fail,
    _require_exact_dict,
    _require_positive_int,
    _require_string,
    _validate_ordered_unique_strings,
    _validate_repo_relative_path,
)


class IntakeResearchSourcesUseCase:
    """Takes input source files and builds a content-addressed SourceIntakeBundleV1."""

    def execute(
        self,
        bundle_id: str,
        bundle_name: str,
        sources: Sequence[tuple[str, str, bytes]],  # (artifact_id, file_path, content_bytes)
    ) -> SourceIntakeBundleV1:
        artifacts: list[SourceArtifactV1] = []
        hasher = hashlib.sha256()

        for art_id, path, raw_bytes in sources:
            sha256 = hashlib.sha256(raw_bytes).hexdigest()
            hasher.update(sha256.encode("utf-8"))
            artifacts.append(
                SourceArtifactV1(
                    source_id=art_id,
                    path=path,
                    role="primary_source",
                    normalization="raw-bytes",
                    sha256=sha256,
                    byte_count=len(raw_bytes),
                    repository_tracked_expected=True,
                )
            )

        bundle_sha256 = hasher.hexdigest()

        return SourceIntakeBundleV1(
            packet_id=bundle_id,
            source_manifest_root=bundle_sha256,
            receipts=(),
        )


class ResearchClaimVerifierUnavailable(RefusalError):
    code = "RESEARCH_CLAIM_VERIFIER_UNAVAILABLE"


class VerifyResearchClaimUseCase:
    """Refuse claim verification until a claim-specific verifier is supplied."""

    def execute(
        self,
        claim: Any,
        bundle: SourceIntakeBundleV1,
    ) -> bool:
        raise ResearchClaimVerifierUnavailable(
            "Source custody does not establish a research claim; no claim verifier is configured"
        )


def verify_source_artifact(
    source: SourceArtifactV1,
    repository_root: str | Path,
) -> SourceIntakeReceiptV1:
    """Verify one declared source against disk without consulting Git."""
    if not isinstance(source, SourceArtifactV1):
        raise TypeError("source must be a SourceArtifactV1")
    root = Path(repository_root).resolve()
    target = root.joinpath(*PurePosixPath(source.path).parts).resolve()
    observed_sha256: str | None = None
    observed_byte_count: int | None = None
    try:
        target.relative_to(root)
        is_safe = True
    except ValueError:
        is_safe = False
    if is_safe and target.is_file():
        try:
            disk_size = target.stat().st_size
            if disk_size <= MAX_SOURCE_BYTES:
                source_bytes = target.read_bytes()
                if len(source_bytes) == disk_size:
                    observed_sha256, observed_byte_count = normalized_source_digest(
                        source_bytes, source.normalization
                    )
        except (OSError, UnicodeDecodeError):
            observed_sha256 = None
            observed_byte_count = None
    available = observed_sha256 is not None and observed_byte_count is not None
    return SourceIntakeReceiptV1(
        source_id=source.source_id,
        path=source.path,
        normalization=source.normalization,
        available=available,
        expected_sha256=source.sha256,
        observed_sha256=observed_sha256,
        hash_matches=available and observed_sha256 == source.sha256,
        expected_byte_count=source.byte_count,
        observed_byte_count=observed_byte_count,
        size_matches=available and observed_byte_count == source.byte_count,
        repository_tracked_expected=source.repository_tracked_expected,
    )


verify_source_intake_receipt = verify_source_artifact


def build_source_artifact(
    repository_root: str | Path,
    *,
    source_id: str,
    path: str,
    role: str,
    normalization: str,
    repository_tracked_expected: bool,
) -> SourceArtifactV1:
    """Freeze one existing repository source without consulting Git."""
    normalized_path = _validate_repo_relative_path(path, "source path")
    root = Path(repository_root).resolve()
    target = root.joinpath(*PurePosixPath(normalized_path).parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CanonicalizationError("source resolves outside the repository") from exc
    if not target.is_file():
        raise FileNotFoundError(target)
    disk_size = target.stat().st_size
    if disk_size > MAX_SOURCE_BYTES:
        _fail("source exceeds the byte resource limit")
    source_bytes = target.read_bytes()
    if len(source_bytes) != disk_size:
        raise CanonicalizationError("source changed while it was read")
    sha256, byte_count = normalized_source_digest(source_bytes, normalization)
    return SourceArtifactV1(
        source_id=source_id,
        path=normalized_path,
        role=role,
        normalization=normalization,
        sha256=sha256,
        byte_count=byte_count,
        repository_tracked_expected=repository_tracked_expected,
    )


def build_source_intake_bundle(
    value: PacketEnvelopeV2 | Mapping[str, Any],
    repository_root: str | Path,
) -> SourceIntakeBundleV1:
    """Verify every packet source locally and bind the sorted receipt aggregate."""
    if isinstance(value, PacketEnvelopeV2):
        envelope = PacketEnvelopeV2.from_dict(value.to_dict())
    else:
        envelope = PacketEnvelopeV2.from_dict(
            _require_exact_dict(value, "research packet envelope")
        )
    payload = parse_research_claim_envelope(envelope)
    receipts = tuple(verify_source_artifact(source, repository_root) for source in payload.sources)
    return SourceIntakeBundleV1(
        packet_id=envelope.packet_id,
        source_manifest_root=payload.source_manifest_root,
        receipts=receipts,
    )


def build_research_claim_envelope(
    payload: ResearchClaimPayloadV1,
    task_id: str,
    carrier_id: str,
    initial_state_payload: Any,
    protected_boundaries: tuple[str, ...],
    step_budget: int,
) -> PacketEnvelopeV2:
    """Bind a typed research payload into the host-owned packet envelope."""
    if not isinstance(payload, ResearchClaimPayloadV1):
        raise TypeError("payload must be a ResearchClaimPayloadV1")
    _require_string(task_id, "task_id", nonempty=True)
    _require_string(carrier_id, "carrier_id", nonempty=True)
    _validate_ordered_unique_strings(protected_boundaries, "protected_boundaries")
    expected_carrier, expected_boundaries = RESEARCH_FAMILY_OWNER_LAWS[payload.family]
    if carrier_id != expected_carrier:
        _fail("carrier_id violates the research-family owner law")
    if protected_boundaries != expected_boundaries:
        _fail("protected_boundaries violate the research-family owner law")
    _require_positive_int(step_budget, "step_budget")
    validated_initial_state = _validate_initial_state(initial_state_payload)
    supplied_initial_hash = domain_digest(
        INITIAL_STATE_DOMAIN,
        {
            "family": payload.family,
            "initial_state_payload": validated_initial_state,
        },
    )
    if supplied_initial_hash != payload.initial_state_hash:
        _fail("initial_state_payload does not match the research payload")
    return PacketEnvelopeV2(
        task_id=task_id,
        packet_family=RESEARCH_PACKET_FAMILY,
        carrier_id=carrier_id,
        initial_state_hash=payload.initial_state_hash,
        payload=payload.to_dict(),
        constraints=RESEARCH_ENVELOPE_CONSTRAINTS,
        protected_boundaries=protected_boundaries,
        terminal_target=RESEARCH_TERMINAL_TARGET,
        evidence_ceiling=RESEARCH_EVIDENCE_CEILING,
        oracle_policy=RESEARCH_ORACLE_POLICY,
        allowed_transforms=RESEARCH_ALLOWED_TRANSFORMS,
        step_budget=step_budget,
        framing_mode="strict",
        packet_kind="problem",
        parent_event_id=None,
        source_digest=payload.source_manifest_root,
        authority_effect="None",
    )


def parse_research_claim_envelope(
    value: PacketEnvelopeV2 | Mapping[str, Any],
) -> ResearchClaimPayloadV1:
    """Strictly parse and cross-check a research envelope and its payload roots."""
    if isinstance(value, PacketEnvelopeV2):
        envelope = PacketEnvelopeV2.from_dict(value.to_dict())
    else:
        envelope = PacketEnvelopeV2.from_dict(
            _require_exact_dict(value, "research packet envelope")
        )
    if envelope.packet_family != RESEARCH_PACKET_FAMILY:
        _fail("research packet family is unsupported")
    if envelope.constraints != RESEARCH_ENVELOPE_CONSTRAINTS:
        _fail("research packet constraints are not canonical")
    if envelope.terminal_target != RESEARCH_TERMINAL_TARGET:
        _fail("research packet terminal target is unsupported")
    if envelope.evidence_ceiling != RESEARCH_EVIDENCE_CEILING:
        _fail("research packet evidence ceiling is unsupported")
    if envelope.oracle_policy != RESEARCH_ORACLE_POLICY:
        _fail("research packet oracle policy is unsupported")
    if envelope.allowed_transforms != RESEARCH_ALLOWED_TRANSFORMS:
        _fail("research packet transforms are unsupported")
    if (
        envelope.packet_kind != "problem"
        or envelope.framing_mode != "strict"
        or envelope.parent_event_id is not None
        or envelope.authority_effect != "None"
    ):
        _fail("research packet framing or authority is unsupported")
    _validate_ordered_unique_strings(envelope.protected_boundaries, "protected_boundaries")
    primitive_payload = thaw(envelope.payload)
    payload = ResearchClaimPayloadV1.from_dict(
        _require_exact_dict(primitive_payload, "research claim payload")
    )
    expected_carrier, expected_boundaries = RESEARCH_FAMILY_OWNER_LAWS[payload.family]
    if envelope.carrier_id != expected_carrier:
        _fail("carrier_id violates the research-family owner law")
    if envelope.protected_boundaries != expected_boundaries:
        _fail("protected_boundaries violate the research-family owner law")
    if envelope.source_digest != payload.source_manifest_root:
        _fail("envelope source_digest does not bind the source manifest")
    if envelope.initial_state_hash != payload.initial_state_hash:
        _fail("envelope initial_state_hash does not bind the initial state")
    return payload


verify_source_intake_bundle = build_source_intake_bundle


__all__ = [
    "build_research_claim_envelope",
    "build_source_artifact",
    "build_source_intake_bundle",
    "parse_research_claim_envelope",
    "verify_source_artifact",
    "verify_source_intake_bundle",
    "verify_source_intake_receipt",
]
