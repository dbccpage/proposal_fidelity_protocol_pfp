"""Pure census coordination and verdict policy over injected squad scans."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from adversary.domain.research_swarm.models import FindingV1, SwarmAuditCensusReportV1
from adversary.domain.research_swarm.ports import AuditSquadPort


class RepoWideCodaLggrAuditor:
    def __init__(self, squads: AuditSquadPort, *, repo_root: Path) -> None:
        self.squads = squads
        self.repo_root = repo_root
        self.findings: List[FindingV1] = []

    def run_full_swarm_audit(self) -> SwarmAuditCensusReportV1:
        """Executes all 5 squad review passes across the monorepo."""
        self.findings = []
        self.squads.files_scanned_count = 0
        # Squad alpha: Rust Sovereign Math
        rust_findings = self.squads.audit_squad_alpha_rust()
        self.findings.extend(rust_findings)

        # Squad beta: Python Operations & Engines
        python_findings = self.squads.audit_squad_beta_python()
        self.findings.extend(python_findings)

        # Squad gamma: Lean 4 Proof Kernels
        lean_findings = self.squads.audit_squad_gamma_lean()
        self.findings.extend(lean_findings)

        # Squad delta: Atlas Literature & Lexicon
        atlas_findings = self.squads.audit_squad_delta_atlas()
        self.findings.extend(atlas_findings)

        # Squad Core: Red Team Red Team & Adversary Reality Gate
        terminal_verdict = self.evaluate_squad_core_terminal()

        # Build Squad Summaries
        squad_summaries = {
            "squad_alpha_rust": self._summarize_findings(rust_findings),
            "squad_beta_python": self._summarize_findings(python_findings),
            "squad_gamma_lean": self._summarize_findings(lean_findings),
            "squad_delta_atlas": self._summarize_findings(atlas_findings),
        }

        report = SwarmAuditCensusReportV1(
            timestamp=datetime.now(timezone.utc).isoformat(),
            repo_root=str(self.repo_root),
            total_files_scanned=self.squads.files_scanned_count,
            findings=self.findings,
            squad_summaries=squad_summaries,
            terminal_verdict=terminal_verdict,
        )

        return report

    def evaluate_squad_core_terminal(self) -> str:
        """Squad Core: Renders the terminal reality verdict based on findings."""
        has_blocker = any(f.severity == "BLOCKER" for f in self.findings)
        has_major = any(f.severity == "MAJOR" for f in self.findings)

        if has_blocker:
            return "REFUSE"
        elif has_major:
            return "OPEN_RESIDUAL"
        else:
            return "PASS_TO_MASTER"

    def _summarize_findings(self, findings: List[FindingV1]) -> Dict[str, int]:
        counts = {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "OBSERVATION": 0}
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def generate_markdown_report(self, report: SwarmAuditCensusReportV1) -> str:
        """Formats the audit census into a diagnostic Markdown report."""
        blockers = [f for f in report.findings if f.severity == "BLOCKER"]
        majors = [f for f in report.findings if f.severity == "MAJOR"]
        minors = [f for f in report.findings if f.severity == "MINOR"]

        md = [
            "# Repo-Wide Swarm Audit Report: CODA, LGGR & The Three Canonical Algorithms",
            "",
            f"**Audit Timestamp:** `{report.timestamp}`  ",
            "**AuthorityEffect:** `None`  ",
            f"**Terminal Reality Verdict:** `{report.terminal_verdict}`  ",
            f"**Total Files Scanned:** `{report.total_files_scanned}`  ",
            f"**Total Findings:** `{len(report.findings)}` (Blockers: {len(blockers)}, Major: {len(majors)}, Minor: {len(minors)})  ",
            "",
            "---",
            "",
            "## 1. Squad Summary Breakdown",
            "",
            "| Squad | Blockers | Major | Minor | Focus Area |",
            "|---|---|---|---|---|",
        ]

        squad_names = [
            (
                "squad_alpha_rust",
                "Squad α (Rust Sovereign Math)",
                "Zero float, exact rational BigRational, FDA grant isolation",
            ),
            (
                "squad_beta_python",
                "Squad β (Python Ops & Swarms)",
                "AdversarySwarm base inheritance, ROP Result monads",
            ),
            (
                "squad_gamma_lean",
                "Squad γ (Lean 4 Proofs)",
                "Axiom honesty, zero sorry, dual witness parity",
            ),
            (
                "squad_delta_atlas",
                "Squad δ (Atlas & Lexicon)",
                "EADC bijections, anti-hallucination nomenclature",
            ),
        ]

        for key, display_name, focus in squad_names:
            s = report.squad_summaries.get(key, {})
            b = s.get("BLOCKER", 0)
            m = s.get("MAJOR", 0)
            mn = s.get("MINOR", 0)
            md.append(f"| **{display_name}** | `{b}` | `{m}` | `{mn}` | {focus} |")

        md.extend(
            [
                "",
                "---",
                "",
                "## 2. Blockers & Critical Obstructions",
                "",
            ]
        )

        if not blockers:
            md.append("✅ **No BLOCKER defects detected across the scanned surface.**\n")
        else:
            for b in blockers:
                loc = f"{b.target_path}:{b.line_number}" if b.line_number else b.target_path
                md.append(f"### 🔴 [{b.category}] `{loc}`")
                md.append(f"- **Finding:** {b.description}")
                md.append(f"- **Remediation:** {b.remediation_advice}\n")

        md.extend(
            [
                "---",
                "",
                "## 3. Major Findings & Residual Invariants",
                "",
            ]
        )

        if not majors:
            md.append("✅ **No MAJOR defects detected.**\n")
        else:
            # Group by category
            by_cat: Dict[str, List[FindingV1]] = {}
            for m in majors:
                by_cat.setdefault(m.category, []).append(m)

            for cat, items in by_cat.items():
                md.append(f"### Category: `{cat}` ({len(items)} items)\n")
                for item in items[:15]:  # Show first 15 for conciseness
                    loc = (
                        f"{item.target_path}:{item.line_number}"
                        if item.line_number
                        else item.target_path
                    )
                    md.append(f"- **`{loc}`**: {item.description}")
                    md.append(f"  *Remediation:* {item.remediation_advice}")
                if len(items) > 15:
                    md.append(f"- *... and {len(items) - 15} more items.*")
                md.append("")

        md.extend(
            [
                "---",
                "",
                "## 4. Claim Discipline Audit",
                "",
                "1. **What It Supports:** Provides an empirical, reproducible baseline census across Rust math crates, Python swarms, Lean 4 proof kernels, and Atlas monographs.",
                "2. **What It Does Not Support:** Does not claim that a clean static scan alone guarantees operational correctness under dynamic runtime conditions without live bout execution.",
                "3. **The Narrowest Defensible Claim:** The scanned packages adhere to the declared static rules with findings localized strictly to the reported source lines and files.",
                "4. **The Next Test Needed:** Execute automated remediation PRs on isolated MAJOR findings.",
            ]
        )

        return "\n".join(md)
