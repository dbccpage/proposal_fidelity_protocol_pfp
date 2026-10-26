"""Pure P3-04 producer for the byte-pinned Paper Repair tent.

The producer freezes one historical carrier, records normalization losses,
builds the deterministic P3-03 candidate, and emits an authority-null
proposal.  It has no filesystem, process, network, provider, decision, or
application port.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from omega_engine_governance.domain.swarm_control import (
    AuthorityEffectV1,
    EvidenceStatus,
    IdentityDomainV1,
    IdentityLinksV1,
    LifecycleStatusV1,
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
)
from .paper_resolution import (
    CLAIM_CEILING,
    KNOWN_RESIDUAL_CLASS,
    LOG_INTEGRITY_HANDLER,
    apply_log_integrity_repair,
    build_unbound_provenance_residual,
    route_residual,
)

NORMALIZATION_SCHEMA_V1 = "omega.paper_repair.normalization.v1"
PROPOSAL_SCHEMA_V1 = "omega.paper_repair_tent.proposal.v1"
SOURCE_FIXTURE_PATH = (
    "omega_engine_operations/tests/fixtures/paper_repair/001_time_historical_lf.md"
)
MAX_SOURCE_BYTES = 262_144
MAX_PROPOSAL_BYTES = 1_200_000
_PROPOSAL_DIGEST_PREFIX = b"omega.paper_repair_tent.proposal.v1\0"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_ZERO_SHA256 = "0" * 64
_LOSS_ORDER = ("BOM_REMOVED", "CRLF_TO_LF", "CR_TO_LF")


class PaperRepairTentError(ValueError):
    """Typed refusal at the P3-04 producer boundary."""

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
        raise PaperRepairTentError(code)


def _require_sha256(value: object, code: str) -> None:
    if (
        type(value) is not str
        or _SHA256_RE.fullmatch(value) is None
        or value == _ZERO_SHA256
    ):
        raise PaperRepairTentError(code)


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
        raise PaperRepairTentError("CANONICAL_JSON_REFUSED") from exc


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode_b64(value: object, code: str) -> bytes:
    if type(value) is not str:
        raise PaperRepairTentError(code)
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeError, ValueError) as exc:
        raise PaperRepairTentError(code) from exc
    if _b64(decoded) != value:
        raise PaperRepairTentError(code)
    return decoded


@dataclass(frozen=True, slots=True)
class PaperNormalizationReceiptV1:
    raw_sha256: str
    raw_byte_count: int
    source_git_blob_oid: str
    normalized_sha256: str
    normalized_byte_count: int
    utf8_bom_removed_byte_count: int
    crlf_to_lf_count: int
    bare_cr_to_lf_count: int
    normalized_lf_count: int
    decode_replacement_count: int
    losses: tuple[str, ...]
    grammar_id: str
    packetization_schema_id: str
    packet_witness_sha256: str
    ast_sha256: str
    reparse_ok: bool
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE
    schema_version: str = NORMALIZATION_SCHEMA_V1

    def __post_init__(self) -> None:
        if type(self) is not PaperNormalizationReceiptV1:
            raise PaperRepairTentError("NORMALIZATION_SUBCLASS_REFUSED")
        _require_sha256(self.raw_sha256, "RAW_SHA256_REFUSED")
        _require_sha256(self.normalized_sha256, "NORMALIZED_SHA256_REFUSED")
        _require_sha256(self.packet_witness_sha256, "WITNESS_SHA256_REFUSED")
        _require_sha256(self.ast_sha256, "AST_SHA256_REFUSED")
        if (
            type(self.source_git_blob_oid) is not str
            or _SHA1_RE.fullmatch(self.source_git_blob_oid) is None
            or self.source_git_blob_oid == "0" * 40
        ):
            raise PaperRepairTentError("GIT_BLOB_OID_REFUSED")
        for name in (
            "raw_byte_count",
            "normalized_byte_count",
            "utf8_bom_removed_byte_count",
            "crlf_to_lf_count",
            "bare_cr_to_lf_count",
            "normalized_lf_count",
            "decode_replacement_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PaperRepairTentError("NORMALIZATION_COUNT_REFUSED")
        if self.raw_byte_count < 1 or self.normalized_byte_count < 1:
            raise PaperRepairTentError("EMPTY_NORMALIZATION_CARRIER_REFUSED")
        if self.utf8_bom_removed_byte_count not in (0, 3):
            raise PaperRepairTentError("BOM_COUNT_REFUSED")
        if self.decode_replacement_count != 0:
            raise PaperRepairTentError("LOSSY_UTF8_REFUSED")
        if type(self.losses) is not tuple or any(
            type(item) is not str for item in self.losses
        ):
            raise PaperRepairTentError("LOSS_LEDGER_TYPE_REFUSED")
        expected_losses = tuple(
            label
            for label, count in zip(
                _LOSS_ORDER,
                (
                    self.utf8_bom_removed_byte_count,
                    self.crlf_to_lf_count,
                    self.bare_cr_to_lf_count,
                ),
                strict=True,
            )
            if count
        )
        if self.losses != expected_losses:
            raise PaperRepairTentError("LOSS_LEDGER_MISMATCH")
        _require_literal(self.grammar_id, GRAMMAR_ID, "GRAMMAR_ID_REFUSED")
        _require_literal(
            self.packetization_schema_id,
            SCHEMA_ID,
            "PACKETIZATION_SCHEMA_REFUSED",
        )
        if type(self.reparse_ok) is not bool or self.reparse_ok is not True:
            raise PaperRepairTentError("REPARSE_REQUIRED")
        if type(self.authority_effect) is not AuthorityEffectV1 or (
            self.authority_effect is not AuthorityEffectV1.NONE
        ):
            raise PaperRepairTentError("AUTHORITY_EFFECT_REFUSED")
        _require_literal(
            self.schema_version,
            NORMALIZATION_SCHEMA_V1,
            "NORMALIZATION_SCHEMA_REFUSED",
        )

    def canonical_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "ast_sha256": self.ast_sha256,
            "authority_effect": self.authority_effect.value,
            "bare_cr_to_lf_count": self.bare_cr_to_lf_count,
            "crlf_to_lf_count": self.crlf_to_lf_count,
            "decode_replacement_count": self.decode_replacement_count,
            "grammar_id": self.grammar_id,
            "losses": list(self.losses),
            "normalized_byte_count": self.normalized_byte_count,
            "normalized_lf_count": self.normalized_lf_count,
            "normalized_sha256": self.normalized_sha256,
            "packet_witness_sha256": self.packet_witness_sha256,
            "packetization_schema_id": self.packetization_schema_id,
            "raw_byte_count": self.raw_byte_count,
            "raw_sha256": self.raw_sha256,
            "reparse_ok": self.reparse_ok,
            "schema_version": self.schema_version,
            "source_git_blob_oid": self.source_git_blob_oid,
            "utf8_bom_removed_byte_count": self.utf8_bom_removed_byte_count,
        }


def normalize_paper_with_loss_v1(
    raw: bytes,
) -> tuple[bytes, PaperNormalizationReceiptV1]:
    """Normalize UTF-8/BOM/newlines in memory and bind every byte loss."""
    if type(raw) is not bytes or not raw or len(raw) > MAX_SOURCE_BYTES:
        raise PaperRepairTentError("SOURCE_BYTES_REFUSED")
    bom_count = 3 if raw.startswith(b"\xef\xbb\xbf") else 0
    encoded = raw[bom_count:]
    crlf_count = encoded.count(b"\r\n")
    without_crlf = encoded.replace(b"\r\n", b"\n")
    bare_cr_count = without_crlf.count(b"\r")
    normalized_wire = without_crlf.replace(b"\r", b"\n")
    try:
        text = normalized_wire.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PaperRepairTentError("INVALID_UTF8_REFUSED") from exc
    normalized = text.encode("utf-8")
    packet = packetize_paper(raw)
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
        losses=tuple(
            label
            for label, count in zip(
                _LOSS_ORDER,
                (bom_count, crlf_count, bare_cr_count),
                strict=True,
            )
            if count
        ),
        grammar_id=packet.witness.grammar_id,
        packetization_schema_id=packet.witness.schema_id,
        packet_witness_sha256=packet.witness.witness_sha256,
        ast_sha256=packet.witness.ast_sha256,
        reparse_ok=packet.witness.reparse_ok,
    )
    if packet.normalized_text.encode("utf-8") != normalized:
        raise PaperRepairTentError("PACKETIZATION_NORMALIZATION_MISMATCH")
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


def _expected_links(proposal: PaperRepairTentProposalV1) -> IdentityLinksV1:
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


@dataclass(frozen=True, slots=True)
class PaperRepairTentProposalV1:
    raw_bytes: bytes
    candidate_bytes: bytes
    patch_text: str
    normalization: PaperNormalizationReceiptV1
    source_path: str
    source_git_blob_oid: str
    source_sha256: str
    candidate_sha256: str
    patch_sha256: str
    initial_trace_sha256: str
    updated_trace_sha256: str
    residual_sha256: str
    repair_proposal_sha256: str
    log_start_byte: int
    log_end_byte: int
    handler_id: str
    claim_ceiling: str
    producer_identity_links_bytes: bytes
    producer_identity_links_sha256: str
    lifecycle_status: LifecycleStatusV1 = LifecycleStatusV1.PROPOSED
    evaluator_status: EvidenceStatus = EvidenceStatus.NOT_ATTEMPTED
    cochain_realization: RealizationStatus = RealizationStatus.UNRESOLVED
    mathematical_terminal: TerminalStatusV1 = TerminalStatusV1.OPEN_OBSTRUCTION
    workflow_terminal: str = "OracleNeeded"
    provider_calls: int = 0
    network_calls: int = 0
    filesystem_writes: int = 0
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE
    schema_version: str = PROPOSAL_SCHEMA_V1

    def __post_init__(self) -> None:
        if type(self) is not PaperRepairTentProposalV1:
            raise PaperRepairTentError("PROPOSAL_SUBCLASS_REFUSED")
        if type(self.raw_bytes) is not bytes or type(self.candidate_bytes) is not bytes:
            raise PaperRepairTentError("PROPOSAL_CARRIER_TYPE_REFUSED")
        if type(self.patch_text) is not str:
            raise PaperRepairTentError("PATCH_TEXT_TYPE_REFUSED")
        try:
            patch_bytes = self.patch_text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise PaperRepairTentError("PATCH_UTF8_REFUSED") from exc
        if type(self.normalization) is not PaperNormalizationReceiptV1:
            raise PaperRepairTentError("NORMALIZATION_TYPE_REFUSED")
        self.normalization.__post_init__()
        if type(self.source_path) is not str or self.source_path != SOURCE_FIXTURE_PATH:
            raise PaperRepairTentError("SOURCE_PATH_REFUSED")
        if (
            type(self.source_git_blob_oid) is not str
            or _SHA1_RE.fullmatch(self.source_git_blob_oid) is None
            or self.source_git_blob_oid == "0" * 40
        ):
            raise PaperRepairTentError("SOURCE_GIT_BLOB_REFUSED")
        if self.source_git_blob_oid != _git_blob_oid(self.raw_bytes):
            raise PaperRepairTentError("SOURCE_GIT_BLOB_MISMATCH")
        if (
            len(self.raw_bytes) != TEST_PAPER_BYTE_COUNT
            or _sha256(self.raw_bytes) != HISTORICAL_FIXTURE_SHA256
            or self.source_git_blob_oid != TEST_PAPER_GIT_BLOB_OID
        ):
            raise PaperRepairTentError("HISTORICAL_FIXTURE_REQUIRED")
        for value, observed, code in (
            (self.source_sha256, _sha256(self.raw_bytes), "SOURCE_SHA256_MISMATCH"),
            (
                self.candidate_sha256,
                _sha256(self.candidate_bytes),
                "CANDIDATE_SHA256_MISMATCH",
            ),
            (
                self.patch_sha256,
                _sha256(patch_bytes),
                "PATCH_SHA256_MISMATCH",
            ),
        ):
            _require_sha256(value, code)
            if value != observed:
                raise PaperRepairTentError(code)
        for name in (
            "initial_trace_sha256",
            "updated_trace_sha256",
            "residual_sha256",
            "repair_proposal_sha256",
            "producer_identity_links_sha256",
        ):
            _require_sha256(getattr(self, name), f"{name.upper()}_REFUSED")
        if (
            type(self.log_start_byte) is not int
            or type(self.log_end_byte) is not int
            or self.log_start_byte < 0
            or self.log_end_byte <= self.log_start_byte
            or self.log_end_byte > len(self.raw_bytes)
        ):
            raise PaperRepairTentError("PROPOSAL_SPAN_REFUSED")
        for field, expected in (
            ("handler_id", LOG_INTEGRITY_HANDLER),
            ("claim_ceiling", CLAIM_CEILING),
            ("workflow_terminal", "OracleNeeded"),
            ("schema_version", PROPOSAL_SCHEMA_V1),
        ):
            _require_literal(getattr(self, field), expected, f"{field.upper()}_REFUSED")
        if (
            type(self.lifecycle_status) is not LifecycleStatusV1
            or self.lifecycle_status is not LifecycleStatusV1.PROPOSED
        ):
            raise PaperRepairTentError("LIFECYCLE_STATUS_REFUSED")
        if (
            type(self.evaluator_status) is not EvidenceStatus
            or self.evaluator_status is not EvidenceStatus.NOT_ATTEMPTED
        ):
            raise PaperRepairTentError("EVALUATOR_STATUS_REFUSED")
        if (
            type(self.cochain_realization) is not RealizationStatus
            or self.cochain_realization is not RealizationStatus.UNRESOLVED
        ):
            raise PaperRepairTentError("COCHAIN_REALIZATION_REFUSED")
        if (
            type(self.mathematical_terminal) is not TerminalStatusV1
            or self.mathematical_terminal is not TerminalStatusV1.OPEN_OBSTRUCTION
        ):
            raise PaperRepairTentError("MATHEMATICAL_TERMINAL_REFUSED")
        if (
            type(self.authority_effect) is not AuthorityEffectV1
            or self.authority_effect is not AuthorityEffectV1.NONE
        ):
            raise PaperRepairTentError("AUTHORITY_EFFECT_REFUSED")
        if (
            type(self.provider_calls) is not int
            or self.provider_calls != 0
            or type(self.network_calls) is not int
            or self.network_calls != 0
            or type(self.filesystem_writes) is not int
            or self.filesystem_writes != 0
        ):
            raise PaperRepairTentError("PRODUCER_EFFECT_COUNTER_REFUSED")
        normalized, expected_normalization = normalize_paper_with_loss_v1(
            self.raw_bytes
        )
        if expected_normalization != self.normalization:
            raise PaperRepairTentError("NORMALIZATION_RECEIPT_MISMATCH")
        if self.normalization.normalized_sha256 != _sha256(normalized):
            raise PaperRepairTentError("NORMALIZED_CARRIER_MISMATCH")
        try:
            links = verify_identity_links_v1(
                self.producer_identity_links_bytes,
                self.producer_identity_links_sha256,
            )
        except ValueError as exc:
            raise PaperRepairTentError("PRODUCER_IDENTITY_LINKS_REFUSED") from exc
        expected_links = _expected_links(self)
        if links != expected_links:
            raise PaperRepairTentError("PRODUCER_IDENTITY_LINKS_MISMATCH")

    def canonical_payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect.value,
            "candidate_bytes_b64": _b64(self.candidate_bytes),
            "candidate_sha256": self.candidate_sha256,
            "claim_ceiling": self.claim_ceiling,
            "cochain_realization": self.cochain_realization.value,
            "evaluator_status": self.evaluator_status.value,
            "filesystem_writes": self.filesystem_writes,
            "handler_id": self.handler_id,
            "initial_trace_sha256": self.initial_trace_sha256,
            "lifecycle_status": self.lifecycle_status.value,
            "log_end_byte": self.log_end_byte,
            "log_start_byte": self.log_start_byte,
            "mathematical_terminal": self.mathematical_terminal.value,
            "normalization": self.normalization.canonical_payload(),
            "patch_sha256": self.patch_sha256,
            "patch_text": self.patch_text,
            "producer_identity_links_b64": _b64(self.producer_identity_links_bytes),
            "producer_identity_links_sha256": self.producer_identity_links_sha256,
            "provider_calls": self.provider_calls,
            "network_calls": self.network_calls,
            "raw_bytes_b64": _b64(self.raw_bytes),
            "repair_proposal_sha256": self.repair_proposal_sha256,
            "residual_sha256": self.residual_sha256,
            "schema_version": self.schema_version,
            "source_git_blob_oid": self.source_git_blob_oid,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "updated_trace_sha256": self.updated_trace_sha256,
            "workflow_terminal": self.workflow_terminal,
        }


def _make_proposal(raw: bytes) -> PaperRepairTentProposalV1:
    _, normalization = normalize_paper_with_loss_v1(raw)
    initial = build_constitutive_succession_trace(raw)
    residual = build_unbound_provenance_residual(initial)
    route = route_residual(residual)
    repair, updated = apply_log_integrity_repair(raw, initial, route)
    empty_links = b"{}"
    draft = PaperRepairTentProposalV1.__new__(PaperRepairTentProposalV1)
    fields: dict[str, object] = {
        "raw_bytes": raw,
        "candidate_bytes": repair.candidate_bytes,
        "patch_text": repair.patch_text,
        "normalization": normalization,
        "source_path": SOURCE_FIXTURE_PATH,
        "source_git_blob_oid": _git_blob_oid(raw),
        "source_sha256": repair.source_sha256,
        "candidate_sha256": repair.candidate_sha256,
        "patch_sha256": repair.patch_sha256,
        "initial_trace_sha256": initial.trace_sha256,
        "updated_trace_sha256": updated.trace_sha256,
        "residual_sha256": residual.residual_sha256,
        "repair_proposal_sha256": repair.proposal_sha256,
        "log_start_byte": repair.log_start_byte,
        "log_end_byte": repair.log_end_byte,
        "handler_id": repair.handler_id,
        "claim_ceiling": repair.claim_ceiling,
        "producer_identity_links_bytes": empty_links,
        "producer_identity_links_sha256": "1" * 64,
        "lifecycle_status": LifecycleStatusV1.PROPOSED,
        "evaluator_status": EvidenceStatus.NOT_ATTEMPTED,
        "cochain_realization": RealizationStatus.UNRESOLVED,
        "mathematical_terminal": TerminalStatusV1.OPEN_OBSTRUCTION,
        "workflow_terminal": repair.workflow_terminal,
        "provider_calls": 0,
        "network_calls": 0,
        "filesystem_writes": 0,
        "authority_effect": AuthorityEffectV1.NONE,
        "schema_version": PROPOSAL_SCHEMA_V1,
    }
    for name, value in fields.items():
        object.__setattr__(draft, name, value)
    links = _expected_links(draft)
    fields["producer_identity_links_bytes"] = canonical_identity_links_bytes(links)
    fields["producer_identity_links_sha256"] = identity_links_sha256(links)
    return PaperRepairTentProposalV1(**fields)  # type: ignore[arg-type]


def produce_paper_repair_tent_v1(raw: bytes) -> PaperRepairTentProposalV1:
    """Produce the one deterministic, in-memory, authority-null tent proposal."""
    if type(raw) is not bytes:
        raise PaperRepairTentError("SOURCE_BYTES_REFUSED")
    if (
        len(raw) != TEST_PAPER_BYTE_COUNT
        or _sha256(raw) != HISTORICAL_FIXTURE_SHA256
        or _git_blob_oid(raw) != TEST_PAPER_GIT_BLOB_OID
    ):
        raise PaperRepairTentError("HISTORICAL_FIXTURE_REQUIRED")
    return _make_proposal(raw)


def canonical_paper_repair_tent_proposal_bytes(
    proposal: PaperRepairTentProposalV1,
) -> bytes:
    if type(proposal) is not PaperRepairTentProposalV1:
        raise PaperRepairTentError("PROPOSAL_TYPE_REFUSED")
    encoded = _canonical_json_bytes(proposal.canonical_payload())
    if not encoded or len(encoded) > MAX_PROPOSAL_BYTES:
        raise PaperRepairTentError("PROPOSAL_SIZE_REFUSED")
    return encoded


def paper_repair_tent_proposal_sha256(
    proposal: PaperRepairTentProposalV1,
) -> str:
    return hashlib.sha256(
        _PROPOSAL_DIGEST_PREFIX + canonical_paper_repair_tent_proposal_bytes(proposal)
    ).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PaperRepairTentError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_float(_: str) -> None:
    raise PaperRepairTentError("JSON_FLOAT_REFUSED")


def _reject_constant(_: str) -> None:
    raise PaperRepairTentError("JSON_CONSTANT_REFUSED")


def _exact_dict(value: object, keys: frozenset[str], code: str) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != keys:
        raise PaperRepairTentError(code)
    return value


def _parse_exact_enum(value: object, expected: Any, code: str) -> Any:
    if type(value) is not str or value != expected.value:
        raise PaperRepairTentError(code)
    return expected


_NORMALIZATION_KEYS = frozenset(PaperNormalizationReceiptV1.__slots__)
_PROPOSAL_WIRE_KEYS = frozenset(
    {
        "authority_effect",
        "candidate_bytes_b64",
        "candidate_sha256",
        "claim_ceiling",
        "cochain_realization",
        "evaluator_status",
        "filesystem_writes",
        "handler_id",
        "initial_trace_sha256",
        "lifecycle_status",
        "log_end_byte",
        "log_start_byte",
        "mathematical_terminal",
        "network_calls",
        "normalization",
        "patch_sha256",
        "patch_text",
        "producer_identity_links_b64",
        "producer_identity_links_sha256",
        "provider_calls",
        "raw_bytes_b64",
        "repair_proposal_sha256",
        "residual_sha256",
        "schema_version",
        "source_git_blob_oid",
        "source_path",
        "source_sha256",
        "updated_trace_sha256",
        "workflow_terminal",
    }
)


def parse_paper_repair_tent_proposal_v1(
    data: bytes,
) -> PaperRepairTentProposalV1:
    if type(data) is not bytes or not data or len(data) > MAX_PROPOSAL_BYTES:
        raise PaperRepairTentError("PROPOSAL_BYTES_REFUSED")
    try:
        raw = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except PaperRepairTentError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PaperRepairTentError("PROPOSAL_JSON_REFUSED") from exc
    root = _exact_dict(raw, _PROPOSAL_WIRE_KEYS, "PROPOSAL_FIELDS_REFUSED")
    normal = _exact_dict(
        root["normalization"],
        _NORMALIZATION_KEYS,
        "NORMALIZATION_FIELDS_REFUSED",
    )
    if type(normal["losses"]) is not list or any(
        type(item) is not str for item in normal["losses"]
    ):
        raise PaperRepairTentError("LOSS_LEDGER_WIRE_REFUSED")
    normalization = PaperNormalizationReceiptV1(
        **{
            **normal,
            "losses": tuple(normal["losses"]),
            "authority_effect": _parse_exact_enum(
                normal["authority_effect"],
                AuthorityEffectV1.NONE,
                "AUTHORITY_EFFECT_REFUSED",
            ),
        }
    )
    proposal = PaperRepairTentProposalV1(
        raw_bytes=_decode_b64(root["raw_bytes_b64"], "RAW_BASE64_REFUSED"),
        candidate_bytes=_decode_b64(
            root["candidate_bytes_b64"], "CANDIDATE_BASE64_REFUSED"
        ),
        patch_text=root["patch_text"],
        normalization=normalization,
        source_path=root["source_path"],
        source_git_blob_oid=root["source_git_blob_oid"],
        source_sha256=root["source_sha256"],
        candidate_sha256=root["candidate_sha256"],
        patch_sha256=root["patch_sha256"],
        initial_trace_sha256=root["initial_trace_sha256"],
        updated_trace_sha256=root["updated_trace_sha256"],
        residual_sha256=root["residual_sha256"],
        repair_proposal_sha256=root["repair_proposal_sha256"],
        log_start_byte=root["log_start_byte"],
        log_end_byte=root["log_end_byte"],
        handler_id=root["handler_id"],
        claim_ceiling=root["claim_ceiling"],
        producer_identity_links_bytes=_decode_b64(
            root["producer_identity_links_b64"], "IDENTITY_LINKS_BASE64_REFUSED"
        ),
        producer_identity_links_sha256=root["producer_identity_links_sha256"],
        lifecycle_status=_parse_exact_enum(
            root["lifecycle_status"],
            LifecycleStatusV1.PROPOSED,
            "LIFECYCLE_STATUS_REFUSED",
        ),
        evaluator_status=_parse_exact_enum(
            root["evaluator_status"],
            EvidenceStatus.NOT_ATTEMPTED,
            "EVALUATOR_STATUS_REFUSED",
        ),
        cochain_realization=_parse_exact_enum(
            root["cochain_realization"],
            RealizationStatus.UNRESOLVED,
            "COCHAIN_REALIZATION_REFUSED",
        ),
        mathematical_terminal=_parse_exact_enum(
            root["mathematical_terminal"],
            TerminalStatusV1.OPEN_OBSTRUCTION,
            "MATHEMATICAL_TERMINAL_REFUSED",
        ),
        workflow_terminal=root["workflow_terminal"],
        provider_calls=root["provider_calls"],
        network_calls=root["network_calls"],
        filesystem_writes=root["filesystem_writes"],
        authority_effect=_parse_exact_enum(
            root["authority_effect"],
            AuthorityEffectV1.NONE,
            "AUTHORITY_EFFECT_REFUSED",
        ),
        schema_version=root["schema_version"],
    )
    if canonical_paper_repair_tent_proposal_bytes(proposal) != data:
        raise PaperRepairTentError("NONCANONICAL_PROPOSAL_BYTES")
    return proposal


__all__ = [
    "MAX_PROPOSAL_BYTES",
    "MAX_SOURCE_BYTES",
    "NORMALIZATION_SCHEMA_V1",
    "PROPOSAL_SCHEMA_V1",
    "SOURCE_FIXTURE_PATH",
    "PaperNormalizationReceiptV1",
    "PaperRepairTentError",
    "PaperRepairTentProposalV1",
    "canonical_paper_repair_tent_proposal_bytes",
    "normalize_paper_with_loss_v1",
    "paper_repair_tent_proposal_sha256",
    "parse_paper_repair_tent_proposal_v1",
    "produce_paper_repair_tent_v1",
]
