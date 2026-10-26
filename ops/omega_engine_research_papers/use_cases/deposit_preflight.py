"""Autonomous Preflight Gate Engine for Research Paper Deposits.

AuthorityEffect: None.

Evaluates research paper deposit envelopes against the four preflight invariants:
1. UNVERIFIED_RELEASE_SCRIPT: Standalone release rebuild and verification script presence.
2. TEX_PDF_HASH_DESYNCHRONIZATION: LaTeX source and pre-compiled PDF rendering alignment.
3. EXACTNESS_WITHOUT_DUAL_WITNESS_CERTIFICATE: Discrete dual-witness certificates for exactness.
4. DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION: Windows MAX_PATH limits (< 250 chars) and directory fences.
"""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..domain.rules import (
    DualWitnessCertificateRule,
    PaperContext,
    PdfExistsAndRenderableRule,
    RestrictedDirectoryStructureRule,
    RuleSeverity,
    StandaloneReleaseVerifierRule,
    WindowsMaxPathRule,
)
from ..infrastructure.rules.filesystem_package_reader import FilesystemPackageReader

FORBIDDEN_DIRS = {"dist", "__pycache__", ".pytest_cache", ".tox", ".mypy_cache", "rt", "evidence"}
MAX_PATH_LIMIT = 250

REQUIRED_CANDIDATE_CODES = {
    "UNVERIFIED_RELEASE_SCRIPT",
    "TEX_PDF_HASH_DESYNCHRONIZATION",
    "EXACTNESS_WITHOUT_DUAL_WITNESS_CERTIFICATE",
    "DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION",
}


@dataclass(frozen=True)
class DepositPreflightReceipt:
    """Local filesystem preflight receipt; no content or proof verification implied."""

    status: str  # "PASS" or "BLOCKED"
    paper_path: str
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]
    metrics: Dict[str, Any]
    timestamp_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    authority_effect: str = "None"
    nonclaims: Tuple[str, ...] = (
        "AuthorityEffect: None",
        "Preflight receipt certifies local filesystem envelope invariants only.",
        "Does not constitute external publication authorization without human author review.",
    )

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "paper_path": self.paper_path,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metrics": self.metrics,
            "timestamp_utc": self.timestamp_utc,
            "authority_effect": self.authority_effect,
            "nonclaims": list(self.nonclaims),
        }

    def to_markdown(self) -> str:
        lines: List[str] = [
            f"# Research Paper Deposit Preflight Receipt: {Path(self.paper_path).name}",
            "",
            f"**AuthorityEffect:** {self.authority_effect}  ",
            f"**Timestamp (UTC):** {self.timestamp_utc}  ",
            f"**Status:** **{self.status}**  ",
            f"**Errors ({len(self.errors)}):**",
        ]
        if self.errors:
            for err in self.errors:
                lines.append(f"- {err}")
        else:
            lines.append("- None")

        lines.extend([
            "",
            f"**Warnings ({len(self.warnings)}):**",
        ])
        if self.warnings:
            for w in self.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- None")

        lines.extend([
            "",
            "## Metrics",
            "",
        ])
        for k, v in self.metrics.items():
            lines.append(f"- **{k}:** {v}")

        return "\n".join(lines)


