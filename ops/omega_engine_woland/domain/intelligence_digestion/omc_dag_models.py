"""Domain models for Operad Morphism Calculus (OMC) DAG audit and review records.

Governing Councils: Logos Thanatos / Council Nomos / Panepistimion
AuthorityEffect: None (Audit, Falsification & Obstruction Detection Only)
"""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

OMC_DAG_SCHEMA_VERSION = "omega.intelligence.omc-dag.v1"


class OMCRecordType(str, Enum):
    MONOGRAPH_AUDIT = "monograph_audit"
    PR_REVIEW = "pr_review"
    SUBSYSTEM_AUDIT = "subsystem_audit"


class OMCVerdict(str, Enum):
    GO = "GO"
    GO_WITH_OBLIGATIONS = "GO_WITH_OBLIGATIONS"
    NO_GO = "NO_GO"
    PASS = "PASS"
    PREFLIGHT_PASS = "PREFLIGHT_PASS"
    FAIL = "FAIL"
    REJECT = "REJECT"
    UNKNOWN = "UNKNOWN"


class DualWitnessStatus(str, Enum):
    EXACT_VERIFIED = "EXACT_VERIFIED"
    PRIMAL_ONLY = "PRIMAL_ONLY"
    MISSING = "MISSING"
    N_A = "N_A"
    UNKNOWN = "UNKNOWN"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class NaturalScienceGates(BaseModel):
    """Natural science adversarial gates evaluated during OMC monograph audits."""

    model_config = ConfigDict(extra="allow", frozen=True)

    dimensional_hygiene: str = "PASS"
    limit_honesty: str = "PASS"
    gauge_invariance: str = "PASS"
    synthetic_curves_free: str = "PASS"
    formal_mechanization: str = "PASS"

    def has_failures(self) -> bool:
        return any(
            str(v).upper() not in ("PASS", "NOT_APPLICABLE", "N_A")
            for v in [
                self.dimensional_hygiene,
                self.limit_honesty,
                self.gauge_invariance,
                self.synthetic_curves_free,
                self.formal_mechanization,
            ]
        )


class CodeCompliance(BaseModel):
    """Code and terminology hygiene gates."""

    model_config = ConfigDict(extra="allow", frozen=True)

    narrative_prose_free: bool = True
    jargon_free: bool = True
    blackboard_definitions_valid: bool = True

    def has_failures(self) -> bool:
        return not (
            self.narrative_prose_free
            and self.jargon_free
            and self.blackboard_definitions_valid
        )


