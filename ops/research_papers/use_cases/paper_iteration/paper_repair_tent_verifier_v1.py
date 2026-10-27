"""Independent, zero-provider verifier for the P3-04 Paper Repair tent."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from typing import Any

from governance.domain.swarm_control import (
    AuthorityEffectV1,
    EvidenceStatus,
    IdentityDomainV1,
    IdentityLinksV1,
    IdentitySlotV1,
    LifecycleStatusV1,
    NotYetCreated,
    TerminalStatusV1,
    canonical_identity_links_bytes,
    identity_links_sha256,
    identity_ref_from_bytes,
    verify_identity_links_v1,
)

from .packetization import GRAMMAR_ID, SCHEMA_ID, packetize_paper
from .paper_obstruction_trace import (
    HISTORICAL_FIXTURE_SHA256,
    TEST_PAPER_BYTE_COUNT,
    TEST_PAPER_GIT_BLOB_OID,
    TEST_PAPER_UNBOUND_LOG_COUNT,
    RealizationStatus,
    build_constitutive_succession_trace,
    count_unbound_iteration_entries,
)
from .paper_repair_tent_v1 import (
    NORMALIZATION_SCHEMA_V1,
    SOURCE_FIXTURE_PATH,
    PaperNormalizationReceiptV1,
    PaperRepairTentProposalV1,
    paper_repair_tent_proposal_sha256,
    parse_paper_repair_tent_proposal_v1,
)
from .paper_replay import verify_repair_replay
from .paper_resolution import (
    CLAIM_CEILING,
    KNOWN_RESIDUAL_CLASS,
    LOG_INTEGRITY_HANDLER,
    apply_log_integrity_repair,
    build_unbound_provenance_residual,
    route_residual,
)

VERIFICATION_SCHEMA_V1 = "core.paper_repair_tent.verification.v1"
BUNDLE_SCHEMA_V1 = "core.paper_repair_tent.bundle.v1"
MAX_BUNDLE_BYTES = 1_500_000
MAX_VERIFICATION_BYTES = 32_768
_VERIFICATION_DIGEST_PREFIX = b"core.paper_repair_tent.verification.v1\0"
_BUNDLE_DIGEST_PREFIX = b"core.paper_repair_tent.bundle.v1\0"
_NORMALIZATION_DIGEST_PREFIX = b"core.paper_repair.normalization.v1\0"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_ZERO_SHA256 = "0" * 64


class PaperRepairTentVerificationError(ValueError):
    """Typed refusal at the independent verification boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_oid(data: bytes) -> str:
    frame = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(frame).hexdigest()


def _require_literal(value: object, expected: str, code: str) -> None:
    if type(value) is not str or value != expected:
        raise PaperRepairTentVerificationError(code)


def _require_sha256(value: object, code: str) -> None:
    if (
        type(value) is not str
        or _SHA256_RE.fullmatch(value) is None
        or value == _ZERO_SHA256
    ):
        raise PaperRepairTentVerificationError(code)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PaperRepairTentVerificationError("CANONICAL_JSON_REFUSED") from exc


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode_b64(value: object, code: str) -> bytes:
    if type(value) is not str:
        raise PaperRepairTentVerificationError(code)
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeError, ValueError) as exc:
        raise PaperRepairTentVerificationError(code) from exc
    if _b64(decoded) != value:
        raise PaperRepairTentVerificationError(code)
    return decoded


def _normalization_bytes(receipt: PaperNormalizationReceiptV1) -> bytes:
    if type(receipt) is not PaperNormalizationReceiptV1:
        raise PaperRepairTentVerificationError("NORMALIZATION_TYPE_REFUSED")
    return _canonical_json_bytes(receipt.canonical_payload())


def _normalization_sha256(receipt: PaperNormalizationReceiptV1) -> str:
    return hashlib.sha256(
        _NORMALIZATION_DIGEST_PREFIX + _normalization_bytes(receipt)
    ).hexdigest()


