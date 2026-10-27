"""Python reference implementation of the anti-skill pharmacy.

The screening path (`mssn_ports.PharmacyMatcher`) does not use this module's
`detect`: it runs the eleven native classes of
`engine/crates_rs/core_prompt_civilization/src/pharmacy.rs` through the
Symbol Game host (`native_pharmacy.NativePharmacy`) plus the Python-only
persona check. This module is kept because its value objects
(`FailureClass`, `DetectionContext`, `HostReplayReceipt`, ...) are the shared
vocabulary of the fixtures and callers, and because the parity test
(`tests/unit/test_pharmacy_parity.py`) runs it against the native pharmacy.

It is not a faithful port. The known behavioural differences from `pharmacy.rs`,
each pinned by the parity test:

1. PERSONA_AUTHORITY_LEAK is Python only (`detectors_run` lists 12 classes
   here, 11 natively), and `DetectionContext.granted_persona_roles` is a
   Python-only field that the native context refuses.
2. `objections` / `proposed_claim_deltas` count as present here when truthy
   (for example a non-empty string); natively only when a non-empty array.
3. Case folding uses Unicode `str.lower` here and `to_ascii_lowercase`
   natively, so non-ASCII case variants of the markers differ.
4. Digests hash `json.dumps(..., sort_keys=True)` with ASCII escaping here and
   serde_json's UTF-8 output natively, so subject and semantic digests (and the
   duplication and replay-receipt checks that compare them) differ for
   non-ASCII payloads.
5. Finding details quote with Python `repr` here and Rust `Debug` natively,
   and duplicates are removed globally here but only when adjacent natively.

AuthorityEffect: None.
"""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from eis.domain.host_checks import (
    persona_authority_leak_loci,
)


class FailureClass(Enum):
    """The 12 mechanical failure classes mined from historical trace corpora."""
    SELF_CERTIFICATION = "SELF_CERTIFICATION"
    FAKE_RECEIPT = "FAKE_RECEIPT"
    CONCLUSION_PRELOAD = "CONCLUSION_PRELOAD"
    SCHEMA_SEMANTIC_LAUNDERING = "SCHEMA_SEMANTIC_LAUNDERING"
    THEOREM_NAME_LAUNDERING = "THEOREM_NAME_LAUNDERING"
    OPTIMALITY_HALLUCINATION = "OPTIMALITY_HALLUCINATION"
    COMPLEXITY_HALLUCINATION = "COMPLEXITY_HALLUCINATION"
    BRANCH_DROP_EXHAUSTION = "BRANCH_DROP_EXHAUSTION"
    PERSONA_AUTHORITY_LEAK = "PERSONA_AUTHORITY_LEAK"
    PRIVATE_COT_DEPENDENCY = "PRIVATE_COT_DEPENDENCY"
    VERSION_DUPLICATION = "VERSION_DUPLICATION"
    DETECT_REPAIR_COUPLING = "DETECT_REPAIR_COUPLING"

    def code(self) -> str:
        return self.value

    def default_disposition(self) -> "Disposition":
        """The default scheduler response. A disposition is a routing decision, not a truth verdict."""
        if self in (
            FailureClass.SELF_CERTIFICATION,
            FailureClass.FAKE_RECEIPT,
            FailureClass.PERSONA_AUTHORITY_LEAK,
        ):
            return Disposition.REFUSE
        elif self in (
            FailureClass.SCHEMA_SEMANTIC_LAUNDERING,
            FailureClass.PRIVATE_COT_DEPENDENCY,
        ):
            return Disposition.HOLD
        else:
            return Disposition.FINDING


class Disposition(Enum):
    """Scheduler routing dispositions ordered strictly by severity."""
    FINDING = "FINDING"
    HOLD = "HOLD"
    REFUSE = "REFUSE"

    def severity_rank(self) -> int:
        if self == Disposition.FINDING:
            return 0
        elif self == Disposition.HOLD:
            return 1
        elif self == Disposition.REFUSE:
            return 2
        raise ValueError(f"Unknown disposition {self}")


