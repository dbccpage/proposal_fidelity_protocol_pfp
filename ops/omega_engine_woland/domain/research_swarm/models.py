"""Audit findings and census wire records. AuthorityEffect: None."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FindingV1:
    """Individual typed audit finding."""

    category: str  # "CODA", "LGGR", "THREE_ALGOS", "LEXICON", "CLEAN_ARCH"
    severity: str  # "BLOCKER", "MAJOR", "MINOR", "OBSERVATION"
    target_path: str
    line_number: Optional[int]
    description: str
    remediation_advice: str


@dataclass
class SwarmAuditCensusReportV1:
    """Comprehensive census report produced by the swarm audit."""

    timestamp: str
    repo_root: str
    total_files_scanned: int
    findings: List[FindingV1] = field(default_factory=list)
    squad_summaries: Dict[str, Dict[str, int]] = field(default_factory=dict)
    terminal_verdict: str = "OPEN_RESIDUAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "repo_root": self.repo_root,
            "total_files_scanned": self.total_files_scanned,
            "findings": [asdict(f) for f in self.findings],
            "squad_summaries": self.squad_summaries,
            "terminal_verdict": self.terminal_verdict,
        }