def _independent_normalization(raw: bytes) -> tuple[bytes, PaperNormalizationReceiptV1]:
    """Recompute loss facts without calling the producer normalizer."""
    if type(raw) is not bytes or not raw:
        raise PaperRepairTentVerificationError("SOURCE_BYTES_REFUSED")
    bom_count = 3 if raw.startswith(b"\xef\xbb\xbf") else 0
    encoded = raw[bom_count:]
    crlf_count = encoded.count(b"\r\n")
    without_crlf = encoded.replace(b"\r\n", b"\n")
    bare_cr_count = without_crlf.count(b"\r")
    normalized_wire = without_crlf.replace(b"\r", b"\n")
    try:
        normalized = normalized_wire.decode("utf-8", errors="strict").encode("utf-8")
    except UnicodeDecodeError as exc:
        raise PaperRepairTentVerificationError("INVALID_UTF8_REFUSED") from exc
    packet = packetize_paper(raw)
    losses = tuple(
        label
        for label, count in zip(
            ("BOM_REMOVED", "CRLF_TO_LF", "CR_TO_LF"),
            (bom_count, crlf_count, bare_cr_count),
            strict=True,
        )
        if count
    )
    receipt = PaperNormalizationReceiptV1(
        raw_sha256=_sha256(raw),
        raw_byte_count=len(raw),
        source_git_blob_oid=_git_blob_oid(raw),
        normalized_sha256=_sha256(normalized),
        normalized_byte_count=len(normalized),
        utf8_bom_removed_byte_count=bom_count,
        crlf_to_lf_count=crlf_count,
        bare_cr_to_lf_count=bare_cr_count,
        normalized_lf_count=normalized.count(b"\n"),
        decode_replacement_count=0,
        losses=losses,
        grammar_id=packet.witness.grammar_id,
        packetization_schema_id=packet.witness.schema_id,
        packet_witness_sha256=packet.witness.witness_sha256,
        ast_sha256=packet.witness.ast_sha256,
        reparse_ok=packet.witness.reparse_ok,
    )
    if packet.normalized_text.encode("utf-8") != normalized:
        raise PaperRepairTentVerificationError("NORMALIZATION_PROVIDER_MISMATCH")
    return normalized, receipt


def _problem_payload(proposal: PaperRepairTentProposalV1) -> bytes:
    return _canonical_json_bytes(
        {
            "claim_ceiling": proposal.claim_ceiling,
            "finding_count": TEST_PAPER_UNBOUND_LOG_COUNT,
            "initial_trace_sha256": proposal.initial_trace_sha256,
            "mathematical_terminal": proposal.mathematical_terminal.value,
            "objective": "repair_unbound_iteration_provenance",
            "residual_class": KNOWN_RESIDUAL_CLASS,
            "residual_sha256": proposal.residual_sha256,
            "source_byte_count": len(proposal.raw_bytes),
            "source_git_blob_oid": proposal.source_git_blob_oid,
            "source_sha256": proposal.source_sha256,
            "span": [proposal.log_start_byte, proposal.log_end_byte],
        }
    )


def _presentation_payload(proposal: PaperRepairTentProposalV1) -> bytes:
    return _canonical_json_bytes(
        {
            "normalization": proposal.normalization.canonical_payload(),
            "source_path": proposal.source_path,
        }
    )


def _execution_payload(proposal: PaperRepairTentProposalV1) -> bytes:
    return _canonical_json_bytes(
        {
            "authority_effect": proposal.authority_effect.value,
            "candidate_sha256": proposal.candidate_sha256,
            "claim_ceiling": proposal.claim_ceiling,
            "cochain_realization": proposal.cochain_realization.value,
            "filesystem_writes": proposal.filesystem_writes,
            "handler_id": proposal.handler_id,
            "initial_trace_sha256": proposal.initial_trace_sha256,
            "lifecycle_status": proposal.lifecycle_status.value,
            "mathematical_terminal": proposal.mathematical_terminal.value,
            "patch_sha256": proposal.patch_sha256,
            "provider_calls": proposal.provider_calls,
            "network_calls": proposal.network_calls,
            "repair_proposal_sha256": proposal.repair_proposal_sha256,
            "residual_sha256": proposal.residual_sha256,
            "source_sha256": proposal.source_sha256,
            "updated_trace_sha256": proposal.updated_trace_sha256,
            "workflow_terminal": proposal.workflow_terminal,
        }
    )