def check_self_consistency(repo_root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Self-check asserting anti-skill registration and anti-pattern catalog alignment."""
    findings: List[str] = []
    if repo_root is None:
        candidate = Path(__file__).resolve()
        while candidate.parent != candidate:
            if (candidate / ".git").exists():
                repo_root = candidate
                break
            candidate = candidate.parent
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[2]

    candidates_file = repo_root / "omega_engine_epistemic_immune_system" / "antiskills" / "ooutwire" / "evidence_mined_candidates.json"
    if not candidates_file.is_file():
        candidates_file = repo_root / ".agents" / "anti_skills" / "ooutwire" / "evidence_mined_candidates.json"
    if candidates_file.is_file():
        try:
            data = json.loads(candidates_file.read_text(encoding="utf-8"))
            codes = {c.get("failure_code") for c in data.get("candidates", [])}
            missing = REQUIRED_CANDIDATE_CODES - codes
            if missing:
                findings.append(f"Missing required failure codes in candidate registry: {sorted(missing)}")
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            findings.append(f"Failed to parse candidates registry: {exc}")
    else:
        findings.append("Missing candidates registry")

    catalog_file = (
        repo_root
        / ".agents"
        / "skills"
        / "governance-research-paper-edit-publish"
        / "references"
        / "research_paper_anti_skills.md"
    )
    if not catalog_file.is_file():
        catalog_file = (
            repo_root
            / ".agents"
            / "skills"
            / "omega-paper-review-swarm"
            / "references"
            / "research_paper_anti_skills.md"
        )
    if catalog_file.is_file():
        text = catalog_file.read_text(encoding="utf-8")
        if "ANTI-UNVERIFIED-RELEASE-SCRIPT" not in text:
            findings.append("Missing ANTI-UNVERIFIED-RELEASE-SCRIPT in catalog")
        if "ANTI-TEX-PDF-DESYNC" not in text:
            findings.append("Missing ANTI-TEX-PDF-DESYNC in catalog")
        if "ANTI-MISSING-DUAL-WITNESS" not in text:
            findings.append("Missing ANTI-MISSING-DUAL-WITNESS in catalog")
    else:
        findings.append("Missing research paper anti-pattern catalog")

    return len(findings) == 0, findings


def check_paper_deposit_preflight(paper_path: Path) -> DepositPreflightReceipt:
    """Execute preflight gate evaluation over an active paper package directory."""
    paper_dir = paper_path.resolve()
    if not paper_dir.is_dir():
        return DepositPreflightReceipt(
            status="BLOCKED",
            paper_path=str(paper_dir),
            errors=(f"Paper path is not a directory: {paper_dir}",),
            warnings=(),
            metrics={"exists": False},
        )

    errors: List[str] = []
    warnings: List[str] = []
    ctx = PaperContext.from_dir(paper_dir, FilesystemPackageReader())

    # Invariant 1: UNVERIFIED_RELEASE_SCRIPT
    rule_verifier = StandaloneReleaseVerifierRule()
    res_verifier = rule_verifier.evaluate(ctx)
    if not res_verifier.passed:
        for f in res_verifier.findings:
            errors.append(f.message)

    # Invariant 2: TEX_PDF_HASH_DESYNCHRONIZATION
    rule_pdf = PdfExistsAndRenderableRule()
    res_pdf = rule_pdf.evaluate(ctx)
    if not res_pdf.passed:
        for f in res_pdf.findings:
            errors.append(f.message)

    # Invariant 3: EXACTNESS_WITHOUT_DUAL_WITNESS_CERTIFICATE
    rule_witness = DualWitnessCertificateRule()
    res_witness = rule_witness.evaluate(ctx)
    if not res_witness.passed:
        for f in res_witness.findings:
            if f.severity == RuleSeverity.BLOCKER:
                errors.append(f.message)
            else:
                warnings.append(f.message)

    # Invariant 4: DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION
    rule_path = WindowsMaxPathRule()
    res_path = rule_path.evaluate(ctx)
    if not res_path.passed:
        for f in res_path.findings:
            errors.append(f.message)

    rule_dir = RestrictedDirectoryStructureRule()
    res_dir = rule_dir.evaluate(ctx)
    if not res_dir.passed:
        for f in res_dir.findings:
            errors.append(f.message)

    # Metrics
    max_path_seen = 0
    longest_path = ""
    for root, dirs, files in os.walk(paper_dir):
        rel_root = Path(root).relative_to(paper_dir)
        for f in files:
            rel_len = len(str(rel_root / f))
            if rel_len > max_path_seen:
                max_path_seen = rel_len
                longest_path = str(rel_root / f)

    pdf_files = list(paper_dir.glob("*.pdf")) + list(paper_dir.glob("docs/*.pdf"))
    status = "PASS" if not errors else "BLOCKED"

    return DepositPreflightReceipt(
        status=status,
        paper_path=str(paper_dir),
        errors=tuple(errors),
        warnings=tuple(warnings),
        metrics={
            "has_verifier": res_verifier.passed,
            "pdf_count": len(pdf_files),
            "exactness_claimed": res_witness.details.get("exactness_claimed", False),
            "max_relative_path_length": max_path_seen,
            "longest_relative_path": longest_path,
        },
    )