@dataclass(frozen=True)
class Finding:
    """What a detector found. Carries no repair field by construction."""
    failure_class: FailureClass
    disposition: Disposition
    locus: str
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.failure_class, FailureClass):
            raise TypeError("failure_class must be a FailureClass")
        if not isinstance(self.disposition, Disposition):
            raise TypeError("disposition must be a Disposition")
        if not isinstance(self.locus, str):
            raise TypeError("locus must be a str")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a str")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Finding)
        return (
            self.failure_class == other.failure_class
            and self.disposition == other.disposition
            and self.locus == other.locus
            and self.detail == other.detail
        )

    def __hash__(self) -> int:
        return hash((type(self), self.failure_class, self.disposition, self.locus, self.detail))


@dataclass(frozen=True)
class HostReplayReceipt:
    """Host-issued receipt certifying that semantic replay executed and passed."""
    receipt_id: str
    host_signer: str
    target_digest: str
    replay_passed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str):
            raise TypeError("receipt_id must be a str")
        if not isinstance(self.host_signer, str):
            raise TypeError("host_signer must be a str")
        if not isinstance(self.target_digest, str):
            raise TypeError("target_digest must be a str")
        if not isinstance(self.replay_passed, bool):
            raise TypeError("replay_passed must be a bool")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HostReplayReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.host_signer == other.host_signer
            and self.target_digest == other.target_digest
            and self.replay_passed == other.replay_passed
        )


@dataclass(frozen=True)
class DetectionContext:
    """Context detectors need beyond the candidate document itself."""
    prompt: Optional[str] = None
    unexplored_branches: int = 0
    seen_digests: tuple[str, ...] = ()
    seen_semantic_digests: tuple[str, ...] = ()
    host_replay_receipt: Optional[HostReplayReceipt] = None
    semantic_replay_passed: bool = False
    granted_persona_roles: tuple[str, ...] = ("agent", "researcher")


@dataclass(frozen=True)
class DetectorReport:
    """Evidence emitted by a pharmacy detection run."""
    normalized_json_digest: str
    raw_bytes_digest: Optional[str]
    subject_digest: str
    semantic_payload_digest: str
    detectors_run: tuple[str, ...]
    findings: tuple[Finding, ...]

    def is_clean(self) -> bool:
        return len(self.findings) == 0

    def strongest_disposition(self) -> Optional[Disposition]:
        if not self.findings:
            return None
        return max(self.findings, key=lambda f: f.disposition.severity_rank()).disposition

    def authority_effect(self) -> str:
        return "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DetectorReport)
        return (
            self.normalized_json_digest == other.normalized_json_digest
            and self.raw_bytes_digest == other.raw_bytes_digest
            and self.subject_digest == other.subject_digest
            and self.semantic_payload_digest == other.semantic_payload_digest
            and self.detectors_run == other.detectors_run
            and self.findings == other.findings
        )


from eis.domain.definitions_loader import (
    load_screening_vocabulary,
)

from .definitions_store import read_definition

_vocab = load_screening_vocabulary(read_definition("screening_vocabulary.yaml"))

# Host-only keys that a candidate model may never write
HOST_ONLY_KEYS: tuple[str, ...] = tuple(_vocab["host_only_keys"])

SELF_CERTIFYING_VALUES: tuple[str, ...] = tuple(_vocab["self_certifying_values"])

SUPERLATIVES: tuple[str, ...] = tuple(_vocab["superlatives"])

COMPLEXITY_MARKERS: tuple[str, ...] = tuple(_vocab["complexity_markers"])

PRIVATE_COT_MARKERS: tuple[str, ...] = tuple(_vocab["private_cot_markers"])



def looks_like_digest(text: str) -> bool:
    candidate = text[7:] if text.startswith("sha256:") else text
    if len(candidate) != 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in candidate)


def _walk_strings(val: Any, path: str, out: list[tuple[str, str]]) -> None:
    if isinstance(val, str):
        out.append((path, val))
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            _walk_strings(item, f"{path}/{idx}", out)
    elif isinstance(val, dict):
        for k, v in val.items():
            _walk_strings(v, f"{path}/{k}", out)