class OMCMonographAuditRecord(BaseModel):
    """Monograph / research paper adversarial audit record emitted by OldManRedTeam."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    record_type: Literal[OMCRecordType.MONOGRAPH_AUDIT] = OMCRecordType.MONOGRAPH_AUDIT
    schema_version: str = OMC_DAG_SCHEMA_VERSION
    authority_effect: Literal["None"] = "None"
    audit_id: str = Field(description="Unique audit identifier, e.g. omc_report_001_...")
    target: str = Field(description="Relative path to audited monograph markdown")
    target_hash: str = Field(description="SHA-256 of target monograph content")
    target_residual_colour: str = Field(default="R-OMC-01", description="Operad residual color")
    verdict: str = Field(description="High-level audit verdict (e.g. GO, GO_WITH_OBLIGATIONS, NO_GO)")
    audited_files: List[str] = Field(default_factory=list, description="All files examined during audit")
    decisive_blockers: List[str] = Field(default_factory=list, description="Unresolved obstruction blockers")
    prior_reports: List[str] = Field(default_factory=list, description="Referenced predecessor reports")
    dual_witness_status: str = Field(default="N_A", description="Status of dual witness pair verification")
    natural_science_gates: NaturalScienceGates = Field(default_factory=NaturalScienceGates)
    code_compliance: CodeCompliance = Field(default_factory=CodeCompliance)
    what_survived: List[str] = Field(default_factory=list, description="Invariants that survived falsification")
    timestamp_utc: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp")
    charitable_steelman: Optional[str] = Field(default="", description="Steelman summary of strongest reading")

    @field_validator("authority_effect")
    @classmethod
    def validate_authority(cls, v: str) -> str:
        if v not in ("None", None):
            raise ValueError(f"authority_effect must be 'None', got '{v}'")
        return "None"

    @field_validator("target_hash")
    @classmethod
    def validate_target_hash(cls, value: str) -> str:
        if re.fullmatch(r"[0-9a-f]{64}", value) is None or value == "0" * 64:
            raise ValueError("a non-placeholder SHA-256 target digest is required")
        return value

    def has_obstructions(self) -> bool:
        """Returns True if decisive blockers or failing natural science gates persist."""
        if bool(self.decisive_blockers):
            return True
        v = self.verdict.upper()
        if v not in ("GO", "PASS", "PREFLIGHT_PASS", "GO_WITH_OBLIGATIONS"):
            return True
        return self.natural_science_gates.has_failures() or self.code_compliance.has_failures()

    def get_obstructions(self) -> List[str]:
        """Collects all active obstruction strings."""
        obstructions: List[str] = list(self.decisive_blockers)
        if self.natural_science_gates.dimensional_hygiene.upper() == "FAIL":
            obstructions.append("DIMENSIONAL_HYGIENE_VIOLATION: Carrier dimensionality mismatch")
        if self.natural_science_gates.limit_honesty.upper() == "FAIL":
            obstructions.append("LIMIT_HONESTY_VIOLATION: Unhedged thermodynamic or continuum limit claim")
        if self.natural_science_gates.gauge_invariance.upper() == "FAIL":
            obstructions.append("GAUGE_INVARIANCE_VIOLATION: Holonomy defect detected")
        if self.natural_science_gates.synthetic_curves_free.upper() == "FAIL":
            obstructions.append("SYNTHETIC_CURVE_VIOLATION: Figure generation contains artificial curves")
        if self.natural_science_gates.formal_mechanization.upper() == "FAIL":
            obstructions.append("FORMAL_MECHANIZATION_VIOLATION: Lean proof terms use sorry or unproven axioms")
        if not obstructions and self.has_obstructions():
            obstructions.append(f"UNRESOLVED_MONOGRAPH_AUDIT:{self.verdict}")
        return obstructions

    def is_cleared(self) -> bool:
        """Returns True if all obstructions have been removed / verified clean."""
        return not self.has_obstructions()


class OMCPRReviewRecord(BaseModel):
    """PR review preflight and compliance audit record."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    record_type: Literal[OMCRecordType.PR_REVIEW] = OMCRecordType.PR_REVIEW
    schema_version: str = OMC_DAG_SCHEMA_VERSION
    authority_effect: Optional[str] = "None"
    pr_number: int = Field(description="Pull Request number")
    verdict: str = Field(description="Review verdict, e.g. PREFLIGHT_PASS")
    base_sha: Optional[str] = Field(default=None, description="Base commit SHA")
    head_sha: Optional[str] = Field(default=None, description="Head commit SHA")
    branch: Optional[str] = Field(default=None, description="Branch name")
    pr_title: Optional[str] = Field(default=None, description="PR Title")
    comment_url: Optional[str] = Field(default=None, description="GitHub comment URL")
    audit_runner: Optional[str] = Field(default=None, description="Review runner script")
    creates_execution_authority: Optional[bool] = Field(default=False)
    timestamp: Optional[str] = Field(default=None, description="Review timestamp")
    checks: Optional[Dict[str, Any]] = Field(default=None, description="Named verification checks")

    @field_validator("authority_effect")
    @classmethod
    def validate_authority(cls, v: Optional[str]) -> Optional[str]:
        if v not in ("None", None):
            raise ValueError(f"authority_effect must be 'None' or null, got '{v}'")
        return "None"

    def has_obstructions(self) -> bool:
        if self.verdict.upper() not in ("PREFLIGHT_PASS", "PASS", "GO"):
            return True
        if self.checks:
            for check_val in self.checks.values():
                if isinstance(check_val, dict) and str(check_val.get("status")).upper() not in ("PASS", "NOT_APPLICABLE", "N_A"):
                    return True
                elif not isinstance(check_val, dict) and str(check_val).upper() not in ("PASS", "NOT_APPLICABLE", "N_A"):
                    return True
        return False

    def get_obstructions(self) -> List[str]:
        obstructions = []
        if self.checks:
            for k, check_val in self.checks.items():
                if isinstance(check_val, dict) and check_val.get("status") in ("FAIL", "BLOCKED"):
                    obstructions.append(f"PR_CHECK_FAILED:{k}")
                elif check_val in ("FAIL", "BLOCKED"):
                    obstructions.append(f"PR_CHECK_FAILED:{k}")
        if not obstructions and self.has_obstructions():
            obstructions.append(f"PR_VERDICT_BLOCKED:{self.verdict}")
        return obstructions

    def is_cleared(self) -> bool:
        return not self.has_obstructions()


