"""evidence_receipt.py

Structured EvidenceReceipt and CommandRecord carrier schemas for 1-ary colored
operad morphisms. Supports machine-readable residual obligations, contract
discovery tracking, ranked counterexample strength, and antibody reports.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple


OpenObligationKind = Literal[
    "unverified_claim",
    "unavailable_gate",
    "type_precision_loss",
    "ambiguous_import",
    "missing_oracle",
    "anti_pattern_detected",
    "dirty_worktree",
    "packaging_mismatch",
    "counterexample_not_property_based",
    "architectural_smell",
    "security_or_resource_boundary",
    "escalation_required",
    "invariant_not_reexecutable",
]


@dataclass(frozen=True)
class CommandRecord:
    """Immutable record of an executed command during gate/verification runs."""
    cmd: Tuple[str, ...]
    cwd: str
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str
    duration_s: float

    @classmethod
    def from_execution(
        cls,
        cmd: Sequence[str],
        cwd: str,
        exit_code: int,
        stdout: str | bytes = "",
        stderr: str | bytes = "",
        duration_s: float = 0.0,
    ) -> CommandRecord:
        stdout_bytes = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
        stderr_bytes = stderr.encode("utf-8") if isinstance(stderr, str) else stderr
        return cls(
            cmd=tuple(cmd),
            cwd=str(cwd),
            exit_code=exit_code,
            stdout_sha256=hashlib.sha256(stdout_bytes).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr_bytes).hexdigest(),
            duration_s=round(float(duration_s), 4),
        )


@dataclass(frozen=True)
class EvidenceReceipt:
    """
    Evidence-bearing structured receipt produced by principal developer skills.
    Serves as the machine-readable residual carrier for operadic composition.
    """
    # Environment
    sys_executable: str
    python_version: str
    platform: str
    packaging_root: str
    layout: str                     # "src" | "flat" | ...

    # Provenance
    git_head: Optional[str]
    git_status_dirty: bool

    # Change
    changed_paths: Tuple[str, ...]
    change_sha256: str              # of normalized source or AST

    # Execution
    commands: Tuple[CommandRecord, ...]
    test_counts: Dict[str, int]     # collected/passed/failed/skipped
    coverage_delta: Optional[Dict[str, Any]] = None
    mutation_score: Optional[float] = None

    # Contract & falsifiers
    contract_discovery: str = "docstring_and_types"
    invariants: Tuple[str, ...] = ()
    counterexample_level: str = "concrete"  # "concrete" | "property" | "differential"

    # Antibodies
    antibodies_applied: Tuple[str, ...] = ()
    witnesses_found: Tuple[str, ...] = ()

    # Residual (open obligations)
    residual: Tuple[str, ...] = ()
    unverified_claims: Tuple[str, ...] = ()
    authority_effect: Literal["None"] = "None"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes receipt into a dictionary."""
        data = asdict(self)
        return data

    def to_json(self, indent: int = 2) -> str:
        """Serializes receipt to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def is_clean(self) -> bool:
        """
        True if all gates passed, no open obligations remain, and no kill witnesses found.
        """
        return (
            len(self.residual) == 0
            and len(self.witnesses_found) == 0
            and self.test_counts.get("failed", 0) == 0
        )


def compute_normalized_source_sha256(source: str) -> str:
    """Computes SHA256 over AST-normalized Python source code."""
    try:
        tree = ast.parse(source)
        normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except SyntaxError:
        # Fallback to normalized raw text if syntax error
        cleaned = "\n".join(line.rstrip() for line in source.strip().splitlines())
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
