"""Immutable paper-repair replay validation and data-only rendering.

Generated modules are data-only: they call trusted replay code and never
contain model-authored executable logic, exec/eval, sys.path mutation,
paper writes, or authority claims.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from omega_engine_pfp.domain.shared_kernel.research_digest import digest_payload

from .paper_obstruction_trace import (
    PRESERVED_OBLIGATIONS,
    PRESERVED_ROUTES,
    PaperObstructionTrace,
    build_constitutive_succession_trace,
)
from .paper_resolution import (
    CLAIM_CEILING,
    LOG_INTEGRITY_HANDLER,
    PaperRepairProposal,
    apply_log_integrity_repair,
    build_unbound_provenance_residual,
    route_residual,
)


class PaperReplayError(ValueError):
    """Typed refusal for replay failures."""


_SAFE = re.compile(r"[^a-z0-9_]+")


def _require_exact_literal(value: object, expected: str, label: str) -> None:
    if type(value) is not str or value != expected:
        raise PaperReplayError(f"{label} must be exact {expected}")


@dataclass(frozen=True)
class PaperReplayReceipt:
    status: str
    source_sha256: str
    candidate_sha256: str
    patch_sha256: str
    trace_sha256: str
    proposal_sha256: str
    module_relpath: str
    module_sha256: str
    provider_calls: int = 0
    authority_effect: str = "None"
    evidence_eligible: bool = False
    schema_version: str = "omega.paper_replay_receipt.v1"

    def __post_init__(self) -> None:
        if type(self.status) is not str or self.status != "NOT_EVALUATED":
            raise PaperReplayError(
                "P3-03 replay projection cannot mint evaluator status"
            )
        for label in (
            "source_sha256",
            "candidate_sha256",
            "patch_sha256",
            "trace_sha256",
            "proposal_sha256",
            "module_sha256",
        ):
            value = getattr(self, label)
            if (
                type(value) is not str
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                or value == "0" * 64
            ):
                raise PaperReplayError(f"{label} must be a nonzero lowercase SHA-256")
        if (
            type(self.module_relpath) is not str
            or not self.module_relpath
            or "\\" in self.module_relpath
            or self.module_relpath.startswith("/")
            or ".." in self.module_relpath.split("/")
        ):
            raise PaperReplayError("module_relpath must be a normalized relative path")
        if type(self.provider_calls) is not int or self.provider_calls != 0:
            raise PaperReplayError("P3-03 replay projection must use zero providers")
        _require_exact_literal(self.authority_effect, "None", "authority_effect")
        if self.evidence_eligible is not False:
            raise PaperReplayError("P3-03 replay projection is not evaluator evidence")
        _require_exact_literal(
            self.schema_version,
            "omega.paper_replay_receipt.v1",
            "schema_version",
        )

    def canonical_payload(self) -> dict[str, Any]:
        self.__post_init__()
        return {
            "authority_effect": self.authority_effect,
            "candidate_sha256": self.candidate_sha256,
            "evidence_eligible": self.evidence_eligible,
            "module_relpath": self.module_relpath,
            "module_sha256": self.module_sha256,
            "patch_sha256": self.patch_sha256,
            "proposal_sha256": self.proposal_sha256,
            "provider_calls": self.provider_calls,
            "schema_version": self.schema_version,
            "source_sha256": self.source_sha256,
            "status": self.status,
            "trace_sha256": self.trace_sha256,
        }

    @property
    def receipt_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_repair_replay(
    *,
    source_bytes: bytes,
    proposal: PaperRepairProposal,
    trace: PaperObstructionTrace,
) -> None:
    """Recompute hashes and prefix identity; raise on mismatch."""
    if type(source_bytes) is not bytes:
        raise PaperReplayError("source carrier must be exact bytes")
    if type(proposal) is not PaperRepairProposal:
        raise PaperReplayError("proposal must be exact PaperRepairProposal")
    if type(trace) is not PaperObstructionTrace:
        raise PaperReplayError("trace must be exact PaperObstructionTrace")
    try:
        proposal.__post_init__()
        trace.__post_init__()
    except ValueError as exc:
        raise PaperReplayError("claim carrier revalidation refused") from exc
    source_sha = _sha256(source_bytes)
    if source_sha != proposal.source_sha256:
        raise PaperReplayError("source hash mismatch")
    if source_sha != trace.source_sha256:
        raise PaperReplayError("trace source hash mismatch")
    if proposal.cochain_realization != "UNRESOLVED":
        raise PaperReplayError("cochain realization must remain UNRESOLVED")
    if proposal.authority_effect != "None":
        raise PaperReplayError("proposal authority effect must remain None")
    if proposal.mathematical_terminal != "OpenObstruction":
        raise PaperReplayError("proposal terminal must remain OpenObstruction")
    if proposal.handler_id != LOG_INTEGRITY_HANDLER:
        raise PaperReplayError("proposal handler mismatch")
    if proposal.claim_ceiling != CLAIM_CEILING:
        raise PaperReplayError("proposal claim ceiling mismatch")
    if proposal.finding_count_after != 0:
        raise PaperReplayError("candidate finding count must be 0")
    if _sha256(proposal.candidate_bytes) != proposal.candidate_sha256:
        raise PaperReplayError("candidate bytes do not match declared hash")
    if _sha256(proposal.patch_text.encode("utf-8")) != proposal.patch_sha256:
        raise PaperReplayError("patch bytes do not match declared hash")
    start = proposal.log_start_byte
    end = proposal.log_end_byte
    if proposal.candidate_bytes[:start] != source_bytes[:start]:
        raise PaperReplayError("prefix bytes before replaced span differ")
    try:
        initial_trace = build_constitutive_succession_trace(source_bytes)
        route = route_residual(build_unbound_provenance_residual(initial_trace))
        expected_proposal, expected_updated_trace = apply_log_integrity_repair(
            source_bytes, initial_trace, route
        )
    except ValueError as exc:
        raise PaperReplayError("source cannot reproduce the canonical repair") from exc
    if trace.canonical_payload() != expected_updated_trace.canonical_payload():
        raise PaperReplayError("trace does not match independent reconstruction")
    if proposal.canonical_payload() != expected_proposal.canonical_payload():
        raise PaperReplayError("proposal does not match independent reconstruction")
    if proposal.candidate_bytes != expected_proposal.candidate_bytes:
        raise PaperReplayError(
            "candidate bytes do not match independent reconstruction"
        )
    if proposal.patch_text != expected_proposal.patch_text:
        raise PaperReplayError("patch does not match independent reconstruction")
    expected_suffix = source_bytes[end:]
    candidate_suffix = proposal.candidate_bytes[
        start + (len(proposal.candidate_bytes) - len(source_bytes) + end - start) :
    ]
    if candidate_suffix != expected_suffix:
        raise PaperReplayError("suffix bytes after replaced span differ")
    if proposal.preserved_routes != PRESERVED_ROUTES:
        raise PaperReplayError("proposal must preserve every declared route")
    if proposal.preserved_obligations != PRESERVED_OBLIGATIONS:
        raise PaperReplayError("proposal must preserve every declared obligation")
    for marker in PRESERVED_ROUTES + PRESERVED_OBLIGATIONS:
        if marker.encode("utf-8") not in proposal.candidate_bytes:
            raise PaperReplayError(f"preserved route missing from candidate: {marker}")


def render_replay_module(
    *,
    run_id: str,
    proposal: PaperRepairProposal,
    trace: PaperObstructionTrace,
) -> str:
    """Render a data-only Python module that re-invokes trusted replay."""
    payload = {
        "run_id": run_id,
        "proposal": proposal.canonical_payload(),
        "trace_sha256": trace.trace_sha256,
        "source_sha256": proposal.source_sha256,
        "candidate_sha256": proposal.candidate_sha256,
        "cochain_realization": "UNRESOLVED",
        "authority_effect": "None",
        "evidence_eligible": False,
        "replay_status": "NOT_EVALUATED",
        "provider_calls": 0,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    # Escape triple quotes if any (should not appear in our payloads).
    if '"""' in payload_json:
        payload_json = payload_json.replace('"""', "'''")
    return f'''# AUTO-GENERATED paper-sweep DDA replay module — DATA ONLY.
# Do not hand-edit. No model-authored code. AuthorityEffect: None.
"""Content-addressed replay stub for paper-sweep structural repair."""

from __future__ import annotations

PAYLOAD = r"""
{payload_json}
"""

def main() -> int:
    try:
        from omega_engine_research_papers.use_cases.paper_iteration.paper_replay import load_and_assert_payload
    except ImportError:
        from omega_engine_operations.use_cases.paper_iteration.paper_replay import load_and_assert_payload

    load_and_assert_payload(PAYLOAD)
    print("REPLAY_NOT_EVALUATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def load_and_assert_payload(payload_text: str) -> dict[str, Any]:
    """Validate the data-only module payload (more than three labels)."""
    data = json.loads(payload_text)
    required = (
        "authority_effect",
        "candidate_sha256",
        "cochain_realization",
        "evidence_eligible",
        "proposal",
        "provider_calls",
        "replay_status",
        "run_id",
        "source_sha256",
        "trace_sha256",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise PaperReplayError(f"module payload missing fields: {missing}")
    if data.get("authority_effect") != "None":
        raise PaperReplayError("module payload must carry authority_effect None")
    if data.get("cochain_realization") != "UNRESOLVED":
        raise PaperReplayError("module payload must keep cochain UNRESOLVED")
    if data.get("provider_calls", 0) != 0:
        raise PaperReplayError("module payload must record provider_calls 0")
    if data.get("evidence_eligible") is not False:
        raise PaperReplayError("module payload is not evaluator evidence")
    if data.get("replay_status") != "NOT_EVALUATED":
        raise PaperReplayError("module payload cannot mint evaluator status")
    for label in ("source_sha256", "candidate_sha256", "trace_sha256"):
        value = data.get(label)
        if (
            type(value) is not str
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            or value == "0" * 64
        ):
            raise PaperReplayError(
                f"module payload {label} must be a nonzero lowercase SHA-256"
            )
    proposal = data.get("proposal")
    if not isinstance(proposal, dict):
        raise PaperReplayError("module payload proposal must be an object")
    for key in (
        "action",
        "candidate_sha256",
        "finding_count_after",
        "finding_count_before",
        "patch_sha256",
        "source_sha256",
    ):
        if key not in proposal:
            raise PaperReplayError(f"module proposal missing {key}")
    if proposal.get("candidate_sha256") != data.get("candidate_sha256"):
        raise PaperReplayError("module proposal/candidate hash desync")
    if proposal.get("source_sha256") != data.get("source_sha256"):
        raise PaperReplayError("module proposal/source hash desync")
    if proposal.get("finding_count_after") != 0:
        raise PaperReplayError("module proposal must report finding_count_after 0")
    if proposal.get("cochain_realization") not in (None, "UNRESOLVED"):
        raise PaperReplayError("module proposal cochain must be UNRESOLVED")
    return data


def build_replay_receipt(
    *,
    source_bytes: bytes,
    proposal: PaperRepairProposal,
    trace: PaperObstructionTrace,
    module_relpath: str,
    module_sha256: str,
) -> PaperReplayReceipt:
    verify_repair_replay(source_bytes=source_bytes, proposal=proposal, trace=trace)
    if (
        type(module_relpath) is not str
        or not module_relpath
        or "\\" in module_relpath
        or module_relpath.startswith("/")
        or ".." in module_relpath.split("/")
    ):
        raise PaperReplayError("module_relpath must be a normalized relative path")
    if (
        type(module_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", module_sha256) is None
        or module_sha256 == "0" * 64
    ):
        raise PaperReplayError("module_sha256 must be a nonzero lowercase SHA-256")
    return PaperReplayReceipt(
        status="NOT_EVALUATED",
        source_sha256=proposal.source_sha256,
        candidate_sha256=proposal.candidate_sha256,
        patch_sha256=proposal.patch_sha256,
        trace_sha256=trace.trace_sha256,
        proposal_sha256=proposal.proposal_sha256,
        module_relpath=module_relpath,
        module_sha256=module_sha256,
    )


__all__ = [
    "PaperReplayError",
    "PaperReplayReceipt",
    "build_replay_receipt",
    "load_and_assert_payload",
    "render_replay_module",
    "verify_repair_replay",
]