def _expected_producer_links(proposal: PaperRepairTentProposalV1) -> IdentityLinksV1:
    problem = identity_ref_from_bytes(
        IdentityDomainV1.PROBLEM,
        "paper.repair.problem.v1",
        _problem_payload(proposal),
    )
    presentation = identity_ref_from_bytes(
        IdentityDomainV1.PRESENTATION,
        "paper.repair.presentation.v1",
        _presentation_payload(proposal),
    )
    execution = identity_ref_from_bytes(
        IdentityDomainV1.EXECUTION,
        "paper.repair.execution.v1",
        _execution_payload(proposal),
    )
    return IdentityLinksV1(problem, presentation).with_execution(execution)


def _independently_verify_proposal(
    proposal: PaperRepairTentProposalV1,
) -> IdentityLinksV1:
    if type(proposal) is not PaperRepairTentProposalV1:
        raise PaperRepairTentVerificationError("PROPOSAL_TYPE_REFUSED")
    try:
        proposal.__post_init__()
    except ValueError as exc:
        raise PaperRepairTentVerificationError("PROPOSAL_REVALIDATION_REFUSED") from exc
    raw = proposal.raw_bytes
    if (
        len(raw) != TEST_PAPER_BYTE_COUNT
        or _sha256(raw) != HISTORICAL_FIXTURE_SHA256
        or _git_blob_oid(raw) != TEST_PAPER_GIT_BLOB_OID
    ):
        raise PaperRepairTentVerificationError("FROZEN_SOURCE_MISMATCH")
    if proposal.source_path != SOURCE_FIXTURE_PATH:
        raise PaperRepairTentVerificationError("SOURCE_PATH_MISMATCH")
    _, normalization = _independent_normalization(raw)
    if normalization.canonical_payload() != proposal.normalization.canonical_payload():
        raise PaperRepairTentVerificationError("NORMALIZATION_REPLAY_MISMATCH")
    if (
        normalization.grammar_id != GRAMMAR_ID
        or normalization.packetization_schema_id != SCHEMA_ID
        or normalization.schema_version != NORMALIZATION_SCHEMA_V1
    ):
        raise PaperRepairTentVerificationError("NORMALIZATION_CONTRACT_MISMATCH")
    try:
        initial = build_constitutive_succession_trace(raw)
        residual = build_unbound_provenance_residual(initial)
        route = route_residual(residual)
        repair, updated = apply_log_integrity_repair(raw, initial, route)
        verify_repair_replay(
            source_bytes=raw,
            proposal=repair,
            trace=updated,
        )
    except ValueError as exc:
        raise PaperRepairTentVerificationError("P3_03_REPLAY_REFUSED") from exc
    expected_scalars = {
        "source_sha256": repair.source_sha256,
        "candidate_sha256": repair.candidate_sha256,
        "patch_sha256": repair.patch_sha256,
        "initial_trace_sha256": initial.trace_sha256,
        "updated_trace_sha256": updated.trace_sha256,
        "residual_sha256": residual.residual_sha256,
        "repair_proposal_sha256": repair.proposal_sha256,
        "handler_id": LOG_INTEGRITY_HANDLER,
        "claim_ceiling": CLAIM_CEILING,
        "log_start_byte": repair.log_start_byte,
        "log_end_byte": repair.log_end_byte,
    }
    for name, expected in expected_scalars.items():
        if getattr(proposal, name) != expected:
            raise PaperRepairTentVerificationError(f"PROPOSAL_{name.upper()}_MISMATCH")
    if proposal.candidate_bytes != repair.candidate_bytes:
        raise PaperRepairTentVerificationError("CANDIDATE_BYTES_MISMATCH")
    if proposal.patch_text != repair.patch_text:
        raise PaperRepairTentVerificationError("PATCH_TEXT_MISMATCH")
    if count_unbound_iteration_entries(proposal.candidate_bytes) != 0:
        raise PaperRepairTentVerificationError("TARGETED_RESIDUAL_REMAINS")
    try:
        producer_links = verify_identity_links_v1(
            proposal.producer_identity_links_bytes,
            proposal.producer_identity_links_sha256,
        )
    except ValueError as exc:
        raise PaperRepairTentVerificationError("PRODUCER_IDENTITY_REFUSED") from exc
    expected_links = _expected_producer_links(proposal)
    if (
        producer_links != expected_links
        or proposal.producer_identity_links_bytes
        != canonical_identity_links_bytes(expected_links)
        or proposal.producer_identity_links_sha256
        != identity_links_sha256(expected_links)
    ):
        raise PaperRepairTentVerificationError("PRODUCER_IDENTITY_MISMATCH")
    if type(producer_links.evidence) is not NotYetCreated:
        raise PaperRepairTentVerificationError("PRODUCER_EVIDENCE_FABRICATION")
    if producer_links.evidence.slot is not IdentitySlotV1.EVIDENCE:
        raise PaperRepairTentVerificationError("PRODUCER_EVIDENCE_SLOT_MISMATCH")
    return producer_links


