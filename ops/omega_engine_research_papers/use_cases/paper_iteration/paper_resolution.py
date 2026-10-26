"""Structural paper-repair operations (C/E/R/I/M/T) with route preservation.

These operations act on the claim-defect layer. They do not construct object
cochains and do not prove paper mathematics.
"""

from __future__ import annotations

import difflib
import hashlib
from dataclasses import dataclass
from typing import Any, Sequence

from omega_engine_pfp.domain.shared_kernel.research_digest import digest_payload

from .paper_obstruction_trace import (
    HISTORICAL_FIXTURE_SHA256,
    PRESERVED_OBLIGATIONS,
    PRESERVED_ROUTES,
    TEST_PAPER_UNBOUND_LOG_COUNT,
    FindingRoute,
    PaperFinding,
    PaperObstructionTrace,
    RealizationStatus,
    append_operation,
    build_constitutive_succession_trace,
    count_unbound_iteration_entries,
    detect_unbound_iteration_log,
    markers_present,
)

KNOWN_RESIDUAL_CLASS = "paper.textual.unbound_provenance.v1"
LOG_INTEGRITY_HANDLER = "paper.log_integrity.v1"
CLAIM_CEILING = "TEXTUAL_STRUCTURE_ONLY"
_CORPUS_FINDING_ID = "F-UNBOUND-LOG-CORPUS"
_HISTORICAL_LOG_START = 98_197
_HISTORICAL_LOG_END = 116_124
_HISTORICAL_TRACE_SHA256 = (
    "52d16e7d5d00e654f51421193e4ad7fa9e27ceb51ca3a7a911c71bdfd2c9d676"
)


class ResolutionError(ValueError):
    """Typed refusal for an invalid structural paper repair."""


_REPLACEMENT_LINES = (
    "## GTOC/GTLA Iteration Provenance",
    "",
    (
        "The previous entries were exploratory iteration outputs. No verified "
        "receipt or content-addressed DDA artifact is bound to this paper for "
        "those entries; they therefore do not establish deletion of any obstruction."
    ),
    "",
    (
        "The cochain realization remains `Unresolved`. The stated "
        "`DetectorAdequacyNeeded`, K6, `TransportLicenseNeeded`, induction, "
        "and `CounterexampleSearch` obligations remain open. "
        "TypeDetectorAdequacy / PL-GTOC-34 remains the next substantive residual."
    ),
)


def _require_digest(value: object, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        or value == "0" * 64
    ):
        raise ResolutionError(f"{label} must be a nonzero lowercase SHA-256")


def _require_exact_literal(value: object, expected: str, label: str) -> None:
    if type(value) is not str or value != expected:
        raise ResolutionError(f"{label} must be exact {expected}")


def _require_string_tuple(value: object, label: str) -> None:
    if type(value) is not tuple or any(
        type(item) is not str or not item for item in value
    ):
        raise ResolutionError(f"{label} must be an exact tuple of nonempty strings")


@dataclass(frozen=True)
class PaperResidualV1:
    """Strict residual payload for the one selected historical incident."""

    residual_class: str
    carrier_sha256: str
    start_byte: int
    end_byte: int
    trace_sha256: str
    finding_id: str
    claim_ceiling: str = CLAIM_CEILING
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.residual_class) is not str or not self.residual_class:
            raise ResolutionError("residual_class must be a nonempty string")
        _require_digest(self.carrier_sha256, "carrier_sha256")
        _require_digest(self.trace_sha256, "trace_sha256")
        if (
            type(self.start_byte) is not int
            or type(self.end_byte) is not int
            or self.start_byte < 0
            or self.end_byte <= self.start_byte
        ):
            raise ResolutionError("residual byte span is invalid")
        if type(self.finding_id) is not str or not self.finding_id:
            raise ResolutionError("finding_id must be a nonempty string")
        _require_exact_literal(self.claim_ceiling, CLAIM_CEILING, "claim_ceiling")
        _require_exact_literal(self.authority_effect, "None", "authority_effect")

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect,
            "carrier_sha256": self.carrier_sha256,
            "claim_ceiling": self.claim_ceiling,
            "end_byte": self.end_byte,
            "finding_id": self.finding_id,
            "residual_class": self.residual_class,
            "start_byte": self.start_byte,
            "trace_sha256": self.trace_sha256,
        }

    @property
    def residual_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


