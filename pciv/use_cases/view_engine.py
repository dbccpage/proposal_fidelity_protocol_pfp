"""Prompt view derivation engine and genome registry.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import threading
from typing import Dict, List, Optional

from ..domain.models import (
    ExecutionOccurrenceV1,
    PromptGenomeV1,
    PromptViewV1,
)


class PromptViewEngineV1:
    """Derives projection views of prompt genomes bound to declared ledger revisions."""

    def derive_view(self, genome: PromptGenomeV1, ledger_revision: int) -> PromptViewV1:
        return PromptViewV1(
            prompt_id=genome.prompt_id,
            ledger_revision=ledger_revision,
            current_custody=genome.birth_custody,
        )


class PromptGenomeRegistryV1:
    """Content-addressed registry managing prompt genomes and occurrences."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._genomes: Dict[str, PromptGenomeV1] = {}
        self._occurrences: Dict[str, ExecutionOccurrenceV1] = {}

    def register_genome(self, genome: PromptGenomeV1) -> None:
        with self._lock:
            self._genomes[genome.prompt_id] = genome

    def get_genome(self, prompt_id: str) -> Optional[PromptGenomeV1]:
        with self._lock:
            return self._genomes.get(prompt_id)

    def record_occurrence(self, occurrence: ExecutionOccurrenceV1) -> None:
        with self._lock:
            self._occurrences[occurrence.occurrence_id] = occurrence

    def record_execution(
        self,
        prompt_id: str,
        session_id: str,
        input_packet_id: str,
        output_packet_id: str,
    ) -> ExecutionOccurrenceV1:
        occ_id = f"occ_{hashlib.sha256(f'{prompt_id}:{session_id}:{input_packet_id}:{output_packet_id}'.encode()).hexdigest()[:16]}"
        occ = ExecutionOccurrenceV1(
            occurrence_id=occ_id,
            prompt_id=prompt_id,
            session_id=session_id,
            input_packet_id=input_packet_id,
            output_packet_id=output_packet_id,
        )
        self.record_occurrence(occ)
        return occ

    def get_occurrences_for_prompt(self, prompt_id: str) -> List[ExecutionOccurrenceV1]:
        with self._lock:
            return [occ for occ in self._occurrences.values() if occ.prompt_id == prompt_id]

    def total_genome_count(self) -> int:
        with self._lock:
            return len(self._genomes)

    def total_occurrence_count(self) -> int:
        with self._lock:
            return len(self._occurrences)


__all__ = [
    "PromptGenomeRegistryV1",
    "PromptViewEngineV1",
]