@dataclass(frozen=True, slots=True)
class PaperRepairTentVerificationReceiptV1:
    verifier_id: str
    producer_proposal_sha256: str
    source_sha256: str
    normalization_receipt_sha256: str
    candidate_sha256: str
    patch_sha256: str
    initial_trace_sha256: str
    updated_trace_sha256: str
    residual_sha256: str
    repair_proposal_sha256: str
    producer_identity_links_sha256: str
    evaluator_class: str = "DETERMINISTIC_LOCAL_REPLAY"
    arithmetic_mode: str = "BYTE_EXACT"
    evidence_status: EvidenceStatus = EvidenceStatus.PASS
    lifecycle_status: LifecycleStatusV1 = LifecycleStatusV1.VERIFIED
    verification_status: str = "REPLAY_VERIFIED"
    allowed_use: str = "HUMAN_HANDOFF_ONLY"
    claim_ceiling: str = CLAIM_CEILING
    cochain_realization: RealizationStatus = RealizationStatus.UNRESOLVED
    mathematical_terminal: TerminalStatusV1 = TerminalStatusV1.OPEN_OBSTRUCTION
    workflow_terminal: str = "OracleNeeded"
    provider_calls: int = 0
    network_calls: int = 0
    filesystem_writes: int = 0
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE
    schema_version: str = VERIFICATION_SCHEMA_V1

    def __post_init__(self) -> None:
        if type(self) is not PaperRepairTentVerificationReceiptV1:
            raise PaperRepairTentVerificationError("RECEIPT_SUBCLASS_REFUSED")
        _require_literal(
            self.verifier_id,
            "paper.repair.independent_replay.v1",
            "VERIFIER_ID_REFUSED",
        )
        for name in (
            "producer_proposal_sha256",
            "source_sha256",
            "normalization_receipt_sha256",
            "candidate_sha256",
            "patch_sha256",
            "initial_trace_sha256",
            "updated_trace_sha256",
            "residual_sha256",
            "repair_proposal_sha256",
            "producer_identity_links_sha256",
        ):
            _require_sha256(getattr(self, name), f"{name.upper()}_REFUSED")
        for name, expected in (
            ("evaluator_class", "DETERMINISTIC_LOCAL_REPLAY"),
            ("arithmetic_mode", "BYTE_EXACT"),
            ("verification_status", "REPLAY_VERIFIED"),
            ("allowed_use", "HUMAN_HANDOFF_ONLY"),
            ("claim_ceiling", CLAIM_CEILING),
            ("workflow_terminal", "OracleNeeded"),
            ("schema_version", VERIFICATION_SCHEMA_V1),
        ):
            _require_literal(getattr(self, name), expected, f"{name.upper()}_REFUSED")
        if (
            type(self.evidence_status) is not EvidenceStatus
            or self.evidence_status is not EvidenceStatus.PASS
        ):
            raise PaperRepairTentVerificationError("EVIDENCE_STATUS_REFUSED")
        if (
            type(self.lifecycle_status) is not LifecycleStatusV1
            or self.lifecycle_status is not LifecycleStatusV1.VERIFIED
        ):
            raise PaperRepairTentVerificationError("LIFECYCLE_STATUS_REFUSED")
        if (
            type(self.cochain_realization) is not RealizationStatus
            or self.cochain_realization is not RealizationStatus.UNRESOLVED
        ):
            raise PaperRepairTentVerificationError("COCHAIN_REALIZATION_REFUSED")
        if (
            type(self.mathematical_terminal) is not TerminalStatusV1
            or self.mathematical_terminal is not TerminalStatusV1.OPEN_OBSTRUCTION
        ):
            raise PaperRepairTentVerificationError("MATHEMATICAL_TERMINAL_REFUSED")
        if (
            type(self.authority_effect) is not AuthorityEffectV1
            or self.authority_effect is not AuthorityEffectV1.NONE
        ):
            raise PaperRepairTentVerificationError("AUTHORITY_EFFECT_REFUSED")
        if (
            type(self.provider_calls) is not int
            or self.provider_calls != 0
            or type(self.network_calls) is not int
            or self.network_calls != 0
            or type(self.filesystem_writes) is not int
            or self.filesystem_writes != 0
        ):
            raise PaperRepairTentVerificationError("VERIFIER_EFFECT_COUNTER_REFUSED")

    def canonical_payload(self) -> dict[str, object]:
        self.__post_init__()
        payload: dict[str, object] = {}
        for name in self.__slots__:
            value = getattr(self, name)
            payload[name] = value.value if hasattr(value, "value") else value
        return payload