@dataclass(frozen=True)
class PaperHandlerRouteV1:
    """Exact handler selection for one strict residual payload."""

    residual: PaperResidualV1
    handler_id: str = LOG_INTEGRITY_HANDLER
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require_routable_residual(self.residual)
        _require_exact_literal(self.handler_id, LOG_INTEGRITY_HANDLER, "handler_id")
        _require_exact_literal(self.authority_effect, "None", "authority_effect")

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect,
            "handler_id": self.handler_id,
            "residual": self.residual.canonical_payload(),
            "residual_sha256": self.residual.residual_sha256,
        }


def _require_routable_residual(residual: object) -> None:
    if type(residual) is not PaperResidualV1:
        raise ResolutionError("route requires exact PaperResidualV1")
    residual.__post_init__()
    if residual.residual_class != KNOWN_RESIDUAL_CLASS:
        raise ResolutionError("UNKNOWN_RESIDUAL_CLASS")
    if residual.carrier_sha256 != HISTORICAL_FIXTURE_SHA256:
        raise ResolutionError("UNKNOWN_RESIDUAL_CARRIER")
    if residual.finding_id != _CORPUS_FINDING_ID:
        raise ResolutionError("UNKNOWN_RESIDUAL_FINDING")
    if (
        residual.start_byte != _HISTORICAL_LOG_START
        or residual.end_byte != _HISTORICAL_LOG_END
    ):
        raise ResolutionError("UNKNOWN_RESIDUAL_SPAN")
    if residual.trace_sha256 != _HISTORICAL_TRACE_SHA256:
        raise ResolutionError("UNKNOWN_RESIDUAL_TRACE")


