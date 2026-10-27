"""Domain models for typed paper review digest records and obstruction harvesting.

Defines the typed structure for individual lines in the canonical paper review
digest JSON-L stream, separating accomplishments from failure obstructions with
typed sub-taxonomies.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class RecordType(str, Enum):
    """Categorical taxonomy of the review source."""
    SWARM_REVIEW = "swarm_review"
    GATE_EXECUTION = "gate_execution"
    BOUT_DELIBERATION = "bout_deliberation"
    MONOGRAPH_AUDIT = "monograph_audit"
    FUTURE_CERTIFICATE = "future_certificate"


class ReviewStatus(str, Enum):
    """Normalized terminal or evaluation status of the review."""
    PASS = "PASS"
    NEEDS_REVISION = "NEEDS_REVISION"
    BLOCKED = "BLOCKED"
    FAIL = "FAIL"
    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    DIALETHEIC_TENSION = "DIALETHEIC_TENSION"
    UNKNOWN = "UNKNOWN"


class AccomplishmentKind(str, Enum):
    """Subtype of successful verification or milestone accomplishment."""
    STAGE_PASSED = "stage_passed"
    TESTS_PASSED = "tests_passed"
    THEOREMS_VERIFIED = "theorems_verified"
    COVERAGE_ACHIEVED = "coverage_achieved"
    ARTIFACT_PRODUCED = "artifact_produced"
    GATE_CLEARED = "gate_cleared"
    REPUBLICATION_CLEARED = "republication_cleared"


class ObstructionKind(str, Enum):
    """Subtype of defect, blocked gate, or unfulfilled proof obligation."""
    BLOCKED_STAGE = "blocked_stage"
    FAILED_STAGE = "failed_stage"
    BLOCKED_GATE = "blocked_gate"
    RESTRICTED_WORD = "restricted_word"
    MISSING_SECTION = "missing_section"
    CITATION_DEFECT = "citation_defect"
    PACKAGING_DEFECT = "packaging_defect"
    SYNTAX_DEFECT = "syntax_defect"
    LINEAGE_CONFLICT = "lineage_conflict"
    UNVERIFIED_CLAIM = "unverified_claim"
    GENERAL_OBSTRUCTION = "general_obstruction"


class Severity(str, Enum):
    """Triaged defect severity."""
    P0 = "P0"  # Blocker / critical soundness failure
    P1 = "P1"  # Major failure / blocked release gate
    P2 = "P2"  # Minor / style / missing optional metadata
    P3 = "P3"  # Informational / advisory warning


class AccomplishmentItem(BaseModel):
    """A single verified success or passed milestone within a review."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str = Field(description="Deterministic item identifier.")
    kind: AccomplishmentKind = Field(description="Subtype of accomplishment.")
    scope: str = Field(description="Scope, stage, or component that passed.")
    details: str = Field(description="Specific metrics, assertion details, or descriptions.")
    evidence_ref: Optional[str] = Field(default=None, description="Cryptographic SHA-256 or file receipt reference.")


class FailureObstructionItem(BaseModel):
    """A single defect, blocked gate, or failure obstruction discovered during review."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str = Field(description="Deterministic defect identifier.")
    kind: ObstructionKind = Field(description="Subtype of failure obstruction.")
    gate_code: Optional[str] = Field(default=None, description="Standard gate code (e.g. B01, C04, E02, G5b).")
    stage_or_phase: str = Field(description="Stage, phase, or module where the failure was detected.")
    severity: Severity = Field(default=Severity.P1, description="Severity triage level.")
    description: str = Field(description="Detailed human-readable explanation of the defect.")
    negative_fixture: Optional[str] = Field(default=None, description="Failing witness, snippet, or citation.")
    remediation_route: Optional[str] = Field(default=None, description="Command or instructions to repair the defect.")
    mined_as_antibody: Optional[str] = Field(default=None, description="Farmed antibody identifier in OEEIS if mined.")


class ReviewSummary(BaseModel):
    """Numerical roll-up of review outcomes."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    stages_run: int = Field(default=0, ge=0)
    stages_passed: int = Field(default=0, ge=0)
    stages_blocked: int = Field(default=0, ge=0)
    total_errors: int = Field(default=0, ge=0)
    total_warnings: int = Field(default=0, ge=0)
    verdict: str = Field(default="", description="High-level narrative verdict or recommendation.")


class PaperReviewDigestRecord(BaseModel):
    """Canonical typed record representing a single line in paper_reviews_digest.jsonl."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(description="Unique record identifier, prefixed with 'rev_rec_'.")
    schema_version: Literal["core.intelligence.paper-review-digest.v1"] = Field(
        default="core.intelligence.paper-review-digest.v1",
        description="Schema version marker.",
    )
    authority_effect: Literal["None"] = Field(
        default="None",
        description="Constitutional governance marker; must strictly be 'None'.",
    )
    review_source: str = Field(description="Relative path of the source directory or file.")
    paper_id: str = Field(description="Identifier or slug of the monograph under review.")
    record_type: RecordType = Field(description="Review modality subtype.")
    status: ReviewStatus = Field(description="Terminal evaluation status.")
    timestamp_utc: str = Field(description="ISO-8601 UTC timestamp of review execution.")
    accomplished: List[AccomplishmentItem] = Field(
        default_factory=list,
        description="List of all verified milestones and passing gates.",
    )
    failures: List[FailureObstructionItem] = Field(
        default_factory=list,
        description="List of all failure modes and blocked obstructions.",
    )
    summary: ReviewSummary = Field(
        default_factory=ReviewSummary,
        description="Summary metrics of the review run.",
    )
    artifacts_examined: List[str] = Field(
        default_factory=list,
        description="Key artifact file paths or manifests audited.",
    )

    def to_json_line(self) -> str:
        """Serializes the record to a single-line compact JSON string."""
        return json.dumps(self.model_dump(mode="json"), separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "PaperReviewDigestRecord":
        """Deserializes a single JSON-L line into a validated PaperReviewDigestRecord."""
        raw = json.loads(line.strip())
        return cls.model_validate(raw)
