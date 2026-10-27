"""Council Nomos Contract Compliance Scanner & Blackrod Defect Investigation Service.

Decomposes the historical rip-lawyers pipeline into native Council Nomos (L3_logos_nomos)
contract compliance scanning, URN enforcement, and automated Blackrod defect investigation
logging under RULE_DEFECT_INVESTIGATION_LOGGING_001.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml

from governance.domain.intelligence_community import canonical_intelligence_route
from operations.domain.rop.result import Err, Ok, Refusal, Result

_LOCUS = "adversary.use_cases.nomos_compliance_use_case"
URN_PATTERN = re.compile(r"^urn:core:[a-z0-9_]+:[a-z0-9_]+:v[0-9]+(\.[0-9]+)*$")


@dataclass(frozen=True)
class ContractInspectionFindingV1:
    file_path: str
    urn: str | None
    schema: str | None
    is_valid: bool
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class NomosComplianceReceiptV1:
    schema_version: str = "core.nomos.compliance-receipt.v1"
    target_path: str = ""
    contracts_inspected: int = 0
    valid_contracts: int = 0
    coverage_percentage: float = 0.0
    direct_urn_bindings: int = 0
    contract_violations: int = 0
    investigation_reports_logged: tuple[str, ...] = ()
    findings: tuple[ContractInspectionFindingV1, ...] = ()
    authority_effect: str = "None"
    timestamp: str = ""


class BlackrodDefectLogger:
    """Writes formal defect investigation reports adhering to RULE_DEFECT_INVESTIGATION_LOGGING_001."""

    @staticmethod
    def log_investigation(
        defect_id: str,
        skill_name: str,
        summary: str,
        trace_context: str,
        affected_files: Sequence[str | Path],
        root_cause: str,
        remediation_plan: str,
        *,
        repo_root: Path | str | None = None,
    ) -> Path:
        root = Path(repo_root) if repo_root is not None else Path.cwd()
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        report_filename = f"investigation_{date_str}_{skill_name}_{defect_id}.md"

        target_dir = root / canonical_intelligence_route("_intelligence/blackrod/investigations")
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / report_filename

        content_lines = [
            f"# Defect Investigation Report: {summary}",
            "",
            f"**Report ID:** `{report_filename.replace('.md', '')}`",
            f"**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}",
            f"**Skill:** `{skill_name}`",
            "**Governing Rule:** `RULE_DEFECT_INVESTIGATION_LOGGING_001`",
            "**AuthorityEffect:** None.",
            "AuthorityEffect: None.",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            summary,
            "",
            "---",
            "",
            "## 2. Trace Context & Error Output",
            "",
            "```text",
            trace_context.strip(),
            "```",
            "",
            "---",
            "",
            "## 3. Affected Files",
            "",
        ]
        for f in affected_files:
            content_lines.append(f"- `{Path(f).as_posix()}`")

        content_lines.extend([
            "",
            "---",
            "",
            "## 4. Root Cause Analysis",
            "",
            root_cause,
            "",
            "---",
            "",
            "## 5. Workflow Remediation Plan",
            "",
            remediation_plan,
            "",
            "---",
            "",
            "Investigation report filed for Blackrod review. Invariant enforcement remains fail-closed.",
            "",
        ])

        report_path.write_text("\n".join(content_lines), encoding="utf-8")
        return report_path


class NomosContractScanner:
    """Scans and validates YAML contracts across target directories for Council Nomos."""

    def __init__(self, repo_root: Path | str | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else Path.cwd()

    def scan_contracts(
        self,
        target_dir: Path | str,
        *,
        fail_on_defect: bool = False,
        synthetic_defect: dict[str, Any] | None = None,
    ) -> Result[NomosComplianceReceiptV1, Refusal]:
        target = Path(target_dir)
        if not target.is_absolute():
            target = self.repo_root / target

        if not target.exists():
            return Err(Refusal("TARGET_DIR_NOT_FOUND", f"Target directory not found: {target}", _LOCUS))

        findings: list[ContractInspectionFindingV1] = []
        reports_logged: list[str] = []

        # Find all .contract.yaml or .yaml files in target
        contract_files = sorted(
            [p for p in target.rglob("*.contract.yaml") if p.is_file()]
            or [p for p in target.rglob("*.yaml") if p.is_file() and "contract" in p.name]
        )

        for path in contract_files:
            rel_path = str(path.relative_to(self.repo_root)) if path.is_relative_to(self.repo_root) else str(path)
            violations: list[str] = []
            urn: str | None = None
            schema: str | None = None

            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    violations.append("Contract content is not a valid YAML mapping")
                else:
                    urn = (
                        data.get("urn")
                        or data.get("contract_urn")
                        or data.get("contract_id")
                        or data.get("id")
                    )
                    schema = data.get("schema") or data.get("schema_version")

                    if not urn:
                        violations.append("Missing required 'urn' or 'contract_id' field")
                    elif not str(urn).startswith("urn:core:"):
                        violations.append(f"URN '{urn}' does not start with canonical prefix 'urn:core:'")

                    if not schema:
                        violations.append("Missing required 'schema' or 'schema_version' field")

            except Exception as exc:
                violations.append(f"YAML parsing error: {exc}")

            is_valid = len(violations) == 0
            finding = ContractInspectionFindingV1(
                file_path=rel_path,
                urn=urn,
                schema=schema,
                is_valid=is_valid,
                violations=tuple(violations),
            )
            findings.append(finding)

            if not is_valid and fail_on_defect:
                report_path = BlackrodDefectLogger.log_investigation(
                    defect_id=f"contract_defect_{hashlib.sha256(rel_path.encode()).hexdigest()[:8]}",
                    skill_name="nomos-law-compliance-hunter",
                    summary=f"Contract validation failure in {rel_path}",
                    trace_context="\n".join(violations),
                    affected_files=[rel_path],
                    root_cause="Contract definition does not adhere to canonical URN schema or YAML structure.",
                    remediation_plan="Update contract file with canonical urn:core:* identifier and standard schema fields.",
                    repo_root=self.repo_root,
                )
                reports_logged.append(str(report_path))

        # Handle synthetic defect if provided (for testing / verification gates)
        if synthetic_defect is not None:
            synth_file = synthetic_defect.get("file_path", "synthetic_test_contract.contract.yaml")
            synth_err = synthetic_defect.get("error", "Synthetic contract URN boundary violation")
            report_path = BlackrodDefectLogger.log_investigation(
                defect_id=synthetic_defect.get("defect_id", "SYNTH-001"),
                skill_name="nomos-law-compliance-hunter",
                summary=f"Synthetic Defect Investigation: {synth_err}",
                trace_context=f"Simulated boundary defect in {synth_file}:\n{synth_err}",
                affected_files=[synth_file],
                root_cause="Synthetic defect injected to verify Blackrod investigation logging pipeline.",
                remediation_plan="Verify Blackrod investigation report is written and check evidence custody.",
                repo_root=self.repo_root,
            )
            reports_logged.append(str(report_path))
            findings.append(
                ContractInspectionFindingV1(
                    file_path=synth_file,
                    urn="urn:core:synthetic:invalid",
                    schema="core.synthetic.v1",
                    is_valid=False,
                    violations=(synth_err,),
                )
            )

        total = len(findings)
        valid = sum(1 for f in findings if f.is_valid)
        cov = (valid / total * 100.0) if total > 0 else 100.0
        direct_urns = sum(1 for f in findings if f.urn and f.urn.startswith("urn:core:"))
        violations_count = sum(len(f.violations) for f in findings)

        receipt = NomosComplianceReceiptV1(
            target_path=str(target),
            contracts_inspected=total,
            valid_contracts=valid,
            coverage_percentage=round(cov, 2),
            direct_urn_bindings=direct_urns,
            contract_violations=violations_count,
            investigation_reports_logged=tuple(reports_logged),
            findings=tuple(findings),
            authority_effect="None",
            timestamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
        return Ok(receipt)


__all__ = [
    "BlackrodDefectLogger",
    "ContractInspectionFindingV1",
    "NomosComplianceReceiptV1",
    "NomosContractScanner",
]