class OMCSubsystemAuditRecord(BaseModel):
    """Subsystem integration and Soviet inspector audit record."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    record_type: Literal[OMCRecordType.SUBSYSTEM_AUDIT] = OMCRecordType.SUBSYSTEM_AUDIT
    schema_version: str = OMC_DAG_SCHEMA_VERSION
    authority_effect: Literal["None"] = "None"
    module: str = Field(description="Parent module, e.g. omega_general_relativity")
    subsystem: str = Field(description="Subsystem name, e.g. regge_4d_and_dec_laplacian")
    verdict: str = Field(description="Audit verdict, e.g. PASS")
    reviewing_authorities: List[str] = Field(default_factory=list)
    checks: Dict[str, Any] = Field(default_factory=dict)
    integration_tests_passed: Optional[int] = Field(default=None)
    library_tests_passed: Optional[int] = Field(default=None)
    total_tests_passed: Optional[int] = Field(default=None)
    audit_finding: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("authority_effect")
    @classmethod
    def validate_authority(cls, v: str) -> str:
        if v not in ("None", None):
            raise ValueError(f"authority_effect must be 'None', got '{v}'")
        return "None"

    def has_obstructions(self) -> bool:
        if self.verdict.upper() not in ("PASS", "GO"):
            return True
        if any(str(v.get("status") if isinstance(v, dict) else v).upper() not in ("PASS", "NOT_APPLICABLE", "N_A") for v in self.checks.values()):
            return True
        if self.audit_finding and self.audit_finding.get("blocking"):
            return True
        return False

    def get_obstructions(self) -> List[str]:
        obstructions = []
        for k, v in self.checks.items():
            if str(v).upper() in ("FAIL", "BLOCKED"):
                obstructions.append(f"SUBSYSTEM_CHECK_FAILED:{self.subsystem}:{k}")
        if self.audit_finding and self.audit_finding.get("blocking"):
            obstructions.append(f"BLOCKING_AUDIT_FINDING:{self.subsystem}:{self.audit_finding.get('severity', 'P1')}")
        if not obstructions and self.has_obstructions():
            obstructions.append(f"UNRESOLVED_SUBSYSTEM_AUDIT:{self.subsystem}:{self.verdict}")
        return obstructions

    def is_cleared(self) -> bool:
        return not self.has_obstructions()


OMCRecord = Union[OMCMonographAuditRecord, OMCPRReviewRecord, OMCSubsystemAuditRecord]


def parse_omc_dict(data: Dict[str, Any]) -> OMCRecord:
    """Dispatches a raw dictionary into the matching validated OMC record type."""
    if "audit_id" in data or "audited_files" in data:
        payload = dict(data)
        payload.setdefault("record_type", OMCRecordType.MONOGRAPH_AUDIT.value)
        return OMCMonographAuditRecord.model_validate(payload)
    elif "pr_number" in data:
        payload = dict(data)
        payload.setdefault("record_type", OMCRecordType.PR_REVIEW.value)
        return OMCPRReviewRecord.model_validate(payload)
    elif "subsystem" in data or "module" in data:
        payload = dict(data)
        payload.setdefault("record_type", OMCRecordType.SUBSYSTEM_AUDIT.value)
        return OMCSubsystemAuditRecord.model_validate(payload)
    else:
        raise ValueError(f"Unable to resolve OMC record type for keys: {list(data.keys())}")


def parse_omc_line(line: str) -> OMCRecord:
    """Parses a single JSON line into a validated OMC record."""
    clean = line.strip()
    if not clean:
        raise ValueError("Cannot parse empty line")
    data = json.loads(clean)
    return parse_omc_dict(data)


def parse_omc_markdown(content: str, filename_stem: str = "omc_report") -> OMCMonographAuditRecord:
    """Parses an OMC companion markdown audit report into an OMCMonographAuditRecord."""
    audit_date = ""
    target = ""
    target_hash = ""
    verdict = "UNKNOWN"
    blockers: List[str] = []
    survived: List[str] = []

    m_date = re.search(r"\*\*Audit Date:\*\*\s*([^\n]+)", content)
    if m_date:
        audit_date = m_date.group(1).strip()

    m_target = re.search(r"\*\*Target:\*\*\s*`([^`]+)`\s*\(SHA-256:\s*`([^`]+)`\)", content)
    if m_target:
        target = m_target.group(1).strip()
        target_hash = m_target.group(2).strip()

    m_verdict = re.search(r"\*\*Verdict:\*\*\s*`?([A-Z_]+)`?", content)
    if m_verdict:
        verdict = m_verdict.group(1).strip()

    m_blockers = re.search(r"\*\*Unresolved Obligations / Blockers:\*\*\s*([^\n]+)", content)
    if m_blockers:
        raw_b = m_blockers.group(1).strip()
        if raw_b and raw_b.lower() != "none":
            blockers = [b.strip() for b in raw_b.split(";") if b.strip()]

    m_survived = re.search(r"\*\*Surviving Invariants:\*\*\s*([^\n]+)", content)
    if m_survived:
        raw_s = m_survived.group(1).strip()
        if raw_s and raw_s.lower() != "none":
            survived = [s.strip() for s in raw_s.split(";") if s.strip()]

    return OMCMonographAuditRecord(
        audit_id=filename_stem,
        target=target or filename_stem,
        target_hash=target_hash,
        verdict=verdict,
        decisive_blockers=blockers,
        what_survived=survived,
        timestamp_utc=audit_date or None,
        authority_effect="None",
    )