@dataclass(frozen=True)
class PaperRepairProposal:
    """Selected structural repair for the pilot log-integrity update."""

    action: str
    realization: str
    selected_finding_id: str
    source_sha256: str
    candidate_sha256: str
    patch_sha256: str
    candidate_bytes: bytes
    patch_text: str
    preserved_routes: tuple[str, ...]
    preserved_obligations: tuple[str, ...]
    residuals_preserved: tuple[str, ...]
    finding_count_before: int
    finding_count_after: int
    log_start_byte: int
    log_end_byte: int
    operations: tuple[str, ...]
    route: PaperHandlerRouteV1
    cochain_realization: str = RealizationStatus.UNRESOLVED.value
    authority_effect: str = "None"
    mathematical_terminal: str = "OpenObstruction"
    workflow_terminal: str = "OracleNeeded"

    def __post_init__(self) -> None:
        _require_exact_literal(
            self.action,
            "REPLACE_UNSUPPORTED_ITERATION_LOG_WITH_PROVENANCE_NOTE",
            "action",
        )
        _require_exact_literal(self.realization, "TEXTUAL_STRUCTURE", "realization")
        if type(self.route) is not PaperHandlerRouteV1:
            raise ResolutionError("proposal requires exact PaperHandlerRouteV1")
        self.route.__post_init__()
        if type(self.selected_finding_id) is not str:
            raise ResolutionError("selected_finding_id must be exact str")
        if self.selected_finding_id != self.route.residual.finding_id:
            raise ResolutionError("proposal finding does not match routed residual")
        if self.source_sha256 != self.route.residual.carrier_sha256:
            raise ResolutionError("proposal source does not match routed residual")
        _require_digest(self.source_sha256, "source_sha256")
        _require_digest(self.candidate_sha256, "candidate_sha256")
        _require_digest(self.patch_sha256, "patch_sha256")
        if type(self.candidate_bytes) is not bytes:
            raise ResolutionError("candidate_bytes must be exact bytes")
        if _sha256(self.candidate_bytes) != self.candidate_sha256:
            raise ResolutionError("candidate bytes do not match candidate_sha256")
        if type(self.patch_text) is not str:
            raise ResolutionError("patch_text must be a string")
        if _sha256(self.patch_text.encode("utf-8")) != self.patch_sha256:
            raise ResolutionError("patch text does not match patch_sha256")
        _require_string_tuple(self.preserved_routes, "preserved_routes")
        _require_string_tuple(self.preserved_obligations, "preserved_obligations")
        _require_string_tuple(self.residuals_preserved, "residuals_preserved")
        _require_string_tuple(self.operations, "operations")
        if self.preserved_routes != PRESERVED_ROUTES:
            raise ResolutionError("proposal must preserve every declared route")
        if self.preserved_obligations != PRESERVED_OBLIGATIONS:
            raise ResolutionError("proposal must preserve every declared obligation")
        if (
            type(self.finding_count_before) is not int
            or type(self.finding_count_after) is not int
            or type(self.log_start_byte) is not int
            or type(self.log_end_byte) is not int
        ):
            raise ResolutionError("proposal counts and span must be exact integers")
        if self.finding_count_before != TEST_PAPER_UNBOUND_LOG_COUNT:
            raise ResolutionError("proposal must bind the historical 84-count")
        if self.finding_count_after != 0:
            raise ResolutionError("proposal must leave zero targeted findings")
        if (
            self.log_start_byte != self.route.residual.start_byte
            or self.log_end_byte != self.route.residual.end_byte
        ):
            raise ResolutionError("proposal span does not match routed residual")
        if self.operations != ("C", "E", "R", "I", "M", "T"):
            raise ResolutionError("proposal operation sequence mismatch")
        _require_exact_literal(
            self.cochain_realization,
            RealizationStatus.UNRESOLVED.value,
            "cochain_realization",
        )
        _require_exact_literal(self.authority_effect, "None", "authority_effect")
        _require_exact_literal(
            self.mathematical_terminal,
            "OpenObstruction",
            "mathematical_terminal",
        )
        _require_exact_literal(
            self.workflow_terminal,
            "OracleNeeded",
            "workflow_terminal",
        )

    @property
    def handler_id(self) -> str:
        return self.route.handler_id

    @property
    def claim_ceiling(self) -> str:
        return self.route.residual.claim_ceiling

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "action": self.action,
            "authority_effect": self.authority_effect,
            "candidate_sha256": self.candidate_sha256,
            "claim_ceiling": self.claim_ceiling,
            "cochain_realization": self.cochain_realization,
            "finding_count_after": self.finding_count_after,
            "finding_count_before": self.finding_count_before,
            "log_end_byte": self.log_end_byte,
            "log_start_byte": self.log_start_byte,
            "handler_id": self.handler_id,
            "mathematical_terminal": self.mathematical_terminal,
            "operations": list(self.operations),
            "patch_sha256": self.patch_sha256,
            "preserved_obligations": list(self.preserved_obligations),
            "preserved_routes": list(self.preserved_routes),
            "realization": self.realization,
            "route": self.route.canonical_payload(),
            "residuals_preserved": list(self.residuals_preserved),
            "selected_finding_id": self.selected_finding_id,
            "source_sha256": self.source_sha256,
            "workflow_terminal": self.workflow_terminal,
        }

    @property
    def proposal_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _newline(raw: bytes) -> bytes:
    if b"\r\n" in raw and raw.count(b"\n") == raw.count(b"\r\n"):
        return b"\r\n"
    if b"\r" in raw and b"\n" not in raw:
        return b"\r"
    return b"\n"


