"""Dense unified diff telemetry and patch metrics across multi-round critique loops.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import difflib
import hashlib


@dataclass(frozen=True)
class DiffTelemetryRecord:
    """Detailed telemetry record for code changes between candidate rounds."""

    round_index: int
    candidate_id: str
    parent_candidate_id: str
    unified_diff: str
    diff_sha256: str
    added_lines: int
    removed_lines: int
    modified_ratio: float
    token_amortization_score: float


def compute_dense_diff_telemetry(
    round_index: int,
    candidate_id: str,
    parent_candidate_id: str,
    base_code: str,
    new_code: str,
    tokens_billed: int = 0,
) -> DiffTelemetryRecord:
    """Compute unified diff and edit distance metrics between candidate versions."""
    base_lines = base_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            base_lines,
            new_lines,
            fromfile=parent_candidate_id or "base",
            tofile=candidate_id,
        )
    )
    unified_diff = "".join(diff_lines)
    diff_hash = "sha256:" + hashlib.sha256(unified_diff.encode("utf-8")).hexdigest()

    added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    total_base_lines = max(len(base_lines), 1)
    modified_ratio = float(added + removed) / float(total_base_lines)

    # Amortization score: edits achieved per 1000 tokens billed
    if tokens_billed > 0:
        amortization = float(added + removed) / (float(tokens_billed) / 1000.0)
    else:
        amortization = float(added + removed)

    return DiffTelemetryRecord(
        round_index=round_index,
        candidate_id=candidate_id,
        parent_candidate_id=parent_candidate_id,
        unified_diff=unified_diff,
        diff_sha256=diff_hash,
        added_lines=added,
        removed_lines=removed,
        modified_ratio=round(modified_ratio, 4),
        token_amortization_score=round(amortization, 4),
    )
