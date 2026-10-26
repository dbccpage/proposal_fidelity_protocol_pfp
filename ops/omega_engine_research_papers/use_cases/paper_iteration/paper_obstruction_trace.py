"""Structural paper-obstruction traces (claim-defect layer, not object cochains).

This trace records textual/claim defects over a frozen paper carrier. It does
NOT construct the paper's object-level C0/C1/C2 or d0/d1, and it never claims
that an obstruction was deleted from the paper mathematics.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Sequence

from omega_engine_pfp.domain.shared_kernel.research_digest import digest_payload

TRACE_SCHEMA = "omega.paper_obstruction_trace.v1"
DETECTOR_UNBOUND_LOG = "paper_sweep.unbound_iteration_log.v1"

# Compatibility identity for the historical CRLF pilot used by the legacy
# paper-sweep coordinator.  P3-03 must not silently rebind this public name.
TEST_PAPER_SHA256 = "251ece1368282b877150b7341e274a5d2f5c4c0394cb3b5fe7cf6963a279c6c4"
HISTORICAL_FIXTURE_SHA256 = (
    "a43fa0a3971124a08554078eaa815e0ff21829b91b02df04fab0bf0d7ed93fff"
)
TEST_PAPER_GIT_BLOB_OID = "402306a417d5b5139161d2b7a657c18fd7e4bae1"
TEST_PAPER_BYTE_COUNT = 116_124
TEST_PAPER_UNBOUND_LOG_COUNT = 84

PRESERVED_OBLIGATIONS: tuple[str, ...] = (
    "P1-C2",
    "PL-GTOC-9",
    "PL-GTOC-34",
    "TypeDetectorAdequacy",
    "K6",
)
PRESERVED_ROUTES: tuple[str, ...] = (
    "CounterexampleSearch",
    "LeanObligation",
    "TransportLicenseNeeded",
    "DetectorAdequacyNeeded",
)

_LOG_HEADING = re.compile(rb"(?m)^## GTOC/GTLA Iteration Log[ \t]*(?:\r\n|\n|\r|$)")
_LOG_ENTRY = re.compile(rb"(?m)^- \*\*Pass [^\r\n]*(?:\r\n|\n|\r|$)")
_DDA_REFERENCE = re.compile(rb"(?:Generated )?DDA module:[ \t]*`[^`\r\n]+`")
_SHA256_IN_TEXT = re.compile(rb"\b[0-9a-fA-F]{64}\b")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")


def _require_digest(value: object, label: str) -> None:
    if (
        type(value) is not str
        or _LOWER_SHA256.fullmatch(value) is None
        or value == "0" * 64
    ):
        raise ValueError(f"{label} must be a nonzero lowercase SHA-256")


def _require_exact_literal(value: object, expected: str, label: str) -> None:
    if type(value) is not str or value != expected:
        raise ValueError(f"{label} must be exact {expected}")


def _require_string_tuple(value: object, label: str) -> None:
    if type(value) is not tuple or any(
        type(item) is not str or not item for item in value
    ):
        raise ValueError(f"{label} must be an exact tuple of nonempty strings")


class RealizationStatus(str, Enum):
    EXACT = "EXACT"
    STRUCTURAL = "STRUCTURAL"
    UNRESOLVED = "UNRESOLVED"


class FindingSeverity(str, Enum):
    BLOCKING = "blocking"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingRoute(str, Enum):
    TEXTUAL_REPAIR = "TextualRepair"
    COUNTEREXAMPLE_SEARCH = "CounterexampleSearch"
    LEAN_OBLIGATION = "LeanObligation"
    TRANSPORT_LICENSE_NEEDED = "TransportLicenseNeeded"
    DETECTOR_ADEQUACY_NEEDED = "DetectorAdequacyNeeded"
    ORACLE_NEEDED = "OracleNeeded"
    OPEN_OBSTRUCTION = "OpenObstruction"


@dataclass(frozen=True)
class PaperFinding:
    finding_id: str
    detector_rule: str
    severity: FindingSeverity
    route: FindingRoute
    start_byte: int
    end_byte: int
    claim_ids: tuple[str, ...]
    summary: str
    evidence_sha256: str
    blocking: bool = True

    def __post_init__(self) -> None:
        if type(self.finding_id) is not str or not self.finding_id:
            raise ValueError("finding_id must be a nonempty string")
        if type(self.detector_rule) is not str or not self.detector_rule:
            raise ValueError("detector_rule must be a nonempty string")
        if type(self.severity) is not FindingSeverity:
            raise ValueError("severity must be FindingSeverity")
        if type(self.route) is not FindingRoute:
            raise ValueError("route must be FindingRoute")
        if (
            type(self.start_byte) is not int
            or type(self.end_byte) is not int
            or self.start_byte < 0
            or self.end_byte < self.start_byte
        ):
            raise ValueError("finding byte span is invalid")
        _require_string_tuple(self.claim_ids, "claim_ids")
        if type(self.summary) is not str or not self.summary:
            raise ValueError("summary must be a nonempty string")
        _require_digest(self.evidence_sha256, "evidence_sha256")
        if type(self.blocking) is not bool:
            raise ValueError("blocking must be bool")

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "blocking": self.blocking,
            "claim_ids": list(self.claim_ids),
            "detector_rule": self.detector_rule,
            "end_byte": self.end_byte,
            "evidence_sha256": self.evidence_sha256,
            "finding_id": self.finding_id,
            "route": self.route.value,
            "severity": self.severity.value,
            "start_byte": self.start_byte,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class TraceOperation:
    op_id: str
    kind: str
    before_hash: str
    after_hash: str
    losses: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if type(self.op_id) is not str or not self.op_id:
            raise ValueError("op_id must be a nonempty string")
        if type(self.kind) is not str or not self.kind:
            raise ValueError("kind must be a nonempty string")
        _require_digest(self.before_hash, "before_hash")
        _require_digest(self.after_hash, "after_hash")
        _require_string_tuple(self.losses, "losses")
        if type(self.notes) is not str:
            raise ValueError("notes must be a string")

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "after_hash": self.after_hash,
            "before_hash": self.before_hash,
            "kind": self.kind,
            "losses": list(self.losses),
            "notes": self.notes,
            "op_id": self.op_id,
        }


@dataclass(frozen=True)
class PaperObstructionTrace:
    """Chained structural obstruction trace for one frozen paper carrier."""

    source_sha256: str
    cochain_realization: RealizationStatus
    findings: tuple[PaperFinding, ...]
    operations: tuple[TraceOperation, ...] = ()
    primitives: tuple[str, ...] = ()
    preserved_routes: tuple[str, ...] = PRESERVED_ROUTES
    preserved_obligations: tuple[str, ...] = PRESERVED_OBLIGATIONS
    log_start_byte: Optional[int] = None
    log_end_byte: Optional[int] = None
    unbound_log_count: int = 0
    schema_version: str = TRACE_SCHEMA
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require_digest(self.source_sha256, "source_sha256")
        if type(self.cochain_realization) is not RealizationStatus:
            raise ValueError("cochain_realization must be RealizationStatus")
        if self.cochain_realization is RealizationStatus.EXACT:
            raise ValueError(
                "paper object cochain must not be marked EXACT in this pilot"
            )
        if type(self.findings) is not tuple or any(
            type(item) is not PaperFinding for item in self.findings
        ):
            raise ValueError("findings must be an exact tuple of PaperFinding")
        for finding in self.findings:
            finding.__post_init__()
        if type(self.operations) is not tuple or any(
            type(item) is not TraceOperation for item in self.operations
        ):
            raise ValueError("operations must be an exact tuple of TraceOperation")
        for operation in self.operations:
            operation.__post_init__()
        _require_string_tuple(self.primitives, "primitives")
        _require_string_tuple(self.preserved_routes, "preserved_routes")
        _require_string_tuple(self.preserved_obligations, "preserved_obligations")
        if len(set(self.preserved_routes)) != len(self.preserved_routes):
            raise ValueError("preserved_routes must not contain duplicates")
        if len(set(self.preserved_obligations)) != len(self.preserved_obligations):
            raise ValueError("preserved_obligations must not contain duplicates")
        if (self.log_start_byte is None) != (self.log_end_byte is None):
            raise ValueError("log byte span must be wholly present or absent")
        if self.log_start_byte is not None and (
            type(self.log_start_byte) is not int
            or type(self.log_end_byte) is not int
            or self.log_start_byte < 0
            or self.log_end_byte <= self.log_start_byte
        ):
            raise ValueError("log byte span is invalid")
        if type(self.unbound_log_count) is not int or self.unbound_log_count < 0:
            raise ValueError("unbound_log_count must be a nonnegative integer")
        if self.unbound_log_count and self.log_start_byte is None:
            raise ValueError("unbound log count requires a declared span")
        _require_exact_literal(self.schema_version, TRACE_SCHEMA, "schema_version")
        _require_exact_literal(self.authority_effect, "None", "authority_effect")
        # Chain validation: each op's before matches previous after or source.
        previous = self.source_sha256
        for op in self.operations:
            if op.before_hash != previous:
                raise ValueError(
                    f"trace chain broken at {op.op_id}: "
                    f"before={op.before_hash} expected={previous}"
                )
            previous = op.after_hash

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect,
            "cochain_realization": self.cochain_realization.value,
            "findings": [item.canonical_payload() for item in self.findings],
            "log_end_byte": self.log_end_byte,
            "log_start_byte": self.log_start_byte,
            "operations": [item.canonical_payload() for item in self.operations],
            "preserved_obligations": list(self.preserved_obligations),
            "preserved_routes": list(self.preserved_routes),
            "primitives": list(self.primitives),
            "schema_version": self.schema_version,
            "source_sha256": self.source_sha256,
            "unbound_log_count": self.unbound_log_count,
        }

    @property
    def trace_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _section_end_byte(raw: bytes, section_start: int) -> int:
    """End of a markdown section: next H1/H2 heading, else EOF."""
    next_heading = re.compile(rb"(?m)^#{1,2}[ \t]+[^\r\n]")
    for match in next_heading.finditer(raw, section_start + 1):
        if match.start() <= section_start:
            continue
        return match.start()
    return len(raw)


def detect_unbound_iteration_log(raw: bytes) -> tuple[int, int, list[tuple[int, int]]]:
    """Return (log_start, log_end, unbound entry spans). Raises if no single log.

    Prose is never a receipt. The words "receipt" + any 64-hex token do not bind.
    """
    if type(raw) is not bytes:
        raise ValueError("paper carrier must be exact bytes")
    headings = list(_LOG_HEADING.finditer(raw))
    if len(headings) != 1:
        raise ValueError(
            f"expected exactly one iteration-log heading, found {len(headings)}"
        )
    log_start = headings[0].start()
    log_end = _section_end_byte(raw, log_start)
    spans: list[tuple[int, int]] = []
    for match in _LOG_ENTRY.finditer(raw, log_start, log_end):
        line = match.group(0)
        if b"DELETED OBSTRUCTION" not in line:
            continue
        if _DDA_REFERENCE.search(line) is None:
            continue
        spans.append((match.start(), match.end()))
    if not spans:
        raise ValueError("no unbound iteration-log entries found")
    return log_start, log_end, spans


def count_unbound_iteration_entries(raw: bytes) -> int:
    """Count the targeted residual globally without requiring the old heading."""
    if type(raw) is not bytes:
        raise ValueError("paper carrier must be exact bytes")
    return sum(
        1
        for match in _LOG_ENTRY.finditer(raw)
        if b"DELETED OBSTRUCTION" in match.group(0)
        and _DDA_REFERENCE.search(match.group(0)) is not None
    )


def markers_present(raw: bytes, markers: Sequence[str]) -> tuple[str, ...]:
    return tuple(m for m in markers if m.encode("utf-8") in raw)


def build_constitutive_succession_trace(raw: bytes) -> PaperObstructionTrace:
    """Build the pilot obstruction trace for 001_gtoc_time (sole-input rule)."""
    source_sha256 = _sha256(raw)
    if source_sha256 != HISTORICAL_FIXTURE_SHA256 or len(raw) != TEST_PAPER_BYTE_COUNT:
        raise ValueError("historical paper fixture bytes are required")
    log_start, log_end, spans = detect_unbound_iteration_log(raw)
    if (
        len(spans) != TEST_PAPER_UNBOUND_LOG_COUNT
        or count_unbound_iteration_entries(raw) != TEST_PAPER_UNBOUND_LOG_COUNT
    ):
        raise ValueError("historical paper fixture must contain exactly 84 entries")
    span_hash = _sha256(raw[log_start:log_end])

    findings: list[PaperFinding] = [
        PaperFinding(
            finding_id="F-UNBOUND-LOG-CORPUS",
            detector_rule=DETECTOR_UNBOUND_LOG,
            severity=FindingSeverity.BLOCKING,
            route=FindingRoute.TEXTUAL_REPAIR,
            start_byte=log_start,
            end_byte=log_end,
            claim_ids=("iteration-log",),
            summary=(
                f"{len(spans)} iteration-log entries assert DELETED OBSTRUCTION "
                "and name DDA modules without a verified receipt or content hash "
                "bound in the paper. Cochain realization remains Unresolved."
            ),
            evidence_sha256=span_hash,
            blocking=True,
        )
    ]
    # Individual entry findings (stable IDs for ranking/downstream).
    for index, (start, end) in enumerate(spans, start=1):
        findings.append(
            PaperFinding(
                finding_id=f"F-UNBOUND-LOG-{index:03d}",
                detector_rule=DETECTOR_UNBOUND_LOG,
                severity=FindingSeverity.HIGH,
                route=FindingRoute.TEXTUAL_REPAIR,
                start_byte=start,
                end_byte=end,
                claim_ids=(f"log-entry-{index}",),
                summary="Unbound DELETED OBSTRUCTION log entry without receipt hash.",
                evidence_sha256=_sha256(raw[start:end]),
                blocking=True,
            )
        )

    # Residual open-work findings (not invented closures).
    residual_routes = (
        (FindingRoute.COUNTEREXAMPLE_SEARCH, "P1-C2"),
        (FindingRoute.LEAN_OBLIGATION, "PL-GTOC-9"),
        (FindingRoute.DETECTOR_ADEQUACY_NEEDED, "PL-GTOC-34"),
        (FindingRoute.TRANSPORT_LICENSE_NEEDED, "self-application-bridge"),
    )
    for route, claim in residual_routes:
        token = claim.encode("utf-8")
        if token not in raw and claim not in PRESERVED_OBLIGATIONS:
            continue
        findings.append(
            PaperFinding(
                finding_id=f"F-OPEN-{route.value}",
                detector_rule="paper_sweep.open_obligation.v1",
                severity=FindingSeverity.MEDIUM,
                route=route,
                start_byte=0,
                end_byte=0,
                claim_ids=(claim,),
                summary=(
                    f"Genuine open obligation/route remains: {claim} → {route.value}. "
                    "Not closed by log repair."
                ),
                evidence_sha256=source_sha256,
                blocking=False,
            )
        )

    present_routes = markers_present(raw, PRESERVED_ROUTES)
    present_obs = markers_present(raw, PRESERVED_OBLIGATIONS)
    if present_routes != PRESERVED_ROUTES:
        raise ValueError("historical paper fixture is missing a preserved route")
    if present_obs != PRESERVED_OBLIGATIONS:
        raise ValueError("historical paper fixture is missing a preserved obligation")

    return PaperObstructionTrace(
        source_sha256=source_sha256,
        cochain_realization=RealizationStatus.UNRESOLVED,
        findings=tuple(findings),
        operations=(),
        primitives=(
            "cuts",
            "immediate_incidence",
            "K11",
            "M3",
            "K6",
            "ZeroRel",
        ),
        preserved_routes=present_routes,
        preserved_obligations=present_obs,
        log_start_byte=log_start,
        log_end_byte=log_end,
        unbound_log_count=len(spans),
    )


def append_operation(
    trace: PaperObstructionTrace,
    *,
    op_id: str,
    kind: str,
    after_hash: str,
    losses: Sequence[str] = (),
    notes: str = "",
) -> PaperObstructionTrace:
    before = (
        trace.operations[-1].after_hash if trace.operations else trace.source_sha256
    )
    op = TraceOperation(
        op_id=op_id,
        kind=kind,
        before_hash=before,
        after_hash=after_hash,
        losses=tuple(losses),
        notes=notes,
    )
    return PaperObstructionTrace(
        source_sha256=trace.source_sha256,
        cochain_realization=trace.cochain_realization,
        findings=trace.findings,
        operations=trace.operations + (op,),
        primitives=trace.primitives,
        preserved_routes=trace.preserved_routes,
        preserved_obligations=trace.preserved_obligations,
        log_start_byte=trace.log_start_byte,
        log_end_byte=trace.log_end_byte,
        unbound_log_count=trace.unbound_log_count,
        schema_version=trace.schema_version,
        authority_effect=trace.authority_effect,
    )


__all__ = [
    "DETECTOR_UNBOUND_LOG",
    "FindingRoute",
    "FindingSeverity",
    "HISTORICAL_FIXTURE_SHA256",
    "PRESERVED_OBLIGATIONS",
    "PRESERVED_ROUTES",
    "PaperFinding",
    "PaperObstructionTrace",
    "RealizationStatus",
    "TEST_PAPER_SHA256",
    "TEST_PAPER_GIT_BLOB_OID",
    "TEST_PAPER_BYTE_COUNT",
    "TEST_PAPER_UNBOUND_LOG_COUNT",
    "TRACE_SCHEMA",
    "TraceOperation",
    "append_operation",
    "build_constitutive_succession_trace",
    "count_unbound_iteration_entries",
    "detect_unbound_iteration_log",
    "markers_present",
]