def canonical_paper_repair_tent_verification_bytes(
    receipt: PaperRepairTentVerificationReceiptV1,
) -> bytes:
    if type(receipt) is not PaperRepairTentVerificationReceiptV1:
        raise PaperRepairTentVerificationError("RECEIPT_TYPE_REFUSED")
    data = _canonical_json_bytes(receipt.canonical_payload())
    if not data or len(data) > MAX_VERIFICATION_BYTES:
        raise PaperRepairTentVerificationError("RECEIPT_SIZE_REFUSED")
    return data


def paper_repair_tent_verification_sha256(
    receipt: PaperRepairTentVerificationReceiptV1,
) -> str:
    return hashlib.sha256(
        _VERIFICATION_DIGEST_PREFIX
        + canonical_paper_repair_tent_verification_bytes(receipt)
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class PaperRepairTentBundleV1:
    proposal_bytes: bytes
    proposal_sha256: str
    verification_receipt_bytes: bytes
    verification_receipt_sha256: str
    verifier_identity_links_bytes: bytes
    verifier_identity_links_sha256: str
    provider_calls: int = 0
    network_calls: int = 0
    filesystem_writes: int = 0
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE
    schema_version: str = BUNDLE_SCHEMA_V1

    def __post_init__(self) -> None:
        if type(self) is not PaperRepairTentBundleV1:
            raise PaperRepairTentVerificationError("BUNDLE_SUBCLASS_REFUSED")
        for name in (
            "proposal_bytes",
            "verification_receipt_bytes",
            "verifier_identity_links_bytes",
        ):
            if type(getattr(self, name)) is not bytes:
                raise PaperRepairTentVerificationError("BUNDLE_BYTES_FIELD_REFUSED")
        for name in (
            "proposal_sha256",
            "verification_receipt_sha256",
            "verifier_identity_links_sha256",
        ):
            _require_sha256(getattr(self, name), f"{name.upper()}_REFUSED")
        try:
            proposal = parse_paper_repair_tent_proposal_v1(self.proposal_bytes)
        except ValueError as exc:
            raise PaperRepairTentVerificationError("BUNDLE_PROPOSAL_REFUSED") from exc
        if paper_repair_tent_proposal_sha256(proposal) != self.proposal_sha256:
            raise PaperRepairTentVerificationError("BUNDLE_PROPOSAL_DIGEST_MISMATCH")
        receipt = parse_paper_repair_tent_verification_v1(
            self.verification_receipt_bytes
        )
        if (
            paper_repair_tent_verification_sha256(receipt)
            != self.verification_receipt_sha256
        ):
            raise PaperRepairTentVerificationError("BUNDLE_RECEIPT_DIGEST_MISMATCH")
        receipt_bindings = {
            "producer_proposal_sha256": self.proposal_sha256,
            "source_sha256": proposal.source_sha256,
            "normalization_receipt_sha256": _normalization_sha256(
                proposal.normalization
            ),
            "candidate_sha256": proposal.candidate_sha256,
            "patch_sha256": proposal.patch_sha256,
            "initial_trace_sha256": proposal.initial_trace_sha256,
            "updated_trace_sha256": proposal.updated_trace_sha256,
            "residual_sha256": proposal.residual_sha256,
            "repair_proposal_sha256": proposal.repair_proposal_sha256,
            "producer_identity_links_sha256": (proposal.producer_identity_links_sha256),
        }
        for name, expected in receipt_bindings.items():
            if getattr(receipt, name) != expected:
                raise PaperRepairTentVerificationError(
                    f"BUNDLE_RECEIPT_{name.upper()}_MISMATCH"
                )
        try:
            links = verify_identity_links_v1(
                self.verifier_identity_links_bytes,
                self.verifier_identity_links_sha256,
            )
        except ValueError as exc:
            raise PaperRepairTentVerificationError("BUNDLE_IDENTITY_REFUSED") from exc
        if type(links.evidence) is NotYetCreated:
            raise PaperRepairTentVerificationError("BUNDLE_EVIDENCE_MISSING")
        try:
            producer_links = verify_identity_links_v1(
                proposal.producer_identity_links_bytes,
                proposal.producer_identity_links_sha256,
            )
        except ValueError as exc:
            raise PaperRepairTentVerificationError(
                "BUNDLE_PRODUCER_IDENTITY_REFUSED"
            ) from exc
        if (
            links.problem != producer_links.problem
            or links.presentation != producer_links.presentation
            or links.execution != producer_links.execution
        ):
            raise PaperRepairTentVerificationError("BUNDLE_IDENTITY_PREFIX_MISMATCH")
        expected_evidence = identity_ref_from_bytes(
            IdentityDomainV1.EVIDENCE,
            "paper.repair.evidence.v1",
            self.verification_receipt_bytes,
        )
        if links.evidence != expected_evidence:
            raise PaperRepairTentVerificationError("BUNDLE_EVIDENCE_IDENTITY_MISMATCH")
        if (
            type(self.provider_calls) is not int
            or self.provider_calls != 0
            or type(self.network_calls) is not int
            or self.network_calls != 0
            or type(self.filesystem_writes) is not int
            or self.filesystem_writes != 0
        ):
            raise PaperRepairTentVerificationError("BUNDLE_EFFECT_COUNTER_REFUSED")
        if (
            type(self.authority_effect) is not AuthorityEffectV1
            or self.authority_effect is not AuthorityEffectV1.NONE
        ):
            raise PaperRepairTentVerificationError("BUNDLE_AUTHORITY_REFUSED")
        _require_literal(self.schema_version, BUNDLE_SCHEMA_V1, "BUNDLE_SCHEMA_REFUSED")

    def canonical_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect.value,
            "filesystem_writes": self.filesystem_writes,
            "proposal_bytes_b64": _b64(self.proposal_bytes),
            "proposal_sha256": self.proposal_sha256,
            "provider_calls": self.provider_calls,
            "network_calls": self.network_calls,
            "schema_version": self.schema_version,
            "verification_receipt_bytes_b64": _b64(self.verification_receipt_bytes),
            "verification_receipt_sha256": self.verification_receipt_sha256,
            "verifier_identity_links_bytes_b64": _b64(
                self.verifier_identity_links_bytes
            ),
            "verifier_identity_links_sha256": self.verifier_identity_links_sha256,
        }


