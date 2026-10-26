"""
Operad Budget Gate Service.
===========================

Verifies line count (<=300 lines) and byte size (<=20,480 bytes) budgets
across SKILL.md packages to prevent LLM context bloat.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from omega_engine_operads.domain.operad import (
    EvidenceObservation,
    EvidenceReceipt,
    EvidenceType,
)

MAX_SKILL_LINES = 300
MAX_SKILL_BYTES = 20480


class OperadBudgetService:
    """Service for auditing skill documentation budgets."""

    def audit_skill_file(self, skill_path: Path) -> Dict[str, any]:
        try:
            content = skill_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            num_lines = len(lines)
            num_bytes = len(content.encode("utf-8"))
            passed = num_lines <= MAX_SKILL_LINES and num_bytes <= MAX_SKILL_BYTES
            return {
                "path": str(skill_path),
                "name": skill_path.parent.name,
                "lines": num_lines,
                "bytes": num_bytes,
                "passed": passed,
            }
        except Exception as e:
            return {
                "path": str(skill_path),
                "name": skill_path.parent.name,
                "error": str(e),
                "passed": False,
            }

    def audit_skills_directory(self, skills_dir: Path) -> EvidenceReceipt:
        results = []
        observations = []
        all_passed = True

        for p in skills_dir.rglob("SKILL.md"):
            res = self.audit_skill_file(p)
            results.append(res)
            if not res.get("passed", False):
                all_passed = False
                observations.append(
                    EvidenceObservation(
                        f"budget_breach_{res['name']}",
                        f"{res.get('lines', 0)} lines / {res.get('bytes', 0)} bytes",
                    )
                )

        observations.append(EvidenceObservation("total_skills_audited", len(results)))
        observations.append(EvidenceObservation("all_skills_within_budget", all_passed))

        return EvidenceReceipt(
            receipt_id=f"receipt_budget_audit_{len(results)}_skills",
            evidence_type=EvidenceType.BUDGET_AUDIT,
            passed=all_passed,
            observations=tuple(observations),
            metadata={"skills_dir": str(skills_dir)},
        )