def rank_findings(findings: Sequence[PaperFinding]) -> list[PaperFinding]:
    """Lexicographic ranking for pilot update selection."""

    severity_rank = {
        "blocking": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    local_repair = {
        FindingRoute.TEXTUAL_REPAIR: 0,
    }

    def key(f: PaperFinding) -> tuple:
        return (
            0 if f.blocking else 1,
            severity_rank.get(f.severity.value, 9),
            local_repair.get(f.route, 1),
            -(f.end_byte - f.start_byte),  # larger span first among peers
            f.end_byte - f.start_byte,  # then prefer smaller patch if equal
            f.finding_id,
        )

    return sorted(findings, key=key)


def build_provenance_replacement(raw: bytes) -> bytes:
    newline = _newline(raw)
    body = newline.join(line.encode("utf-8") for line in _REPLACEMENT_LINES)
    if raw.endswith((b"\r\n", b"\n", b"\r")):
        body += newline
    return body


def replace_declared_span(
    source: bytes,
    start_byte: int,
    end_byte: int,
    replacement: bytes,
) -> bytes:
    """Pure exact-span replacement used by the no-write handler."""
    if type(source) is not bytes or type(replacement) is not bytes:
        raise ResolutionError("source and replacement must be exact bytes")
    if (
        type(start_byte) is not int
        or type(end_byte) is not int
        or start_byte < 0
        or end_byte <= start_byte
        or end_byte > len(source)
    ):
        raise ResolutionError("declared replacement span is invalid")
    return source[:start_byte] + replacement + source[end_byte:]


def build_unbound_provenance_residual(
    trace: PaperObstructionTrace,
) -> PaperResidualV1:
    """Bind the canonical corpus finding into the strict residual payload."""
    if type(trace) is not PaperObstructionTrace:
        raise ResolutionError("residual builder requires exact PaperObstructionTrace")
    if trace.source_sha256 != HISTORICAL_FIXTURE_SHA256:
        raise ResolutionError("residual requires the historical fixture trace")
    if trace.operations:
        raise ResolutionError("residual must bind the pre-execution trace")
    if trace.unbound_log_count != TEST_PAPER_UNBOUND_LOG_COUNT:
        raise ResolutionError("residual trace must bind the historical 84-count")
    if trace.trace_sha256 != _HISTORICAL_TRACE_SHA256:
        raise ResolutionError("residual trace digest does not match the frozen fixture")
    finding = next(
        (item for item in trace.findings if item.finding_id == _CORPUS_FINDING_ID),
        None,
    )
    if (
        finding is None
        or finding.detector_rule != "paper_sweep.unbound_iteration_log.v1"
    ):
        raise ResolutionError("canonical corpus finding is missing")
    if (
        finding.start_byte != trace.log_start_byte
        or finding.end_byte != trace.log_end_byte
    ):
        raise ResolutionError("corpus finding span does not match trace")
    return PaperResidualV1(
        residual_class=KNOWN_RESIDUAL_CLASS,
        carrier_sha256=trace.source_sha256,
        start_byte=finding.start_byte,
        end_byte=finding.end_byte,
        trace_sha256=trace.trace_sha256,
        finding_id=finding.finding_id,
    )


def route_residual(residual: PaperResidualV1) -> PaperHandlerRouteV1:
    """Route the one frozen tent residual; refuse every unknown payload."""
    _require_routable_residual(residual)
    return PaperHandlerRouteV1(residual=residual)


def apply_log_integrity_repair(
    raw: bytes,
    trace: PaperObstructionTrace,
    route: PaperHandlerRouteV1,
) -> tuple[PaperRepairProposal, PaperObstructionTrace]:
    """Replace unsupported iteration log; preserve open obligations/routes."""
    if type(raw) is not bytes or type(trace) is not PaperObstructionTrace:
        raise ResolutionError("handler requires exact source bytes and trace")
    expected_trace = build_constitutive_succession_trace(raw)
    if trace.canonical_payload() != expected_trace.canonical_payload():
        raise ResolutionError("trace does not match canonical source diagnosis")
    expected_route = route_residual(build_unbound_provenance_residual(trace))
    if type(route) is not PaperHandlerRouteV1 or route != expected_route:
        raise ResolutionError("handler route does not bind the source diagnosis")
    if trace.cochain_realization is not RealizationStatus.UNRESOLVED:
        raise ResolutionError("pilot requires cochain_realization=UNRESOLVED")
    log_start, log_end, spans = detect_unbound_iteration_log(raw)
    if len(spans) != trace.unbound_log_count:
        raise ResolutionError("trace unbound count drifted from raw detection")
    if (
        trace.source_sha256 == HISTORICAL_FIXTURE_SHA256
        and len(spans) != TEST_PAPER_UNBOUND_LOG_COUNT
    ):
        raise ResolutionError("historical fixture must contain exactly 84 entries")

    ranked = rank_findings(trace.findings)
    selected = next(
        (f for f in ranked if f.finding_id == "F-UNBOUND-LOG-CORPUS"),
        ranked[0] if ranked else None,
    )
    if selected is None:
        raise ResolutionError("no finding available for selection")

    suffix = raw[log_end:]
    # Only force trailing newline when the log section ended the file.
    newline = _newline(raw)
    body = newline.join(line.encode("utf-8") for line in _REPLACEMENT_LINES)
    if not suffix and raw.endswith((b"\r\n", b"\n", b"\r")):
        body += newline
    elif suffix and not body.endswith((b"\r\n", b"\n", b"\r")):
        body += newline
    replacement = body
    candidate = replace_declared_span(raw, log_start, log_end, replacement)
    if candidate[:log_start] != raw[:log_start]:
        raise ResolutionError("prefix bytes changed before log span")
    if candidate[len(raw[:log_start]) + len(replacement) :] != suffix:
        raise ResolutionError("suffix bytes changed after log span")

    # The deterministic repair removes the old heading, so recount the targeted
    # residual globally rather than treating detector exceptions as success.
    after_count = count_unbound_iteration_entries(candidate)
    if after_count != 0:
        raise ResolutionError("candidate still has unbound log entries")

    preserved_routes = markers_present(candidate, PRESERVED_ROUTES)
    preserved_obs = markers_present(candidate, PRESERVED_OBLIGATIONS)
    missing_routes = set(PRESERVED_ROUTES) - set(preserved_routes)
    if missing_routes:
        raise ResolutionError(f"candidate lost routes: {sorted(missing_routes)}")
    missing_obligations = set(PRESERVED_OBLIGATIONS) - set(preserved_obs)
    if missing_obligations:
        raise ResolutionError(
            f"candidate lost obligations: {sorted(missing_obligations)}"
        )

    # Operations C/E/R/I/M/T (structural codes).
    # C=classify, E=evidence-bind, R=replace, I=identity-prefix,
    # M=marker-preserve, T=retain the existing open terminal.
    ops = ("C", "E", "R", "I", "M", "T")
    source_sha = _sha256(raw)
    candidate_sha = _sha256(candidate)
    text_src = raw.decode(
        "utf-8" if not raw.startswith(b"\xef\xbb\xbf") else "utf-8-sig"
    )
    text_cand = candidate.decode(
        "utf-8" if not candidate.startswith(b"\xef\xbb\xbf") else "utf-8-sig"
    )
    patch = "".join(
        difflib.unified_diff(
            text_src.replace("\r\n", "\n")
            .replace("\r", "\n")
            .splitlines(keepends=True),
            text_cand.replace("\r\n", "\n")
            .replace("\r", "\n")
            .splitlines(keepends=True),
            fromfile="a/001_gtoc_time.md",
            tofile="b/001_gtoc_time.md.candidate",
            lineterm="\n",
        )
    )
    patch_sha = _sha256(patch.encode("utf-8"))

    updated = append_operation(
        trace,
        op_id="op-01-log-replace",
        kind="REPLACE_WITH_PROVENANCE_NOTE",
        after_hash=candidate_sha,
        losses=("unsupported_iteration_log",),
        notes="Textual structural repair only; cochain remains UNRESOLVED.",
    )

    residuals = tuple(
        f.finding_id
        for f in trace.findings
        if not f.blocking and f.route is not FindingRoute.TEXTUAL_REPAIR
    )

    proposal = PaperRepairProposal(
        action="REPLACE_UNSUPPORTED_ITERATION_LOG_WITH_PROVENANCE_NOTE",
        realization="TEXTUAL_STRUCTURE",
        selected_finding_id=selected.finding_id,
        source_sha256=source_sha,
        candidate_sha256=candidate_sha,
        patch_sha256=patch_sha,
        candidate_bytes=candidate,
        patch_text=patch,
        preserved_routes=preserved_routes,
        preserved_obligations=preserved_obs,
        residuals_preserved=residuals,
        finding_count_before=len(spans),
        finding_count_after=0,
        log_start_byte=log_start,
        log_end_byte=log_end,
        operations=ops,
        route=route,
    )
    return proposal, updated


__all__ = [
    "PaperRepairProposal",
    "PaperHandlerRouteV1",
    "PaperResidualV1",
    "ResolutionError",
    "CLAIM_CEILING",
    "KNOWN_RESIDUAL_CLASS",
    "LOG_INTEGRITY_HANDLER",
    "apply_log_integrity_repair",
    "build_unbound_provenance_residual",
    "build_provenance_replacement",
    "rank_findings",
    "replace_declared_span",
    "route_residual",
]