def _build_expected_bundle(proposal_bytes: bytes) -> PaperRepairTentBundleV1:
    try:
        proposal = parse_paper_repair_tent_proposal_v1(proposal_bytes)
    except ValueError as exc:
        raise PaperRepairTentVerificationError("PROPOSAL_PARSE_REFUSED") from exc
    producer_links = _independently_verify_proposal(proposal)
    receipt = PaperRepairTentVerificationReceiptV1(
        verifier_id="paper.repair.independent_replay.v1",
        producer_proposal_sha256=paper_repair_tent_proposal_sha256(proposal),
        source_sha256=proposal.source_sha256,
        normalization_receipt_sha256=_normalization_sha256(proposal.normalization),
        candidate_sha256=proposal.candidate_sha256,
        patch_sha256=proposal.patch_sha256,
        initial_trace_sha256=proposal.initial_trace_sha256,
        updated_trace_sha256=proposal.updated_trace_sha256,
        residual_sha256=proposal.residual_sha256,
        repair_proposal_sha256=proposal.repair_proposal_sha256,
        producer_identity_links_sha256=proposal.producer_identity_links_sha256,
    )
    receipt_bytes = canonical_paper_repair_tent_verification_bytes(receipt)
    evidence = identity_ref_from_bytes(
        IdentityDomainV1.EVIDENCE,
        "paper.repair.evidence.v1",
        receipt_bytes,
    )
    verifier_links = producer_links.with_evidence(evidence)
    return PaperRepairTentBundleV1(
        proposal_bytes=proposal_bytes,
        proposal_sha256=paper_repair_tent_proposal_sha256(proposal),
        verification_receipt_bytes=receipt_bytes,
        verification_receipt_sha256=paper_repair_tent_verification_sha256(receipt),
        verifier_identity_links_bytes=canonical_identity_links_bytes(verifier_links),
        verifier_identity_links_sha256=identity_links_sha256(verifier_links),
    )


