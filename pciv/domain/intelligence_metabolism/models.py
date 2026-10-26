"""Immutable intelligence records, obstruction episodes and evidence-bound motifs.

AuthorityEffect: None. These values perform no host I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any


@dataclass(frozen=True)
class MinedRecordV1:
    source_id: str
    file_path: str
    file_sha256: str
    offset: int
    record_type: str
    payload: dict[str, Any]
    authority_effect: str = "None"


@dataclass(frozen=True)
class MiningFailureV1:
    """Observable refusal at a specific source file and byte offset."""

    code: str
    message: str
    source_id: str
    file_path: str
    file_sha256: str
    offset: int
    authority_effect: str = "None"


@dataclass(frozen=True)
class ObstructionEpisodeV1:
    run_id: str
    start_step_hash: str
    end_step_hash: str
    phi_1_before: Fraction | str
    phi_1_after: Fraction | str
    gamma_2_before: Fraction | str
    gamma_2_after: Fraction | str
    defect_count_before: int
    defect_count_after: int
    ddc_word: str
    outcome: str
    authority_effect: str = "None"


@dataclass(frozen=True)
class MotifRecordV1:
    motif: str
    n_gram_len: int
    success_count: int
    stall_count: int
    antimorphism_label: str | None = None
    evidence_runs: tuple[str, ...] = ()
    authority_effect: str = "None"
