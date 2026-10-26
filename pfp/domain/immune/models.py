"""Legacy Symbol Game copy of the anti-skill pharmacy domain models.

See the package docstring: this copy is legacy, diverged from both OEEIS
(`omega_engine_epistemic_immune_system`) and the native pharmacy
(`omega_engine/crates_rs/omega_prompt_civilization/src/pharmacy.rs`), and is
kept only for existing callers. It is not a faithful port of either.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class CodeString(str):
    """String subclass that is callable, allowing fc.code and fc.code() interoperability."""

    def __call__(self) -> str:
        return str(self)


class PharmacyDisposition(str, Enum):
    """Scheduler routing dispositions ordered strictly by severity."""

    FINDING = "FINDING"
    HOLD = "HOLD"
    REFUSE = "REFUSE"

    def severity_rank(self) -> int:
        if self == PharmacyDisposition.FINDING:
            return 0
        elif self == PharmacyDisposition.HOLD:
            return 1
        elif self == PharmacyDisposition.REFUSE:
            return 2
        raise ValueError(f"Unknown disposition {self}")

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PharmacyDisposition):
            return NotImplemented
        return self.severity_rank() < other.severity_rank()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, PharmacyDisposition):
            return NotImplemented
        return self.severity_rank() <= other.severity_rank()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, PharmacyDisposition):
            return NotImplemented
        return self.severity_rank() > other.severity_rank()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, PharmacyDisposition):
            return NotImplemented
        return self.severity_rank() >= other.severity_rank()


# Also provide alias Disposition for compatibility
Disposition = PharmacyDisposition


class FailureClass(str, Enum):
    """The 12 mechanical failure classes matching pharmacy.rs."""

    SelfCertification = "SELF_CERTIFICATION"
    FakeReceipt = "FAKE_RECEIPT"
    ConclusionPreload = "CONCLUSION_PRELOAD"
    SchemaSemanticLaundering = "SCHEMA_SEMANTIC_LAUNDERING"
    TheoremNameLaundering = "THEOREM_NAME_LAUNDERING"
    OptimalityHallucination = "OPTIMALITY_HALLUCINATION"
    ComplexityHallucination = "COMPLEXITY_HALLUCINATION"
    BranchDropExhaustion = "BRANCH_DROP_EXHAUSTION"
    PersonaAuthorityLeak = "PERSONA_AUTHORITY_LEAK"
    PrivateCotDependency = "PRIVATE_COT_DEPENDENCY"
    VersionDuplication = "VERSION_DUPLICATION"
    DetectRepairCoupling = "DETECT_REPAIR_COUPLING"

    # Screaming snake case aliases (point to same enum members)
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

    @property
    def code(self) -> CodeString:
        """Returns the canonical string code, callable as fc.code() or readable as fc.code."""
        return CodeString(self.value)

    def default_disposition(self) -> PharmacyDisposition:
        """The default scheduler response. A disposition is a routing decision, not a truth verdict."""
        if self in (
            FailureClass.SelfCertification,
            FailureClass.FakeReceipt,
            FailureClass.PersonaAuthorityLeak,
        ):
            return PharmacyDisposition.REFUSE
        elif self in (
            FailureClass.SchemaSemanticLaundering,
            FailureClass.PrivateCotDependency,
        ):
            return PharmacyDisposition.HOLD
        else:
            return PharmacyDisposition.FINDING


@dataclass(frozen=True, slots=True)
class Finding:
    """What a detector found. Strictly decoupled from repair by construction (no repair field)."""

    failure_class: FailureClass
    disposition: PharmacyDisposition
    locus: str
    detail: str

    def __init__(
        self,
        failure_class: FailureClass,
        disposition: PharmacyDisposition,
        locus: str,
        detail: str,
        **kwargs: Any,
    ) -> None:
        if "repair" in kwargs:
            raise TypeError("Finding is strictly decoupled from repair by construction; repair field is forbidden")
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments for Finding: {list(kwargs.keys())}")
        if not isinstance(failure_class, FailureClass):
            raise TypeError(f"failure_class must be a FailureClass, got {type(failure_class).__name__}")
        if not isinstance(disposition, PharmacyDisposition):
            raise TypeError(f"disposition must be a PharmacyDisposition, got {type(disposition).__name__}")
        if not isinstance(locus, str):
            raise TypeError(f"locus must be a str, got {type(locus).__name__}")
        if not isinstance(detail, str):
            raise TypeError(f"detail must be a str, got {type(detail).__name__}")
        object.__setattr__(self, "failure_class", failure_class)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "locus", locus)
        object.__setattr__(self, "detail", detail)

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


@dataclass(frozen=True, slots=True)
class FailureReceipt:
    """Cryptographic evidence receipt sealing an observed failure class finding."""

    receipt_id: str
    failure_class: FailureClass
    disposition: PharmacyDisposition
    locus: str
    detail: str
    evidence_span_sha256: str
    canonical_hash: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(self.failure_class, FailureClass):
            raise TypeError("failure_class must be a FailureClass")
        if not isinstance(self.disposition, PharmacyDisposition):
            raise TypeError("disposition must be a PharmacyDisposition")
        if not isinstance(self.locus, str):
            raise TypeError("locus must be a str")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a str")
        if not isinstance(self.evidence_span_sha256, str) or len(self.evidence_span_sha256) != 64:
            raise ValueError("evidence_span_sha256 must be a 64-character hex string")
        if not isinstance(self.canonical_hash, str) or len(self.canonical_hash) != 64:
            raise ValueError("canonical_hash must be a 64-character hex string")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, FailureReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.failure_class == other.failure_class
            and self.disposition == other.disposition
            and self.locus == other.locus
            and self.detail == other.detail
            and self.evidence_span_sha256 == other.evidence_span_sha256
            and self.canonical_hash == other.canonical_hash
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.failure_class,
            self.disposition,
            self.locus,
            self.detail,
            self.evidence_span_sha256,
            self.canonical_hash,
            self.authority_effect,
        ))

    @classmethod
    def create(
        cls,
        finding: Finding,
        evidence_span: str = "",
        receipt_id: str = "",
    ) -> FailureReceipt:
        """Create a FailureReceipt sealed with an RFC 8785 canonical hash."""
        evidence_digest = hashlib.sha256(evidence_span.encode("utf-8")).hexdigest()
        if not receipt_id:
            receipt_id = f"FR-{evidence_digest[:12]}"

        body = {
            "authority_effect": "None",
            "detail": finding.detail,
            "disposition": finding.disposition.value,
            "evidence_span_sha256": evidence_digest,
            "failure_class": finding.failure_class.code(),
            "locus": finding.locus,
            "receipt_id": receipt_id,
        }
        canonical_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return cls(
            receipt_id=receipt_id,
            failure_class=finding.failure_class,
            disposition=finding.disposition,
            locus=finding.locus,
            detail=finding.detail,
            evidence_span_sha256=evidence_digest,
            canonical_hash=canonical_hash,
            authority_effect="None",
        )


@dataclass(frozen=True, slots=True)
class HostReplayReceipt:
    """A host-issued receipt certifying that semantic replay executed and passed."""

    receipt_id: str
    host_signer: str
    target_digest: str
    replay_passed: bool
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HostReplayReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.host_signer == other.host_signer
            and self.target_digest == other.target_digest
            and self.replay_passed is other.replay_passed
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.host_signer,
            self.target_digest,
            self.replay_passed,
            self.authority_effect,
        ))


@dataclass(frozen=True, slots=True)
class DetectionContext:
    """Evaluation context for pharmacy detectors."""

    host_replay_receipt: HostReplayReceipt | None = None
    semantic_replay_passed: bool = False
    unexplored_branches: int = 0
    # Legacy default; OEEIS defaults to ("agent", "researcher"). See the package docstring.
    granted_persona_roles: tuple[str, ...] = ()
    seen_digests: frozenset[str] = frozenset()
    seen_semantic_digests: frozenset[str] = frozenset()
    prompt: str | None = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DetectionContext)
        return (
            self.host_replay_receipt == other.host_replay_receipt
            and self.semantic_replay_passed is other.semantic_replay_passed
            and self.unexplored_branches == other.unexplored_branches
            and self.granted_persona_roles == other.granted_persona_roles
            and self.seen_digests == other.seen_digests
            and self.seen_semantic_digests == other.seen_semantic_digests
            and self.prompt == other.prompt
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.host_replay_receipt,
            self.semantic_replay_passed,
            self.unexplored_branches,
            self.granted_persona_roles,
            self.seen_digests,
            self.seen_semantic_digests,
            self.prompt,
        ))


@dataclass(frozen=True, slots=True)
class DetectorReport:
    """Immutable report emitted by detector sweeps."""

    normalized_json_digest: str
    raw_bytes_digest: str | None
    subject_digest: str
    semantic_payload_digest: str
    detectors_run: tuple[str, ...]
    findings: tuple[Finding, ...]

    def is_clean(self) -> bool:
        return len(self.findings) == 0

    def highest_severity(self) -> PharmacyDisposition | None:
        if not self.findings:
            return None
        return max(f.disposition for f in self.findings)

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

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.normalized_json_digest,
            self.raw_bytes_digest,
            self.subject_digest,
            self.semantic_payload_digest,
            self.detectors_run,
            self.findings,
        ))


HOST_ONLY_KEYS = frozenset({
    "receipt",
    "receipt_sha256",
    "sealed_sha256",
    "host_signature",
    "authority_effect_hash",
})

SELF_CERTIFYING_VALUES = frozenset({
    "verified",
    "admitted",
    "authorized",
    "certified",
    "proven",
    "guaranteed",
    "flawless",
    "fully verified",
})

SUPERLATIVES = frozenset({
    "optimal",
    "maximally",
    "minimally",
    "strictly superior",
    "strictly dominating",
    "uniquely best",
})

COMPLEXITY_MARKERS = frozenset({
    "in o(n)",
    "in o(1)",
    "in o(n log n)",
    "in o(n^2)",
    "linear time",
    "constant time",
    "polynomial time",
    "np-complete",
})

PRIVATE_COT_MARKERS = frozenset({
    "<think>",
    "</think>",
    "<scratchpad>",
    "</scratchpad>",
    "<private_reasoning>",
    "</private_reasoning>",
})

UNAUTHORIZED_PERSONA_MARKERS = frozenset({
    "unrestricted authority",
    "sovereign arbiter",
    "absolute certifier",
    "master authority",
    "final arbiter",
})


def _looks_like_digest(val: str) -> bool:
    if val.startswith("sha256:") and len(val) == 71:
        return bool(re.fullmatch(r"sha256:[0-9a-fA-F]{64}", val))
    return False


def _walk_strings(obj: Any, path: str, result: list[tuple[str, str]]) -> None:
    if isinstance(obj, str):
        result.append((path or "/", obj))
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            child = f"{path}/{k}" if path else f"/{k}"
            _walk_strings(v, child, result)
    elif isinstance(obj, Sequence) and not isinstance(obj, (bytes, bytearray)):
        for idx, item in enumerate(obj):
            child = f"{path}[{idx}]"
            _walk_strings(item, child, result)


def _walk_keys(obj: Any, path: str, result: list[tuple[str, str, Any]]) -> None:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            current_path = f"{path}/{k}" if path else f"/{k}"
            result.append((current_path, str(k), v))
            _walk_keys(v, current_path, result)
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        for idx, item in enumerate(obj):
            _walk_keys(item, f"{path}[{idx}]", result)


def detect(
    candidate: Any,
    context: DetectionContext | None = None,
    raw_bytes: bytes | None = None,
) -> DetectorReport:
    """Run the 12-class mechanical pharmacy detector suite over a candidate payload."""
    if context is None:
        context = DetectionContext()

    normalized_bytes = json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    normalized_json_digest = f"sha256:{hashlib.sha256(normalized_bytes).hexdigest()}"
    raw_bytes_digest = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}" if raw_bytes is not None else None
    subject_digest = normalized_json_digest

    semantic_payload = candidate
    if isinstance(candidate, dict) and "candidate" in candidate:
        semantic_payload = candidate["candidate"]
    sem_bytes = json.dumps(semantic_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    semantic_digest = f"sha256:{hashlib.sha256(sem_bytes).hexdigest()}"

    strings: list[tuple[str, str]] = []
    _walk_strings(candidate, "", strings)
    keys: list[tuple[str, str, Any]] = []
    _walk_keys(candidate, "", keys)

    findings: list[Finding] = []

    # 1 & 2. Host-only keys and Fake Receipt checks
    for path, key, value in keys:
        if key in HOST_ONLY_KEYS:
            findings.append(Finding(
                failure_class=FailureClass.SelfCertification,
                disposition=FailureClass.SelfCertification.default_disposition(),
                locus=path,
                detail=f"candidate declares host-only field {key!r}",
            ))
            if isinstance(value, str) and _looks_like_digest(value):
                findings.append(Finding(
                    failure_class=FailureClass.FakeReceipt,
                    disposition=FailureClass.FakeReceipt.default_disposition(),
                    locus=path,
                    detail="candidate supplies a digest-shaped value for a host-computed field",
                ))

    # Text-based checks
    for path, text in strings:
        lower = text.lower()

        # Self-certification values
        if any(lower == word for word in SELF_CERTIFYING_VALUES):
            findings.append(Finding(
                failure_class=FailureClass.SelfCertification,
                disposition=FailureClass.SelfCertification.default_disposition(),
                locus=path,
                detail=f"candidate asserts {text!r}",
            ))

        # Optimality Hallucination
        if any(word in lower for word in SUPERLATIVES):
            findings.append(Finding(
                failure_class=FailureClass.OptimalityHallucination,
                disposition=FailureClass.OptimalityHallucination.default_disposition(),
                locus=path,
                detail="superlative claim without a candidate class, objective, and lower bound",
            ))

        # Complexity Hallucination
        if any(word in lower for word in COMPLEXITY_MARKERS):
            findings.append(Finding(
                failure_class=FailureClass.ComplexityHallucination,
                disposition=FailureClass.ComplexityHallucination.default_disposition(),
                locus=path,
                detail="complexity claim without an algorithm, cost model, or measurement",
            ))

        # Private CoT Dependency
        if any(word in lower for word in PRIVATE_COT_MARKERS):
            findings.append(Finding(
                failure_class=FailureClass.PrivateCotDependency,
                disposition=FailureClass.PrivateCotDependency.default_disposition(),
                locus=path,
                detail="conclusion leans on reasoning the public trace cannot show",
            ))

        # Theorem Name Laundering
        if "by " in lower and "theorem" in lower and "assum" not in lower:
            findings.append(Finding(
                failure_class=FailureClass.TheoremNameLaundering,
                disposition=FailureClass.TheoremNameLaundering.default_disposition(),
                locus=path,
                detail="theorem invoked by name with no applicability obligations stated",
            ))

        # Branch Drop Exhaustion
        if ("exhaustive" in lower or "exhausted" in lower) and context.unexplored_branches > 0:
            findings.append(Finding(
                failure_class=FailureClass.BranchDropExhaustion,
                disposition=FailureClass.BranchDropExhaustion.default_disposition(),
                locus=path,
                detail=f"exhaustion claimed while {context.unexplored_branches} branches remain unexplored",
            ))

        # Persona Authority Leak
        if any(marker in lower for marker in UNAUTHORIZED_PERSONA_MARKERS):
            if not any(role in lower for role in context.granted_persona_roles):
                findings.append(Finding(
                    failure_class=FailureClass.PersonaAuthorityLeak,
                    disposition=FailureClass.PersonaAuthorityLeak.default_disposition(),
                    locus=path,
                    detail="persona asserting authority beyond its declared grant",
                ))

    # Detect/Repair Coupling
    has_findings = bool(candidate.get("objections")) if isinstance(candidate, dict) else False
    has_repair = bool(candidate.get("proposed_claim_deltas")) if isinstance(candidate, dict) else False
    if has_findings and has_repair:
        findings.append(Finding(
            failure_class=FailureClass.DetectRepairCoupling,
            disposition=FailureClass.DetectRepairCoupling.default_disposition(),
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
            failure_class=FailureClass.SchemaSemanticLaundering,
            disposition=FailureClass.SchemaSemanticLaundering.default_disposition(),
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
            failure_class=FailureClass.VersionDuplication,
            disposition=FailureClass.VersionDuplication.default_disposition(),
            locus="",
            detail="payload is semantically or byte-identical to one already recorded under another label",
        ))

    # Conclusion Preload in prompt
    if context.prompt is not None:
        lower_prompt = context.prompt.lower()
        for word in SELF_CERTIFYING_VALUES:
            if f"must be {word}" in lower_prompt or f"conclude that it is {word}" in lower_prompt:
                findings.append(Finding(
                    failure_class=FailureClass.ConclusionPreload,
                    disposition=FailureClass.ConclusionPreload.default_disposition(),
                    locus="/prompt",
                    detail=f"prompt fixes the required conclusion {word!r}",
                ))

    # Deduplicate and sort findings deterministically
    unique_findings = sorted(
        list({(f.failure_class.code(), f.disposition.value, f.locus, f.detail): f for f in findings}.values()),
        key=lambda f: (f.failure_class.code(), f.locus, f.detail),
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