def verify_paper_repair_tent_proposal_v1(
    data: bytes,
) -> PaperRepairTentBundleV1:
    """Independently verify a producer proposal and bind evaluator evidence."""
    if type(data) is not bytes:
        raise PaperRepairTentVerificationError("PROPOSAL_BYTES_REQUIRED")
    return _build_expected_bundle(data)


def canonical_paper_repair_tent_bundle_bytes(
    bundle: PaperRepairTentBundleV1,
) -> bytes:
    if type(bundle) is not PaperRepairTentBundleV1:
        raise PaperRepairTentVerificationError("BUNDLE_TYPE_REFUSED")
    data = _canonical_json_bytes(bundle.canonical_payload())
    if not data or len(data) > MAX_BUNDLE_BYTES:
        raise PaperRepairTentVerificationError("BUNDLE_SIZE_REFUSED")
    return data


def paper_repair_tent_bundle_sha256(bundle: PaperRepairTentBundleV1) -> str:
    return hashlib.sha256(
        _BUNDLE_DIGEST_PREFIX + canonical_paper_repair_tent_bundle_bytes(bundle)
    ).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PaperRepairTentVerificationError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_float(_: str) -> None:
    raise PaperRepairTentVerificationError("JSON_FLOAT_REFUSED")


def _reject_constant(_: str) -> None:
    raise PaperRepairTentVerificationError("JSON_CONSTANT_REFUSED")


def _load_strict_json(data: bytes, maximum: int, size_code: str) -> object:
    if type(data) is not bytes or not data or len(data) > maximum:
        raise PaperRepairTentVerificationError(size_code)
    try:
        return json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except PaperRepairTentVerificationError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PaperRepairTentVerificationError("JSON_REFUSED") from exc


def _exact_dict(value: object, keys: frozenset[str], code: str) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != keys:
        raise PaperRepairTentVerificationError(code)
    return value


def _parse_exact_enum(value: object, expected: Any, code: str) -> Any:
    if type(value) is not str or value != expected.value:
        raise PaperRepairTentVerificationError(code)
    return expected


_RECEIPT_KEYS = frozenset(PaperRepairTentVerificationReceiptV1.__slots__)
_BUNDLE_KEYS = frozenset(
    {
        "authority_effect",
        "filesystem_writes",
        "network_calls",
        "proposal_bytes_b64",
        "proposal_sha256",
        "provider_calls",
        "schema_version",
        "verification_receipt_bytes_b64",
        "verification_receipt_sha256",
        "verifier_identity_links_bytes_b64",
        "verifier_identity_links_sha256",
    }
)


def parse_paper_repair_tent_verification_v1(
    data: bytes,
) -> PaperRepairTentVerificationReceiptV1:
    root = _exact_dict(
        _load_strict_json(data, MAX_VERIFICATION_BYTES, "RECEIPT_SIZE_REFUSED"),
        _RECEIPT_KEYS,
        "RECEIPT_FIELDS_REFUSED",
    )
    receipt = PaperRepairTentVerificationReceiptV1(
        **{
            **root,
            "evidence_status": _parse_exact_enum(
                root["evidence_status"],
                EvidenceStatus.PASS,
                "EVIDENCE_STATUS_REFUSED",
            ),
            "lifecycle_status": _parse_exact_enum(
                root["lifecycle_status"],
                LifecycleStatusV1.VERIFIED,
                "LIFECYCLE_STATUS_REFUSED",
            ),
            "cochain_realization": _parse_exact_enum(
                root["cochain_realization"],
                RealizationStatus.UNRESOLVED,
                "COCHAIN_REALIZATION_REFUSED",
            ),
            "mathematical_terminal": _parse_exact_enum(
                root["mathematical_terminal"],
                TerminalStatusV1.OPEN_OBSTRUCTION,
                "MATHEMATICAL_TERMINAL_REFUSED",
            ),
            "authority_effect": _parse_exact_enum(
                root["authority_effect"],
                AuthorityEffectV1.NONE,
                "AUTHORITY_EFFECT_REFUSED",
            ),
        }
    )
    if canonical_paper_repair_tent_verification_bytes(receipt) != data:
        raise PaperRepairTentVerificationError("NONCANONICAL_RECEIPT_BYTES")
    return receipt