def _walk_keys(val: Any, path: str, out: list[tuple[str, str, Any]]) -> None:
    if isinstance(val, dict):
        for k, v in val.items():
            out.append((f"{path}/{k}", k, v))
            _walk_keys(v, f"{path}/{k}", out)
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            _walk_keys(item, f"{path}/{idx}", out)


def compute_semantic_payload_bytes(candidate: Any) -> bytes:
    if isinstance(candidate, dict):
        filtered = {
            k: v for k, v in candidate.items()
            if k not in ("schema_version", "version", "version_label", "schema")
        }
        return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_semantic_payload_digest(candidate: Any) -> str:
    raw = compute_semantic_payload_bytes(candidate)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def detect(
    candidate: Any,
    context: Optional[DetectionContext] = None,
    raw_bytes: Optional[bytes] = None,
) -> DetectorReport:
    """Run the 12-class mechanical pharmacy detector suite over a candidate payload."""
    if context is None:
        context = DetectionContext()

    normalized_bytes = json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    normalized_json_digest = f"sha256:{hashlib.sha256(normalized_bytes).hexdigest()}"
    raw_bytes_digest = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}" if raw_bytes is not None else None
    subject_digest = normalized_json_digest
    semantic_digest = compute_semantic_payload_digest(candidate)

    strings: list[tuple[str, str]] = []
    _walk_strings(candidate, "", strings)
    keys: list[tuple[str, str, Any]] = []
    _walk_keys(candidate, "", keys)

    findings: list[Finding] = []

    # 1 & 2. Host-only keys and Fake Receipt checks
    for path, key, value in keys:
        if key in HOST_ONLY_KEYS:
            findings.append(Finding(
                failure_class=FailureClass.SELF_CERTIFICATION,
                disposition=FailureClass.SELF_CERTIFICATION.default_disposition(),
                locus=path,
                detail=f"candidate declares host-only field {key!r}",
            ))
            if isinstance(value, str) and looks_like_digest(value):
                findings.append(Finding(
                    failure_class=FailureClass.FAKE_RECEIPT,
                    disposition=FailureClass.FAKE_RECEIPT.default_disposition(),
                    locus=path,
                    detail="candidate supplies a digest-shaped value for a host-computed field",
                ))

    # Text-based checks
    for path, text in strings:
        lower = text.lower()

        # Self-certification values
        if any(lower == word for word in SELF_CERTIFYING_VALUES):
            findings.append(Finding(
                failure_class=FailureClass.SELF_CERTIFICATION,
                disposition=FailureClass.SELF_CERTIFICATION.default_disposition(),
                locus=path,
                detail=f"candidate asserts {text!r}",
            ))

        # Optimality Hallucination
        if any(word in lower for word in SUPERLATIVES):
            findings.append(Finding(
                failure_class=FailureClass.OPTIMALITY_HALLUCINATION,
                disposition=FailureClass.OPTIMALITY_HALLUCINATION.default_disposition(),
                locus=path,
                detail="superlative claim without a candidate class, objective, and lower bound",
            ))

        # Complexity Hallucination
        if any(word in lower for word in COMPLEXITY_MARKERS):
            findings.append(Finding(
                failure_class=FailureClass.COMPLEXITY_HALLUCINATION,
                disposition=FailureClass.COMPLEXITY_HALLUCINATION.default_disposition(),
                locus=path,
                detail="complexity claim without an algorithm, cost model, or measurement",
            ))

        # Private CoT Dependency
        if any(word in lower for word in PRIVATE_COT_MARKERS):
            findings.append(Finding(
                failure_class=FailureClass.PRIVATE_COT_DEPENDENCY,
                disposition=FailureClass.PRIVATE_COT_DEPENDENCY.default_disposition(),
                locus=path,
                detail="conclusion leans on reasoning the public trace cannot show",
            ))

        # Theorem Name Laundering
        if "by " in lower and "theorem" in lower and "assum" not in lower:
            findings.append(Finding(
                failure_class=FailureClass.THEOREM_NAME_LAUNDERING,
                disposition=FailureClass.THEOREM_NAME_LAUNDERING.default_disposition(),
                locus=path,
                detail="theorem invoked by name with no applicability obligations stated",
            ))

        # Branch Drop Exhaustion
        if ("exhaustive" in lower or "exhausted" in lower) and context.unexplored_branches > 0:
            findings.append(Finding(
                failure_class=FailureClass.BRANCH_DROP_EXHAUSTION,
                disposition=FailureClass.BRANCH_DROP_EXHAUSTION.default_disposition(),
                locus=path,
                detail=f"exhaustion claimed while {context.unexplored_branches} branches remain unexplored",
            ))


    # Persona Authority Leak: the Python-only check shared with PharmacyMatcher.
    for path in persona_authority_leak_loci(candidate, tuple(context.granted_persona_roles)):
        findings.append(Finding(
            failure_class=FailureClass.PERSONA_AUTHORITY_LEAK,
            disposition=FailureClass.PERSONA_AUTHORITY_LEAK.default_disposition(),
            locus=path,
            detail="persona asserting authority beyond its declared grant",
        ))

    # Detect/Repair Coupling
    has_findings = bool(candidate.get("objections")) if isinstance(candidate, dict) else False
    has_repair = bool(candidate.get("proposed_claim_deltas")) if isinstance(candidate, dict) else False
    if has_findings and has_repair:
        findings.append(Finding(
            failure_class=FailureClass.DETECT_REPAIR_COUPLING,
            disposition=FailureClass.DETECT_REPAIR_COUPLING.default_disposition(),
            locus="/objections",
            detail="one artifact carries both a finding and its repair; they must be separate",
        ))

    # Schema Semantic Laundering
    host_replay_certified = False
    if context.host_replay_receipt is not None and context.host_replay_receipt.replay_passed:
        target = context.host_replay_receipt.target_digest.replace("sha256:", "")
        if target in (subject_digest.replace("sha256:", ""), semantic_digest.replace("sha256:", "")):
            host_replay_certified = True

    if has_repair and not host_replay_certified:
        detail_msg = (
            "deltas carry caller-provided semantic_replay_passed without host-issued replay receipt binding"
            if context.semantic_replay_passed
            else "well-formed deltas with no semantic replay; the candidate remains PARSED only"
        )
        findings.append(Finding(
            failure_class=FailureClass.SCHEMA_SEMANTIC_LAUNDERING,
            disposition=FailureClass.SCHEMA_SEMANTIC_LAUNDERING.default_disposition(),
            locus="/proposed_claim_deltas",
            detail=detail_msg,
        ))

    # Version Duplication
    if (
        subject_digest in context.seen_digests
        or semantic_digest in context.seen_digests
        or semantic_digest in context.seen_semantic_digests
    ):
        findings.append(Finding(
            failure_class=FailureClass.VERSION_DUPLICATION,
            disposition=FailureClass.VERSION_DUPLICATION.default_disposition(),
            locus="",
            detail="payload is semantically or byte-identical to one already recorded under another label",
        ))

    # Conclusion Preload in prompt
    if context.prompt is not None:
        lower_prompt = context.prompt.lower()
        for word in SELF_CERTIFYING_VALUES:
            if f"must be {word}" in lower_prompt or f"conclude that it is {word}" in lower_prompt:
                findings.append(Finding(
                    failure_class=FailureClass.CONCLUSION_PRELOAD,
                    disposition=FailureClass.CONCLUSION_PRELOAD.default_disposition(),
                    locus="/prompt",
                    detail=f"prompt fixes the required conclusion {word!r}",
                ))

    # Deterministic sorting and deduplication
    unique_findings = sorted(
        list(set(findings)),
        key=lambda f: (f.failure_class.code(), f.locus, f.detail)
    )

    detectors_run = tuple(fc.code() for fc in FailureClass)

    return DetectorReport(
        normalized_json_digest=normalized_json_digest,
        raw_bytes_digest=raw_bytes_digest,
        subject_digest=subject_digest,
        semantic_payload_digest=semantic_digest,
        detectors_run=detectors_run,
        findings=tuple(unique_findings),
    )