def parse_paper_repair_tent_bundle_v1(data: bytes) -> PaperRepairTentBundleV1:
    root = _exact_dict(
        _load_strict_json(data, MAX_BUNDLE_BYTES, "BUNDLE_SIZE_REFUSED"),
        _BUNDLE_KEYS,
        "BUNDLE_FIELDS_REFUSED",
    )
    bundle = PaperRepairTentBundleV1(
        proposal_bytes=_decode_b64(
            root["proposal_bytes_b64"], "PROPOSAL_BASE64_REFUSED"
        ),
        proposal_sha256=root["proposal_sha256"],
        verification_receipt_bytes=_decode_b64(
            root["verification_receipt_bytes_b64"], "RECEIPT_BASE64_REFUSED"
        ),
        verification_receipt_sha256=root["verification_receipt_sha256"],
        verifier_identity_links_bytes=_decode_b64(
            root["verifier_identity_links_bytes_b64"], "LINKS_BASE64_REFUSED"
        ),
        verifier_identity_links_sha256=root["verifier_identity_links_sha256"],
        provider_calls=root["provider_calls"],
        network_calls=root["network_calls"],
        filesystem_writes=root["filesystem_writes"],
        authority_effect=_parse_exact_enum(
            root["authority_effect"],
            AuthorityEffectV1.NONE,
            "BUNDLE_AUTHORITY_REFUSED",
        ),
        schema_version=root["schema_version"],
    )
    if canonical_paper_repair_tent_bundle_bytes(bundle) != data:
        raise PaperRepairTentVerificationError("NONCANONICAL_BUNDLE_BYTES")
    return bundle


def replay_paper_repair_tent_bundle_v1(data: bytes) -> PaperRepairTentBundleV1:
    """Replay every nested binding and compare the complete canonical bundle."""
    observed = parse_paper_repair_tent_bundle_v1(data)
    expected = _build_expected_bundle(observed.proposal_bytes)
    if not hmac.compare_digest(
        canonical_paper_repair_tent_bundle_bytes(observed),
        canonical_paper_repair_tent_bundle_bytes(expected),
    ):
        raise PaperRepairTentVerificationError("BUNDLE_REPLAY_MISMATCH")
    return observed


def verify_paper_repair_tent_bundle_v1(
    data: bytes,
    expected_sha256: str,
) -> PaperRepairTentBundleV1:
    _require_sha256(expected_sha256, "EXPECTED_BUNDLE_DIGEST_REFUSED")
    bundle = replay_paper_repair_tent_bundle_v1(data)
    if not hmac.compare_digest(
        paper_repair_tent_bundle_sha256(bundle), expected_sha256
    ):
        raise PaperRepairTentVerificationError("BUNDLE_DIGEST_MISMATCH")
    return bundle


__all__ = [
    "BUNDLE_SCHEMA_V1",
    "MAX_BUNDLE_BYTES",
    "MAX_VERIFICATION_BYTES",
    "VERIFICATION_SCHEMA_V1",
    "PaperRepairTentBundleV1",
    "PaperRepairTentVerificationError",
    "PaperRepairTentVerificationReceiptV1",
    "canonical_paper_repair_tent_bundle_bytes",
    "canonical_paper_repair_tent_verification_bytes",
    "paper_repair_tent_bundle_sha256",
    "paper_repair_tent_verification_sha256",
    "parse_paper_repair_tent_bundle_v1",
    "parse_paper_repair_tent_verification_v1",
    "replay_paper_repair_tent_bundle_v1",
    "verify_paper_repair_tent_bundle_v1",
    "verify_paper_repair_tent_proposal_v1",
]
